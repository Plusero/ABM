import numba
import numpy as np

from utils import maths


@numba.jit(nopython=True, cache=True, fastmath=True)
def normalized_collective_motion(p, p_i, i_r, i_o, i_a):
    f_r = np.zeros(2)
    if np.any(i_r):
        f_r = -np.sum(maths.row_normalize(p[i_r, :2] - p_i[:2]), axis=0)
    f_o = np.zeros(2)
    if np.any(i_o):
        f_o[0] = np.cos(p_i[2]) + np.sum(np.cos(p[i_o, 2]), axis=0)
        f_o[1] = np.sin(p_i[2]) + np.sum(np.sin(p[i_o, 2]), axis=0)
    f_a = np.zeros(2)
    if np.any(i_a):
        f_a = np.sum(maths.row_normalize(p[i_a, :2] - p_i[:2]), axis=0)

    return f_r, f_o, f_a
