"""던전/컨텐츠를 정해진 순서대로 누르는 매크로. config.yaml의 tasks로 정의한다."""
import time


class MacroRunner:
    def __init__(self, dev, vision, log):
        self.dev, self.vision, self.log = dev, vision, log
        self.last_run = {}

    def due(self, tasks, now=None):
        now = now or time.time()
        for t in tasks:
            if not t.get("enabled", True):
                continue
            last = self.last_run.get(t["name"], 0)
            if now - last >= t.get("every_minutes", 60) * 60:
                yield t

    def run(self, task):
        self.log(f"매크로 시작: {task['name']}")
        self.last_run[task["name"]] = time.time()
        for i, step in enumerate(task["steps"]):
            if not self._step(step):
                self.log(f"매크로 중단: {task['name']} step {i + 1} {step}")
                return False
        self.log(f"매크로 완료: {task['name']}")
        return True

    def _step(self, s):
        if "tap" in s:
            self.dev.tap(*s["tap"])
        elif "wait" in s:
            time.sleep(s["wait"])
        elif "drag" in s:
            x0, y0, x1, y1 = s["drag"]
            self.dev.drag(x0, y0, x1, y1, s.get("ms", 400))
        elif "tap_template" in s:  # 화면에서 그림을 찾아 누른다. 못 찾으면 실패
            return self._until(s["tap_template"], s, tap=True)
        elif "wait_template" in s:  # 그림이 보일 때까지 기다린다
            return self._until(s["wait_template"], s, tap=False)
        else:
            raise ValueError(f"알 수 없는 step: {s}")
        time.sleep(s.get("after", 0.6))
        return True

    def _until(self, name, s, tap):
        deadline = time.time() + s.get("timeout", 8)
        thr = s.get("threshold", 0.8)
        while time.time() < deadline:
            score, pos = self.vision.find(self.dev.screencap(), name)
            if score >= thr:
                if tap:
                    self.dev.tap(*pos)
                time.sleep(s.get("after", 0.6))
                return True
            time.sleep(0.7)
        return s.get("optional", False)
