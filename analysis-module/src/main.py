# Python Imports

# Project Imports
from src import vars
from src import arg_parser
from src import topology
from src import log_parser
from src import analysis
from src import analysis_logger
from src import cproc
from src import cadvisor
from src import plotting
from src import plotting_configurations
from src import prometheus

if __name__ == "__main__":
    """ Parse args """
    simulation_path, prom_port, infra_type = arg_parser.parse_args()

    """Load Configuration"""
    simulation_config = topology.load_json(simulation_path + "config/config.json")
    metrics = simulation_config["plotting"]

    """ Load Topics Structure """
    topology_info = topology.load_json(simulation_path + vars.G_TOPOLOGY_FILE_NAME)
    topology.load_topics_into_topology(topology_info, simulation_path + "config/topology_generated/")

    """ Load Simulation Messages """
    injected_msgs_dict = log_parser.load_messages(simulation_path)
    node_logs, msgs_dict, min_tss, max_tss = analysis.analyze_containers(topology_info,
                                                                         simulation_path)

    """ Compute simulation time window """
    simulation_time_ms = round((max_tss - min_tss) / 1000000)
    analysis_logger.G_LOGGER.info(f'Simulation started at {min_tss}, ended at {max_tss}. '
                                  f'Effective simulation time was {simulation_time_ms} ms.')

    analysis.compute_message_delivery(msgs_dict, injected_msgs_dict)
    analysis.compute_message_latencies(msgs_dict)
    msg_propagation_times = analysis.compute_propagation_times(msgs_dict)
    msg_injection_times = analysis.compute_injection_times(injected_msgs_dict)

    """ Generate stats depending on the type of measurements infrastructure """
    if infra_type == 'container-proc':
        cproc.run(simulation_config, simulation_path, msgs_dict, node_logs, msg_propagation_times, msg_injection_times, min_tss, max_tss)
    elif infra_type == 'cadvisor':
        cadvisor.run(simulation_config, metrics, topology_info, msg_propagation_times, msg_injection_times, min_tss, max_tss, prom_port)
    else:
        analysis_logger.G_LOGGER.error(f'Unknown infrastructure type: {infra_type}')
        analysis.inject_metric_in_dict(plotting_configurations.plotting_config, "propagation",
                                    "Propagation Time (per message)", "Propagation Time (ms)",
                                    "msg_propagation_times", msg_propagation_times)
        analysis.inject_metric_in_dict(plotting_configurations.plotting_config, "injection",
                                    "Injection Time (per message)", "Milliseconds (ms)",
                                    "msg_injection_times", msg_injection_times)

        prometheus.get_hardware_metrics(metrics, topology_info, min_tss, max_tss, prom_port)

    """ Generate Figure """
    plotting.plot_figure_ex(simulation_config)

    """ We are done """
    analysis_logger.G_LOGGER.info('Ended')
