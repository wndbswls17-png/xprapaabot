"""화면 인식. 모든 좌표는 기준 해상도(REF_W x REF_H) 기준이다."""
from pathlib import Path

import cv2
import numpy as np

REF_W, REF_H = 1440, 3120


class Vision:
    def __init__(self, template_dir):
        self.dir = Path(template_dir)
        self._cache = {}

    def template(self, name):
        if name not in self._cache:
            img = cv2.imread(str(self.dir / f"{name}.png"), cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise FileNotFoundError(f"템플릿 없음: {self.dir / (name + '.png')}")
            self._cache[name] = img
        return self._cache[name]

    def find(self, frame, name, roi=None, white=False):
        """(점수, (중심x, 중심y)). roi=(x0,y0,x1,y1)면 그 안에서만 찾는다.

        white=True면 흰색 픽셀만 남겨 비교한다. 배경이 비치는 아이콘용.
        """
        x0, y0, x1, y1 = roi or (0, 0, frame.shape[1], frame.shape[0])
        gray = cv2.cvtColor(frame[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY)
        tpl = self.template(name)
        if white:
            gray = (gray > 215).astype(np.uint8) * 255
            tpl = (tpl > 215).astype(np.uint8) * 255
        if gray.shape[0] < tpl.shape[0] or gray.shape[1] < tpl.shape[1]:
            return 0.0, (0, 0)
        res = cv2.matchTemplate(gray, tpl, cv2.TM_CCOEFF_NORMED)
        _, score, _, loc = cv2.minMaxLoc(res)
        h, w = tpl.shape
        return float(score), (x0 + loc[0] + w // 2, y0 + loc[1] + h // 2)

    def has(self, frame, name, thr=0.8, roi=None, white=False):
        return self.find(frame, name, roi, white)[0] >= thr


def load_frame(path):
    img = cv2.imread(str(path))
    if img is None:
        raise FileNotFoundError(path)
    return normalize(img)


def normalize(img):
    h, w = img.shape[:2]
    if w != REF_W:
        img = cv2.resize(img, (REF_W, int(h * REF_W / w)), interpolation=cv2.INTER_AREA)
    return img
