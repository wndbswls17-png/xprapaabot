#!/data/data/com.termux/files/usr/bin/bash
# Termux에서 한 번만 실행: bash termux/setup.sh
set -e
cd "$(dirname "$0")/.."

echo "== 1/3 패키지 업데이트 =="
pkg update -y
pkg upgrade -y

echo "== 2/3 프로그램 설치 (OpenCV 는 필요 없음) =="
pkg install -y python python-numpy python-pillow android-tools git
pip install pyyaml

echo "== 3/3 확인 =="
python -c "import numpy, PIL, yaml; print('python 라이브러리 OK')"
adb version | head -1
echo
echo "설치 끝. 다음 단계는 채팅에서 알려줄게."
