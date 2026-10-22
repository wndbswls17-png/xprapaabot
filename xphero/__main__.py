import argparse
import subprocess
import time
from pathlib import Path

import cv2
import yaml

from .bot import Bot, log
from .device import Device
from .vision import Vision, load_frame, normalize

ROOT = Path(__file__).resolve().parent.parent


def load_cfg(path):
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def main():
    ap = argparse.ArgumentParser(prog="xphero")
    ap.add_argument("-c", "--config", default=str(ROOT / "config.yaml"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="봇 실행")
    r.add_argument("--dry-run", action="store_true")
    r.add_argument("--delay", type=int, default=0, help="시작 전 대기 초 (그 사이 게임 화면으로 전환)")
    p = sub.add_parser("pair", help="무선 디버깅 페어링: pair IP:포트 코드")
    p.add_argument("addr"), p.add_argument("code")
    sub.add_parser("connect", help="무선 디버깅 연결: connect IP:포트").add_argument("addr")
    sub.add_parser("shot", help="폰 화면을 shots/ 에 저장").add_argument("name", nargs="?", default="shot")
    sub.add_parser("where", help="폰 지도에서 내 점/집 좌표를 실시간 출력 (경로 좌표 잡을 때)")
    sub.add_parser("calibrate", help="지도 열어 둔 상태에서 걷기 방향 보정")
    p = sub.add_parser("check", help="저장된 스크린샷으로 인식 결과 확인")
    p.add_argument("image")
    p = sub.add_parser("crop", help="스크린샷에서 템플릿 잘라 저장 (좌표는 1440x3120 기준)")
    p.add_argument("image"), p.add_argument("name")
    p.add_argument("box", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    a = ap.parse_args()
    if a.cmd in ("pair", "connect"):
        args = ["adb", a.cmd, a.addr] + ([a.code] if a.cmd == "pair" else [])
        raise SystemExit(subprocess.call(args))
    cfg = load_cfg(a.config)
    vision = Vision(ROOT / "templates")

    if a.cmd == "check":
        bot = Bot(cfg, Device(dry_run=True), vision)
        fr = load_frame(a.image)
        d = cfg["detect"]
        print("가방 가득(MAX):", bot.bag_full(fr), vision.find(fr, "bag_max", d["bag_roi"])[0])
        print("마을 여부     :", bot.in_town(fr),
              vision.find(fr, "home_arrow", d["home_icon_roi"], white=True)[0])
    elif a.cmd in ("where", "calibrate"):
        dev = Device(cfg.get("serial"), jitter=cfg["walk"].get("jitter", 8))
        bot = Bot(cfg, dev, vision)
        if a.cmd == "calibrate":
            bot.nav.open()
            bot.nav.calibrate()
        else:
            print("지도를 열고 직접 걸어다니면서 좌표를 읽어. Ctrl+C로 종료")
            try:
                while True:
                    dot, house = bot.nav.locate(dev.screencap())
                    print(f"내 점={dot}  집={house}", flush=True)
                    time.sleep(0.7)
            except KeyboardInterrupt:
                pass
    elif a.cmd == "crop":
        x0, y0, x1, y1 = a.box
        out = ROOT / "templates" / f"{a.name}.png"
        cv2.imwrite(str(out), load_frame(a.image)[y0:y1, x0:x1])
        print("저장:", out)
    elif a.cmd == "shot":
        dev = Device(cfg.get("serial"))
        out = ROOT / "shots" / f"{a.name}.png"
        cv2.imwrite(str(out), dev.screencap())
        print("저장:", out)
    else:
        dev = Device(cfg.get("serial"), dry_run=a.dry_run, jitter=cfg["walk"].get("jitter", 8))
        try:
            if a.delay:
                log(f"{a.delay}초 뒤 시작. 지금 게임 화면(전체 화면, 마을)으로 전환해.")
                time.sleep(a.delay)
            Bot(cfg, dev, vision).run()
        except KeyboardInterrupt:
            log("중지")


main()
