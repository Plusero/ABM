import numba
import numpy as np


@numba.jit(nopython=True, cache=True, fastmath=True)
def get_time_space():
    return np.array(
        [5*i for i in range(0, 20)] +
        [100+10*i for i in range(0, 10)] +
        [200+25*i for i in range(0, 4)] +
        [300+50*i for i in range(0, 2)] +
        [400+100*i for i in range(0, 7)]
    )


@numba.jit(nopython=True, cache=True, fastmath=True)
def get_time_space_batch_end():
    return np.array(
        [5 * i for i in range(0, 20)] +
        [100 + 10 * i for i in range(0, 10)] +
        [200 + 25 * i for i in range(0, 4)] +
        [300 + 50 * i for i in range(0, 2)] +
        [400 + 100 * i for i in range(0, 26)] +
        [2990 + 1 * i for i in range(0, 11)]
    )


@numba.jit(nopython=True, cache=True, fastmath=True)
def get_long_time_space_batch_end():
    return np.array(
        [5 * i for i in range(0, 20)] +
        [100 + 10 * i for i in range(0, 10)] +
        [200 + 25 * i for i in range(0, 4)] +
        [300 + 50 * i for i in range(0, 2)] +
        [400 + 100 * i for i in range(0, 26)] +
        [2990 + 1 * i for i in range(0, 10)] +
        [3000 + 10 * i for i in range(0, 101)]
    )


@numba.jit(nopython=True, cache=True, fastmath=True)
def get_long_recovering_time_space_batch_end():
    return np.array(
        [5 * i for i in range(0, 20)] +
        [100 + 10 * i for i in range(0, 10)] +
        [200 + 25 * i for i in range(0, 4)] +
        [300 + 50 * i for i in range(0, 2)] +
        [400 + 100 * i for i in range(0, 26)] +
        [2990 + 1 * i for i in range(0, 10)] +
        [3000 + 10 * i for i in range(0, 100)] +
        [4000 + 10 * i for i in range(0, 101)]
    )
