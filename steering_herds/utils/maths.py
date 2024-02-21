import numba
import numpy as np


def sign(x):
    return -1 if x < 0 else 1


@numba.jit(nopython=True, cache=True, fastmath=True)
def unit_vector(angle):
    return np.array([np.cos(angle), np.sin(angle)])


@numba.jit(nopython=True, cache=True, fastmath=True)
def angle_between_vectors(a, b):
    inner = np.sum(a[:]*b[:])  # inner = np.inner(a, b)
    norms = np.linalg.norm(a) * np.linalg.norm(b)

    cos = inner / norms
    rad = np.arccos(max(min(cos, 1.0), -1.0))  # rad = np.arccos(np.clip(cos, -1.0, 1.0))

    return np.pi - rad


def circles_intersection(c1, c2, r):
    d = np.linalg.norm(c2 - c1)
    if d > 2*r:
        return None, None
    else:
        a = 0.5 * r
        h = np.sqrt(r**2 - a**2)
        z = c1 + a*(c2 - c1) / d
        p1 = np.array([
            z[0] + h * (c2[1] - c1[1]) / d,
            z[1] - h * (c2[0] - c1[0]) / d,
        ])
        p2 = np.array([
            z[0] - h * (c2[1] - c1[1]) / d,
            z[1] + h * (c2[0] - c1[0]) / d,
        ])
        return p1, p2


def sigmoid(x, L, x0, k, b):
    y = L / (1 + np.exp(-k*(x-x0)))
    return (y)


@numba.jit(nopython=True, cache=True, fastmath=True)
def line_circle_intersection(line_start, line_end, circle_center, circle_radius):
    d = (line_end - line_start).astype(np.float32)
    f = (line_start - circle_center).astype(np.float32)

    a = np.dot(d, d)
    b = 2 * np.dot(f, d)
    c = np.dot(f, f) - circle_radius**2

    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        # no intersection
        return 0, np.array([0., 0.])
    else:
        discriminant = np.sqrt(discriminant)
        t1 = (-b - discriminant)/(2*a)
        t2 = (-b + discriminant)/(2*a)
        if 0 <= t1 <= 1:
            return 1, line_start + t1 * d
        if 0 <= t2 <= 1:
            return 2, line_start + t2 * d
        return 0, np.array([0., 0.])


@numba.jit(nopython=True, cache=True, fastmath=True)
def row_norm(matrix):
    return np.sqrt(np.sum(matrix ** 2, axis=1))


@numba.jit(nopython=True, cache=True, fastmath=True)
def row_normalize(matrix):
    return matrix / (np.reshape(row_norm(matrix), (-1, 1)) + 1e-8)


@numba.jit(nopython=True, cache=True, fastmath=True)
def ccw(a, b, c):
    return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])


@numba.jit(nopython=True, cache=True, fastmath=True)
def no_intersect(a, b, c, d):
    return ccw(a, c, d) == ccw(b, c, d) or ccw(a, b, c) == ccw(a, b, d)
