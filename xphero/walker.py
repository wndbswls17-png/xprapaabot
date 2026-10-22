"""가상 조이스틱 드래그로 걷기."""
import random


class Walker:
    def __init__(self, dev, origin, radius):
        self.dev, self.origin, self.radius = dev, origin, radius

    def move(self, ux, uy, seconds):
        """단위벡터 (ux,uy) 방향으로 seconds초 동안 조이스틱을 민다."""
        ox, oy = self.origin
        ms = int(seconds * random.uniform(0.95, 1.05) * 1000)
        self.dev.drag(ox, oy, ox + ux * self.radius, oy + uy * self.radius, ms)
