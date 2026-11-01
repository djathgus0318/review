# 사이 · SAI
모바일 3D 소셜 여행 공간. React Three Fiber + Socket.IO.

## 실행
Node.js 22.12 이상. 이 디렉터리에서 `npm ci` 후 두 터미널에서 실행합니다.

- `npm run server`: 실시간 서버, 포트 3001
- `npm run dev`: 웹, 포트 5173 (Socket.IO 요청은 Vite 프록시 사용)
- `npm test`: 서버 입력 검증
- `npm run build`: 프로덕션 클라이언트 생성

입장 전 성별·닉네임·헤어·옷을 선택합니다. 입장 후 터치 조이스틱 또는 WASD/방향키로 이동합니다. 화면 드래그로 시점을 회전합니다. 해운대에서 수영·모래성·모래 파기 동작을 선택할 수 있고 바다에 들어가면 자동으로 수영합니다. 장소 변경 시 해당 장소 사용자만 보입니다. 지형은 장소를 모티브로 만든 절차적 3D 표현이며 실측 복원이 아닙니다.

## 배포
Vercel 프로젝트 Root Directory를 `avatar-world`로 지정합니다. 포함된 vercel.json이 Vite 빌드를 설정합니다.
실시간 서버는 Vercel 함수가 아닌 Render/Railway/Fly 등 지속 실행 Node 서비스에 배포합니다. 서버 루트도 이 디렉터리로 지정하고 `npm ci`, 시작 명령 `npm run server`를 사용합니다. `PORT`는 호스팅 제공 값을 사용합니다.

- 서버 `CLIENT_ORIGIN=https://your-app.vercel.app` (여러 origin은 쉼표로 구분, 와일드카드 사용 안 함)
- Vercel `VITE_REALTIME_URL=https://your-realtime-service.example` 설정 후 재배포
- 서버 `/` JSON의 status=ok 확인, 두 브라우저에서 같은 장소에 입장 후 이동이 서로 보이는지 확인

현재 버전은 메모리 기반 단일 서버입니다. 재시작 시 접속 상태가 초기화됩니다. 로그인·DB·영구 모래성 저장·메시지 채팅은 포함되지 않습니다. 수영/파기/모래성은 캐릭터 동작과 임시 시각 효과입니다. 운영 규모 확장 시 인증, 접속/이벤트 제한, 공유 상태 저장이 필요합니다.

## 대시보드에서 처음 배포하기
1. Render: New → Web Service → GitHub의 djathgus0318/review 연결. 배포용 브랜치를 선택하고 Root Directory는 avatar-world, Build Command는 npm ci --omit=dev, Start Command는 npm run server, Instance Type은 Free로 설정합니다. 서버가 실행되면 실제 https://…onrender.com 주소를 복사합니다.
2. Vercel: Add New → Project → 같은 저장소와 배포용 브랜치를 선택합니다. Root Directory는 avatar-world입니다. Environment Variables에 VITE_REALTIME_URL을 추가하고 Render의 실제 주소(끝 슬래시 없음)를 입력한 후 Deploy합니다. main이 아닌 브랜치는 프로젝트의 Production Branch도 해당 배포용 브랜치로 지정합니다.
3. Render: Environment에 CLIENT_ORIGIN을 추가해 Vercel의 실제 production 주소(https:// 포함, 끝 슬래시 없음)를 입력하고 저장·재배포합니다.
4. Vercel 주소를 휴대폰과 다른 브라우저에서 열어 같은 장소에 입장합니다. 온라인 상태, 서로의 닉네임과 이동이 보이는지 확인합니다.

무료 플랜의 제공 여부·제한은 서비스 대시보드에서 확인하세요. Render 무료 서비스가 휴면 상태이면 첫 접속 때 서버 시작을 기다려야 할 수 있습니다.

## 추가 활동
- 머리 위 이름표, 긴 생머리, 웃음·편안함·놀람 표정 선택을 지원합니다. 다른 사용자에게도 동일한 프로필이 표시됩니다.
- 미륵사지 산책로를 넓혔으며 전망 계단과 상부 전망대를 추가했습니다. “석탑 올라가기”는 가상 전망대로 바로 이동하고, 계단에서도 직접 걸을 수 있습니다. 실제 문화재 출입 안내가 아닌 가상 공간 체험입니다.
- 미륵사지 포장마차의 “음료 마시기” 버튼은 가판대 앞으로 이동해 컵을 드는 동작을 표시합니다.
- 해운대 비치베드 5개 중 비어 있는 베드를 “베드에 눕기”로 선택합니다. 이동 조작을 하면 일어납니다. 베드 선택은 현재 접속 상태를 참고하며 예약·영구 저장 기능은 없습니다.
- 카메라가 캐릭터 위치와 높이를 따라가며 드래그 회전·확대/축소도 가능합니다.

## 카페 테이블
미륵사지 포장마차 앞에 2인용 테이블과 의자 2개가 있습니다. “음료 받기” → 의자 또는 의자 이름 버튼 터치 → “앉기 · 커피 마시기”로 이용합니다. 커피잔은 이동 중에도 유지되며, 앉으면 다리를 굽히고 컵을 들어 마십니다. 조이스틱·방향키 또는 산책 버튼으로 일어납니다. 두 사용자가 같은 의자를 동시에 선택하면 서버가 먼저 선택한 사용자만 허용합니다. 퇴장·연결 종료·장소 이동 시 자리는 비워집니다. 커피와 좌석 상태는 현재 접속 동안만 유지됩니다.

서버 실행 후 `node scripts/cafe-smoke.mjs`로 음료 수령 조건, 좌석 동시 선택, 두 명 착석과 퇴장 처리를 검증할 수 있습니다.
