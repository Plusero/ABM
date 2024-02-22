import numba
import numpy as np

from experiments.school_models import metric_model, topological_model, visual_model, longrange_model
from utils.settings import get_time_space_batch_end


@numba.jit(nopython=True, cache=True, fastmath=True)
def run_simulation(n_school,
                   model_s,
                   knn_s,
                   klr_s,
                   zor_s,
                   zoo_s,
                   zoa_s,
                   kor_s,
                   koo_s,
                   koa_s,
                   sigma_s,
                   rho_s,
                   v_s_max,
                   w_s_max,
                   t_max,
                   dt=1., ):
    # derived params
    time_space = get_time_space_batch_end()

    # initialize random school poses
    school_poses = np.zeros((len(time_space), n_school, 3), dtype=np.float32)
    l_size_s = np.sqrt(n_school / rho_s)
    school_poses[0] = np.random.rand(n_school, 3) * l_size_s - l_size_s / 2
    school_poses[0, :, 2] = np.random.randn(n_school) * sigma_s

    # system dynamics over time
    current_school_poses = np.copy(school_poses[0])
    v_s = np.full((n_school,), v_s_max)
    _t = 1
    for t in range(1, t_max + 1):
        # # SCHOOL
        next_school_poses = np.zeros_like(current_school_poses)
        # compute next position, with a fixed velocity and the heading
        next_school_poses[:, 0] = current_school_poses[:,
                                                       0] + v_s * np.cos(current_school_poses[:, 2])
        next_school_poses[:, 1] = current_school_poses[:,
                                                       1] + v_s * np.sin(current_school_poses[:, 2])
        # compute next orientation
        for i in range(n_school):
            # desired orientation [0, 2π]
            if model_s == "METRIC":
                force = metric_model.metric_normalized_model(current_school_poses, i, zor_s, zoo_s, zoa_s, kor_s, koo_s,
                                                             koa_s)
            elif model_s == "TOPOLOGICAL":
                force = topological_model.topological_normalized_model(current_school_poses, i, knn_s, zor_s, zoo_s,
                                                                       zoa_s, kor_s, koo_s, koa_s)
            elif model_s == "VISUAL":
                force = visual_model.visual_normalized_model(current_school_poses, i, zor_s, zoo_s, zoa_s, kor_s, koo_s,
                                                             koa_s)
            elif model_s == "LONGRANGE":
                force = longrange_model.longrange_normalized_model(current_school_poses, i, knn_s, klr_s, zor_s, zoo_s,
                                                                   zoa_s, kor_s, koo_s, koa_s)
            else:
                force = np.zeros(2)
            print("current school poses", current_school_poses)
            print("current_school_poses[i, 2] ", current_school_poses[i, 2])
            # force is a two element vector, the first one being x-axis and the second one being y-axis
            d_theta = np.arctan2(force[1], force[0]) % (2 * np.pi)
            # necessary turn
            turn = current_school_poses[i, 2] - d_theta
            print("turn", turn)
            # converted to [-π, π]
            turn = (turn + np.pi) % (2 * np.pi) - np.pi
            # rotating duration (limited)
            dt_w = min(abs(turn) / w_s_max, dt)
            # limited turn
            turn = np.sign(turn) * w_s_max * dt_w
            # remaining duration to move
            next_school_poses[i, 2] = (
                current_school_poses[i, 2] - turn + np.random.randn() * sigma_s) % (2 * np.pi)
            # remaining duration to move
            v_s[i] = v_s_max * (dt - dt_w)
        # memory swap and store
        current_school_poses = np.copy(next_school_poses)
        if t in time_space:
            school_poses[_t] = np.copy(current_school_poses)
            _t += 1

    return school_poses
