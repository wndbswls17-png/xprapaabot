#!/data/data/com.termux/files/usr/bin/bash
# Termux:Widget 홈 화면 버튼 설치: bash termux/install-shortcuts.sh
cd "$(dirname "$0")"
mkdir -p ~/.shortcuts && chmod 700 ~/.shortcuts
rm -f ~/.shortcuts/[0-9]-*.sh
cp shortcuts/*.sh ~/.shortcuts/ && chmod +x ~/.shortcuts/*.sh
echo "버튼 설치 완료:"; ls ~/.shortcuts
echo "홈 화면을 길게 눌러 위젯 -> Termux:Widget 을 추가해. (이미 있으면 위젯의 새로고침 버튼)"
