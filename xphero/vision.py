"""화면 인식. 모든 좌표는 기준 해상도(REF_W x REF_H) 기준이다."""
from pathlib import Path

import numpy as np

from . import imaging

REF_W, REF_H = 1440, 3120


class Vision:
    def __init__(self, template_dir):
        self.dir = Path(template_dir)
        self._cache = {}

    def template(self, name):
        if name not in self._cache:
            p = self.dir / f"{name}.png"
            if not p.exists():
                raise FileNotFoundError(f"템플릿 없음: {p}")
            self._cache[name] = imaging.gray(imaging.load(p))
        return self._cache[name]

    def find(self, frame, name, roi=None, white=False):
        """(점수, (중심x, 중심y)). roi=(x0,y0,x1,y1)면 그 안에서만 찾는다.

        white=True면 흰색 픽셀만 남겨 비교한다. 배경이 비치는 아이콘용.
        """
        x0, y0, x1, y1 = roi or (0, 0, frame.shape[1], frame.shape[0])
        g = imaging.gray(frame[y0:y1, x0:x1])
        tpl = self.template(name)
        if white:
            g = (g > 215).astype(np.uint8) * 255
            tpl = (tpl > 215).astype(np.uint8) * 255
        if g.shape[0] < tpl.shape[0] or g.shape[1] < tpl.shape[1]:
            return 0.0, (0, 0)
        res = imaging.match_ncc(g, tpl)
        iy, ix = np.unravel_index(np.argmax(res), res.shape)
        h, w = tpl.shape
        return float(res[iy, ix]), (x0 + int(ix) + w // 2, y0 + int(iy) + h // 2)

    def has(self, frame, name, thr=0.8, roi=None, white=False):
        return self.find(frame, name, roi, white)[0] >= thr


def load_frame(path):
    return normalize(imaging.load(path))


def normalize(img):
    if img.shape[1] != REF_W:
        img = imaging.resize_width(img, REF_W)
    return img
