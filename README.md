# 🍞 매일 아침 8시 리뷰 리포트 — 설치 가이드

애월빵공장 기장점의 네이버/카카오맵/구글 평점·리뷰수·신규 리뷰를 매일 수집해서,
변동(+N건)과 ⚠️3점 이하 주의 리뷰를 정리한 리포트 메일을 **매일 아침 8시**에 자동 발송합니다.

서버 없이 GitHub Actions(무료)로 돌아갑니다. 한 번만 세팅하면 끝이에요.

---

## 준비물 (모두 무료)

| 준비물 | 용도 | 소요시간 |
|---|---|---|
| 지메일 앱 비밀번호 | 메일 발송 | 3분 |
| GitHub 계정 | 매일 자동 실행 | 5분 |
| 네이버 개발자 API 키 | 신규 블로그 글 탐지 | 5분 |
| (선택) 구글 Places API 키 | 구글 평점·리뷰 | 10분 |
| (선택) Anthropic API 키 | AI 요약 & 제안 | 3분 |

---

## STEP 1. 지메일 앱 비밀번호 만들기

1. https://myaccount.google.com/security 접속
2. **2단계 인증**이 꺼져 있으면 먼저 켜기
3. 검색창에 "앱 비밀번호" 검색 → 앱 비밀번호 생성
4. 이름은 아무거나 (예: 리뷰리포트) → **16자리 비밀번호**가 나오면 복사해두기

## STEP 2. 네이버 API 키 만들기 (신규 블로그 글 탐지용)

1. https://developers.naver.com/apps 접속 → 네이버 로그인
2. **애플리케이션 등록** 클릭
3. 이름: 리뷰리포트 / 사용 API: **검색** 선택 / 환경: WEB, URL은 `http://localhost`
4. 등록하면 **Client ID**와 **Client Secret**이 나옴 → 복사해두기

## STEP 3. 플레이스 ID 찾기

**네이버 플레이스 ID**
1. 네이버지도에서 "애월빵공장 기장" 검색 → 매장 클릭
2. PC 브라우저 주소창을 보면 `map.naver.com/p/entry/place/1234567890` 형태
3. 숫자 부분(`1234567890`)이 플레이스 ID

**카카오맵 ID**
1. 카카오맵에서 매장 검색 → 매장 상세 → **공유** 버튼 → URL 복사
2. `place.map.kakao.com/987654321` 형태 → 숫자 부분이 ID

찾은 ID를 `stores.json` 파일에 입력:

```json
[
  {
    "name": "애월빵공장 기장점",
    "naver_place_id": "1234567890",
    "kakao_place_id": "987654321",
    "google_place_id": "",
    "blog_query": "애월빵공장 기장"
  }
]
```

매장을 추가하고 싶으면 중괄호 블록을 복사해서 뒤에 붙이면 됩니다 (쉼표 주의).

## STEP 4. GitHub에 올리기

1. https://github.com 가입 → 우측 상단 **+** → **New repository**
2. 이름: `review-report` / **Private** 선택 → Create
3. **Add file → Upload files**로 이 폴더의 파일 전부 업로드:
   - `review_report.py`
   - `stores.json` (ID 입력한 버전)
   - `README.md`
   - `.github/workflows/daily-report.yml` ← 폴더 구조 그대로!
   
   ⚠️ 웹 업로드 시 `.github` 폴더가 안 만들어지면: **Add file → Create new file** →
   파일명에 `.github/workflows/daily-report.yml` 이라고 치면 폴더가 자동 생성됨.
   그 안에 yml 내용을 붙여넣고 Commit.

## STEP 5. 비밀키 등록

리포지토리에서 **Settings → Secrets and variables → Actions → New repository secret**

아래 항목을 하나씩 등록 (이름은 정확히 동일하게):

| Name | Value |
|---|---|
| `GMAIL_ADDRESS` | 발송용 지메일 주소 |
| `GMAIL_APP_PASSWORD` | STEP 1의 16자리 앱 비밀번호 |
| `RECIPIENT` | 받을 메일 주소 (여러 명이면 일단 대표 1개) |
| `NAVER_CLIENT_ID` | STEP 2의 Client ID |
| `NAVER_CLIENT_SECRET` | STEP 2의 Client Secret |
| `GOOGLE_API_KEY` | (선택) 구글 API 키 — 없으면 등록 안 해도 됨 |
| `ANTHROPIC_API_KEY` | (선택) AI 요약용 — 없으면 등록 안 해도 됨 |

## STEP 6. 테스트 실행

1. 리포지토리 상단 **Actions** 탭 → "매일 아침 리뷰 리포트" 클릭
2. **Run workflow** 버튼 → Run
3. 1~2분 뒤 초록 체크가 뜨고 메일이 도착하면 성공 🎉
4. 이후로는 매일 아침 8시에 자동 발송됩니다

> 첫 실행은 비교할 어제 데이터가 없어서 변화 칸이 "—"로 나옵니다.
> 둘째 날부터 "(리뷰 +2건)" 식으로 표시돼요.

---

## 자주 묻는 것

**Q. 네이버 칸이 "수집 실패"로 나와요**
네이버는 공식 리뷰 API가 없어서 비공식 방식으로 수집합니다. 네이버가 페이지 구조를
바꾸면 깨질 수 있어요. 그럴 땐 Actions 로그를 복사해서 클로드에게 보여주면 수정해드립니다.
블로그 신규 글 탐지는 공식 API라 계속 잘 돌아갑니다.

**Q. 발송 시간을 바꾸고 싶어요**
`daily-report.yml`의 `cron: "0 23 * * *"`를 수정하세요. UTC 기준이라 한국시간 −9시간입니다.
(예: 아침 7시 발송 → `"0 22 * * *"`)

**Q. 3점 '미만'만 잡고 싶어요 (3점은 제외)**
`review_report.py`에서 `r["star"] <= 3`을 `r["star"] < 3`으로 두 군데 바꾸면 됩니다.

**Q. 메일이 안 와요**
1. Actions 로그에서 빨간 X 확인 → 에러 메시지 확인
2. GMAIL_APP_PASSWORD가 일반 비밀번호가 아닌 **앱 비밀번호**인지 확인
3. 스팸함 확인
