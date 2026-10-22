# xprapaabot (XP Hero 자동 사냥 봇)

XP Hero 자동 사냥 보조 봇. PC에 USB(또는 무선 디버깅)로 연결한 안드로이드 폰을 ADB로 조작한다.

**순환**: 점선 원에서 입금 → (던전 매크로) → 지도 좌표로 순찰 → 가방 `MAX` 감지 → 지도에서 집 아이콘으로 이동 → 마을 감지 → 반복

> 게임 약관상 매크로는 제재 대상일 수 있다. 부계정으로 먼저 돌려볼 것.

## 준비
1. 폰: 설정 → 개발자 옵션 → **USB 디버깅** 켜기, PC에 연결해 허용
2. PC: [platform-tools(adb)](https://developer.android.com/tools/releases/platform-tools) 설치, `adb devices` 에 폰이 보여야 함
3. `pip install -r requirements.txt`

폰 단독으로 돌리려면 **[TERMUX.md](TERMUX.md)** 를 먼저 본다 (PC 없이 가능).

## 처음 세팅 순서
1. 마을에서 `python -m xphero shot` 으로 화면이 잡히는지 확인
2. 지도를 연 채로 `python -m xphero calibrate` — 걷기 방향이 지도에서 어느 쪽인지 폰이 스스로 보정
3. `python -m xphero record patrol --delay 20` 후 게임에서 사냥할 길을 직접 한 바퀴 걷는다 (경로 자동 저장)
4. `config.yaml` 의 `town.circle`, `route.patrol` 에 좌표를 적는다
5. `python -m xphero run --dry-run` 후 `python -m xphero run` (마을에서 시작)

## 명령
```
python -m xphero check shots/town.jpg      # 저장된 사진으로 인식 확인
python -m xphero crop shots/x.png name X0 Y0 X1 Y1   # 템플릿 자르기 (1440x3120 기준)
```

## 튜닝 (config.yaml)
- `walk.origin/radius`: 조이스틱 드래그 위치. 지도 창(위쪽)과 겹치지 않는 빈 땅이어야 함
- `map.px_per_second`: 1초 걸을 때 지도에서 움직이는 거리. 크게 틀리면 한 번에 너무 길게/짧게 걷는다
- `map.arrive_px`: 도착 판정 거리
- `tasks`: 던전/컨텐츠 매크로 (나중에)

## 동작 원리와 한계
- 가방 가득: 주황색 `MAX` 바 템플릿 매칭 (연속 2프레임 확인)
- 이동: 지도 위 파란 점과 목표 좌표 차이를 보고 조이스틱을 밀고, 1~1.5초마다 점 위치를 다시 읽는 폐루프
- 마을 여부: 지도를 닫았을 때 필드에만 뜨는 집 아이콘이 없으면 마을
- 지도에서 점이 집 아이콘 위에 겹쳐 가려지면 인식이 끊길 수 있다 (실기기 확인 필요)
- 실패하면 `shots/debug_*` 를 남기고 멈춘다
