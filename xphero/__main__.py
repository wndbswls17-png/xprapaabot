import argparse
import json
import subprocess
import time
from pathlib import Path

import yaml

from . import imaging
from .bot import Bot, log
from .mapnav import simplify
from .device import Device
from .vision import Vision, load_frame, normalize

ROOT = Path(__file__).resolve().parent.parent


def load_cfg(path):
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    rj = ROOT / "route.json"  # `record` 명령이 저장한 경로가 config.yaml 값을 덮어쓴다
    if rj.exists():
        saved = json.loads(rj.read_text())
        if "patrol" in saved:
            cfg["route"]["patrol"] = saved["patrol"]
        if "circle" in saved:
            cfg["town"]["circle"] = saved["circle"]
    return cfg


def save_route(**kw):
    rj = ROOT / "route.json"
    saved = json.loads(rj.read_text()) if rj.exists() else {}
    saved.update(kw)
    rj.write_text(json.dumps(saved))


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
    p = sub.add_parser("shot", help="폰 화면을 shots/ 에 저장")
    p.add_argument("name", nargs="?", default="shot")
    p.add_argument("--delay", type=int, default=0)
    p = sub.add_parser("calibrate", help="걷기 방향 보정 (게임 화면에서 지도를 자동으로 연다)")
    p.add_argument("--delay", type=int, default=0)
    p = sub.add_parser("record", help="내가 직접 걷는 길을 기록: record patrol|circle")
    p.add_argument("what", choices=["patrol", "circle"])
    p.add_argument("--seconds", type=int, default=0)
    p.add_argument("--delay", type=int, default=0)
    p = sub.add_parser("check", help="저장된 스크린샷으로 인식 결과 확인")
    p.add_argument("image")
    p = sub.add_parser("crop", help="스크린샷에서 템플릿 잘라 저장 (좌표는 1440x3120 기준)")
    p.add_argument("image"), p.add_argument("name")
    p.add_argument("box", type=int, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    a = ap.parse_args()

    def wait(sec):
        if sec:
            log(f"{sec}초 뒤 시작. 지금 게임 화면(전체 화면)으로 전환해.")
            time.sleep(sec)
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
    elif a.cmd in ("calibrate", "record"):
        dev = Device(cfg.get("serial"), jitter=cfg["walk"].get("jitter", 8))
        bot = Bot(cfg, dev, vision)
        wait(a.delay)
        if a.cmd == "calibrate":
            bot.nav.open()
            bot.nav.calibrate()
            bot.nav.close()
        else:
            secs = a.seconds or (90 if a.what == "patrol" else 6)
            log(f"기록 시작: {secs}초. 지금부터 {'사냥할 길을 한 바퀴 직접 걸어' if a.what == 'patrol' else '점선 원 안에 서 있어'}.")
            pts = bot.nav.record(secs)
            bot.nav.close()
            if len(pts) < 2:
                raise SystemExit("점을 거의 못 읽었어. 지도가 열려 있고 점이 보이는지 확인해줘.")
            if a.what == "circle":
                cx = round(sum(p[0] for p in pts) / len(pts)); cy = round(sum(p[1] for p in pts) / len(pts))
                save_route(circle=[cx, cy])
                log(f"점선 원 위치 저장: {[cx, cy]}  (읽은 점 {len(pts)}개)")
            else:
                wp = [list(p) for p in simplify(pts)]
                save_route(patrol=wp)
                log(f"순찰 경로 저장: 점 {len(pts)}개 -> 꺾이는 지점 {len(wp)}개 {wp}")
    elif a.cmd == "crop":
        x0, y0, x1, y1 = a.box
        out = ROOT / "templates" / f"{a.name}.png"
        imaging.save(out, load_frame(a.image)[y0:y1, x0:x1])
        print("저장:", out)
    elif a.cmd == "shot":
        dev = Device(cfg.get("serial"))
        wait(a.delay)
        out = ROOT / "shots" / f"{a.name}.png"
        imaging.save(out, dev.screencap())
        print("저장:", out)
    else:
        dev = Device(cfg.get("serial"), dry_run=a.dry_run, jitter=cfg["walk"].get("jitter", 8))
        try:
            wait(a.delay)
            Bot(cfg, dev, vision).run()
        except KeyboardInterrupt:
            log("중지")


main()
