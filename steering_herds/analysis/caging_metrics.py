import numpy as np
from shapely.geometry import MultiPoint, Point, LineString
from shapely.ops import unary_union

from utils.topology import ConcaveHull


def metric_caging_probability(threshold):
    def compute(t, poses_agent, poses_school):
        poses_agent_t = np.copy(poses_agent[t])
        poses_school_t = np.copy(poses_school[t])

        n_agent = poses_agent_t.shape[0]
        if n_agent < 3:
            return 0.

        polygon = MultiPoint(poses_agent_t[:, :2]).convex_hull

        points = np.array(list(polygon.boundary.coords))
        shape_closed = True
        i = 0
        while i < len(points) and shape_closed:
            distance = np.linalg.norm(points[i] - points[(i + 1) % len(points)])
            shape_closed = distance <= threshold
            i += 1

        if not shape_closed:
            concave_hull = ConcaveHull()
            concave_hull.loadpoints(poses_agent_t[:, :2])
            concave_hull.calculatehull(tol=threshold)
            polygon = concave_hull.boundary

            points = np.array(list(polygon.boundary.coords))
            shape_closed = True
            i = 0
            while i < len(points) and shape_closed:
                distance = np.linalg.norm(points[i] - points[(i + 1) % len(points)])
                shape_closed = distance <= threshold
                i += 1

        if not shape_closed:
            return 0.

        caging = True

        for pose in poses_school_t:
            caging = caging and polygon.contains(Point(pose[0], pose[1]))

        if caging:
            return 1.
        else:
            return 0.

    return compute


def metric_distance_upper_error(threshold):
    def compute(t, poses_agent, poses_school):
        poses_agent_t = np.copy(poses_agent[t])
        poses_school_t = np.copy(poses_school[t])

        error = 0.
        norm = 0.
        for pose in poses_agent_t:
            dist = np.sqrt(np.min(np.sum((poses_school_t[:, :2] - pose[:2]) ** 2, axis=1)))
            if dist - threshold > 0:
                error += dist - threshold
                norm += 1

        if norm > 0:
            return error / norm
        else:
            return 0.

    return compute


def metric_distance_lower_error(threshold):
    def compute(t, poses_agent, poses_school):
        poses_agent_t = np.copy(poses_agent[t])
        poses_school_t = np.copy(poses_school[t])
        n_school = poses_school_t.shape[0]

        error = 0.
        for pose in poses_agent_t:
            dist = np.sqrt(np.sum((poses_school_t[:, :2] - pose[:2]) ** 2, axis=1))
            error += np.sum(np.maximum(threshold - dist, 0))
        return error / n_school

    return compute


def metric_convex_enclosure_rate():
    def compute(t, poses_agent, poses_school):
        poses_agent_t = np.copy(poses_agent[t])
        poses_school_t = np.copy(poses_school[t])
        n_school = poses_school_t.shape[0]

        n_agent = poses_agent_t.shape[0]
        if n_agent < 3:
            return 0.

        polygon = MultiPoint(poses_agent_t[:, :2]).convex_hull

        n_enclosed = 0
        for pose in poses_school_t:
            if polygon.contains(Point(pose[0], pose[1])):
                n_enclosed += 1
        return n_enclosed / n_school

    return compute


def metric_max_nearest_agent_distance():
    def compute(t, poses_agent, poses_school):
        poses_agent_t = np.copy(poses_agent[t])

        max_dist = 0.
        for pose in poses_agent_t:
            dist = np.sqrt(np.sum((poses_agent_t[:, :2] - pose[:2]) ** 2, axis=1))
            max_dist = max(max_dist, dist.max())

        return max_dist

    return compute


def metric_min_caging_agents(threshold):
    def compute(t, _, poses_school):
        poses_school_t = np.copy(poses_school[t])

        herd_circles = []
        for school_pose in poses_school_t:
            herd_circles.append(Point(*school_pose[:2]).buffer(threshold))
        herd_union = unary_union(herd_circles)

        if herd_union.geom_type == 'MultiPolygon':
            return -1

        xs, ys = herd_union.exterior.xy

        N = 5
        samples = []
        for n in range(N):
            index = np.random.choice(len(xs), 1, replace=False)[0]

            start_x, start_y = xs[index], ys[index]

            finished = False
            points = [Point(start_x, start_y)]
            i = 0
            while not finished:
                a = points[-1]

                circle = LineString(np.column_stack(a.buffer(threshold).exterior.xy))
                intersections = circle.intersection(LineString(np.column_stack(herd_union.exterior.xy)))
                v, w = intersections[0], intersections[1]

                center = np.mean(poses_school_t[:, :2], axis=0)
                txy = np.array([a.x, a.y]) - center
                angle = np.arctan2(txy[1], txy[0])
                c, s = np.cos(angle), np.sin(angle)
                R = np.array(((c, -s), (s, c)))
                rel_v = (np.array([v.x, v.y]) - center).dot(R)

                if rel_v[1] < 0:
                    new_point = v
                else:
                    new_point = w

                points.append(new_point)

                i += 1
                if len(points) > 2 and np.sqrt(
                        (points[0].x - points[-1].x) ** 2 + (points[0].y - points[-1].y) ** 2) < threshold:
                    finished = True
                if i > 1000:
                    finished = True
            samples.append(len(points))

        return np.mean(samples)

    return compute
