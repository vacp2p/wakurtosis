# Python Imports

# Project Imports
from src import vars
from src import arg_parser
from src import topology
from src import log_parser
from src import analysis
from src import prometheus
from src import analysis_logger
from src import plotting


if __name__ == "__main__":
    """ Parse args """
    simulation_path, tomls_folder = arg_parser.parse_args()

    """ Load Topics Structure """
    topology_info = topology.load_topology(simulation_path + vars.G_TOPOLOGY_FILE_NAME)
    topology.load_topics_into_topology(topology_info, tomls_folder)

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
    cpu_usage, memory_usage, bandwith_in, bandwith_out = prometheus.get_hardware_metrics(
        topology_info,
        node_logs,
        min_tss,
        max_tss)

    """ Generate Figure """
    plotting.plot_figure(msg_propagation_times, cpu_usage, memory_usage, bandwith_in, bandwith_out)

    """ We are done """
    analysis_logger.G_LOGGER.info('Ended')
