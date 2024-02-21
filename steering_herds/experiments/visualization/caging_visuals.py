import numpy as np
from matplotlib import pyplot as plt
from shapely.geometry import Point
from shapely.ops import unary_union


def run(seed, poses_school, poses_agents):
    t_max = poses_school.shape[0]
    n_agents = poses_agents.shape[1]
    n_school = poses_school.shape[1]

    for t in range(1, t_max):
        fig, ax = plt.subplots(1, 1, figsize=(10, 10))

        centroid = np.mean(poses_school[t, :, :2], axis=0)

        color = 'tab:blue'
        for g_j in range(n_school):
            g_position = poses_school[t, g_j, :2]  # - centroid
            ax.scatter(*g_position, s=21., color=color, zorder=1)
            ax.annotate(r'$f_{' + str(g_j) + '}$', g_position, fontsize=10, zorder=1)
            ax.quiver(g_position[0], g_position[1],
                      np.cos(poses_school[t, g_j, 2]), np.sin(poses_school[t, g_j, 2]),
                      linewidths=0.05, width=0.003, color=color)

        herd_circles = []
        for i, school_pose in enumerate(poses_school[t]):
            herd_circles.append(Point(*school_pose[:2]).buffer(19.))
        herd_union = unary_union(herd_circles)
        xs, ys = herd_union.exterior.xy
        line_width_school = 0.85
        alpha = 0.8
        ax.plot(xs, ys, color=color, alpha=alpha, linewidth=line_width_school, zorder=0)

        color = 'tab:green'
        for r_i in range(n_agents):
            r_position = poses_agents[t, r_i, :2]  # - centroid
            ax.scatter(*r_position, s=21., color=color)
            ax.annotate(r'$r_{' + str(r_i) + '}$', r_position, fontsize=10, zorder=1)
            ax.quiver(r_position[0], r_position[1],
                      np.cos(poses_agents[t, r_i, 2]), np.sin(poses_agents[t, r_i, 2]),
                      linewidths=0.05, width=0.003, color=color)

        bound = 60.
        x_lim = np.array([-bound, bound]) + centroid[0]
        ax.set_xlim(x_lim.tolist())
        y_lim = np.array([-bound, bound]) + centroid[1]
        ax.set_ylim(y_lim.tolist())

        # create file name and append it to a list
        filename = f'seed={seed}_t={t}.png'

        # save frame
        fig.savefig(filename)
        plt.close()
