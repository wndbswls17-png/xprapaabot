#!/data/data/com.termux/files/usr/bin/bash
cd ~/xprapaabot || { echo "~/xprapaabot 폴더가 없어"; exit 1; }
export ANDROID_SERIAL=localhost:5555
if pkill -INT -f "xphero run"; then echo "봇 멈춤"; else echo "돌고 있는 봇 없음"; fi
termux-wake-unlock
