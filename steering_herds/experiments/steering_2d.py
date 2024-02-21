import numba
import numpy as np

from experiments.caging_2d import searching_model
from experiments.school_models import metric_model, topological_model, visual_model, longrange_model
from utils import maths

NUMBA_NULL = np.inf


@numba.jit(nopython=True, cache=True, fastmath=True)
def patch_potential_gradient(agent_pose, patch_poses, mu=19., zoi_a=None, zoi_d=None):
    if not zoi_a:
        delta = 2 * mu
        zoi_a = 1.5 * delta
    if not zoi_d:
        zoi_d = 1.25 * zoi_a

    if np.any(np.isinf(patch_poses)):
        potential = NUMBA_NULL
        gradient = np.array([NUMBA_NULL, NUMBA_NULL])
    else:
        dist = np.sqrt(np.sum((patch_poses[:, :2] - agent_pose[:2]) ** 2, axis=1))
        i_q = dist <= zoi_d
        if not np.any(i_q):
            potential = NUMBA_NULL
            gradient = np.array([NUMBA_NULL, NUMBA_NULL])
        else:
            q = -np.sum((patch_poses[i_q, :2] - agent_pose[:2]), axis=0)
            potential = -np.linalg.norm(q)
            q_angle = np.arctan2(q[1], q[0]) % (2 * np.pi)
            gradient = np.array([np.cos(q_angle), np.sin(q_angle)])

    return potential, gradient.astype(np.float32)


@numba.jit(nopython=True, cache=True, fastmath=True)
def enclosure_potential_gradient(agent_pose, encl_center, encl_radius, mu=19., zoi_a=None, zoi_d=None):
    if not zoi_a:
        delta = 2 * mu
        zoi_a = 1.5 * delta
    if not zoi_d:
        zoi_d = 1.25 * zoi_a

    if np.any(np.isinf(encl_center)):
        potential = NUMBA_NULL
        gradient = np.array([NUMBA_NULL, NUMBA_NULL])
    else:
        q = encl_center - agent_pose[:2]
        q_norm = np.linalg.norm(q)
        if encl_radius - q_norm > zoi_d:
            potential = NUMBA_NULL
            gradient = np.array([NUMBA_NULL, NUMBA_NULL])
        else:
            potential = q_norm
            q_angle = np.arctan2(q[1], q[0]) % (2 * np.pi)
            gradient = np.array([np.cos(q_angle), np.sin(q_angle)])
    return potential, gradient.astype(np.float32)


@numba.jit(nopython=True, cache=True, fastmath=True)
def steering_2d_model(agents_all, school_all, scenario, i, potential, gradient, var_theta, search_msg_all,
                      steer_msg_all,
                      eta=.5,
                      mu=19.,
                      v_a_max=6.,
                      v_h_max=2.,
                      v_h_avg=2.,
                      eps_a=None,
                      eps_h=None,
                      zoi_a=None,
                      tau=0.1, ):
    delta = 2 * mu

    e_star = 2 * v_h_max + eta
    r_star = mu + e_star

    e_steer = v_h_max
    R_star = r_star + mu / 2

    if not eps_a:
        eps_a = v_h_max
    if not eps_h:
        eps_h = 3 * v_h_max
    if not zoi_a:
        zoi_a = 1.5 * delta
    zor_h = 1
    zor_a = 1
    zoo_a = zoi_a - zor_a
    zoa_a = 0.

    # initialize variables
    v_h_hat = v_h_max
    agent_pose = agents_all[i]
    n_agents = agents_all.shape[0]

    school_dist2 = np.sum((school_all[:, :2] - agent_pose[:2]) ** 2, axis=1)
    h_indexes = school_dist2 <= zoi_a ** 2
    steer_message = np.full((n_agents, 4), NUMBA_NULL, dtype=np.float32)
    steer_message[:, 0] = 0
    if np.any(h_indexes):
        search_message = 1

        # filter herd neighbours
        school_dist2 = school_dist2[h_indexes]
        h_star = np.argmin(school_dist2)
        h_star_pose = school_all[h_indexes][h_star]
        d_star = np.sqrt(school_dist2[h_star])
        theta_star = h_star_pose[2]
        # theta_star = np.arctan2(np.mean(np.sin(school_all[h_indexes, 2])),
        #                         np.mean(np.cos(school_all[h_indexes, 2]))) % (2 * np.pi)

        # filter agent neighbours
        agents_dist2 = np.sum((agents_all[:, :2] - agent_pose[:2]) ** 2, axis=1)
        a_indexes = np.logical_and(0.0 < agents_dist2, agents_dist2 <= zoi_a ** 2)

        # (1) STEERING - generate steering messages (before COLLISION AVOIDANCE)
        steer_message[i] = np.array([steer_msg_all[i, i, 0] + 1, potential, gradient[0], gradient[1]])
        potentials, gradients_x, gradients_y = [], [], []
        if not np.isinf(potential):
            potentials.append(potential)
            gradients_x.append(gradient[0])
            gradients_y.append(gradient[1])
        if np.any(a_indexes):
            steer_messages = steer_msg_all[a_indexes]
            for a_j in range(n_agents):
                if a_j != i:
                    a_i = np.argmax(steer_messages[:, a_j, 0])
                    steer_message[a_j] = steer_messages[a_i, a_j]
                    if not np.isinf(steer_message[a_j, 1]):
                        potentials.append(steer_message[a_j, 1])
                        gradients_x.append(steer_message[a_j, 2])
                        gradients_y.append(steer_message[a_j, 3])
        b_steering = len(potentials) > 0
        if b_steering:
            if scenario == "predator" or scenario == "enclosure" or scenario == "patchs":
                gradients_x, gradients_y = np.array(gradients_x), np.array(gradients_y)
                d_theta = np.arctan2(np.sum(gradients_y), np.sum(gradients_x)) % (2 * np.pi)
            if scenario == "path":
                d_theta = np.arctan2(gradient[1], gradient[0]) % (2 * np.pi)

        # (0) COLLISION AVOIDANCE WITH HERD
        h_col_indexes = school_dist2 <= zor_h ** 2
        if np.any(h_col_indexes):
            q = -np.sum(maths.row_normalize(school_all[h_col_indexes, :2] - agent_pose[:2]), axis=0)
            d_theta = np.arctan2(q[1], q[0]) % (2 * np.pi)
            d_v = np.linalg.norm(q)
            return d_theta, d_v, var_theta, search_message, steer_message

        # (1) STEERING
        gamma_o = np.arctan2(agent_pose[1] - h_star_pose[1], agent_pose[0] - h_star_pose[0])
        beta = 1 if gamma_o >= 0 else -1

        d_bound = R_star
        b_active_steering = False
        if b_steering:
            close_h_indexes = school_dist2 <= (mu + v_h_max) ** 2
            if np.any(close_h_indexes):
                gammas = np.arctan2(agent_pose[1] - school_all[close_h_indexes, 1],
                                    agent_pose[0] - school_all[close_h_indexes, 0])
                b_active_steering = True
                for gamma in gammas:
                    b_active_steering = b_active_steering and abs(
                        np.arctan2(np.sin(d_theta - gamma), np.cos(d_theta - gamma))) > np.pi / 2
                if b_active_steering:
                    d_bound = mu - e_steer
            else:
                # if robot is behind the herd and should steer into the herd
                if abs(np.arctan2(np.sin(d_theta - gamma_o), np.cos(d_theta - gamma_o))) > np.pi / 2:
                    d_bound = mu - e_steer
                    b_active_steering = True

        # (0) AVOID ENTERING HERD AREA at d_bound
        if d_star - d_bound <= -e_star:
            d = -(h_star_pose[:2] - agent_pose[:2]) / np.linalg.norm(h_star_pose[:2] - agent_pose[:2])
            theta = np.arctan2(d[1], d[0]) % (2 * np.pi)
            eta = -v_h_hat * np.cos(theta_star - theta) + np.sqrt(
                (v_h_hat ** 2) * (np.cos(theta_star - theta) ** 2 - 1) + v_a_max ** 2)
            q = np.array([v_h_hat * np.cos(theta_star) + eta * np.cos(theta),
                          v_h_hat * np.sin(theta_star) + eta * np.sin(theta)])
            d_theta = np.arctan2(q[1], q[0]) % (2 * np.pi)
            d_v = np.linalg.norm(q)
            return d_theta, d_v, var_theta, search_message, steer_message
        # (0) COLLISION AVOIDANCE WITH AGENTS
        if d_star >= d_bound:
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
                return d_theta, d_v, var_theta, search_message, steer_message

        # (2) CAGING
        if np.any(a_indexes):
            agents = agents_all[a_indexes]
            # compute agent (neighbour) variables
            p_tilde = agents[:, :2] - h_star_pose[:2]
            gamma_agents = gamma_o - np.arctan2(p_tilde[:, 1], p_tilde[:, 0])
            a_bar_indexes = np.logical_and(0 < beta * gamma_agents, beta * gamma_agents <= np.pi)
            a_under_indexes = ~a_bar_indexes
            d_bar = d_under = 2 * mu - eps_a
            if np.any(a_bar_indexes):
                d_bar = np.sqrt(np.min(agents_dist2[a_indexes][a_bar_indexes]))
            if np.any(a_under_indexes):
                d_under = np.sqrt(np.min(agents_dist2[a_indexes][a_under_indexes]))
            # caging logic
            if abs(d_bar - d_under) <= eps_a / 2:
                if 0 <= d_star - d_bound <= eps_h:
                    d_theta = theta_star % (2 * np.pi)
                    d_v = v_h_hat
                    return d_theta, d_v, var_theta, search_message, steer_message
            else:
                var_theta = beta if d_bar < d_under else -beta
        # move along the circular path around the herd
        theta = gamma_o + var_theta * (np.pi / 2 + np.arctan(tau * (d_star - d_bound)))
        # overwrite normal caging logic -> move to steering-radius (d_bound=r_star) as fast as possible!
        if b_active_steering:
            if d_star - d_bound > eps_h:
                eta = -v_h_hat * np.cos(theta_star - theta) + np.sqrt(
                    (v_h_hat ** 2) * (np.cos(theta_star - theta) ** 2 - 1) + v_a_max ** 2)
        # desired motion vector
        q = np.array([v_h_hat * np.cos(theta_star) + eta * np.cos(theta),
                      v_h_hat * np.sin(theta_star) + eta * np.sin(theta)])
        d_theta = np.arctan2(q[1], q[0]) % (2 * np.pi)
        d_v = np.linalg.norm(q)
    else:
        d_theta, search_message = searching_model(p=agents_all,
                                                  c=search_msg_all,
                                                  i=i,
                                                  zor=2 * eps_a,
                                                  zoo=zoo_a,
                                                  zoa=zoa_a,
                                                  zoi=zoi_a)
        d_v = v_a_max
    return d_theta, d_v, var_theta, search_message, steer_message


@numba.jit(nopython=True, cache=True, fastmath=True)
def run_simulation(scenario,
                   n_agents,
                   n_school,
                   n_predators,
                   model_s,
                   knn_s,
                   klr_s,
                   kor_s,
                   koo_s,
                   koa_s,
                   kox_s,
                   koz_s,
                   sigma_a,
                   sigma_s,
                   rho_a,
                   rho_s,
                   v_a_max,
                   v_s_max,
                   v_s_avg,
                   v_z_max,
                   w_a_max,
                   w_s_max,
                   zor_s,
                   zoo_s,
                   zoa_s,
                   zoi_a,
                   zoi_d,
                   mu,
                   eta,
                   tau,
                   t_z,
                   t_z_end,
                   t_max,
                   dt=1., ):
    # derived params
    l_size_a, l_size_s = np.sqrt(n_agents / rho_a), np.sqrt(n_school / rho_s)

    time_space = [0] + list(range(920, 1000))  # get_long_recovering_time_space_batch_end()

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

    # allocate zone poses
    # if scenario == "patches":
    n_patches = 1
    patch_time_period = 100
    patch_mul = 1.1
    patch_timesteps = [83, 193, 324, 466, 626, 773, 950, 1079, 1247, 1365, 1515, 1654, 1811, 1961, 2139]
    patch_timesteps = [o_t + t_z for o_t in patch_timesteps]
    patch_poses = np.full((len(time_space), n_patches, 3), NUMBA_NULL, dtype=np.float32)
    # if scenario == "enclosure":
    enclosure_shape = np.full((len(time_space), 3), NUMBA_NULL, dtype=np.float32)  # center_x, center_y, radius

    # system dynamics over time
    current_school_poses = np.copy(school_poses[0])
    current_agent_poses = np.copy(agent_poses[0])
    if scenario == "patches":
        current_patch_poses = np.copy(patch_poses[0])
    if scenario == "enclosure":
        current_enclosure_shape = np.copy(enclosure_shape[0])
    v_a, v_s = np.full((n_agents,), v_a_max), np.full((n_school,), v_s_max)
    var_thetas = np.full((n_agents,), 1)
    current_search_messages = np.full((n_agents,), 1)
    current_steer_messages = np.full((n_agents, n_agents, 4), NUMBA_NULL, dtype=np.float32)
    current_steer_messages[:, :, 0] = 0
    _t = 1
    for t in range(1, t_max + 1):
        # # AGENTS
        next_agent_poses = np.zeros_like(current_agent_poses)
        next_search_messages = np.zeros_like(current_search_messages)
        next_steer_messages = np.zeros_like(current_steer_messages)
        if n_agents > 0:
            # compute next position
            next_agent_poses[:, 0] = current_agent_poses[:, 0] + v_a * np.cos(current_agent_poses[:, 2])
            next_agent_poses[:, 1] = current_agent_poses[:, 1] + v_a * np.sin(current_agent_poses[:, 2])
        # compute next orientation
        for i in range(n_agents):
            # potential and gradient
            if scenario == "patches":
                potential, gradient = patch_potential_gradient(current_agent_poses[i],
                                                               current_patch_poses,
                                                               mu=mu, zoi_a=zoi_a, zoi_d=zoi_d)
            if scenario == "enclosure":
                potential, gradient = enclosure_potential_gradient(current_agent_poses[i],
                                                                   current_enclosure_shape[:2],
                                                                   current_enclosure_shape[2],
                                                                   mu=mu, zoi_a=zoi_a, zoi_d=zoi_d)
            # desired orientation [0, 2π]
            d_theta, d_v, var_theta, search_message, steer_message = steering_2d_model(agents_all=current_agent_poses,
                                                                                       school_all=current_school_poses,
                                                                                       scenario=scenario,
                                                                                       i=i,
                                                                                       potential=potential,
                                                                                       gradient=gradient,
                                                                                       var_theta=var_thetas[i],
                                                                                       search_msg_all=current_search_messages,
                                                                                       steer_msg_all=current_steer_messages,
                                                                                       eta=eta,
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
            # remaining duration to move
            v_a[i] = min(d_v, v_a_max * (dt - dt_w))
            # save current var_theta
            var_thetas[i] = var_theta
            # save current search communication
            next_search_messages[i] = search_message
            next_steer_messages[i] = steer_message
        # # SCHOOL
        next_school_poses = np.zeros_like(current_school_poses)
        # compute next position
        next_school_poses[:, 0] = current_school_poses[:, 0] + v_s * np.cos(current_school_poses[:, 2])
        next_school_poses[:, 1] = current_school_poses[:, 1] + v_s * np.sin(current_school_poses[:, 2])
        # compute next orientation
        for i in range(n_school):
            # desired orientation [0, 2π]
            if scenario == "patches":
                if model_s == "METRIC":
                    force = metric_model.metric_normalized_predator_prey_model(p_h=current_school_poses,
                                                                               p_a=current_agent_poses,
                                                                               p_z=current_patch_poses,
                                                                               i=i, zor=zor_s, zoo=zoo_s, zoa=zoa_s,
                                                                               zox=mu, zoz=mu, k_r=kor_s, k_o=koo_s,
                                                                               k_a=koa_s, k_x=kox_s, k_z=koz_s)
                elif model_s == "TOPOLOGICAL":
                    force = topological_model.topological_normalized_predator_prey_model(p_h=current_school_poses,
                                                                                         p_a=current_agent_poses,
                                                                                         p_z=current_patch_poses,
                                                                                         i=i, m=knn_s, zor=zor_s,
                                                                                         zoo=zoo_s, zoa=zoa_s,
                                                                                         zox=mu, zoz=mu, k_r=kor_s,
                                                                                         k_o=koo_s, k_a=koa_s,
                                                                                         k_x=kox_s, k_z=koz_s)
                elif model_s == "VISUAL":
                    force = visual_model.visual_normalized_predator_prey_model(p_h=current_school_poses,
                                                                               p_a=current_agent_poses,
                                                                               p_z=current_patch_poses,
                                                                               i=i, zor=zor_s,
                                                                               zoo=zoo_s, zoa=zoa_s,
                                                                               zox=mu, zoz=mu, k_r=kor_s,
                                                                               k_o=koo_s, k_a=koa_s,
                                                                               k_x=kox_s, k_z=koz_s)
                elif model_s == "LONGRANGE":
                    force = longrange_model.longrange_normalized_predator_prey_model(p_h=current_school_poses,
                                                                                     p_a=current_agent_poses,
                                                                                     p_z=current_patch_poses,
                                                                                     i=i, m=knn_s, kap=klr_s, zor=zor_s,
                                                                                     zoo=zoo_s, zoa=zoa_s,
                                                                                     zox=mu, zoz=mu, k_r=kor_s,
                                                                                     k_o=koo_s, k_a=koa_s,
                                                                                     k_x=kox_s, k_z=koz_s)
                else:
                    force = np.zeros(2)
            elif scenario == "enclosure":
                if model_s == "METRIC":
                    force = metric_model.metric_normalized_enclosure_model(p_h=current_school_poses,
                                                                           p_a=current_agent_poses,
                                                                           c_z=current_enclosure_shape[:2],
                                                                           r_z=current_enclosure_shape[2],
                                                                           i=i, zor=zor_s, zoo=zoo_s, zoa=zoa_s,
                                                                           zox=mu, zoz=0, k_r=kor_s, k_o=koo_s,
                                                                           k_a=koa_s, k_x=kox_s, k_z=koz_s)
                elif model_s == "TOPOLOGICAL":
                    force = topological_model.topological_normalized_enclosure_model(p_h=current_school_poses,
                                                                                     p_a=current_agent_poses,
                                                                                     c_z=current_enclosure_shape[:2],
                                                                                     r_z=current_enclosure_shape[2],
                                                                                     i=i, m=knn_s, zor=zor_s,
                                                                                     zoo=zoo_s, zoa=zoa_s,
                                                                                     zox=mu, zoz=0, k_r=kor_s,
                                                                                     k_o=koo_s, k_a=koa_s,
                                                                                     k_x=kox_s, k_z=koz_s)
                elif model_s == "VISUAL":
                    force = visual_model.visual_normalized_enclosure_model(p_h=current_school_poses,
                                                                           p_a=current_agent_poses,
                                                                           c_z=current_enclosure_shape[:2],
                                                                           r_z=current_enclosure_shape[2],
                                                                           i=i, zor=zor_s,
                                                                           zoo=zoo_s, zoa=zoa_s,
                                                                           zox=mu, zoz=0, k_r=kor_s,
                                                                           k_o=koo_s, k_a=koa_s,
                                                                           k_x=kox_s, k_z=koz_s)
                elif model_s == "LONGRANGE":
                    force = longrange_model.longrange_normalized_enclosure_model(p_h=current_school_poses,
                                                                                 p_a=current_agent_poses,
                                                                                 c_z=current_enclosure_shape[:2],
                                                                                 r_z=current_enclosure_shape[2],
                                                                                 i=i, m=knn_s, kap=klr_s, zor=zor_s,
                                                                                 zoo=zoo_s, zoa=zoa_s,
                                                                                 zox=mu, zoz=0, k_r=kor_s,
                                                                                 k_o=koo_s, k_a=koa_s,
                                                                                 k_x=kox_s, k_z=koz_s)
                else:
                    force = np.zeros(2)
            else:  # includes scenario == "path":
                if model_s == "METRIC":
                    force = metric_model.metric_normalized_aversive_model(p_h=current_school_poses,
                                                                          p_a=current_agent_poses,
                                                                          i=i, zor=zor_s, zoo=zoo_s, zoa=zoa_s,
                                                                          zox=mu, k_r=kor_s, k_o=koo_s,
                                                                          k_a=koa_s, k_x=kox_s)
                elif model_s == "TOPOLOGICAL":
                    force = topological_model.topological_normalized_aversive_model(p_h=current_school_poses,
                                                                                    p_a=current_agent_poses,
                                                                                    i=i, m=knn_s, zor=zor_s,
                                                                                    zoo=zoo_s, zoa=zoa_s,
                                                                                    zox=mu, k_r=kor_s,
                                                                                    k_o=koo_s, k_a=koa_s,
                                                                                    k_x=kox_s, )
                elif model_s == "VISUAL":
                    force = visual_model.visual_normalized_aversive_model(p_h=current_school_poses,
                                                                          p_a=current_agent_poses,
                                                                          i=i, zor=zor_s,
                                                                          zoo=zoo_s, zoa=zoa_s,
                                                                          zox=mu, k_r=kor_s,
                                                                          k_o=koo_s, k_a=koa_s,
                                                                          k_x=kox_s, )
                elif model_s == "LONGRANGE":
                    force = longrange_model.longrange_normalized_aversive_model(p_h=current_school_poses,
                                                                                p_a=current_agent_poses,
                                                                                i=i, m=knn_s, kap=klr_s, zor=zor_s,
                                                                                zoo=zoo_s, zoa=zoa_s,
                                                                                zox=mu, k_r=kor_s,
                                                                                k_o=koo_s, k_a=koa_s,
                                                                                k_x=kox_s, )
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
        # # SCENARIOS
        if t == t_z:
            # initialize danger zone poses (when caging is established), deterministic (close to agents)
            school_mean_orientation = np.arctan2(np.mean(np.sin(current_school_poses[:, 2])),
                                                 np.mean(np.cos(current_school_poses[:, 2]))) % (2 * np.pi)
            school_centroid = np.array([np.mean(current_school_poses[:, 0]), np.mean(current_school_poses[:, 1])])
            agents_box_size = np.sqrt(
                (np.max(current_agent_poses[:, 0]) - np.min(current_agent_poses[:, 0])) *
                (np.max(current_agent_poses[:, 1]) - np.min(current_agent_poses[:, 1]))
            )
            school_mean_direction = np.array([np.cos(school_mean_orientation), np.sin(school_mean_orientation)])
            # zone_position = school_centroid + 2 * agents_box_size * school_mean_direction
            # focal_agent = np.argmin(
            #     np.sum((current_agent_poses[:, :2] - zone_position) ** 2, axis=1)
            # )
            if scenario == "patches":
                school_box_size = np.sqrt(
                    (np.max(current_school_poses[:, 0]) - np.min(current_school_poses[:, 0])) *
                    (np.max(current_school_poses[:, 1]) - np.min(current_school_poses[:, 1]))
                )
                zone_position = school_centroid + 2 * school_box_size * school_mean_direction
                focal_school = np.argmin(
                    np.sum((current_school_poses[:, :2] - zone_position) ** 2, axis=1)
                )
                for i in range(n_patches):
                    patch_start_position = current_school_poses[focal_school, :2]
                    patch_start_direction = np.array([
                        np.cos(school_mean_orientation), np.sin(school_mean_orientation)
                    ])
                    current_patch_poses[i, :2] = patch_start_position + patch_mul * zoi_a * patch_start_direction
                    # chi_xy = current_patch_poses[i, :2] - current_school_poses[np.argmin(
                    #     np.sum((current_school_poses[:, :2] - current_patch_poses[i, :2]) ** 2, axis=1)
                    # ), :2]
                    # chi = (np.arctan2(chi_xy[1], chi_xy[0]) + np.pi) % (2 * np.pi)
                    # current_patch_poses[i, 2] = chi + (1 if random.random() < 0.5 else -1) * 0.5 * np.pi
                    current_patch_poses[i, 2] = 0
            if scenario == "enclosure":
                current_enclosure_shape[:2] = school_centroid
                box_size = agents_box_size
                if n_agents == 0:
                    school_box_size = np.sqrt(
                        (np.max(current_school_poses[:, 0]) - np.min(current_school_poses[:, 0])) *
                        (np.max(current_school_poses[:, 1]) - np.min(current_school_poses[:, 1]))
                    )
                    box_size = school_box_size
                current_enclosure_shape[2] = box_size + 1.1 * zoi_a
        if t_z < t <= t_z_end:
            if scenario == "patches":
                next_patch_poses = np.copy(current_patch_poses)
                for i in range(n_patches):
                    if t in patch_timesteps:
                        # if (t - t_z) % patch_time_period == 0:
                        school_mean_orientation = np.arctan2(np.mean(np.sin(current_school_poses[:, 2])),
                                                             np.mean(np.cos(current_school_poses[:, 2]))) % (2 * np.pi)
                        school_centroid = np.array(
                            [np.mean(current_school_poses[:, 0]), np.mean(current_school_poses[:, 1])])
                        school_mean_direction = np.array(
                            [np.cos(school_mean_orientation), np.sin(school_mean_orientation)])
                        school_box_size = np.sqrt(
                            (np.max(current_school_poses[:, 0]) - np.min(current_school_poses[:, 0])) *
                            (np.max(current_school_poses[:, 1]) - np.min(current_school_poses[:, 1]))
                        )
                        zone_position = school_centroid + 2 * school_box_size * school_mean_direction
                        focal_school = np.argmin(
                            np.sum((current_school_poses[:, :2] - zone_position) ** 2, axis=1)
                        )
                        patch_start_position = current_school_poses[focal_school, :2]
                        patch_start_direction = np.array([
                            np.cos(school_mean_orientation), np.sin(school_mean_orientation)
                        ])
                        next_patch_poses[i, :2] = patch_start_position + patch_mul * zoi_a * patch_start_direction
                        next_patch_poses[i, 2] = 0
                current_patch_poses = np.copy(next_patch_poses)
            if scenario == "enclosure":
                current_enclosure_shape[2] = max(1.5 * l_size_s, current_enclosure_shape[2] - v_z_max)
        if t > t_z_end:
            if scenario == "enclosure":
                current_enclosure_shape.fill(NUMBA_NULL)
        # memory swap and store
        current_agent_poses = np.copy(next_agent_poses)
        current_search_messages = np.copy(next_search_messages)
        current_steer_messages = np.copy(next_steer_messages)
        current_school_poses = np.copy(next_school_poses)
        # # SAVE
        if t in time_space:
            agent_poses[_t] = np.copy(current_agent_poses)
            school_poses[_t] = np.copy(current_school_poses)
            if scenario == "patches":
                patch_poses[_t] = np.copy(current_patch_poses)
            if scenario == "enclosure":
                enclosure_shape[_t] = np.copy(current_enclosure_shape)
            _t += 1

    return school_poses, agent_poses, patch_poses, enclosure_shape
