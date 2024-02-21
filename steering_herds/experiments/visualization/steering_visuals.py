import numpy as np
from matplotlib import pyplot as plt
from shapely.geometry import Point
from shapely.ops import unary_union


def run(seed, scenario_type, poses_school, poses_agents, poses_scenario, centroid=None, show_quiver=True):
    bound = 100.
    if scenario_type == "objects":
        bound = 150.
    if scenario_type == "enclosure":
        bound = 100.

    t_max = poses_school.shape[0]

    for t in range(1, t_max):
        z_i = 19

        color_agent = 'tab:green'
        marker_agent = 'D'
        color_herd = 'tab:blue'

        scatter_scale = 21.

        quiver_linewidth = 0.05
        quiver_alpha = 0.5
        quiver_scale = 0.09

        contour_linewidth = 0.5

        fig, ax = plt.subplots(1, 1, figsize=(10, 10))

        if scenario_type == "enclosure":
            centroid = poses_scenario[t, :2]
        if centroid is None:
            centroid = np.mean(poses_school[t, :, :2], axis=0)

        herd_circles = []
        for i in range(poses_school.shape[1]):
            position = poses_school[t, i, :2] - centroid
            orientation = poses_school[t, i, 2]
            ax.scatter(*position, s=scatter_scale, color=color_herd)
            if show_quiver:
                ax.quiver(position[0], position[1], np.cos(orientation), np.sin(orientation),
                          scale=quiver_scale, scale_units='xy',
                          linewidths=quiver_linewidth, width=0.003, color=color_herd, alpha=quiver_alpha)
            herd_circles.append(Point(*position).buffer(z_i))
        herd_union = unary_union(herd_circles)
        xs, ys = herd_union.exterior.xy
        ax.plot(xs, ys, color=color_herd, linewidth=contour_linewidth, zorder=0)

        for i in range(poses_agents.shape[1]):
            position = poses_agents[t, i, :2] - centroid
            orientation = poses_agents[t, i, 2]
            ax.scatter(*position, s=scatter_scale, color=color_agent, marker=marker_agent)
            if show_quiver:
                ax.quiver(position[0], position[1], np.cos(orientation), np.sin(orientation),
                          scale=quiver_scale, scale_units='xy',
                          linewidths=quiver_linewidth, width=0.003, color=color_agent, alpha=quiver_alpha)

        if scenario_type == "enclosure":
            run_enclosure(t, ax, poses_scenario)
        if scenario_type == "patches":
            run_patches(t, ax, poses_scenario, z_i, centroid)

        x_ticks = [-bound, -bound / 2, 0, bound / 2, bound]
        y_ticks = [-bound, -bound / 2, 0, bound / 2, bound]

        x_lim = np.array([-bound, bound])
        ax.set_xlim(x_lim.tolist())
        y_lim = np.array([-bound, bound])
        ax.set_ylim(y_lim.tolist())

        ax.set_xticks(x_ticks)
        ax.set_yticks(y_ticks)

        fontsize_xlabel = 14
        fontsize_ylabel = 14
        fontsize_ticks = 10
        ax.set_xlabel(r'$x$', fontsize=fontsize_xlabel)
        ax.set_ylabel(r'$y$', fontsize=fontsize_ylabel)
        ax.tick_params(axis='both', labelsize=fontsize_ticks)

        # save frame
        fig.savefig(f'seed={seed}_t={t}.png')
        plt.close()


def run_enclosure(t, ax, pose_scenario):
    color_danger = 'xkcd:salmon'
    if not np.any(np.isinf(pose_scenario[t])):
        ax.set_facecolor(color_danger)
        ax.add_patch(
            plt.Circle((pose_scenario[t, 0], pose_scenario[t, 1]), pose_scenario[t, 2], color='white', zorder=0,
                       fill=True))


def run_patches(t, ax, pose_scenario, z_i, centroid):
    color_danger = 'tab:red'
    alpha_danger = 0.5
    marker_danger = 'x'
    scatter_scale = 21.

    if not np.any(np.isinf(pose_scenario[t])):
        for i in range(pose_scenario.shape[1]):
            position = pose_scenario[t, i, :2] - centroid
            ax.scatter(*position, s=scatter_scale, color=color_danger, marker=marker_danger)
            ax.add_patch(plt.Circle(position, z_i, color=color_danger, alpha=alpha_danger, zorder=15, fill=True))
