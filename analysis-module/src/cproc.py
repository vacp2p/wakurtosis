# Python Imports

# Project Imports
from src import analysis_logger
from src import plotting
from src import analysis_cproc

def run(simulation_config, simulation_path, msgs_dict, node_logs, msg_propagation_times, msg_injection_times, min_tss, max_tss):
    analysis_logger.G_LOGGER.info('Generating stats for CPROC infrastructure ...')

    metrics_info, max_cpu_usage, max_memory_usage, total_network_usage, max_disk_usage, avg_samples_per_node = analysis_cproc.compute_process_level_metrics(simulation_path, simulation_config)
    
    """ Build simulation summary """
    summary = analysis_cproc.build_summary(simulation_config, metrics_info, msgs_dict, node_logs, [], min_tss, max_tss, avg_samples_per_node)
    
    """ Generate Figure """
    plotting.plot_figure_cproc(msg_propagation_times, max_cpu_usage, max_memory_usage, total_network_usage, max_disk_usage, 
                    msg_injection_times, summary['general'], summary['parameters'])
    
    """ Export summary """
    analysis_cproc.export_summary(simulation_path, summary)

    