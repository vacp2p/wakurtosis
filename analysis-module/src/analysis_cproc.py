# Python Imports
import re
import sys
import json
from datetime import datetime
from typing import Any, Dict, List, Set, Optional, Tuple

# Project Imports
from src import analysis_logger

def compute_simulation_time_window(min_tss: float, max_tss: float) -> Tuple[float, float, float]:
    simulation_start_ts = min_tss
    simulation_end_ts = max_tss
    simulation_time_ms = round((simulation_end_ts - simulation_start_ts) / 1000000)
    return simulation_start_ts, simulation_end_ts, simulation_time_ms


def build_summary(config_obj: Dict[str, Any], metrics_info: Dict[str, Any], msgs_dict: Dict[str, Any], 
                  node_logs: Dict[str, Any], topics: Set[str], min_tss: float, max_tss: float, 
                  avg_samples_per_node: float) -> Dict[str, Any]:

    simulation_summary = {'general' : {}, 'nodes' : {}, 'messages' : {}, 'parameters' : {}}
    
    simulation_summary['general']['datetime'] = datetime.now().isoformat()
    simulation_summary['general']['num_messages'] = len(msgs_dict)
    simulation_summary['general']['num_nodes'] = len(node_logs)
    simulation_summary['general']['num_topics'] = len(topics)
    simulation_summary['general']['topics'] = list(topics)

    simulation_start_ts, simulation_end_ts, simulation_time_ms = compute_simulation_time_window(min_tss, max_tss)

    simulation_summary['general']['simulation_start_ts'] = simulation_start_ts
    simulation_summary['general']['simulation_end_ts'] = simulation_end_ts
    simulation_summary['general']['simulation_time_ms'] = simulation_time_ms

    simulation_summary['general']['metrics'] = metrics_info
    simulation_summary['general']['metrics']['avg_samples_per_node'] = avg_samples_per_node
    simulation_summary['general']['metrics']['esr'] = simulation_summary['general']['metrics']['avg_samples_per_node'] / (simulation_summary['general']['simulation_time_ms'] / 1000.0)

    simulation_summary['parameters'] = config_obj
        
    return simulation_summary


def extract_node_id(s: str) -> str:
    pattern = r"node-(\d+)\.toml"
    match = re.search(pattern, s)
    if match:
        return f"node_{match.group(1)}"
    else:
        return None


def add_sample_to_metrics(sample: Dict[str, Any], node_id: str, metrics_dict: Dict[str, Dict[str, Any]]) -> int:
    if node_id in metrics_dict:
        metrics_dict[node_id]['samples'].append(sample)
        return 0
    else:
        metrics_dict[node_id] = {'samples' : [sample]}
        return 1


def parse_container_nodes(container_id: str, container_data: Dict[str, Any], container_nodes: Dict[int, Any], metrics_dict: Dict[Any, Dict[str, Any]]) -> int:    
    nodes_cnt = 0

    for sample in container_data['samples']:
        pid = sample['PID']
        if pid not in container_nodes:
            analysis_logger.G_LOGGER.error('Couldn\'t find node id for PID %d in container %s' %(pid, container_id))
            continue

        node_id = container_nodes[pid]
        if not node_id:
            analysis_logger.G_LOGGER.error('Couldn\'t find node id for PID %d in container %s' %(pid, container_id))
            continue

        nodes_cnt += add_sample_to_metrics(sample, node_id, metrics_dict)

    return nodes_cnt


def extract_container_nodes(container_id: str, container_data: Dict[str, Any]) -> Dict[int, Any]:
    container_nodes = {}

    for process in container_data['info']['processes']:
        node_id = extract_node_id(process['binary'])
        if not node_id:
            analysis_logger.G_LOGGER.error('Couldn\'t match %s to node id in container %s' %(process['binary'], container_id))
            continue

        pid = process['pid']
        container_nodes[pid] = node_id  

    return container_nodes


def load_metrics_file(metrics_file_path: str) -> Dict[str, Any]:
    with open(metrics_file_path, 'r') as file:
        return json.load(file)


def process_metrics_file(metrics_obj: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    metrics_dict = {}
    info = metrics_obj['header']
    all_samples = metrics_obj['containers']

    if len(all_samples) != info['num_containers']:
        analysis_logger.G_LOGGER.error('Number of containers in header does not match number of containers in samples')
        return metrics_dict, info

    for container_id, container_data in all_samples.items():
        container_nodes = extract_container_nodes(container_id, container_data)
        parse_container_nodes(container_id, container_data, container_nodes, metrics_dict)

    return metrics_dict, info

def load_process_level_metrics(metrics_file_path: str) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    try:
        metrics_obj = load_metrics_file(metrics_file_path)
        metrics_dict, info = process_metrics_file(metrics_obj)
    except Exception as e:
        analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__,e))
        sys.exit()

    analysis_logger.G_LOGGER.info('Loaded metrics for %d nodes.' %len(metrics_dict))

    return metrics_dict, info


def compute_node_metrics(node_obj: Dict[str, Any]) -> Tuple[int, float, float, float, float, float, float]:
    num_samples = len(node_obj['samples'])
    
    """ Peak values """
    max_cpu_usage = max(obj['CPUPercentage'] for obj in node_obj['samples'])
    max_memory_usage = max(obj['MemoryUsageMB'] for obj in node_obj['samples'])
    
    """ Accumulated """
    total_rx_mbytes = max(obj['NetStats']['all']['total_received'] for obj in node_obj['samples']) / (1024*1024)
    total_tx_mbytes = max(obj['NetStats']['all']['total_sent'] for obj in node_obj['samples']) / (1024*1024)

    """ Accumulated """
    max_disk_read_mbytes = max(obj['DiskIORChar'] for obj in node_obj['samples']) / (1024*1024)
    max_disk_write_mbytes = max(obj['DiskIOWChar'] for obj in node_obj['samples']) / (1024*1024)

    return num_samples, max_cpu_usage, max_memory_usage, total_rx_mbytes, total_tx_mbytes, max_disk_read_mbytes, max_disk_write_mbytes


def compute_process_level_metrics(simulation_path: str, config_obj: Dict[str, Any]) -> Tuple[Dict[str, Any], List[float], List[float], Dict[str, List[float]], Dict[str, List[float]], float]:
    
    """ Load Metrics """
    metrics_file_path = f'{simulation_path}/cproc_metrics.json'
    node_metrics, metrics_info = load_process_level_metrics(metrics_file_path)
    
    """ Compute Metrics """
    max_cpu_usage = []
    max_memory_usage = []
    total_network_usage = {'rx_mbytes' : [], 'tx_mbytes' : []}
    max_disk_usage = {'disk_read_mbytes' : [], 'disk_write_mbytes' : []}
    num_samples = []

    for _, node_obj in node_metrics.items():
        samples, cpu, mem, rx, tx, disk_read, disk_write = compute_node_metrics(node_obj)
        num_samples.append(samples)
        max_cpu_usage.append(cpu)
        max_memory_usage.append(mem)
        total_network_usage['rx_mbytes'].append(rx)
        total_network_usage['tx_mbytes'].append(tx)
        max_disk_usage['disk_read_mbytes'].append(disk_read)
        max_disk_usage['disk_write_mbytes'].append(disk_write)
        
    avg_samples_per_node = sum(num_samples) / len(num_samples)
   
    return metrics_info, max_cpu_usage, max_memory_usage, total_network_usage, max_disk_usage, avg_samples_per_node


def export_summary(simulation_path: str, summary: Dict[str, Any]) -> None:
    summary_path = f'{simulation_path}/summary.json'
    with open(summary_path, 'w') as fp:
        json.dump(summary, fp, indent=4)
    analysis_logger.G_LOGGER.info(f'Analysis summary saved in {summary_path}')
