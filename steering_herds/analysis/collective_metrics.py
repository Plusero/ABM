import numpy as np
from shapely.geometry import MultiPoint
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree


def metric_herd_density():
    def compute(t, poses_agent, poses_school):
        poses_school_t = np.copy(poses_school[t])
        n_school = poses_school.shape[0]
        area = MultiPoint(poses_school_t[:, :2]).convex_hull.area
        return n_school / area

    return compute


def metric_herd_furthest_neighbor():
    def compute(t, poses_agent, poses_school):
        poses_school_t = np.copy(poses_school[t])
        n_school = poses_school.shape[0]
        dist = 0
        for pose in poses_school_t:
            dist += np.sqrt(np.max(np.sum((poses_school_t[:, :2] - pose[:2]) ** 2, axis=1)))
        return dist / n_school

    return compute


def metric_herd_connectivity(threshold):
    def compute(t, poses_agent, poses_school):
        poses_school_t = np.copy(poses_school[t])
        n_school = poses_school_t.shape[0]
        kd_tree = cKDTree(poses_school_t[:, :2])
        kd_pairs = kd_tree.query_pairs(r=threshold)
        A = np.zeros((n_school, n_school))
        for (i, j) in kd_pairs:
            A[i, j] = 1
            A[j, i] = 1
        csr_m = csr_matrix(A)
        n_components, _ = connected_components(csr_m)
        return n_components

    return compute


def metric_herd_nearest_k_neighbors(k_neighbors):
    def compute(t, poses_agent, poses_school):
        poses_school_t = np.copy(poses_school[t])
        n_school = poses_school.shape[0]
        kd_tree = cKDTree(poses_school_t[:, :2])
        k = min(k_neighbors + 1, n_school)
        dist = 0.
        for pose in poses_school_t:
            d, _ = kd_tree.query(pose[:2], k=k)
            dist += np.mean(d[d > 0])
        return dist / n_school

    return compute


def metric_herd_order():
    def compute(t, poses_agent, poses_school):
        poses_school_t = np.copy(poses_school[t])
        n_school = poses_school.shape[0]
        return np.linalg.norm(
            np.array([np.sum(np.cos(poses_school_t[:, 2])),
                      np.sum(np.sin(poses_school_t[:, 2]))])
        ) / n_school

    return compute

