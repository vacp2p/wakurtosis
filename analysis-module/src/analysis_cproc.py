# Python Imports
import re
import sys
import json
from datetime import datetime

# Project Imports
from src import vars
from src import analysis_logger

def extract_node_id(s: str) -> str:
    pattern = r"node-(\d+)\.toml"
    match = re.search(pattern, s)
    if match:
        return f"node_{match.group(1)}"
    else:
        return None


def load_process_level_metrics(metrics_file_path: str):
    
    metrics_dict = {}
    
    try:
        with open(metrics_file_path, 'r') as file:
            
            metrics_obj = json.load(file)
            
            info = metrics_obj['header']
            all_samples = metrics_obj['containers']
            nodes_cnt = 0

            if len(all_samples) != info['num_containers']:
                G_LOGGER.error('Number of containers in header does not match number of containers in samples')
                return {}, None

            for container_id, container_data in all_samples.items():

                # tomls file names are unique per node
                container_nodes = {}
                for process in container_data['info']['processes']:
                    
                    node_id = extract_node_id(process['binary'])
                    if not node_id:
                        G_LOGGER.error('Couldn\'t match %s to node id in container %s' %(process['binary'], container_id))
                        continue
                    
                    pid = process['pid']
                    container_nodes[pid] = node_id  
                
                # Parse samples for each node
                for sample in container_data['samples']:
                    
                    if sample['PID'] not in container_nodes:
                        G_LOGGER.error('Couldn\'t find node id for PID %d in container %s' %(sample['PID'], container_id))
                        continue
                    
                    node_id = container_nodes[sample['PID']]
                    if not node_id:
                        G_LOGGER.error('Couldn\'t find node id for PID %d in container %s' %(sample['PID'], container_id))
                        continue

                    if node_id in metrics_dict:
                        metrics_dict[node_id]['samples'].append(sample)
                    else:
                        nodes_cnt += 1
                        metrics_dict[node_id] = {'samples' : [sample]}
            
    except Exception as e:
        analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    analysis_logger.G_LOGGER.info('Loaded metrics for %d nodes.' %len(metrics_dict))

    # for node_id, node_data in metrics_dict.items():
    #     G_LOGGER.info('Node %s has %d samples' %(node_id, len(node_data['samples'])))

    return metrics_dict, info


def build_summary(config_obj, metrics_info, msgs_dict, node_logs, topics, min_tss, max_tss, avg_samples_per_node):

    simulation_summary = {'general' : {}, 'nodes' : {}, 'messages' : {}, 'parameters' : {}}
    simulation_summary['general']['datetime'] = datetime.now().isoformat()
    simulation_summary['general']['num_messages'] = len(msgs_dict)
    simulation_summary['general']['num_nodes'] = len(node_logs)
    simulation_summary['general']['num_topics'] = len(topics)
    simulation_summary['general']['topics'] = list(topics)

    # Compute effective simulation time window
    simulation_start_ts = min_tss
    simulation_end_ts = max_tss
    simulation_time_ms = round((simulation_end_ts - simulation_start_ts) / 1000000)
    simulation_summary['general']['simulation_start_ts'] = simulation_start_ts
    simulation_summary['general']['simulation_end_ts'] = simulation_end_ts
    simulation_summary['general']['simulation_time_ms'] = simulation_time_ms

    simulation_summary['general']['metrics'] = metrics_info
    simulation_summary['general']['metrics']['avg_samples_per_node'] = avg_samples_per_node
    simulation_summary['general']['metrics']['esr'] = simulation_summary['general']['metrics']['avg_samples_per_node'] / (simulation_summary['general']['simulation_time_ms'] / 1000.0)

    simulation_summary['parameters'] = config_obj
        
    return simulation_summary

def compute_process_level_metrics(simulation_path, config_obj):

    """ Load Metrics """
    metrics_file_path = f'{simulation_path}/cproc_metrics.json'
    node_metrics, metrics_info = load_process_level_metrics(metrics_file_path)
    
    """ Compute Metrics """
    max_cpu_usage = []
    max_memory_usage = []
    total_network_usage = {'rx_mbytes' : [], 'tx_mbytes' : []}
    max_disk_usage = {'disk_read_mbytes' : [], 'disk_write_mbytes' : []}
    num_samples = []

    for node_id, node_obj in node_metrics.items():

        num_samples.append(len(node_obj['samples']))
        
        # Peak values
        max_cpu_usage.append(max(obj['CPUPercentage'] for obj in node_obj['samples']))
        max_memory_usage.append(max(obj['MemoryUsageMB'] for obj in node_obj['samples']))
        
        # Accumulated 
        total_network_usage['rx_mbytes'].append(max(obj['NetStats']['all']['total_received'] for obj in node_obj['samples']) / (1024*1024))
        total_network_usage['tx_mbytes'].append(max(obj['NetStats']['all']['total_sent'] for obj in node_obj['samples']) / (1024*1024))

        # Accumulated
        max_disk_usage['disk_read_mbytes'].append(max(obj['DiskIORChar'] for obj in node_obj['samples']) / (1024*1024))
        max_disk_usage['disk_write_mbytes'].append(max(obj['DiskIOWChar'] for obj in node_obj['samples']) / (1024*1024))
    
    avg_samples_per_node = sum(num_samples) / len(num_samples)
   
    return metrics_info, max_cpu_usage, max_memory_usage, total_network_usage, max_disk_usage, avg_samples_per_node


def export_sumary(simulation_path, summary):
    
    summary_path = f'{simulation_path}/sumary.json'

    with open(summary_path, 'w') as fp:
        json.dump(summary, fp, indent=4)
    analysis_logger.G_LOGGER.info(f'Analsysis sumnmary saved in {summary_path}')
