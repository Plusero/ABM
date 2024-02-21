import numpy as np

from bodies import Polygon


class GuppyBody(Polygon):
    def __init__(self, color=np.array((133, 133, 133)), **kwargs):
        vertices = np.array(
            [
                (+3.0, +0.0),
                (+2.5, +1.0),
                (+1.5, +1.5),
                (-2.5, +1.0),
                (-4.5, +0.0),
                (-2.5, -1.0),
                (+1.5, -1.5),
                (+2.5, -1.0),
            ]
        )
        self.width = 2.
        self.height = 0.4
        super().__init__(width=self.width, height=self.height, vertices=vertices, color=color, **kwargs)

    @property
    def optic_vertex(self):
        return self.centroid  # self.vertices[0]

    @property
    def mirror_line(self):
        return np.array((self.vertices[0], self.vertices[4]))
