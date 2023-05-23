# Python Imports
import math
import numpy as np
import matplotlib.pyplot as plt

# Project Imports
from src import vars
from src import analysis_logger
from src import plotting_configurations

def plot_figure_cproc(msg_propagation_times, cpu_usage, memory_usage, network_usage, disk_usage, injection_times, simulation_summary, simulation_config):

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
        colors = [cmean_colors[0],'red',cmean_colors[0],cmean_colors[0]]
        parts['cmeans'].set_color(colors)

        # loop over the paths of the mean lines
        xy = [[l.vertices[:,0].mean(),l.vertices[0,1]] for l in parts['cmeans'].get_paths()]
        xy = np.array(xy)
        ax.scatter(xy[:,0], xy[:,1],s=25, c="crimson", marker="o", zorder=3)

        # make lines invisible
        parts['cmeans'].set_visible(False)
    
    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(15, 15))
    
    if msg_propagation_times:
        parts = ax1.violinplot(msg_propagation_times, showmeans=True)
        ax1.set_title('Popagation Time (per message)')
        ax1.set_ylabel('Propagation Time (ms)')
        ax1.spines[['right', 'top']].set_visible(False)
        ax1.axes.xaxis.set_visible(False)
        style_violin(parts, ax1)

    parts = ax2.violinplot(cpu_usage, showmeans=True)
    ax2.set_title('Peak CPU Usage (per node)')
    ax2.set_ylabel('CPU Usage (%)')
    ax2.spines[['right', 'top']].set_visible(False)
    ax2.axes.xaxis.set_visible(False)
    style_violin(parts, ax2)

    parts = ax3.violinplot(memory_usage, showmeans=True)
    ax3.set_title('Peak Memory Usage (per node)')
    ax3.set_ylabel('Memory (MBytes)')
    ax3.spines[['right', 'top']].set_visible(False)
    ax3.axes.xaxis.set_visible(False)
    style_violin(parts, ax3)

    parts = ax4.violinplot([network_usage['rx_mbytes'], network_usage['tx_mbytes']], showmeans=True)
    ax4.set_title('Total Netowrk IO (per node)')
    ax4.set_ylabel('Bandwidth (MBytes)')
    ax4.spines[['right', 'top']].set_visible(False)
    ax4.set_xticks([1, 2])
    ax4.set_xticklabels(['Received (Rx)', 'Sent (Tx)'])
    style_violin(parts, ax4)

    parts = ax5.violinplot(injection_times, showmeans=True)
    ax5.set_title('Injection Time (per message)')
    ax5.set_ylabel('Milliseconds (ms)')
    ax5.spines[['right', 'top']].set_visible(False)
    ax5.axes.xaxis.set_visible(False)
    style_violin(parts, ax5)
    
    parts = ax6.violinplot([disk_usage['disk_read_mbytes'], disk_usage['disk_write_mbytes']], showmeans=True)
    ax6.set_title('Peak Disk IO (per node)')
    ax6.set_ylabel('Disk IO (MBytes)')
    ax6.spines[['right', 'top']].set_visible(False)
    ax6.set_xticks([1, 2])
    ax6.set_xticklabels(['Read', 'Write'])
    style_violin(parts, ax6)
    
    fig.suptitle('Wakurtosis Simulation Node Level Analysis\n(%d nodes, %d topic(s), Rate: %d msg/s, Time: %.2f s. Sampling Rate: %.2f samples/s.)\n' %(simulation_summary['num_nodes'], \
    simulation_summary['num_topics'], simulation_config['wls']['message_rate'], simulation_summary['simulation_time_ms'] / 1000.0, \
    simulation_summary['metrics']['esr']), fontsize=20)
    
    plt.tight_layout()

    figure_path = f'{vars.G_DEFAULT_SIMULATION_PATH}/{vars.G_DEFAULT_FIG_FILENAME}'
    plt.savefig(figure_path, format="pdf", bbox_inches="tight")

    analysis_logger.G_LOGGER.info(f'Figure saved in {figure_path}')


def plot_figure_ex(simulation_config):
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

    metrics = plotting_configurations.plotting_config
    num_subplots = len(metrics.keys())
    num_cols = 3
    num_rows = math.ceil(num_subplots / num_cols)

    fig, axs = plt.subplots(num_rows, num_cols, figsize=(15, 15))
    axs = axs.flatten()

    # Remove unused subplots
    for i in range(num_subplots, num_rows * num_cols):
        fig.delaxes(axs[i])

    for i, key in enumerate(metrics.keys()):
        # if type(metrics[key]) is list:
        #     if sum([plotting_configurations[val]["values"] for val in metrics[key]]) == 0:
        #         continue
        metric = metrics[key]
        analysis_logger.G_LOGGER.info(f"Plotting {key}: {metric['values']}")
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

    figure_path = f'{vars.G_DEFAULT_SIMULATION_PATH}{vars.G_DEFAULT_FIG_FILENAME}'
    plt.savefig(figure_path, format="pdf", bbox_inches="tight")

    analysis_logger.G_LOGGER.info(f'Figure saved in {figure_path}')