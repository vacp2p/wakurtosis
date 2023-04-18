# Python Imports
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

    figure_path = f'{vars.G_DEFAULT_SIMULATION_PATH}/{vars.G_DEFAULT_FIG_FILENAME}'
    plt.savefig(figure_path, format="pdf", bbox_inches="tight")

    analysis_logger.G_LOGGER.info(f'Figure saved in {figure_path}')
