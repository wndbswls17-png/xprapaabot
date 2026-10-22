"""ADB로 폰 화면을 읽고 조작한다. 입력 좌표는 모두 기준 해상도(1440x3120) 기준."""
import random
import subprocess
import time

from . import imaging
from .vision import REF_W, normalize


class Device:
    def __init__(self, serial=None, dry_run=False, jitter=8):
        self.base = ["adb"] + (["-s", serial] if serial else [])
        self.dry = dry_run
        self.jitter = jitter
        self.scale = 1.0
        if not dry_run:
            self._detect_size()

    def _run(self, *args, binary=False, timeout=15):
        out = subprocess.run(self.base + list(args), capture_output=True, timeout=timeout)
        if out.returncode != 0:
            raise RuntimeError(f"adb 실패: {' '.join(args)}\n{out.stderr.decode(errors='ignore')}")
        return out.stdout if binary else out.stdout.decode(errors="ignore")

    def _detect_size(self):
        w = int(self._run("shell", "wm", "size").split()[-1].split("x")[0])
        self.scale = w / REF_W

    def _px(self, v):
        return int(round(v * self.scale))

    def _j(self, v):
        return v + random.randint(-self.jitter, self.jitter)

    def screencap(self):
        png = self._run("exec-out", "screencap", "-p", binary=True, timeout=20)
        try:
            return normalize(imaging.decode(png))
        except Exception as e:
            raise RuntimeError(f"스크린샷 디코딩 실패: {e}")

    def tap(self, x, y):
        x, y = self._j(x), self._j(y)
        if self.dry:
            print(f"[dry] tap {x},{y}")
            return
        self._run("shell", "input", "tap", str(self._px(x)), str(self._px(y)))

    def drag(self, x0, y0, x1, y1, ms):
        if self.dry:
            print(f"[dry] drag {x0},{y0}->{x1},{y1} {ms}ms")
            time.sleep(ms / 1000)
            return
        a = [self._px(v) for v in (x0, y0, x1, y1)]
        self._run("shell", "input", "swipe", *map(str, a), str(ms), timeout=ms / 1000 + 10)

    def foreground_package(self):
        out = self._run("shell", "dumpsys", "window")
        for line in out.splitlines():
            if "mCurrentFocus" in line:
                return line
        return ""

    def launch(self, package):
        self._run("shell", "monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1")
