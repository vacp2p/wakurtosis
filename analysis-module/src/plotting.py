# Python Imports
import math
import numpy as np
import matplotlib.pyplot as plt

# Project Imports
from src import vars
from src import analysis_logger


def plot_figure_ex(metrics, simulation_config):
    def style_violin(parts, ax):

        # Change the extrema lines to dashed grey lines
        for line in parts['cmaxes'].get_segments() + parts['cmins'].get_segments():
            line_obj = plt.Line2D(line[:, 0], line[:, 1], color='grey', linestyle='dashed', linewidth=0.5)
            ax.add_line(line_obj)

        # Remove the original extrema lines
        parts['cmaxes'].set_visible(False)
        parts['cmins'].set_visible(False)

        # Change the vertical lines to dashed grey lines
        for line in parts['cbars'].get_segments():
            line_obj = plt.Line2D(line[:, 0], line[:, 1], color='grey', linestyle='dashed', linewidth=0.5)
            ax.add_line(line_obj)

        # Remove the original vertical lines
        parts['cbars'].set_visible(False)

        cmean_colors = parts['cmeans'].get_color()
        colors = [cmean_colors[0], 'red', cmean_colors[0], cmean_colors[0]]
        parts['cmeans'].set_color(colors)

        # loop over the paths of the mean lines
        xy = [[l.vertices[:, 0].mean(), l.vertices[0, 1]] for l in parts['cmeans'].get_paths()]
        xy = np.array(xy)
        ax.scatter(xy[:, 0], xy[:, 1], s=25, c="crimson", marker="o", zorder=3)

        # make lines invisible
        parts['cmeans'].set_visible(False)

    num_subplots = len(metrics["to_query"]) + len(metrics.keys()) - 1
    num_cols = 3
    num_rows = math.ceil(num_subplots / num_cols)

    fig, axs = plt.subplots(num_rows, num_cols, figsize=(15, 15))
    axs = axs.flatten()

    # Remove unused subplots
    for i in range(num_subplots, num_rows * num_cols):
        fig.delaxes(axs[i])

    # Loop through the subplots and plot your data
    metrics = {
        **metrics.pop("to_query"),
        **metrics
    }

    for i, metric in enumerate(metrics.values()):
        if type(metric["values"][0]) is list:
            if sum([len(sublist) for sublist in metric["values"]]) == 0:
                continue
        analysis_logger.G_LOGGER.info(f"Plotting {metric['metric_name']}: {metric['values']}")
        parts = axs[i].violinplot(metric["values"], showmeans=True)
        axs[i].set_title(metric["title"])
        axs[i].set_ylabel(metric["y_label"])
        axs[i].spines[['right', 'top']].set_visible(False)
        axs[i].axes.xaxis.set_visible(False)
        if "xtic_labels" in metric.keys():
            axs[i].set_xticks([i+1 for i in range(len(metric["xtic_labels"]))])
            axs[i].set_xticklabels(metric["xtic_labels"])
            axs[i].axes.xaxis.set_visible(True)
        style_violin(parts, axs[i])

    fig.suptitle(
        'Wakurtosis Simulation Node Level Analysis\n(%d nodes, %d topic(s), Rate: %d msg/s, Time: %.2f s. Message Rate: %.2f. Min/Max size: %d/%d.)\n' % (
        simulation_config['gennet']['num_nodes'], \
        simulation_config['gennet']['num_topics'], simulation_config['wls']['message_rate'],
        simulation_config['wls']['simulation_time'], \
        simulation_config['wls']['message_rate'],
        simulation_config['wls']['min_packet_size'],
        simulation_config['wls']['max_packet_size']
        ), fontsize=20)

    plt.tight_layout()

    figure_path = f'{vars.G_DEFAULT_SIMULATION_PATH}/{vars.G_DEFAULT_FIG_FILENAME}'
    plt.savefig(figure_path, format="pdf", bbox_inches="tight")

    analysis_logger.G_LOGGER.info(f'Figure saved in {figure_path}')
