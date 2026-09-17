# Steam 패치노트 → 디스코드 웹훅 (GitHub Actions)

상시 구동 서버 없이, GitHub Actions cron으로 30분마다 Steam RSS를 확인해서
새 글이 있으면 등록해둔 디스코드 웹훅으로 임베드를 보내는 방식.

## 1. 디스코드 웹훅 만들기
서버 설정 → 연동 → 웹훅 → 새 웹훅 → 알림 받을 채널 지정 → 웹훅 URL 복사
(채널 여러 개에 보내고 싶으면 채널마다 웹훅을 하나씩 만들면 됨)

## 2. 이 코드를 GitHub 리포로 올리기
이 폴더 전체를 새 깃허브 리포에 push (퍼블릭이어도 상관없음, 토큰류가 코드에 없음).

## 3. 시크릿 / 변수 등록
리포의 **Settings → Secrets and variables → Actions**에서:

- **Secrets 탭**
  - `DISCORD_WEBHOOKS` : 웹훅 URL. 여러 개면 쉼표(,)로 구분
    예) `https://discord.com/api/webhooks/aaa,https://discord.com/api/webhooks/bbb`
- **Variables 탭** (선택, 비밀값 아니라 그냥 설정값)
  - `STEAM_APPID` : 감시할 게임 appid. 안 넣으면 기본값 1422450

## 4. 확인
**Actions 탭 → Steam 패치노트 -> 디스코드 → Run workflow**로 한 번 수동 실행해보기.
- 마지막으로 본 글(`last_guid.txt`)은 리포에 커밋되지 않고 **GitHub Actions 캐시**에 저장됨
  (Settings → Actions → Caches 에서 `last-guid-...` 항목으로 확인 가능)
- 처음 실행하면 과거 글은 보내지 않고 캐시에 기준점만 기록됨
- 그다음 새 글이 올라오고 나서 실행되는 회차부터 실제로 디스코드에 전송됨
- 캐시라서 별도 쓰기 권한 설정이나 커밋이 필요 없음. 다만 캐시는 7일간 안 쓰이면 자동 삭제되는데,
  이 워크플로우는 30분마다 계속 접근하므로 평소엔 해당 없음

## 5. 다른 게임으로 바꾸려면
Variables의 `STEAM_APPID`만 원하는 게임의 appid로 바꾸면 됨
(스토어 URL `store.steampowered.com/app/{appid}/`에서 확인).
여러 게임을 동시에 감시하고 싶으면 워크플로우 파일을 복사해서
`STEAM_APPID`와 `STATE_FILE`(예: `last_guid_다른게임.txt`)을 다르게 지정하면 됨.

## 참고
- GitHub Actions의 `schedule` cron은 정확히 30분마다 도는 게 아니라 몇 분씩 밀릴 수 있음.
  타이밍이 칼같이 중요하면 이 방식보다 상시구동 봇 쪽이 나음.
- 리포가 60일 이상 완전히 비활성 상태면 GitHub가 scheduled workflow를 자동으로 꺼버릴 수 있음
  (이 워크플로우 자체가 계속 실행/커밋을 하므로 평소엔 해당 없음).
