# Steam Patchnotes into Discord Webhooks

상시 구동 서버 없이, GitHub Actions cron으로 30분마다 Steam RSS를 확인해서
새 글이 있으면 등록해둔 디스코드 웹훅으로 임베드를 보내는 방식.

## 1. 디스코드 웹훅 만들기
서버 설정 -> 연동 -> 웹훅 -> 새 웹훅 -> 알림 받을 채널 지정 -> 웹훅 URL 복사
(채널 여러 개에 보내고 싶으면 채널마다 웹훅을 하나씩 만들면 됨)

## 2. 코드를 깃헙 리포에 올리기
.github/workflows/.yml과 main.py만 있으면 됨.
아무 토큰도 공개되지 않기 때문에 퍼블릭도 상관없음.

## 3. 시크릿, 변수 등록
리포의 **Settings → Secrets and variables → Actions**에서:

- **Secrets 탭**
  - `DISCORD_WEBHOOKS`: 웹훅 URL. 여러 개면 공백없는 쉼표(,)로 구분
  - 예) `https://discord.com/api/webhooks/aaa,https://discord.com/api/webhooks/bbb`
- **Variables 탭** (선택, 비밀값 아니라 그냥 설정값)
  - `STEAM_APPID`: 감시할 게임의 appid. 안 넣으면 오류반환
  - `COLOR`: 0xFFFFFF 포맷으로 임베드 색깔을 정할 수 있음.
  - `EMBED_DESC_LIMIT`: 최대 4000자 까지 설정가능.

## 4. 확인
**Actions 탭 -> patchnote-to-discord -> Run workflow**로 한 번 수동 실행해보기.
- 마지막으로 본 글(`last_guid.txt`)은 리포에 커밋되지 않고 **GitHub Actions 캐시**에 저장됨
  (Settings -> Actions -> Caches 에서 `last-guid-...` 항목으로 확인 가능)
- 처음 실행하면 과거 글은 보내지 않고 캐시의 기준점만 기록됨
- 그다음 새 글이 올라오고 나서 실행되는 회차부터 실제로 디스코드에 전송됨
- 캐시라서 별도 쓰기 권한 설정이나 커밋이 필요 없음. 다만 캐시는 7일간 안 쓰이면 자동 삭제되므로 cron 간격을 7일 이상으로 하는 것은 어려움.

## 5. 그외
- 게임의 appid는 스토어 URL에서 `store.steampowered.com/app/{appid}/`와 같은 형식으로 확인가능.
- 여러 게임을 동시에 감시하고 싶으면 워크플로우 파일을 복사해서 env 부분의 `STEAM_APPID`와 `uses: actions/cache@v4`부분의 `last_guid.txt`를 `last_guid_다른게임.txt`등으로 다르게 지정하여 새로운 워크플로우 액션으로 실행하면 됨.
