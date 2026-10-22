"""지도를 열어 둔 채, 지도 위 내 점(파란 점)을 목표 좌표로 밀어서 이동한다.

좌표는 전부 '지도가 열린 화면'의 기준 해상도(1440x3120) 픽셀 좌표다.
`python -m xphero where` 로 지금 점/집 위치를 읽어서 경로 좌표를 잡는다.
"""
import json
import math
import time

MAP_ROI = (0, 600, 1440, 1700)


class MapNav:
    def __init__(self, dev, vision, walker, cfg, log, root):
        self.dev, self.vision, self.walker, self.log = dev, vision, walker, log
        self.cfg = cfg["map"]
        self.calib_path = root / "calibration.json"
        self.m = None  # 조이스틱 방향 -> 지도 이동 방향 2x2 행렬
        if self.calib_path.exists():
            self.m = json.loads(self.calib_path.read_text())

    # ---- 지도 열고 닫기 / 위치 읽기 ----
    def open(self):
        self.dev.tap(*self.cfg["open_button"])
        time.sleep(1.0)

    def close(self):
        self.dev.tap(*self.cfg["close_button"])
        time.sleep(0.8)

    def locate(self, frame, house=True):
        """(점 좌표 or None, 집 좌표 or None). house=False면 집 탐색을 건너뛴다(더 빠름)."""
        thr = self.cfg["threshold"]
        out = []
        for name in ("map_dot", "map_house") if house else ("map_dot",):
            score, pos = self.vision.find(frame, name, MAP_ROI)
            out.append(pos if score >= thr else None)
        return tuple(out) + (None,) * (2 - len(out))

    # ---- 방향 보정 ----
    def calibrate(self, seconds=1.5):
        """오른쪽/아래로 한 번씩 걸어서 지도 위 점의 이동을 잰다. 지도를 연 상태에서 호출."""
        def dot():
            for _ in range(5):
                d, _h = self.locate(self.dev.screencap(), house=False)
                if d:
                    return d
                time.sleep(0.5)
            raise RuntimeError("지도에서 내 점을 못 찾았어. 지도를 연 상태인지 확인해줘.")

        p0 = dot()
        self.walker.move(1, 0, seconds)
        time.sleep(0.4)
        p1 = dot()
        self.walker.move(0, 1, seconds)
        time.sleep(0.4)
        p2 = dot()
        ex, ey = (p1[0] - p0[0], p1[1] - p0[1]), (p2[0] - p1[0], p2[1] - p1[1])
        if math.hypot(*ex) < 2 or math.hypot(*ey) < 2:
            raise RuntimeError(f"점이 거의 안 움직였어({ex}, {ey}). 걷기 드래그가 먹는지 확인해줘.")
        self.m = [[ex[0], ey[0]], [ex[1], ey[1]]]
        self.calib_path.write_text(json.dumps(self.m))
        self.log(f"보정 완료: 오른쪽 1드래그={ex}, 아래쪽 1드래그={ey}")

    def _joystick_dir(self, vx, vy):
        """원하는 지도 이동 (vx,vy) -> 조이스틱 단위벡터."""
        if not self.m:
            return vx / math.hypot(vx, vy), vy / math.hypot(vx, vy)  # 보정 없으면 화면=지도라고 가정
        (a, b), (c, d) = self.m
        det = a * d - b * c
        ux, uy = (d * vx - b * vy) / det, (-c * vx + a * vy) / det
        n = math.hypot(ux, uy)
        return ux / n, uy / n

    # ---- 이동 ----
    def goto(self, target, tol=None, stop=None, timeout=None):
        """지도 좌표 target 근처(tol px)까지 간다. stop(frame)이 True면 중간에 멈추고 'stop' 반환.
        도착이면 'arrived', 시간 초과/점 분실이면 'lost'."""
        tol = tol or self.cfg["arrive_px"]
        timeout = timeout or self.cfg["goto_timeout_seconds"]
        deadline, lost = time.time() + timeout, 0
        while time.time() < deadline:
            frame = self.dev.screencap()
            if stop and stop(frame):
                return "stop"
            dot, _ = self.locate(frame, house=False)
            if not dot:
                lost += 1
                if lost >= 4:
                    return "lost"
                time.sleep(0.4)
                continue
            lost = 0
            vx, vy = target[0] - dot[0], target[1] - dot[1]
            dist = math.hypot(vx, vy)
            if dist <= tol:
                return "arrived"
            ux, uy = self._joystick_dir(vx, vy)
            # 멀면 길게, 가까우면 짧게
            self.walker.move(ux, uy, min(self.cfg["max_step_seconds"], max(0.4, dist / self.cfg["px_per_second"])))
        return "lost"
