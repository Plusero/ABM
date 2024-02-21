import numpy as np
from matplotlib import colors


def color_to_rgba(color, alpha):
    c = color / 255
    return np.append(c, [alpha])


def exp_tick(x, _):
    if x == 0:
        return "$0$"

    exp = int(np.log10(x))
    co = x / 10 ** exp

    if co == 1:
        return r"$10^{{ {:2d} }}$".format(exp)
    else:
        return r"${:2.0f} \cdot 10^{{ {:2d} }}$".format(co, exp)


tableau_palette = [
    'tab:blue',
    'tab:orange',
    'tab:green',
    'tab:red',
    'tab:purple',
    'tab:brown',
    'tab:pink',
    'tab:gray',
    'tab:olive',
    'tab:cyan'
]


def truncate_colormap(cmap, minval=0.0, maxval=1.0, n=100):
    new_cmap = colors.LinearSegmentedColormap.from_list(
        'trunc({n},{a:.2f},{b:.2f})'.format(n=cmap.name, a=minval, b=maxval),
        cmap(np.linspace(minval, maxval, n)))
    return new_cmap


""" Main class for making fast plots """
# Import necessary libraries
import numpy as np
import matplotlib
import matplotlib.pyplot as plt


class Plotr(object):
    def __init__(self):
        # Set plotting font for TeX labels
        plt.rcParams.update({
            'text.usetex': True,
            'font.family': 'serif',
            'text.latex.preamble': r'\usepackage{amsfonts}' r'\usepackage{amsmath}'
        })

        # Set markers & colors
        self.markers = ['s', 'o', 'D', 'p', '^', '*', '>', 'h', 'v', '<']
        self.colors = [
            'k', 'firebrick', 'navy', 'darkgreen', 'darkmagenta',  # 'seagreen',
            'darkorange', 'indigo', 'maroon', 'peru', 'orchid'
        ]
        self.lightcolors = [
            'lightgrey', 'steelblue', 'lightcoral', 'mediumseagreen', 'orchid',
            'sandybrown', 'mediumpurple'
        ]
        self.figlabels = [
            r'A', r'B', r'C', r'D',
            r'E', r'F', r'G', r'H'
        ]
        self.figbflabels = [
            r'\textbf{A}', r'\textbf{B}', r'\textbf{C}', r'\textbf{D}',
            r'\textbf{E}', r'\textbf{F}', r'\textbf{G}', r'\textbf{H}'
        ]
        self.linestyles = ['-', '--', ':', '-.']

    def plot(self, fig, axes, data, yerr=None):
        """ Plot the data onto the axes """
        pass
