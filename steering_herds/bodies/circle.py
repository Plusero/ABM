import numpy as np

from bodies import Body


class Circle(Body):
    def __init__(self, radius: float, **kwargs):
        super().__init__(**kwargs)

        self._radius = radius
        self._circumference = 2 * np.pi * radius
        self._area = np.pi * (radius ** 2)

    @property
    def circumference(self):
        return self._circumference

    @property
    def area(self):
        return self._area

    def draw(self, viewer):
        return None

    def plot(self, axes, **kwargs):
        return None
