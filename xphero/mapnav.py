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

    # ---- 경로 기록 (사람이 직접 걸은 길을 저장) ----
    def record(self, seconds, interval=0.8, timed=False):
        """지도를 열고 seconds 동안 내 점 위치를 모은다. [(x,y), ...] (timed면 (x,y,초))"""
        self.open()
        pts, t0 = [], time.time()
        while time.time() - t0 < seconds:
            dot, _ = self.locate(self.dev.screencap(), house=False)
            if dot:
                pts.append((dot[0], dot[1], time.time() - t0) if timed else dot)
            time.sleep(interval)
        return pts


def simplify(pts, eps=25):
    """Ramer-Douglas-Peucker: 직선에 가까운 점들을 솎아 꺾이는 지점만 남긴다."""
    if len(pts) < 3:
        return list(pts)
    (x0, y0), (x1, y1) = pts[0], pts[-1]
    dx, dy = x1 - x0, y1 - y0
    norm = math.hypot(dx, dy) or 1.0
    idx, dmax = 0, 0.0
    for i in range(1, len(pts) - 1):
        d = abs(dy * (pts[i][0] - x0) - dx * (pts[i][1] - y0)) / norm if norm > 1 else math.hypot(pts[i][0] - x0, pts[i][1] - y0)
        if d > dmax:
            idx, dmax = i, d
    if dmax <= eps:
        return [pts[0], pts[-1]]
    return simplify(pts[: idx + 1], eps)[:-1] + simplify(pts[idx:], eps)


def split_route(timed, still_px=12, still_s=6, moved_px=40):
    """한 번에 걸은 경로를 '멈춘 지점'에서 (가는 길, 순찰 길)로 나눈다. 못 찾으면 None.

    출발점을 벗어난 뒤 처음으로 still_s초 이상 제자리(still_px 이내)에 있던 곳이 경계다.
    """
    pts = [(x, y) for x, y, _ in timed]
    start = next((i for i, p in enumerate(pts) if math.hypot(p[0] - pts[0][0], p[1] - pts[0][1]) > moved_px), None)
    if start is None:
        return None
    for i in range(start, len(timed)):
        j = i
        while j + 1 < len(timed) and math.hypot(pts[j + 1][0] - pts[i][0], pts[j + 1][1] - pts[i][1]) <= still_px:
            j += 1
        if timed[j][2] - timed[i][2] >= still_s:
            return pts[: i + 1], pts[j:]
    return None
