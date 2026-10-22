#!/data/data/com.termux/files/usr/bin/bash
# Termux에서 한 번만 실행: bash termux/setup.sh
set -e
cd "$(dirname "$0")/.."

echo "== 1/3 패키지 설치 =="
pkg update -y
pkg install -y python android-tools git termux-api

echo "== 2/3 파이썬 라이브러리 (OpenCV 는 pkg 로 설치하는 게 제일 잘 됨) =="
pkg install -y python-numpy opencv-python 2>/dev/null || {
  echo "!! pkg 로 opencv 설치 실패. 'pkg install tur-repo' 후 다시 시도하거나 README(TERMUX.md) 문제 해결 참고"
  exit 1
}
pip install pyyaml 2>/dev/null || pkg install -y python-pyyaml

echo "== 3/3 확인 =="
python -c "import cv2, numpy, yaml; print('python 라이브러리 OK, opencv', cv2.__version__)"
adb version | head -1
echo
echo "다음: TERMUX.md 의 '무선 디버깅 연결' 단계로 가."
