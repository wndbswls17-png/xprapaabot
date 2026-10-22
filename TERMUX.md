# 폰 단독(Termux)으로 돌리기

PC 없이 폰 안에서 봇과 게임을 같이 돌린다. 봇은 폰 자신에게 **무선 디버깅(adb)** 으로 접속해서 화면을 읽고 조작한다.

> 이 경로는 개발 환경에서 직접 테스트하지 못했다. 막히는 단계의 오류 메시지를 그대로 알려주면 고친다.

## 0. 준비물
- Android 11 이상 (갤럭시 최근 기종 OK)
- **Termux는 F-Droid 버전**을 설치 (구글 플레이 버전은 오래돼서 패키지 설치가 깨진다)
- Wi-Fi 연결 (무선 디버깅은 Wi-Fi가 켜져 있어야 함)

## 1. 설치 (한 번만)
Termux 에 아래 두 줄을 차례로 붙여넣는다:
```
pkg install -y git
git clone https://github.com/wndbswls17-png/xprapaabot && cd xprapaabot && bash termux/setup.sh
```

## 2. 무선 디버깅 연결 (Wi-Fi 바뀌거나 재부팅하면 다시)
1. 폰 설정 → 개발자 옵션 → **무선 디버깅** 켜기
2. **"페어링 코드로 기기 페어링"** 을 누르면 `IP:포트` 와 6자리 코드가 뜬다. (이 창을 띄워 둔 채로)
3. 분할 화면이나 알림창으로 Termux 를 열어 입력:
   ```
   python -m xphero pair 192.168.0.12:37123 123456
   ```
   (페어링 창에 뜬 IP:포트와 코드를 그대로)
4. 페어링 창을 닫고, 무선 디버깅 **메인 화면**에 뜨는 `IP:포트`(페어링 포트와 다름)로 연결:
   ```
   python -m xphero connect 192.168.0.12:40567
   ```
5. 확인: `adb devices` 에 `device` 로 뜨면 성공.

## 3. 배터리 설정 (밤새 돌릴 때 필수)
- 설정 → 애플리케이션 → Termux → 배터리 → **제한 없음**
- 설정 → 배터리 → 백그라운드 사용 제한 → **절전 예외 앱**에 Termux 추가
- Termux 에서 `termux-wake-lock` 실행 (알림창에 Termux 가 상주하며 프로세스를 지켜준다)
- 개발자 옵션 → **충전 중 화면 켜짐 유지** 켜고 충전기 연결, 방해 금지 모드 켜기

## 4. 실행
Termux 에서 명령을 치고 → 홈으로 나가 게임을 **전체 화면 세로**로 켜는 순서다.
```
termux-wake-lock
python -m xphero run --delay 20
```
`--delay 20` 은 시작 전 20초를 기다려 주는 옵션이다. 그 사이에 게임 화면(마을)으로 전환한다.
봇은 폰의 화면을 읽으므로 게임이 계속 전체 화면 전경에 떠 있어야 한다. 중지는 Termux 로 돌아와 Ctrl+C.

## 문제 해결
- `adb: command not found` → `pkg install android-tools`
- `unauthorized`/`failed to connect` → 무선 디버깅을 껐다 켜고 4번(connect)부터 다시. 포트는 켤 때마다 바뀐다
- opencv 설치 실패 → `pkg install tur-repo` 후 `pkg install opencv-python`, 그래도 안 되면 에러 전문을 알려줄 것
- 게임이 꺼지거나 Termux 가 죽음 → 3번 배터리 설정 재확인
