import numba
import numpy as np

from experiments.school_models import base
from utils import maths


@numba.jit(nopython=True, cache=True, fastmath=True)
def metric_neighbours(p, i, zor, zoo, zoa):
    # Neighbors N = {radii of zor+zoo+zoa}

    dist = np.sqrt(np.sum((p[:, :2] - p[i, :2]) ** 2, axis=1))

    i_r = np.logical_and(0.0 < dist, dist <= zor)
    i_o = np.logical_and(zor < dist, dist <= zor + zoo)
    i_a = np.logical_and(zor + zoo < dist, dist <= zor + zoo + zoa)

    return i_r, i_o, i_a


@numba.jit(nopython=True, cache=True, fastmath=True)
def metric_normalized_model(p, i, zor, zoo, zoa, k_r, k_o, k_a):
    i_r, i_o, i_a = metric_neighbours(p, i, zor, zoo, zoa)
    f_r, f_o, f_a = base.normalized_collective_motion(p, p[i], i_r, i_o, i_a)

    f = k_r * f_r + k_o * f_o + k_a * f_a

    return f


@numba.jit(nopython=True, cache=True, fastmath=True)
def metric_normalized_aversive_model(p_h, p_a, i, zor, zoo, zoa, zox, k_r, k_o, k_a, k_x):
    i_r, i_o, i_a = metric_neighbours(p_h, i, zor, zoo, zoa)
    f_r, f_o, f_a = base.normalized_collective_motion(p_h, p_h[i], i_r, i_o, i_a)

    dist = np.sqrt(np.sum((p_a[:, :2] - p_h[i, :2]) ** 2, axis=1))
    i_x = dist <= zox
    f_x = np.zeros(2)
    if np.any(i_x):
        f_x = -np.sum(maths.row_normalize(p_a[i_x, :2] - p_h[i, :2]), axis=0)

    f = k_r * f_r + k_o * f_o + k_a * f_a + k_x * f_x

    return f


@numba.jit(nopython=True, cache=True, fastmath=True)
def metric_normalized_predator_prey_model(p_h, p_a, p_z, i, zor, zoo, zoa, zox, zoz, k_r, k_o, k_a, k_x, k_z):
    i_r, i_o, i_a = metric_neighbours(p_h, i, zor, zoo, zoa)
    f_r, f_o, f_a = base.normalized_collective_motion(p_h, p_h[i], i_r, i_o, i_a)

    # aversive to agent
    dist = np.sqrt(np.sum((p_a[:, :2] - p_h[i, :2]) ** 2, axis=1))
    i_x = dist <= zox
    f_x = np.zeros(2)
    if np.any(i_x):
        if not np.any(i_r):
            f_o = np.zeros(2)
            f_a = np.zeros(2)
        f_x = -np.sum(maths.row_normalize(p_a[i_x, :2] - p_h[i, :2]), axis=0)

    # aversive to predator
    f_z = np.zeros(2)
    if not np.any(np.isinf(p_z)):
        dist_z = np.sqrt(np.sum((p_z[:, :2] - p_h[i, :2]) ** 2, axis=1))
        i_z = dist_z <= zoz
        if np.any(i_z):
            if not np.any(i_r) and not np.any(i_x):
                f_o = np.zeros(2)
                f_a = np.zeros(2)
            f_z = -np.sum(maths.row_normalize(p_z[i_z, :2] - p_h[i, :2]), axis=0)
        # dist_z = np.linalg.norm(p_z[:2] - p_h[i, :2])
        # if dist_z <= zoz:
        #     if not np.any(i_r) and not np.any(i_x):
        #         f_o = np.zeros(2)
        #         f_a = np.zeros(2)
        #     f_z = -(p_z[:2] - p_h[i, :2]) / (dist_z + 1e-8)

    f = k_r * f_r + k_o * f_o + k_a * f_a + k_x * f_x + k_z * f_z

    return f


@numba.jit(nopython=True, cache=True, fastmath=True)
def metric_normalized_enclosure_model(p_h, p_a, c_z, r_z, i, zor, zoo, zoa, zox, zoz, k_r, k_o, k_a, k_x, k_z):
    i_r, i_o, i_a = metric_neighbours(p_h, i, zor, zoo, zoa)
    f_r, f_o, f_a = base.normalized_collective_motion(p_h, p_h[i], i_r, i_o, i_a)

    dist = np.sqrt(np.sum((p_a[:, :2] - p_h[i, :2]) ** 2, axis=1))
    i_x = dist <= zox
    f_x = np.zeros(2)
    if np.any(i_x):
        f_x = -np.sum(maths.row_normalize(p_a[i_x, :2] - p_h[i, :2]), axis=0)

    f_z = np.zeros(2)
    if not np.any(np.isinf(c_z)):
        dist_z = np.linalg.norm(c_z - p_h[i, :2])
        if r_z - dist_z <= zoz:
            if not np.any(i_r) and not np.any(i_x):
                f_o = np.zeros(2)
                f_a = np.zeros(2)
            f_z = (c_z - p_h[i, :2]) / (dist_z + 1e-8)

    f = k_r * f_r + k_o * f_o + k_a * f_a + k_x * f_x + k_z * f_z

    return f
