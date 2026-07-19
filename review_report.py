# -*- coding: utf-8 -*-
"""
매일 아침 리뷰 리포트 메일 발송 스크립트
- 네이버 플레이스: 평점 / 방문자·블로그 리뷰수 (비공식 수집 — 구조 변경 시 수정 필요)
- 네이버 신규 블로그 글: 공식 검색 API (안정적)
- 카카오맵: 평점 / 리뷰수 / 최근 리뷰 (비공식 수집)
- 구글: 공식 Places API (선택)
- 3점 이하 리뷰 → ⚠️ 주의 리뷰로 추출
- 어제 데이터(state.json)와 비교해 변동(+N건) 계산
- AI 요약 (선택, ANTHROPIC_API_KEY 있을 때만)
"""

import json
import os
import re
import smtplib
import sys
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.header import Header

import requests

KST = timezone(timedelta(hours=9))
NOW = datetime.now(KST)
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
DATE_STR = f"{NOW.month}월 {NOW.day}일({WEEKDAYS[NOW.weekday()]})"

STATE_FILE = "state.json"
STORES_FILE = "stores.json"

MOBILE_UA = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    )
}

# ──────────────────────────────────────────────
# 데이터 수집
# ──────────────────────────────────────────────

def fetch_naver_place(place_id):
    """네이버 플레이스 모바일 페이지에서 평점/방문자리뷰/블로그리뷰 수를 추출.
    비공식 방식이라 네이버 구조 변경 시 None 반환될 수 있음."""
    if not place_id:
        return None
    try:
        url = f"https://m.place.naver.com/restaurant/{place_id}/home"
        html = requests.get(url, headers=MOBILE_UA, timeout=15).text

        def grab(*patterns):
            for p in patterns:
                m = re.search(p, html)
                if m:
                    return m.group(1)
            return None

        rating = grab(r'"visitorReviewsScore"\s*:\s*"?([\d.]+)')
        visitor = grab(r'"visitorReviewsTotal"\s*:\s*"?([\d,]+)')
        blog = grab(
            r'"fsasReviews"[^}]*?"total"\s*:\s*(\d+)',
            r'"blogCafeReviewCount"\s*:\s*"?([\d,]+)',
        )
        if rating is None and visitor is None:
            return None
        return {
            "rating": float(rating) if rating else None,
            "visitor_count": int(str(visitor).replace(",", "")) if visitor else None,
            "blog_count": int(str(blog).replace(",", "")) if blog else None,
        }
    except Exception as e:
        print(f"[naver] 수집 실패: {e}")
        return None


def fetch_naver_new_blogs(query, seen_links):
    """네이버 공식 검색 API로 매장 언급 신규 블로그 글 탐지 (안정적)."""
    cid = os.environ.get("NAVER_CLIENT_ID")
    csec = os.environ.get("NAVER_CLIENT_SECRET")
    if not (cid and csec and query):
        return []
    try:
        r = requests.get(
            "https://openapi.naver.com/v1/search/blog.json",
            params={"query": query, "display": 10, "sort": "date"},
            headers={"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": csec},
            timeout=15,
        )
        items = r.json().get("items", [])
        new = []
        for it in items:
            link = it.get("link", "")
            if link and link not in seen_links:
                clean = lambda s: re.sub(r"</?b>|&quot;|&amp;", lambda m: {"&quot;": '"', "&amp;": "&"}.get(m.group(0), ""), s or "")
                d = it.get("postdate", "")
                new.append({
                    "source": "네이버 블로그",
                    "author": clean(it.get("bloggername", "")),
                    "date": f"{d[:4]}.{d[4:6]}.{d[6:]}" if len(d) == 8 else d,
                    "text": clean(it.get("title", "")) + " — " + clean(it.get("description", "")),
                    "link": link,
                })
        return new
    except Exception as e:
        print(f"[naver blog api] 실패: {e}")
        return []


def fetch_kakao_place(place_id):
    """카카오맵 place JSON에서 평점/리뷰수/최근 리뷰 추출 (비공식)."""
    if not place_id:
        return None
    try:
        url = f"https://place.map.kakao.com/main/v/{place_id}"
        r = requests.get(url, headers=MOBILE_UA, timeout=15)
        data = r.json()
        fb = data.get("basicInfo", {}).get("feedback", {})
        scorecnt = fb.get("scorecnt") or 0
        scoresum = fb.get("scoresum") or 0
        rating = round(scoresum / scorecnt, 1) if scorecnt else None
        reviews = []
        for c in (data.get("comment", {}) or {}).get("list", [])[:10]:
            reviews.append({
                "source": "카카오맵",
                "author": c.get("username", ""),
                "date": (c.get("date", "") or "").replace(".", "-"),
                "star": c.get("point"),
                "text": (c.get("contents", "") or "").strip(),
            })
        return {"rating": rating, "count": scorecnt, "reviews": reviews}
    except Exception as e:
        print(f"[kakao] 수집 실패: {e}")
        return None


def fetch_google_place(place_id):
    """구글 공식 Places API (선택). GOOGLE_API_KEY 필요."""
    key = os.environ.get("GOOGLE_API_KEY")
    if not (key and place_id):
        return None
    try:
        r = requests.get(
            "https://maps.googleapis.com/maps/api/place/details/json",
            params={
                "place_id": place_id,
                "fields": "rating,user_ratings_total,reviews",
                "language": "ko",
                "key": key,
            },
            timeout=15,
        )
        res = r.json().get("result", {})
        reviews = []
        for rv in res.get("reviews", [])[:5]:
            reviews.append({
                "source": "구글",
                "author": rv.get("author_name", ""),
                "date": rv.get("relative_time_description", ""),
                "star": rv.get("rating"),
                "text": (rv.get("text", "") or "").strip(),
            })
        return {
            "rating": res.get("rating"),
            "count": res.get("user_ratings_total"),
            "reviews": reviews,
        }
    except Exception as e:
        print(f"[google] 수집 실패: {e}")
        return None


# ──────────────────────────────────────────────
# AI 요약 (선택)
# ──────────────────────────────────────────────

def ai_summary(all_reviews, warn_reviews):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key or not all_reviews:
        return None
    try:
        review_text = "\n".join(
            f"- [{r.get('source')}] {r.get('star', '')}점 {r.get('text', '')[:200]}"
            for r in all_reviews[:30]
        )
        warn_text = "\n".join(
            f"- {r.get('star')}점: {r.get('text', '')[:200]}" for r in warn_reviews
        ) or "없음"
        prompt = (
            "다음은 베이커리 카페의 최근 고객 리뷰입니다.\n\n"
            f"[전체 리뷰]\n{review_text}\n\n[낮은 평점 리뷰]\n{warn_text}\n\n"
            "사장님에게 보낼 아침 리포트용 요약을 한국어로 작성하세요. 형식:\n"
            "1) 전반 분위기 한 줄\n2) 칭찬한 점 (2~3개)\n3) 불만/개선할 점 (1~2개)\n"
            "4) 오늘 실천 제안 (1개, 구체적으로)\n"
            "각 항목은 짧게. 인사말·마크다운 없이 번호 목록만."
        )
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 800,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=60,
        )
        blocks = r.json().get("content", [])
        return "".join(b.get("text", "") for b in blocks if b.get("type") == "text").strip()
    except Exception as e:
        print(f"[ai] 요약 실패: {e}")
        return None


# ──────────────────────────────────────────────
# HTML 메일 생성
# ──────────────────────────────────────────────

def esc(s):
    return (str(s or "")).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def delta_text(cur, prev):
    if cur is None or prev is None:
        return "—"
    d = cur - prev
    if isinstance(d, float):
        d = round(d, 2)
    if d > 0:
        return f'<span style="color:#1a7f37;font-weight:700">▲ +{d}</span>'
    if d < 0:
        return f'<span style="color:#d63a06;font-weight:700">▼ {d}</span>'
    return "—"


def build_html(stores_data, new_reviews, warn_reviews, summary):
    css_table = 'border-collapse:collapse;width:100%;font-size:14px;'
    css_th = 'border:1px solid #ddd;padding:9px 10px;background:#fafafa;font-weight:700;text-align:center;'
    css_td = 'border:1px solid #ddd;padding:9px 10px;text-align:center;'

    parts = [f"""
    <div style="font-family:'Apple SD Gothic Neo','Malgun Gothic',sans-serif;max-width:640px;margin:0 auto;color:#111;">
    <h1 style="font-size:24px;margin:8px 0 6px;">🍞 {DATE_STR} 리뷰 리포트</h1>
    <div style="height:3px;background:#E0450A;margin-bottom:18px;"></div>
    """]

    # 상단 상태 박스
    if warn_reviews:
        parts.append(
            f'<div style="background:#fdecea;border:1px solid #f5b3a3;border-radius:10px;'
            f'padding:14px 16px;font-size:15px;margin-bottom:18px;">'
            f'⚠️ <b>주의가 필요한 리뷰 {len(warn_reviews)}건</b> — 아래 내용을 확인하세요.</div>'
        )
    else:
        parts.append(
            '<div style="background:#e6f6e6;border-radius:10px;padding:14px 16px;'
            'font-size:15px;margin-bottom:18px;">✅ 나쁜 리뷰 없음! 좋은 하루의 시작이에요.</div>'
        )

    # 매장별 표
    for sd in stores_data:
        parts.append(
            f'<div style="background:#3d4147;color:#fff;border-radius:8px;padding:11px 16px;'
            f'font-size:16px;font-weight:800;margin:22px 0 10px;">🏪 {esc(sd["name"])}</div>'
        )
        parts.append(f'<table style="{css_table}"><tr>'
                     f'<th style="{css_th}">플랫폼</th><th style="{css_th}">평점</th>'
                     f'<th style="{css_th}">리뷰 수</th><th style="{css_th}">변화</th></tr>')
        for row in sd["rows"]:
            rating = f'⭐ {row["rating"]}' if row["rating"] is not None else '수집 실패'
            count = f'{row["count"]:,}' if row["count"] is not None else '—'
            parts.append(
                f'<tr><td style="{css_td}">{esc(row["platform"])}</td>'
                f'<td style="{css_td}">{rating}</td>'
                f'<td style="{css_td}">{count}</td>'
                f'<td style="{css_td}">{row["delta"]}</td></tr>'
            )
        parts.append('</table>')

    # 새로 달린 리뷰
    parts.append(f'<h2 style="font-size:17px;margin:26px 0 10px;">💬 새로 달린 리뷰 ({len(new_reviews)}건)</h2>')
    if new_reviews:
        for r in new_reviews:
            star = f' · ⭐{r["star"]}점' if r.get("star") else ""
            link = (f'<div style="margin-top:6px;"><a href="{esc(r["link"])}" '
                    f'style="color:#2b6cb0;font-size:13px;">📝 글 보러가기</a></div>') if r.get("link") else ""
            parts.append(
                f'<div style="border:1px solid #e2e2e2;border-radius:10px;padding:13px 15px;margin-bottom:10px;">'
                f'<div style="font-size:13px;color:#555;margin-bottom:5px;">'
                f'<b>{esc(r["source"])}</b> · {esc(r.get("author",""))} · {esc(r.get("date",""))}{star}</div>'
                f'<div style="font-size:14px;line-height:1.6;">{esc(r["text"][:260])}{"…" if len(r["text"])>260 else ""}</div>'
                f'{link}</div>'
            )
    else:
        parts.append('<div style="color:#777;font-size:14px;">어제 새로 달린 리뷰가 없습니다.</div>')

    # 주의 리뷰
    if warn_reviews:
        inner = ""
        for r in warn_reviews:
            inner += (
                f'<div style="background:#fff;border-radius:8px;padding:11px 13px;margin-top:8px;">'
                f'<b>{esc(r.get("store",""))}</b> · {esc(r["source"])} · ⭐{r["star"]}점 · {esc(r.get("date",""))}<br>'
                f'<span style="font-size:14px;">{esc(r["text"][:300])}</span></div>'
            )
        parts.append(
            f'<div style="background:#fdecea;border:2px solid #e0450a;border-radius:12px;'
            f'padding:14px 16px;margin-top:24px;">'
            f'<b style="font-size:15px;">⚠️ 주의가 필요한 리뷰 {len(warn_reviews)}건</b>{inner}</div>'
        )

    # AI 요약
    if summary:
        parts.append(
            f'<div style="background:#e8f2fb;border-radius:12px;padding:16px 18px;margin-top:20px;'
            f'font-size:14px;line-height:1.75;white-space:pre-wrap;">'
            f'<b>🤖 AI 요약 &amp; 제안</b>\n{esc(summary)}</div>'
        )

    parts.append(
        '<div style="color:#999;font-size:12px;margin:26px 0 10px;">'
        '자동 발송 리포트 · SYMBOLIZE Review Monitor</div></div>'
    )
    return "".join(parts)


# ──────────────────────────────────────────────
# 메일 발송
# ──────────────────────────────────────────────

def send_mail(subject, html):
    sender = os.environ["GMAIL_ADDRESS"]
    password = os.environ["GMAIL_APP_PASSWORD"]
    recipient = os.environ.get("RECIPIENT", sender)

    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = sender
    msg["To"] = recipient

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(sender, password)
        s.sendmail(sender, [recipient], msg.as_string())
    print(f"메일 발송 완료 → {recipient}")


# ──────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────

def send_test_mail():
    """TEST_MODE=1 일 때: 수집 없이 샘플 데이터로 형식 확인용 메일 발송."""
    stores_data = [{
        "name": "애월빵공장 기장점",
        "rows": [
            {"platform": "네이버", "rating": 4.62, "count": 1625,
             "delta": '— <span style="color:#1a7f37;font-weight:700">(리뷰 +2건)</span>'},
            {"platform": "카카오맵", "rating": 4.2, "count": 43, "delta": "—"},
            {"platform": "구글", "rating": 4.6, "count": 32, "delta": "—"},
        ],
    }]
    new_reviews = [
        {"source": "네이버 블로그", "author": "빵순이", "date": "2026.07.18",
         "text": "기장 연화리 오션뷰 카페 애월빵공장 다녀왔어요. 국내산 쌀가루 빵이라 속이 편하고, 창밖 바다뷰가 진짜 제주 느낌...",
         "link": "https://blog.naver.com"},
        {"source": "카카오맵", "author": "김**", "date": "2026-07-18", "star": 2,
         "text": "웨이팅이 너무 길고 빵이 차갑게 나왔어요", "store": "애월빵공장 기장점"},
    ]
    warn_reviews = [new_reviews[1]]
    summary = ("1) 전반적으로 뷰와 빵 맛 칭찬이 많은 좋은 분위기예요.\n"
               "2) 칭찬한 점\n- 오션뷰, 쌀빵의 편안함, 한라봉 메뉴\n"
               "3) 불만/개선할 점\n- 주말 웨이팅이 길다는 언급\n"
               "4) 오늘 실천 제안\n- 입구에 예상 대기시간 안내판을 두세요.")
    html = build_html(stores_data, new_reviews, warn_reviews, summary)
    send_mail(f"🍞 [테스트] {DATE_STR} 리뷰 리포트 — 형식 확인용", html)


def main():
    if os.environ.get("TEST_MODE") == "1":
        send_test_mail()
        return

    with open(STORES_FILE, encoding="utf-8") as f:
        stores = json.load(f)

    state = {"stores": {}, "seen_blog_links": []}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding="utf-8") as f:
            state = json.load(f)

    stores_data, new_reviews, warn_reviews, all_reviews = [], [], [], []
    seen_links = set(state.get("seen_blog_links", []))

    for store in stores:
        name = store["name"]
        prev = state["stores"].get(name, {})
        rows = []

        # 네이버
        nv = fetch_naver_place(store.get("naver_place_id"))
        pnv = prev.get("naver") or {}
        nv_total = None
        if nv:
            nv_total = (nv["visitor_count"] or 0) + (nv["blog_count"] or 0)
            p_total = (pnv.get("visitor_count") or 0) + (pnv.get("blog_count") or 0) if pnv else None
            d = delta_text(nv_total, p_total)
            if p_total is not None and nv_total - p_total > 0:
                d = f'— <span style="color:#1a7f37;font-weight:700">(리뷰 +{nv_total - p_total}건)</span>'
            rows.append({"platform": "네이버", "rating": nv["rating"], "count": nv_total, "delta": d})
        else:
            rows.append({"platform": "네이버", "rating": None, "count": None, "delta": "—"})

        # 카카오맵
        kk = fetch_kakao_place(store.get("kakao_place_id"))
        pkk = prev.get("kakao") or {}
        if kk:
            rows.append({"platform": "카카오맵", "rating": kk["rating"], "count": kk["count"],
                         "delta": delta_text(kk["count"], pkk.get("count"))})
            prev_texts = {r.get("text") for r in pkk.get("reviews", [])}
            for r in kk["reviews"]:
                r["store"] = name
                all_reviews.append(r)
                if r["text"] and r["text"] not in prev_texts:
                    new_reviews.append(r)
                if r.get("star") is not None and r["star"] <= 3 and r["text"]:
                    if r["text"] not in prev_texts:
                        warn_reviews.append(r)
        else:
            rows.append({"platform": "카카오맵", "rating": None, "count": None, "delta": "—"})

        # 구글
        gg = fetch_google_place(store.get("google_place_id"))
        pgg = prev.get("google") or {}
        if gg:
            rows.append({"platform": "구글", "rating": gg["rating"], "count": gg["count"],
                         "delta": delta_text(gg["count"], pgg.get("count"))})
            prev_texts = {r.get("text") for r in pgg.get("reviews", [])}
            for r in gg["reviews"]:
                r["store"] = name
                all_reviews.append(r)
                if r["text"] and r["text"] not in prev_texts:
                    new_reviews.append(r)
                if r.get("star") is not None and r["star"] <= 3 and r["text"]:
                    if r["text"] not in prev_texts:
                        warn_reviews.append(r)

        # 신규 블로그 글 (공식 API)
        blogs = fetch_naver_new_blogs(store.get("blog_query"), seen_links)
        for b in blogs:
            b["store"] = name
            new_reviews.append(b)
            seen_links.add(b["link"])

        stores_data.append({"name": name, "rows": rows})
        state["stores"][name] = {"naver": nv, "kakao": kk, "google": gg}

    state["seen_blog_links"] = list(seen_links)[-500:]

    summary = ai_summary(all_reviews, warn_reviews)
    html = build_html(stores_data, new_reviews, warn_reviews, summary)

    if warn_reviews:
        tail = f"⚠️ 주의 리뷰 {len(warn_reviews)}건"
    elif new_reviews:
        tail = f"새 리뷰 {len(new_reviews)}건"
    else:
        tail = "새 리뷰 없음"
    subject = f"🍞 {DATE_STR} 리뷰 리포트 — {tail}"

    send_mail(subject, html)

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    print("state.json 저장 완료")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"실행 실패: {e}")
        sys.exit(1)
