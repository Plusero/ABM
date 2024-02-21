import numpy as np


# PREDATOR
def metric_distance_predator():
    def compute(t, poses_agent, poses_school, poses_predator):
        poses_school_t = np.copy(poses_school[t])
        poses_predator_t = np.copy(poses_predator[t])

        distances = []
        for p_pose in poses_predator_t:
            distance = np.sqrt(np.sum((poses_school_t[:, :2] - p_pose[:2]) ** 2, axis=1))
            distances.append(distance)

        return np.mean(distances)

    return compute


def metric_distance_predator_nearest_prey():
    def compute(t, poses_agent, poses_school, poses_predator):
        poses_school_t = np.copy(poses_school[t])
        poses_predator_t = np.copy(poses_predator[t])

        min_dist = np.inf
        for p_pose in poses_predator_t:
            distance = np.sqrt(np.min(np.sum((poses_school_t[:, :2] - p_pose[:2]) ** 2, axis=1)))
            min_dist = min(min_dist, distance)
        return min_dist

    return compute


def metric_predator_prey_death_ratio(predator_distance_threshold, predator_prey_death_probability):
    def compute(poses_agent, poses_school, poses_predator):
        n_school = poses_school.shape[1]
        school_alive_bool = np.ones(n_school, dtype=bool)
        for t, poses_school_t in poses_school:
            poses_predator_t = poses_predator[t, :]
            for predator_pose in poses_predator_t:
                dist = np.sqrt(np.sum((poses_school_t[:, :2] - predator_pose[:2]) ** 2, axis=1))
                school_attacked_bool = dist < predator_distance_threshold
                random_bool = np.random.rand(n_school) <= predator_prey_death_probability
                school_death_bool = np.logical_and(school_attacked_bool, random_bool)
                school_alive_bool = np.logical_and(school_alive_bool, np.logical_not(school_death_bool))
        return 1 - (sum(school_alive_bool) / n_school)

    return compute


def metric_number_of_prey_in_proximity(threshold):
    def compute(t, poses_agent, poses_school, poses_predator):
        poses_school_t = np.copy(poses_school[t])
        n_school = poses_school.shape[1]
        poses_predator_t = np.copy(poses_predator[t])

        i_prox = np.zeros(n_school, dtype=bool)
        for p_pose in poses_predator_t:
            distance = np.sqrt(np.sum((poses_school_t[:, :2] - p_pose[:2]) ** 2, axis=1))
            i_prox = np.logical_or(i_prox, distance <= threshold)
        return np.sum(i_prox) / n_school

    return compute


def metric_duration_of_prey_in_proximity(threshold, t_z=73):
    def compute(poses_agent, poses_school, poses_predator):
        poses_school_all = np.copy(poses_school[t_z:])
        n_school = poses_school.shape[1]

        durations = np.zeros(n_school)
        for t_prime, poses_school_t in enumerate(poses_school_all[:]):
            i_prox = np.zeros(n_school, dtype=bool)
            for p_pose in poses_predator[t_prime]:
                dist = np.sqrt(np.sum((poses_school_t[:, :2] - p_pose[:2]) ** 2, axis=1))
                i_prox = np.logical_or(i_prox, dist <= threshold)
            durations[i_prox] += 1

        if np.any(durations > 0):
            return np.mean(durations[durations > 0])
        else:
            return 0.

    return compute


# OBJECTS
def metric_number_of_prey_in_range(threshold):
    def compute(t, poses_agent, poses_school, poses_predator):
        poses_school_t = np.copy(poses_school[t])
        n_school = poses_school.shape[1]
        poses_predator_t = np.copy(poses_predator[t])

        i_prox = np.zeros(n_school, dtype=bool)
        for p_pose in poses_predator_t:
            distance = np.sqrt(np.sum((poses_school_t[:, :2] - p_pose[:2]) ** 2, axis=1))
            i_prox = np.logical_or(i_prox, distance <= threshold)
        return np.sum(i_prox) / n_school

    return compute


# ENCLOSURE
def metric_relative_distance_enclosure():
    def compute(t, poses_agent, poses_school, poses_enclosure):
        poses_school_t = np.copy(poses_school[t])
        pose_enclosure_t = np.copy(poses_enclosure[t])

        distance = np.sqrt(np.sum((poses_school_t[:, :2] - pose_enclosure_t[:2]) ** 2, axis=1))
        return pose_enclosure_t[2] - np.mean(distance)

    return compute


def metric_relative_distance_enclosure_furthest_prey():
    def compute(t, poses_agent, poses_school, poses_enclosure):
        poses_school_t = np.copy(poses_school[t])
        pose_enclosure_t = np.copy(poses_enclosure[t])

        distance = np.sqrt(np.max(np.sum((poses_school_t[:, :2] - pose_enclosure_t[:2]) ** 2, axis=1)))
        return pose_enclosure_t[2] - distance

    return compute


def metric_number_of_prey_out_enclosure(sub_range=0):
    def compute(t, poses_agent, poses_school, poses_enclosure):
        poses_school_t = np.copy(poses_school[t])
        n_school = poses_school.shape[1]
        pose_enclosure_t = np.copy(poses_enclosure[t])

        distance = np.sqrt(np.sum((poses_school_t[:, :2] - pose_enclosure_t[:2]) ** 2, axis=1))
        return np.sum(distance > pose_enclosure_t[2] - sub_range) / n_school

    return compute


def metric_duration_of_prey_out_enclosure(sub_range=0, t_z=73):
    def compute(poses_agent, poses_school, poses_enclosure):
        poses_school_all = np.copy(poses_school[t_z:])
        n_school = poses_school.shape[1]

        durations = np.zeros(n_school)
        for t_prime, poses_school_t in enumerate(poses_school_all[:]):
            dist = np.sqrt(np.sum((poses_school_t[:, :2] - poses_enclosure[t_prime, :2]) ** 2, axis=1))
            durations[dist > poses_enclosure[t_prime, 2] - sub_range] += 1

        if np.any(durations > 0):
            return np.mean(durations[durations > 0])
        else:
            return 0.

    return compute
