import abc

import numpy as np


class Body(abc.ABC):
    def __init__(self,
                 color=np.array((93, 133, 195))):
        self._color = color

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        color = np.asarray(color, dtype=np.int32)
        color = np.maximum(color, np.zeros_like(color, dtype=np.int32))
        color = np.minimum(color, np.full_like(color, 255, dtype=np.int32))
        self._color = color

    @abc.abstractmethod
    def circumference(self):
        raise NotImplementedError(
            "The circumference property needs to be implemented by the subclass of Body."
        )

    @abc.abstractmethod
    def area(self):
        raise NotImplementedError(
            "The area property needs to be implemented by the subclass of Body."
        )

    @abc.abstractmethod
    def draw(self, viewer):
        raise NotImplementedError(
            "The draw method needs to be implemented by the subclass of Body."
        )

    @abc.abstractmethod
    def plot(self, axes, **kwargs):
        raise NotImplementedError(
            "The plot method needs to be implemented by the subclass of Body."
        )
