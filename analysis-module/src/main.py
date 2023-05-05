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
from src import analysis_cproc
from src import config

if __name__ == "__main__":
    """ Parse args """
    simulation_path, tomls_folder, prom_port, infra_type = arg_parser.parse_args()

    """ Load Topics Structure """
    topology_info = topology.load_topology(simulation_path + vars.G_TOPOLOGY_FILE_NAME)
    topology.load_topics_into_topology(topology_info, tomls_folder)

    """ Load Config """
    config_obj = config.load_config(simulation_path)

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

    """ Generate stats depending on the type of measurements we have """
    if infra_type == 'container-proc':
        analysis_logger.G_LOGGER.info('Generating stats for container_proc infrastructure ...')

        metrics_info, max_cpu_usage, max_memory_usage, total_network_usage, max_disk_usage, avg_samples_per_node = analysis_cproc.compute_process_level_metrics(simulation_path, config_obj)
        
        """ Build simulation summary """
        summary = analysis_cproc.build_summary(config_obj, metrics_info, msgs_dict, node_logs, [], min_tss, max_tss, avg_samples_per_node)
        
        """ Generate Figure """
        plotting.plot_figure_host_proc(msg_propagation_times, max_cpu_usage, max_memory_usage, total_network_usage, max_disk_usage, 
                       msg_injection_times, summary['general'], summary['parameters'])
        
        """ Export summary """
        analysis_cproc.export_sumary(simulation_path, summary)
        
    # Add cadvisor and host-proc logic cases bellow
    else:

        cpu_usage, memory_usage, bandwith_in, bandwith_out = prometheus.get_hardware_metrics(
            topology_info,
            min_tss,
            max_tss, prom_port)

        total_network_usage = {'rx_mbytes': bandwith_in, 'tx_mbytes': bandwith_out}
        # plotting.plot_figure_ex(msg_propagation_times, cpu_usage, memory_usage, total_network_usage)

        """ Generate Figure """
        plotting.plot_figure(msg_propagation_times, cpu_usage, memory_usage, bandwith_in, bandwith_out)

    """ We are done """
    analysis_logger.G_LOGGER.info('Ended')
