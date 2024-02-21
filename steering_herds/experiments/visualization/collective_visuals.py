import numpy as np
from matplotlib import pyplot as plt


def run(seed, poses_school):
    t_max = poses_school.shape[0]
    n_school = poses_school.shape[1]
    for t in range(1, t_max):
        fig, ax = plt.subplots(1, 1, figsize=(10, 10))

        centroid = np.mean(poses_school[t, :, :2], axis=0)

        color = 'tab:blue'
        for i in range(n_school):
            g_position = poses_school[t, i, :2]  # - centroid
            ax.scatter(*g_position, s=21., color=color, zorder=1)
            ax.annotate(r'$f_{' + str(i) + '}$', g_position, fontsize=10, zorder=1)
            ax.quiver(g_position[0], g_position[1],
                      np.cos(poses_school[t, i, 2]), np.sin(poses_school[t, i, 2]),
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
