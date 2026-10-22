"""마을 -> 사냥터 순찰 -> 가방 가득 -> 걸어서 귀환 -> 입금 -> 반복."""
import time
from datetime import datetime
from pathlib import Path

from . import imaging
from .macro import MacroRunner
from .mapnav import MapNav
from .walker import Walker

ROOT = Path(__file__).resolve().parent.parent


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


class Bot:
    def __init__(self, cfg, dev, vision):
        self.cfg, self.dev, self.vision = cfg, dev, vision
        w = cfg["walk"]
        self.walker = Walker(dev, w["origin"], w["radius"])
        self.nav = MapNav(dev, vision, self.walker, cfg, log, ROOT)
        self.macro = MacroRunner(dev, vision, log)
        self.trips = 0

    # ---- 화면 판정 ----
    def bag_full(self, frame):
        d = self.cfg["detect"]
        return self.vision.has(frame, "bag_max", d["bag_full_threshold"], d["bag_roi"])

    def in_town(self, frame):
        # 필드에서는 캐릭터 옆에 집 아이콘이 뜨고, 마을에서는 사라진다. (지도를 닫은 화면에서만 유효)
        d = self.cfg["detect"]
        return not self.vision.has(frame, "home_arrow", d["home_icon_threshold"], d["home_icon_roi"], white=True)

    def _confirmed(self, check, need=2):
        """check(frame)이 연속 need번 True일 때만 True. 한 프레임 오인식을 거른다."""
        hits = 0

        def f(frame):
            nonlocal hits
            hits = hits + 1 if check(frame) else 0
            return hits >= need

        return f

    def _debug_shot(self, tag):
        path = ROOT / "shots" / f"debug_{tag}_{datetime.now():%H%M%S}.png"
        imaging.save(path, self.dev.screencap())
        log(f"디버그 스크린샷 저장: {path}")

    # ---- 단계 ----
    def town(self):
        """점선 원 안에서 입금되길 기다린 뒤, 사냥터 첫 지점으로 간다. 지도는 닫힌 상태에서 시작."""
        t = self.cfg["town"]
        self.nav.open()
        res = self.nav.goto(t["circle"], t.get("circle_tol", self.cfg["map"]["arrive_px"]))
        self.nav.close()
        log(f"마을 원 이동: {res}")
        for _ in range(t["deposit_retries"]):
            time.sleep(t["deposit_wait_seconds"])
            if not self.bag_full(self.dev.screencap()):
                break
            log("아직 가방이 가득 참, 더 기다림")
        else:
            self._debug_shot("deposit_fail")
            raise RuntimeError("입금이 안 돼. town.circle 좌표(점선 원 위치)를 확인해줘.")
        for task in self.macro.due(self.cfg.get("tasks", [])):
            self.macro.run(task)

    def hunt(self):
        self.trips += 1
        log(f"사냥 시작 (#{self.trips})")
        if not self.cfg["route"]["patrol"]:
            raise RuntimeError("config.yaml 의 route.patrol 이 비어 있어. `python -m xphero where` 로 좌표를 잡아 채워줘.")
        full = self._confirmed(self.bag_full)
        self.nav.open()
        while True:
            for wp in self.cfg["route"]["patrol"]:
                res = self.nav.goto(wp, stop=full)
                if res == "stop":
                    log("가방 가득 참 -> 귀환")
                    return
                if res == "lost":
                    self._debug_shot("lost")
                    raise RuntimeError("지도에서 내 점을 놓쳤어. 지도가 열려 있는지 확인해줘.")

    def go_home(self):
        """지도에서 집 아이콘 위치로 간다. 지도는 열린 상태에서 시작."""
        for attempt in range(1, 4):
            _, house = self.nav.locate(self.dev.screencap())
            if not house:
                self._debug_shot("no_house")
                raise RuntimeError("지도에서 집 아이콘을 못 찾았어.")
            self.nav.goto(house, self.cfg["town"].get("home_tol", 40))
            self.nav.close()
            if self.in_town(self.dev.screencap()):
                log("마을 도착")
                return
            log(f"집 근처지만 아직 필드 (시도 {attempt}), 지도를 다시 열고 접근")
            self.nav.open()
        self._debug_shot("home_fail")
        raise RuntimeError("집으로 갔는데 마을로 안 들어가져. 점/집 아이콘 좌표를 확인해줘.")

    def run(self):
        if not self.in_town(self.dev.screencap()):
            raise RuntimeError("마을에서 시작해줘.")
        while True:
            self.town()
            self.hunt()
            self.go_home()
