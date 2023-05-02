# Python Imports
import numpy as np
import matplotlib.pyplot as plt

# Project Imports
from src import vars
from src import analysis_logger


def plot_figure(msg_propagation_times, cpu_usage, memory_usage, bandwith_in, bandwith_out):
    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(1, 5, figsize=(15, 10))

    ax1.violinplot(msg_propagation_times, showmedians=True)
    ax1.set_title(
        f'Message propagation times \n(sample size: {len(msg_propagation_times)} messages)')
    ax1.set_ylabel('Propagation Time (ms)')
    ax1.spines[['right', 'top']].set_visible(False)
    ax1.axes.xaxis.set_visible(False)

    ax2.violinplot(cpu_usage, showmedians=True)
    ax2.set_title(f'Maximum CPU usage per Waku node \n(sample size: {len(cpu_usage)} nodes)')
    ax2.set_ylabel('CPU Cycles')
    ax2.spines[['right', 'top']].set_visible(False)
    ax2.axes.xaxis.set_visible(False)

    ax3.violinplot(memory_usage, showmedians=True)
    ax3.set_title(
        f'Maximum memory usage per Waku node \n(sample size: {len(memory_usage)} nodes)')
    ax3.set_ylabel('Bytes')
    ax3.spines[['right', 'top']].set_visible(False)
    ax3.axes.xaxis.set_visible(False)

    ax4.violinplot(bandwith_in, showmedians=True)
    ax4.set_title(f'Bandwith IN usage per Waku node \n(sample size: {len(bandwith_in)} nodes)')
    ax4.set_ylabel('Bytes')
    ax4.spines[['right', 'top']].set_visible(False)
    ax4.axes.xaxis.set_visible(False)

    ax5.violinplot(bandwith_out, showmedians=True)
    ax5.set_title(f'Bandwith OUT usage per Waku node \n(sample size: {len(bandwith_out)} nodes)')
    ax5.set_ylabel('Bytes')
    ax5.spines[['right', 'top']].set_visible(False)
    ax5.axes.xaxis.set_visible(False)

    plt.tight_layout()

    figure_path = f'{vars.G_DEFAULT_SIMULATION_PATH + vars.G_DEFAULT_FIG_FILENAME}'
    plt.savefig(figure_path, format="pdf", bbox_inches="tight")

    analysis_logger.G_LOGGER.info(f'Figure saved in {figure_path}')


def plot_figure_ex(msg_propagation_times, cpu_usage, memory_usage, network_usage, disk_usage, injection_times,
                   simulation_config):
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

    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(15, 15))

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
