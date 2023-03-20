#!/usr/bin/env python3
"""
Description: Tracks WSL execution and stores Docker stats of the nodes in the enclave

"""

""" Dependencies """
import sys, logging, json, argparse, tomllib, glob, re, requests, statistics, os, time
from time import sleep
from datetime import datetime
from pathlib import Path
from tqdm_loggable.auto import tqdm
from tqdm_loggable.tqdm_logging import tqdm_logging
import matplotlib.pyplot as plt
from scipy import stats
import docker
import psutil

#from prometheus_api_client import PrometheusConnect

""" Globals """
G_APP_NAME = 'WLS-ANALYSIS'
G_LOG_LEVEL = 'INFO'
G_DEFAULT_CONFIG_FILE = './config/config.json'
G_DEFAULT_TOPOLOGY_PATH = './config/topology_generated'
G_DEFAULT_SIMULATION_PATH = './wakurtosis_logs'
G_DEFAULT_NODES_FIG_FILENAME = 'nodes_analysis.pdf'
G_DEFAULT_MSGS_FIG_FILENAME = 'msg_distributions.pdf'
G_DEFAULT_SUMMARY_FILENAME = 'summary.json'
G_DEFAULT_METRICS_FILENAME = 'metrics.log'

G_LOGGER = None

""" Custom logging formatter """
class CustomFormatter(logging.Formatter):
    
    # Set different formats for every logging level
    time_name_stamp = "[%(asctime)s.%(msecs)03d] [" + G_APP_NAME + "]"
    FORMATS = {
        logging.ERROR: time_name_stamp + " ERROR in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.WARNING: time_name_stamp + " WARNING - %(msg)s",
        logging.CRITICAL: time_name_stamp + " CRITICAL in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.INFO:  time_name_stamp + " %(msg)s",
        logging.DEBUG: time_name_stamp + " %(funcName)s() %(msg)s",
        'DEFAULT': time_name_stamp + " %(msg)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])
        formatter = logging.Formatter(log_fmt, '%d-%m-%Y %H:%M:%S')
        return formatter.format(record)

def get_snapshot(container, interval, nonce, nonce_ts, process_str="waku"):

    t_start = time.time()

    # Get the container's PID
    pid = container.attrs['State']['Pid']
    # print('--->', pid)

    # net_connections = psutil.net_connections(kind='all')
    # for net_connection in net_connections:
    #     print(net_connection.pid)
    #     if net_connection.pid == pid:
    #         print(net_connection)

    processes = container.top(ps_args="-eo pid,cmd").get("Processes")
    # print('Parsing %d processe(s) from container %s' %(len(processes), container.id))

    node_cnt = 0
    metrics = []
    for process in processes:
        
        process_id = process[0]
        process_name = process[1]
        if process_str not in process_name:
            continue

        node_cnt += 1

        # Keep track of the node  
        node_id = os.path.splitext(process_name.split('/')[-1])[0]
        toml_name = process_name.split('/')[-1]
        binary_name = process_name.split()[0].split('/')[-1]

        # print('- Monitoring process %s in container %s ...' %(node_id, container.id))

        # Get the process object for the process ID
        process = psutil.Process(int(process_id))

        # Get the CPU usage percentage for the process
        cpu_percent = process.cpu_percent(interval=None)
    
        # Get the memory usage for the process
        memory_info = process.memory_info()
        memory_usage = memory_info.rss / 1024 / 1024  # convert from bytes to megabytes
        # memory_usage = 0

        # Get the disk I/O metrics for the process
        io_counters = process.io_counters()
        # disk_read_bytes = 0
        # disk_write_bytes = 0
        disk_read_bytes = io_counters.read_chars
        disk_write_bytes = io_counters.write_chars

        # print(io_counters)
        # Get the network I/O metrics (this is container level, nor process)
        network_rx_bytes = 0
        network_tx_bytes = 0
        # network_stats = container.stats(stream=False)
        # for network_interface in network_stats["networks"]:
        #     network_rx_bytes += network_stats["networks"][network_interface]["rx_bytes"]
        #     network_tx_bytes += network_stats["networks"][network_interface]["tx_bytes"]

        # Get the network I/O statistics for the container's processes
        network_io_counters = psutil.net_io_counters(pernic=True)
        # print(network_io_counters)

        # Filter the network I/O statistics to only include the container's network interface
        # my_container_network_io_counters = {k:v for k,v in network_io_counters.items() if veth_id in k}
        # print(my_container_network_io_counters)

        # Hack that divides the total bandwitdth of the container by the number of nodes
        # This needs further work in order to try to capture network traffic at a process level instead
        # We could also try scalling with CPU usages
        network_rx_bytes /= node_cnt
        network_tx_bytes /= node_cnt

        # Keep track of the metrics of the current process/node
        metrics.append({'nonce' : nonce, 'nonce_ts' : nonce_ts,  'container_id' : container.id, 'process_id' : process_id, 'node' : node_id,
                        'binary' : binary_name, 'toml' : toml_name, 'cpu_percent' : cpu_percent, 'memory_usage' : memory_usage, 
                        'network_rx_bytes' : network_rx_bytes, 'network_tx_bytes' : network_tx_bytes, 'disk_read_bytes' : disk_read_bytes, 
                        'disk_write_bytes' : disk_write_bytes, 'ts' : time.time_ns()})

    # elapsed = (time.time() - t_start) * 1000
    # print('Elapsed: get_snapshot() %.4f ms.' %elapsed)
    
    return metrics

def main():

    # Connect to the Docker API
    client = docker.from_env()

    wsl_container = None

    interval_s = 10

    # Wait for WSL to start
    while True:
        print('Waiting for WSL to start ...')
        
        # Get a list of all containers
        try:
            containers = client.containers.list()
        except:
            continue

        wsl_container = [container for container in containers if container.status == 'running' and 'wsl' in container.image.tags[0]]
        if len(wsl_container):
            wsl_container = wsl_container[0]
            print('Found WSL container as %s' %wsl_container)
            break
        
        sleep(interval_s)

    # Get a list of all running containers
    containers = client.containers.list()

    # Define the image name you want to filter for
    image_name = "waku"

    # Filter the list of containers to only include running containers that match the specified image
    matching_containers = [container for container in containers if container.status == 'running' and image_name in container.image.tags[0]]
    
    # Start monitoring
    print('Starting to monitor Docker stats of the enclave ...')
    
    docker_data = [] 
    nonce = 0
    while wsl_container and wsl_container.status == 'running':

        # Update WSL container status   
        wsl_container = client.containers.get(wsl_container.name)

        print('[%d] Monitoring %d containers' %(nonce, len(matching_containers)))
        
        # Print the names of the matching containers
        ts = time.time_ns()
        t_start = time.time() 
        for container in matching_containers:
            
            snapshot = get_snapshot(container, interval_s, nonce, ts)
            docker_data.extend(snapshot)
        
        nonce += 1  

        elapsed = (time.time() - t_start) * 1000
        delta_t = interval_s - elapsed    
        print('Snapshot took %.4f ms. Next in %.4f ms' %(elapsed, delta_t))
               
        if delta_t > 0:
            sleep(delta_t)

    # Generate summary
    summary_path = '%s/%s' %(G_DEFAULT_SIMULATION_PATH, G_DEFAULT_METRICS_FILENAME)
    with open(summary_path, 'w') as fp:
        json.dump(docker_data, fp, indent=4)
    
    print('WSL Ended. Docker metrics saved to %s' %summary_path)

if __name__ == "__main__":
    main()