"""OpenCV 없이 numpy + Pillow 만으로 하는 이미지 처리 (Termux 에는 opencv 패키지가 없다)."""
import io

import numpy as np
from PIL import Image


def decode(data):
    return np.asarray(Image.open(io.BytesIO(data)).convert("RGB"))


def load(path):
    return np.asarray(Image.open(path).convert("RGB"))


def save(path, arr):
    Image.fromarray(np.ascontiguousarray(arr)).save(str(path))


def resize_width(arr, w):
    h, cur = arr.shape[:2]
    return np.asarray(Image.fromarray(arr).resize((w, round(h * w / cur)), Image.LANCZOS))


def gray(arr):
    return np.asarray(Image.fromarray(np.ascontiguousarray(arr)).convert("L"))


def _fast_len(n):
    while True:
        m = n
        for p in (2, 3, 5):
            while m % p == 0:
                m //= p
        if m == 1:
            return n
        n += 1


def match_ncc(img, tpl):
    """OpenCV TM_CCOEFF_NORMED 와 같은 점수 맵. 크기 (H-h+1, W-w+1), 값 -1..1."""
    img = img.astype(np.float64)
    tpl = tpl.astype(np.float64)
    H, W = img.shape
    h, w = tpl.shape
    t = tpl - tpl.mean()
    tnorm = np.sqrt((t * t).sum())
    oh, ow = H - h + 1, W - w + 1
    if tnorm < 1e-9:
        return np.zeros((oh, ow))
    fh, fw = _fast_len(H), _fast_len(W)
    corr = np.fft.irfft2(np.fft.rfft2(img, (fh, fw)) * np.conj(np.fft.rfft2(t, (fh, fw))), (fh, fw))[:oh, :ow]

    def window_sum(a):
        c = np.zeros((a.shape[0] + 1, a.shape[1] + 1))
        c[1:, 1:] = a.cumsum(0).cumsum(1)
        return c[h:, w:] - c[:-h, w:] - c[h:, :-w] + c[:-h, :-w]

    n = h * w
    s, s2 = window_sum(img), window_sum(img * img)
    var = s2 - s * s / n
    ok = var > 1e-2
    out = np.zeros((oh, ow))
    out[ok] = corr[ok] / (tnorm * np.sqrt(var[ok]))
    return np.clip(out, -1.0, 1.0)
