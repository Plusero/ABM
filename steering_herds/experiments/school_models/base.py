import numba
import numpy as np

from utils import maths


@numba.jit(nopython=True, cache=True, fastmath=True)
def normalized_collective_motion(p, p_i, i_r, i_o, i_a):
    """
    Calculate the normalized collective motion forces for an agent.

    Parameters:
    p (numpy.ndarray): Array of agent positions.
    p_i (numpy.ndarray): Position of the current agent.
    i_r (numpy.ndarray): Indices of neighboring agents within the repulsion range.
    i_o (numpy.ndarray): Indices of neighboring agents within the orientation range.
    i_a (numpy.ndarray): Indices of neighboring agents within the attraction range.

    Returns:
    tuple: A tuple containing the repulsion force, orientation force, and attraction force.
    """
    f_r = np.zeros(2)
    if np.any(i_r):
        # p[i_r, :2] gives the poses of the agents in the repulsion zone
        f_r = -np.sum(maths.row_normalize(p[i_r, :2] - p_i[:2]), axis=0)
        # this gives a vector pointing away from the agent
    f_o = np.zeros(2)
    if np.any(i_o):
        f_o[0] = np.cos(p_i[2]) + np.sum(np.cos(p[i_o, 2]), axis=0)
        f_o[1] = np.sin(p_i[2]) + np.sum(np.sin(p[i_o, 2]), axis=0)
        # this gives a vector pointing in the direction of the average orientation of the neighbors
    f_a = np.zeros(2)
    if np.any(i_a):
        f_a = np.sum(maths.row_normalize(p[i_a, :2] - p_i[:2]), axis=0)
        # this gives a vector pointing towards the agent
    return f_r, f_o, f_a
