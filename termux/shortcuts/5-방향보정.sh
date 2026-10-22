#!/data/data/com.termux/files/usr/bin/bash
cd ~/xprapaabot || { echo "~/xprapaabot 폴더가 없어"; exit 1; }
export ANDROID_SERIAL=localhost:5555
adb connect localhost:5555 >/dev/null
echo "15초 안에 게임으로 넘어가. (필드 넓은 곳, 지도 닫고)"
python -m xphero calibrate --delay 15
