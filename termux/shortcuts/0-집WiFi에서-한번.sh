#!/data/data/com.termux/files/usr/bin/bash
# 집 Wi-Fi + 무선 디버깅으로 연결된 상태에서 한 번 실행. 재부팅 전까지 Wi-Fi 없이도 localhost:5555 로 접속된다.
cd ~/xprapaabot || exit 1
echo "== 지금 연결된 기기 =="
adb devices
echo "== 고정 포트(5555) 모드로 전환 =="
adb tcpip 5555 || { echo "!! 실패. 먼저 무선 디버깅으로 connect 해둬야 해."; exit 1; }
sleep 3
adb connect localhost:5555
sleep 1
adb devices
echo
echo "위에 'localhost:5555  device' 가 보이면 성공."
echo "폰에 '디버깅 허용' 팝업이 뜨면 '항상 허용' 체크 후 허용하고 '1-연결' 버튼을 눌러."
