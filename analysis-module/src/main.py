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
    simulation_path, tomls_folder, prom_port = arg_parser.parse_args()

    """ Load Topics Structure """
    topology_info = topology.load_json(simulation_path + vars.G_TOPOLOGY_FILE_NAME)
    topology.load_topics_into_topology(topology_info, tomls_folder)

    simulation_config = topology.load_json(simulation_path + "config/config.json")

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

    metrics = {
        "to_query": {
            "cpu": {
                "title": "Peak CPU Usage (per node)",
                "y_label": "CPU Usage (%)",
                "metric_name": "container_cpu_load_average_10s",
                "statistic": "max",
                "toMB": False},
            "memory": {
                "title": 'Peak Memory Usage (per node)',
                "y_label": 'Memory (MBytes)',
                "metric_name": "container_memory_usage_bytes",
                "statistic": "max",
                "toMB": True},
            "bandwith": {
                "title": 'Total Netowrk IO (per node)',
                "y_label": 'Bandwidth (MBytes)',
                "metric_name": ["container_network_receive_bytes_total",
                                "container_network_transmit_bytes_total"],
                "statistic": "max",
                "toMB": True},
            "disk": {
                "title": 'Peak Disk IO (per node)',
                "y_label": 'Disk IO (MBytes)',
                "metric_name": ["container_fs_reads_bytes_total",
                                "container_fs_writes_bytes_total"],
                "statistic": "max",
                "toMB": True}
        },
        "propagation": {
            "title": 'Propagation Time (per message)',
            "y_label": 'Propagation Time (ms)',
            "metric_name": "msg_propagation_times",
            "values": msg_propagation_times},
        "injection": {
            "title": 'Injection Time (per message)',
            "y_label": 'Milliseconds (ms)',
            "metric_name": "msg_injection_times",
            "values": msg_injection_times}
    }
    prometheus.get_hardware_metrics(metrics, topology_info, min_tss, max_tss, prom_port)
    # cpu_usage, memory_usage, bandwith_in, bandwith_out, max_disk_usage = prometheus.get_hardware_metrics(
    #     topology_info,
    #     min_tss,
    #     max_tss, prom_port)

    # total_network_usage = {'rx_mbytes': bandwith_in, 'tx_mbytes': bandwith_out}

    # each metric would have:
    # list of values or list of list values
    # title
    # y lavel
    """ Generate Figure """
    #plotting.plot_figure_ex(msg_propagation_times, cpu_usage, memory_usage, total_network_usage, max_disk_usage,
    #                        msg_injection_times, simulation_config)
    plotting.plot_figure_ex(metrics, simulation_config)
    """ We are done """
    analysis_logger.G_LOGGER.info('Ended')
