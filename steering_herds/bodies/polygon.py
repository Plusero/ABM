import numpy as np

from bodies import Body


class Polygon(Body):
    def __init__(self, width: float, height: float, vertices: np.ndarray, **kwargs):
        super().__init__(**kwargs)

        # resize the shape to desired width and height
        v_size = np.amax(vertices, 0) - np.amin(vertices, 0)
        vertices /= v_size
        vertices *= np.array((width, height))

        centroid = np.zeros(2)
        area = 0.5 * np.abs(
            np.dot(vertices[:, 0], np.roll(vertices[:, 1], 1))
            - np.dot(vertices[:, 1], np.roll(vertices[:, 0], 1))
        )
        centroid += vertices.mean(axis=0) * area
        centroid /= area

        self._vertices = vertices - centroid
        self._mirror_vector = self._vertices[[0, int(self._vertices.shape[0]/2)], :]

        self._circumference = None  # TODO
        self._area = area

        self._centroid = centroid

    @property
    def circumference(self):
        return self._circumference

    @property
    def area(self):
        return self._area

    @property
    def vertices(self):
        return self._vertices

    @property
    def centroid(self):
        return self._centroid

    @property
    def mirror_vector(self):
        return self._mirror_vector

    def draw(self, viewer):
        return None

    def plot(self, axes, **kwargs):
        return None
