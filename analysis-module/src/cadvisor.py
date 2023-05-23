# Python Imports

# Project Imports
from src import analysis_logger
from src import analysis
from src import prometheus
from src import plotting

def run(simulation_config, metrics, topology_info, msg_propagation_times, msg_injection_times, min_tss, max_tss, prom_port):
    analysis_logger.G_LOGGER.info('Generating stats for CADVISOR infrastructure ...')

    analysis.inject_metric_in_dict(metrics, "propagation", "Propagation Time (per message)", "Propagation Time (ms)",
                        "msg_propagation_times", msg_propagation_times)
    analysis.inject_metric_in_dict(metrics, "injection", "Injection Time (per message)", "Milliseconds (ms)",
                    "msg_injection_times", msg_injection_times)

    prometheus.get_hardware_metrics(metrics, topology_info, min_tss, max_tss, prom_port)

    """ Generate Figure """
    plotting.plot_figure_ex(simulation_config)
