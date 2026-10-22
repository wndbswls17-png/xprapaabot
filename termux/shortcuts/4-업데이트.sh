#!/data/data/com.termux/files/usr/bin/bash
cd ~/xprapaabot || { echo "~/xprapaabot 폴더가 없어"; exit 1; }
export ANDROID_SERIAL=localhost:5555
git pull
