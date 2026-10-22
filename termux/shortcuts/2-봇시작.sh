#!/data/data/com.termux/files/usr/bin/bash
cd ~/xprapaabot || { echo "~/xprapaabot 폴더가 없어"; exit 1; }
export ANDROID_SERIAL=localhost:5555
termux-wake-lock
adb connect localhost:5555 >/dev/null
mkdir -p shots
echo "15초 안에 게임으로 넘어가. (사냥 자리에 서서, 지도 닫고)"
python -m xphero run --delay 15 2>&1 | tee -a shots/run.log
