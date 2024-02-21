import numba
import numpy as np

from bodies import GuppyBody
from experiments.school_models import base
from utils import maths
from utils.maths import no_intersect

body = GuppyBody(color=np.array((220, 20, 60)))
body_segment = body.mirror_line

CTE_SCHOOL = 0.
CTE_AGENTS = 1.
CTE_PREDATOR = 2.


@numba.jit(nopython=True, cache=True, fastmath=True)
def get_neighbours_states(p, p_i):
    # transformation to rotate positions by focal orientation ϑ clockwise
    c, s = np.cos(p_i[2]), np.sin(p_i[2])
    R = np.array(((c, -s), (s, c)), dtype=np.float64)
    relative_positions = (p[:, :2] - p_i[:2]).dot(R)
    # transform orientations relative to ϑ
    relative_orientations = p[:, 2] - p_i[2]
    # filter local neighbor orientations to [-π, π]
    relative_orientations = (relative_orientations + np.pi) % (2 * np.pi) - np.pi

    # polar coordinates
    dist = np.sqrt(np.sum(relative_positions ** 2, axis=1))
    # phi = np.arctan2(relative_positions[:, 1], relative_positions[:, 0])

    return np.hstack((relative_positions, np.stack((relative_orientations, dist), axis=1), p))


@numba.jit(nopython=True, cache=True, fastmath=True)
def _visual_neighbours(p, p_i):
    neighbours_states = get_neighbours_states(p, p_i)
    neighbours_states = neighbours_states[(0. < neighbours_states[:, 3])]

    n = neighbours_states.shape[0]
    neighbours_segments = np.zeros((n, 2, 2))
    for k, theta in enumerate(neighbours_states[:, 2]):
        c, s = np.cos(theta), np.sin(theta)
        R = np.array(((c, s), (-s, c)))
        neighbours_segments[k, 0] = neighbours_states[k, :2] + body_segment[0].dot(R)
        neighbours_segments[k, 1] = neighbours_states[k, :2] + body_segment[1].dot(R)

    i, j = 0, 0
    visible_mask = np.full(n, True)
    optic_position = np.array((0., 0.))  # optic_position is always zero
    while i < n:
        j = 0
        visible = True
        while visible and j < n:
            if i != j:
                # visible = no_intersect(
                #     optic_position,
                #     neighbours_states[i, :2],
                #     neighbours_segments[j, 0],
                #     neighbours_segments[j, 1]
                # )
                visible = no_intersect(
                    optic_position,
                    neighbours_segments[i, 0],
                    neighbours_segments[j, 0],
                    neighbours_segments[j, 1]
                ) and no_intersect(
                    optic_position,
                    neighbours_segments[i, 1],
                    neighbours_segments[j, 0],
                    neighbours_segments[j, 1]
                )
            j += 1
        visible_mask[i] = visible
        i += 1

    return neighbours_states[visible_mask, 3:]


@numba.jit(nopython=True, cache=True, fastmath=True)
def visual_neighbours(p, p_i, zor, zoo, zoa):
    p = _visual_neighbours(p, p_i)

    p_n = p[p[:, 4] == CTE_SCHOOL]

    # Neighbors N = {visually recognisable}
    dist = p_n[:, 0]

    i_r = np.logical_and(0.0 < dist, dist <= zor)
    i_o = np.logical_and(zor < dist, dist <= zor + zoo)
    i_a = np.logical_and(zor + zoo < dist, dist <= zor + zoo + zoa)

    p = p[:, 1:]
    p_n = p_n[:, 1:]

    return p, p_n, i_r, i_o, i_a


@numba.jit(nopython=True, cache=True, fastmath=True)
def visual_normalized_model(p, i, zor, zoo, zoa, k_r, k_o, k_a):
    p_i = p[i]
    n_school = p.shape[0]
    p = np.hstack((p, np.full((n_school, 1), CTE_SCHOOL)))
    _, p_n, i_r, i_o, i_a = visual_neighbours(p, p_i, zor, zoo, zoa)
    f_r, f_o, f_a = base.normalized_collective_motion(p_n, p_i, i_r, i_o, i_a)

    f = k_r * f_r + k_o * f_o + k_a * f_a

    return f


@numba.jit(nopython=True, cache=True, fastmath=True)
def visual_normalized_aversive_model(p_h, p_a, i, zor, zoo, zoa, zox, k_r, k_o, k_a, k_x):
    p_i = p_h[i]
    n_school, n_agents = p_h.shape[0], p_a.shape[0]
    p = np.vstack((
        np.hstack((p_h, np.full((n_school, 1), CTE_SCHOOL))),
        np.hstack((p_a, np.full((n_agents, 1), CTE_AGENTS))),
    ))
    p_t, p_n, i_r, i_o, i_a = visual_neighbours(p, p_i, zor, zoo, zoa)
    f_r, f_o, f_a = base.normalized_collective_motion(p_n, p_i, i_r, i_o, i_a)

    p_na = p_t[p_t[:, 3] == CTE_AGENTS]

    dist = np.sqrt(np.sum((p_na[:, :2] - p_i[:2]) ** 2, axis=1))
    i_x = dist <= zox
    f_x = np.zeros(2)
    if np.any(i_x):
        f_x = -np.sum(maths.row_normalize(p_na[i_x, :2] - p_i[:2]), axis=0)

    f = k_r * f_r + k_o * f_o + k_a * f_a + k_x * f_x

    return f


@numba.jit(nopython=True, cache=True, fastmath=True)
def visual_normalized_predator_prey_model(p_h, p_a, p_z, i, zor, zoo, zoa, zox, zoz, k_r, k_o, k_a, k_x, k_z):
    p_i = p_h[i]
    n_school, n_agents = p_h.shape[0], p_a.shape[0]
    p = np.vstack((
        np.hstack((p_h, np.full((n_school, 1), CTE_SCHOOL))),
        np.hstack((p_a, np.full((n_agents, 1), CTE_AGENTS))),
        np.hstack((p_z, np.full((1, 1), CTE_PREDATOR)))
    ))
    p_t, p_n, i_r, i_o, i_a = visual_neighbours(p, p_i, zor, zoo, zoa)
    f_r, f_o, f_a = base.normalized_collective_motion(p_n, p_i, i_r, i_o, i_a)

    p_na = p_t[p_t[:, 3] == CTE_AGENTS]

    f_x = np.zeros(2)
    i_x = np.array([False] * p_na.shape[0])
    if np.any(p_na):
        dist = np.sqrt(np.sum((p_na[:, :2] - p_i[:2]) ** 2, axis=1))
        i_x = dist <= zox
        if np.any(i_x):
            f_x = -np.sum(maths.row_normalize(p_na[i_x, :2] - p_i[:2]), axis=0)

    p_nz = p_t[p_t[:, 3] == CTE_PREDATOR]

    f_z = np.zeros(2)
    if np.any(p_nz):
        if not np.any(np.isinf(p_nz)):
            dist_z = np.sqrt(np.sum((p_z[:, :2] - p_h[i, :2]) ** 2, axis=1))
            i_z = dist_z <= zoz
            if np.any(i_z):
                if not np.any(i_r) and not np.any(i_x):
                    f_o = np.zeros(2)
                    f_a = np.zeros(2)
                f_z = -np.sum(maths.row_normalize(p_z[i_z, :2] - p_h[i, :2]), axis=0)

    f = k_r * f_r + k_o * f_o + k_a * f_a + k_x * f_x + k_z * f_z

    return f


@numba.jit(nopython=True, cache=True, fastmath=True)
def visual_normalized_enclosure_model(p_h, p_a, c_z, r_z, i, zor, zoo, zoa, zox, zoz, k_r, k_o, k_a, k_x, k_z):
    p_i = p_h[i]
    n_school, n_agents = p_h.shape[0], p_a.shape[0]
    p = np.vstack((
        np.hstack((p_h, np.full((n_school, 1), CTE_SCHOOL))),
        np.hstack((p_a, np.full((n_agents, 1), CTE_AGENTS))),
    ))
    p_t, p_n, i_r, i_o, i_a = visual_neighbours(p, p_i, zor, zoo, zoa)
    f_r, f_o, f_a = base.normalized_collective_motion(p_n, p_i, i_r, i_o, i_a)

    p_na = p_t[p_t[:, 3] == CTE_AGENTS]

    f_x = np.zeros(2)
    i_x = np.array([False] * p_na.shape[0])
    if np.any(p_na):
        dist = np.sqrt(np.sum((p_na[:, :2] - p_i[:2]) ** 2, axis=1))
        i_x = dist <= zox
        if np.any(i_x):
            f_x = -np.sum(maths.row_normalize(p_na[i_x, :2] - p_i[:2]), axis=0)

    f_z = np.zeros(2)
    if not np.any(np.isinf(c_z)):
        dist_z = np.linalg.norm(c_z - p_i[:2])
        if r_z - dist_z <= zoz:
            if not np.any(i_r) and not np.any(i_x):
                f_o = np.zeros(2)
                f_a = np.zeros(2)
            f_z = (c_z - p_i[:2]) / (dist_z + 1e-8)

    f = k_r * f_r + k_o * f_o + k_a * f_a + k_x * f_x + k_z * f_z

    return f
