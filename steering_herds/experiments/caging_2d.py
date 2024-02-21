import numba
import numpy as np

from experiments.school_models import metric_model, topological_model, visual_model, longrange_model
from utils import maths
from utils.settings import get_time_space_batch_end


@numba.jit(nopython=True, cache=True, fastmath=True)
def searching_model(p, c, i, zor, zoo, zoa, zoi):
    dist = np.sqrt(np.sum((p[:, :2] - p[i, :2]) ** 2, axis=1))
    i_r = np.logical_and(0.0 < dist, dist <= zor)
    if np.any(i_r):
        d = -np.sum(maths.row_normalize(p[i_r, :2] - p[i, :2]), axis=0)
    else:
        i_ca = np.logical_and(c, dist <= zoi)
        if np.any(i_ca):
            d = np.sum(maths.row_normalize(p[i_ca, :2] - p[i, :2]), axis=0)
        else:
            b = 0
            d = np.zeros(2)
            i_o = np.logical_and(zor < dist, dist <= zor + zoo)
            if np.any(i_o):
                b += 1
                d[0] = np.cos(p[i, 2]) + np.sum(np.cos(p[i_o, 2]), axis=0)
                d[1] = np.sin(p[i, 2]) + np.sum(np.sin(p[i_o, 2]), axis=0)
            i_a = np.logical_and(zor + zoo < dist, dist <= zor + zoo + zoa)
            if np.any(i_a):
                b += 1
                d += np.sum(maths.row_normalize(p[i_a, :2] - p[i, :2]), axis=0)
            if b > 0:
                d /= b
    if np.any(d):
        d_theta = np.arctan2(d[1], d[0]) % (2 * np.pi)
    else:
        d_theta = 0.
    return d_theta, 0


@numba.jit(nopython=True, cache=True, fastmath=True)
def caging_2d_model(agents_all, school_all, i, var_theta, search_msg_all,
                    mu=19.,
                    v_a_max=6.,
                    v_h_max=2.,
                    v_h_avg=2.,
                    eps_a=None,
                    eps_h=None,
                    zoi_a=None,
                    tau=0.1, ):
    eta = 1.
    e_star = 2 * v_h_max + eta
    r_star = mu + e_star
    delta = 2 * mu

    if not eps_a:
        eps_a = v_h_max
    if not eps_h:
        eps_h = 3 * v_h_max
    if not zoi_a:
        zoi_a = 1.5 * delta
    zor_h = 1.
    zor_a = 1.
    zoo_a = zoi_a - zor_a
    zoa_a = 0.

    # initialize variables
    v_h_hat = v_h_max
    agent_pose = agents_all[i]

    school_dist2 = np.sum((school_all[:, :2] - agent_pose[:2]) ** 2, axis=1)
    h_indexes = school_dist2 <= zoi_a ** 2
    if np.any(h_indexes):
        search_message = 1

        # filter herd neighbours
        school_dist2 = school_dist2[h_indexes]
        h_star = np.argmin(school_dist2)
        h_star_pose = school_all[h_indexes][h_star]
        d_star = np.sqrt(school_dist2[h_star])
        theta_star = np.arctan2(np.mean(np.sin(school_all[h_indexes, 2])),
                                np.mean(np.cos(school_all[h_indexes, 2]))) % (2 * np.pi)
        # filter agent neighbours
        agents_dist2 = np.sum((agents_all[:, :2] - agent_pose[:2]) ** 2, axis=1)

        # (0) COLLISION AVOIDANCE WITH HERD
        h_col_indexes = school_dist2 <= zor_h ** 2
        if np.any(h_col_indexes):
            d = -np.sum(maths.row_normalize(school_all[h_col_indexes, :2] - agent_pose[:2]), axis=0)
            theta = np.arctan2(d[1], d[0]) % (2 * np.pi)
            eta = -v_h_hat * np.cos(theta_star - theta) + np.sqrt(
                (v_h_hat ** 2) * (np.cos(theta_star - theta) ** 2 - 1) + v_a_max ** 2)
            q = np.array([v_h_hat * np.cos(theta_star) + eta * np.cos(theta),
                          v_h_hat * np.sin(theta_star) + eta * np.sin(theta)])
            d_theta = np.arctan2(q[1], q[0]) % (2 * np.pi)
            d_v = np.linalg.norm(q)
            return d_theta, d_v, var_theta, search_message
        # (0) AVOID ENTERING HERD AREA
        if d_star - r_star <= -e_star:
            d = -(h_star_pose[:2] - agent_pose[:2]) / np.linalg.norm(h_star_pose[:2] - agent_pose[:2])
            theta = np.arctan2(d[1], d[0]) % (2 * np.pi)
            eta = -v_h_hat * np.cos(theta_star - theta) + np.sqrt(
                (v_h_hat ** 2) * (np.cos(theta_star - theta) ** 2 - 1) + v_a_max ** 2)
            q = np.array([v_h_hat * np.cos(theta_star) + eta * np.cos(theta),
                          v_h_hat * np.sin(theta_star) + eta * np.sin(theta)])
            d_theta = np.arctan2(q[1], q[0]) % (2 * np.pi)
            d_v = np.linalg.norm(q)
            return d_theta, d_v, var_theta, search_message
        # (0) COLLISION AVOIDANCE WITH AGENTS
        if d_star >= r_star:
            col_indexes = np.logical_and(0.0 < agents_dist2, agents_dist2 <= zor_a ** 2)
            if np.any(col_indexes):
                d = -np.sum(maths.row_normalize(agents_all[col_indexes, :2] - agent_pose[:2]), axis=0)
                theta = np.arctan2(d[1], d[0]) % (2 * np.pi)
                eta = -v_h_hat * np.cos(theta_star - theta) + np.sqrt(
                    (v_h_hat ** 2) * (np.cos(theta_star - theta) ** 2 - 1) + v_a_max ** 2)
                b_int, int_position = maths.line_circle_intersection(
                    agent_pose[:2],
                    agent_pose[:2] + v_a_max * np.array([np.cos(theta), np.sin(theta)], dtype=np.float32),
                    h_star_pose[:2], r_star)
                if b_int == 1:
                    # maximum distance to move in the direction of theta
                    eta = min(eta, np.linalg.norm(agent_pose[:2] - int_position))
                q = np.array([v_h_hat * np.cos(theta_star) + eta * np.cos(theta),
                              v_h_hat * np.sin(theta_star) + eta * np.sin(theta)])
                d_theta = np.arctan2(q[1], q[0]) % (2 * np.pi)
                d_v = np.linalg.norm(q)
                return d_theta, d_v, var_theta, search_message

        # (1) CAGING
        gamma_o = np.arctan2(agent_pose[1] - h_star_pose[1], agent_pose[0] - h_star_pose[0])
        beta = 1 if gamma_o >= 0 else -1

        a_indexes = np.logical_and(0.0 < agents_dist2, agents_dist2 <= zoi_a ** 2)
        if np.any(a_indexes):
            agents = agents_all[a_indexes]
            # compute agent (neighbour) variables
            p_tilde = agents[:, :2] - h_star_pose[:2]
            gamma_agents = gamma_o - np.arctan2(p_tilde[:, 1], p_tilde[:, 0])
            a_bar_indexes = np.logical_and(0 < beta * gamma_agents, beta * gamma_agents <= np.pi)
            a_under_indexes = ~a_bar_indexes
            d_bar = d_under = 2 * mu - 2 * eps_a
            if np.any(a_bar_indexes):
                d_bar = np.sqrt(np.min(agents_dist2[a_indexes][a_bar_indexes]))
            if np.any(a_under_indexes):
                d_under = np.sqrt(np.min(agents_dist2[a_indexes][a_under_indexes]))
            # caging logic
            if abs(d_bar - d_under) <= eps_a / 2:
                if 0 <= d_star - r_star <= eps_h:
                    d_theta = theta_star % (2 * np.pi)
                    d_v = v_h_hat
                    return d_theta, d_v, var_theta, search_message
                # else use var_theta of earlier time step
            else:
                var_theta = beta if d_bar < d_under else -beta
        # move along the circular path around the herd
        theta = gamma_o + var_theta * (np.pi / 2 + np.arctan(tau * (d_star - r_star)))
        # desired motion vector
        q = np.array([v_h_hat * np.cos(theta_star) + eta * np.cos(theta),
                      v_h_hat * np.sin(theta_star) + eta * np.sin(theta)])
        d_theta = np.arctan2(q[1], q[0]) % (2 * np.pi)
        d_v = np.linalg.norm(q)
        return d_theta, d_v, var_theta, search_message
    else:
        d_theta, search_message = searching_model(p=agents_all,
                                                  c=search_msg_all,
                                                  i=i,
                                                  zor=2 * eps_a,
                                                  zoo=zoo_a,
                                                  zoa=zoa_a,
                                                  zoi=zoi_a)
        d_v = v_a_max
        return d_theta, d_v, var_theta, search_message


@numba.jit(nopython=True, cache=True, fastmath=True)
def run_simulation(n_agents,
                   n_school,
                   model_s,
                   knn_s,
                   klr_s,
                   zor_s,
                   zoo_s,
                   zoa_s,
                   kor_s,
                   koo_s,
                   koa_s,
                   sigma_a,
                   sigma_s,
                   rho_a,
                   rho_s,
                   v_a_max,
                   v_s_max,
                   v_s_avg,
                   w_a_max,
                   w_s_max,
                   mu,
                   tau,
                   t_max,
                   dt=1., ):
    # derived params
    r_star, delta = mu + 2 * v_s_max, 2 * mu
    zoi_a = 1.25 * delta
    l_size_a, l_size_s = np.sqrt(n_agents / rho_a), np.sqrt(n_school / rho_s)

    time_space = get_time_space_batch_end()

    # initialize random school poses
    school_poses = np.zeros((len(time_space), n_school, 3), dtype=np.float32)
    school_poses[0] = np.random.rand(n_school, 3) * l_size_s - l_size_s / 2
    school_poses[0, :, 2] = np.random.randn(n_school) * sigma_s

    # initialize agent poses, semi-random (close to school)
    if n_agents > 0:
        agent_poses = np.zeros((len(time_space), n_agents, 3), dtype=np.float32)
        psi_xy = np.random.randint(0, 4) * np.pi / 2  # at a random side of the school
        psi_o = (psi_xy + np.pi) % (2 * np.pi)
        init_d = l_size_s / 2 + 0.5 * zoi_a
        agent_poses[0, 0] = np.array([np.cos(psi_xy) * init_d, np.sin(psi_xy) * init_d, psi_o], dtype=np.float32)
        agent_poses[0, 1:, 0] = np.cos(psi_xy) * (init_d + np.sqrt(2) * l_size_a / 2) + (
                2 * np.random.rand(n_agents - 1) - 1) * (np.sqrt(2) * l_size_a / 2)
        agent_poses[0, 1:, 1] = np.sin(psi_xy) * (init_d + np.sqrt(2) * l_size_a / 2) + (
                2 * np.random.rand(n_agents - 1) - 1) * (np.sqrt(2) * l_size_a / 2)
        agent_poses[0, 1:, 2] = psi_o + np.random.randn(n_agents - 1) * sigma_a
    else:
        agent_poses = np.zeros((len(time_space), 1, 3), dtype=np.float32)

    # system dynamics over time
    current_school_poses = np.copy(school_poses[0])
    current_agent_poses = np.copy(agent_poses[0])
    v_a, v_s = np.full((n_agents,), v_a_max), np.full((n_school,), v_s_max)
    var_thetas = np.full((n_agents,), 1)
    current_search_messages = np.full((n_agents,), 1)
    _t = 1
    for t in range(1, t_max + 1):
        # # AGENTS
        next_agent_poses = np.zeros_like(current_agent_poses)
        # compute next position
        if n_agents > 0:
            next_agent_poses[:, 0] = current_agent_poses[:, 0] + v_a * np.cos(current_agent_poses[:, 2])
            next_agent_poses[:, 1] = current_agent_poses[:, 1] + v_a * np.sin(current_agent_poses[:, 2])
        # compute next orientation
        for i in range(n_agents):
            # desired orientation [0, 2π]
            d_theta, d_v, var_theta, search_message = caging_2d_model(agents_all=current_agent_poses,
                                                                      school_all=current_school_poses,
                                                                      i=i,
                                                                      var_theta=var_thetas[i],
                                                                      search_msg_all=current_search_messages,
                                                                      mu=mu,
                                                                      v_a_max=v_a_max,
                                                                      v_h_max=v_s_max,
                                                                      v_h_avg=v_s_avg,
                                                                      tau=tau)
            # necessary turn
            turn = current_agent_poses[i, 2] - d_theta
            # converted to [-π, π]
            turn = (turn + np.pi) % (2 * np.pi) - np.pi
            # rotating duration (limited)
            dt_w = min(abs(turn) / w_a_max, dt)
            # limited turn
            turn = np.sign(turn) * w_a_max * dt_w
            # update orientation (noisy)
            next_agent_poses[i, 2] = (current_agent_poses[i, 2] - turn + np.random.randn() * sigma_a) % (2 * np.pi)
            # remaining velocity to move
            v_a[i] = min(d_v, v_a_max * (dt - dt_w))
            # save current var_theta
            var_thetas[i] = var_theta
            # save current communication
            current_search_messages[i] = search_message
        # # SCHOOL
        next_school_poses = np.zeros_like(current_school_poses)
        # compute next position
        next_school_poses[:, 0] = current_school_poses[:, 0] + v_s * np.cos(current_school_poses[:, 2])
        next_school_poses[:, 1] = current_school_poses[:, 1] + v_s * np.sin(current_school_poses[:, 2])
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
            d_theta = np.arctan2(force[1], force[0]) % (2 * np.pi)
            # necessary turn
            turn = current_school_poses[i, 2] - d_theta
            # converted to [-π, π]
            turn = (turn + np.pi) % (2 * np.pi) - np.pi
            # rotating duration (limited)
            dt_w = min(abs(turn) / w_s_max, dt)
            # limited turn
            turn = np.sign(turn) * w_s_max * dt_w
            # remaining duration to move
            next_school_poses[i, 2] = (current_school_poses[i, 2] - turn + np.random.randn() * sigma_s) % (2 * np.pi)
            # remaining duration to move
            v_s[i] = v_s_max * (dt - dt_w)
        # memory swap and store
        current_agent_poses = np.copy(next_agent_poses)
        current_school_poses = np.copy(next_school_poses)
        if t in time_space:
            agent_poses[_t] = np.copy(current_agent_poses)
            school_poses[_t] = np.copy(current_school_poses)
            _t += 1

    return school_poses, agent_poses
