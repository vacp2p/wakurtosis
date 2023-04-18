#!/usr/bin/env python3
"""
Description: Wakurtosis simulation analysis
"""
import os
import subprocess

""" Dependencies """
import sys, logging, json, argparse, tomllib, glob, re, statistics
from datetime import datetime
from tqdm_loggable.auto import tqdm
from tqdm_loggable.tqdm_logging import tqdm_logging
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np

from prometheus_api_client import PrometheusConnect

""" Globals """
G_APP_NAME = 'WLS-ANALYSIS'
G_LOG_LEVEL = 'DEBUG'
G_DEFAULT_CONFIG_FILE = './config/config.json'
G_DEFAULT_TOPOLOGY_PATH = './config/topology_generated'
G_DEFAULT_SIMULATION_PATH = './wakurtosis_logs'
G_DEFAULT_CONTAINER_FIG_FILENAME = 'container_analysis.pdf'
G_DEFAULT_NODES_FIG_FILENAME = 'node_analysis.pdf'
G_DEFAULT_SUMMARY_FILENAME = 'summary.json'
G_DEFAULT_METRICS_FILENAME = './monitoring/metrics.json'
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


def plot_figure_ex(msg_propagation_times, cpu_usage, memory_usage, network_usage, disk_usage, injection_times, simulation_summary, simulation_config):

    def style_violin(parts, ax):

        # Change the extrema lines to dashed grey lines
        for line in parts['cmaxes'].get_segments() + parts['cmins'].get_segments():
            line_obj = plt.Line2D(line[:, 0], line[:, 1], color='grey', linestyle='dashed', linewidth=0.5)
            ax.add_line(line_obj)

        # Remove the original extrema lines
        parts['cmaxes'].set_visible(False)
        parts['cmins'].set_visible(False)

        # Change the vertical lines to dashed grey lines
        for line in parts['cbars'].get_segments():
            line_obj = plt.Line2D(line[:, 0], line[:, 1], color='grey', linestyle='dashed', linewidth=0.5)
            ax.add_line(line_obj)

        # Remove the original vertical lines
        parts['cbars'].set_visible(False)

        cmean_colors = parts['cmeans'].get_color()
        colors = [cmean_colors[0],'red',cmean_colors[0],cmean_colors[0]]
        parts['cmeans'].set_color(colors)

        # loop over the paths of the mean lines
        xy = [[l.vertices[:,0].mean(),l.vertices[0,1]] for l in parts['cmeans'].get_paths()]
        xy = np.array(xy)
        ax.scatter(xy[:,0], xy[:,1],s=25, c="crimson", marker="o", zorder=3)

        # make lines invisible
        parts['cmeans'].set_visible(False)
    
    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(15, 15))
    
    parts = ax1.violinplot(msg_propagation_times, showmeans=True)
    ax1.set_title('Popagation Time (per message)')
    ax1.set_ylabel('Propagation Time (ms)')
    ax1.spines[['right', 'top']].set_visible(False)
    ax1.axes.xaxis.set_visible(False)
    style_violin(parts, ax1)

    parts = ax2.violinplot(cpu_usage, showmeans=True)
    ax2.set_title('Peak CPU Usage (per node)')
    ax2.set_ylabel('CPU Usage (%)')
    ax2.spines[['right', 'top']].set_visible(False)
    ax2.axes.xaxis.set_visible(False)
    style_violin(parts, ax2)

    parts = ax3.violinplot(memory_usage, showmeans=True)
    ax3.set_title('Peak Memory Usage (per node)')
    ax3.set_ylabel('Memory (MBytes)')
    ax3.spines[['right', 'top']].set_visible(False)
    ax3.axes.xaxis.set_visible(False)
    style_violin(parts, ax3)

    parts = ax4.violinplot([network_usage['rx_mbytes'], network_usage['tx_mbytes']], showmeans=True)
    ax4.set_title('Total Netowrk IO (per node)')
    ax4.set_ylabel('Bandwidth (MBytes)')
    ax4.spines[['right', 'top']].set_visible(False)
    ax4.set_xticks([1, 2])
    ax4.set_xticklabels(['Received (Rx)', 'Sent (Tx)'])
    style_violin(parts, ax4)

    parts = ax5.violinplot(injection_times, showmeans=True)
    ax5.set_title('Injection Time (per message)')
    ax5.set_ylabel('Milliseconds (ms)')
    ax5.spines[['right', 'top']].set_visible(False)
    ax5.axes.xaxis.set_visible(False)
    style_violin(parts, ax5)
    
    parts = ax6.violinplot([disk_usage['disk_read_mbytes'], disk_usage['disk_write_mbytes']], showmeans=True)
    ax6.set_title('Peak Disk IO (per node)')
    ax6.set_ylabel('Disk IO (MBytes)')
    ax6.spines[['right', 'top']].set_visible(False)
    ax6.set_xticks([1, 2])
    ax6.set_xticklabels(['Read', 'Write'])
    style_violin(parts, ax6)
    
    fig.suptitle('Wakurtosis Simulation Node Level Analysis\n(%d nodes, %d topic(s), Rate: %d msg/s, Time: %.2f s. Sampling Rate: %.2f samples/s.)\n' %(simulation_summary['num_nodes'], \
    simulation_summary['num_topics'], simulation_config['wls']['message_rate'], simulation_summary['simulation_time_ms'] / 1000.0, \
    simulation_summary['metrics']['esr']), fontsize=20)
    
    plt.tight_layout()

    figure_path = '%s/%s' %(G_DEFAULT_SIMULATION_PATH, G_DEFAULT_NODES_FIG_FILENAME)
    plt.savefig(figure_path, format="pdf", bbox_inches="tight")

    G_LOGGER.info('Nodes analysis figure saved in %s' %figure_path)


def plot_stats(msg_propagation_times, cpu_usage, memory_usage, network_usage, disk_usage, injection_times, simulation_summary, simulation_config):

    def style_violin(parts, ax):

        # Change the extrema lines to dashed grey lines
        for line in parts['cmaxes'].get_segments() + parts['cmins'].get_segments():
            line_obj = plt.Line2D(line[:, 0], line[:, 1], color='grey', linestyle='dashed', linewidth=0.5)
            ax.add_line(line_obj)

        # Remove the original extrema lines
        parts['cmaxes'].set_visible(False)
        parts['cmins'].set_visible(False)

        # Change the vertical lines to dashed grey lines
        for line in parts['cbars'].get_segments():
            line_obj = plt.Line2D(line[:, 0], line[:, 1], color='grey', linestyle='dashed', linewidth=0.5)
            ax.add_line(line_obj)

        # Remove the original vertical lines
        parts['cbars'].set_visible(False)

        cmean_colors = parts['cmeans'].get_color()
        colors = [cmean_colors[0],'red',cmean_colors[0],cmean_colors[0]]
        parts['cmeans'].set_color(colors)

        # loop over the paths of the mean lines
        xy = [[l.vertices[:,0].mean(),l.vertices[0,1]] for l in parts['cmeans'].get_paths()]
        xy = np.array(xy)
        ax.scatter(xy[:,0], xy[:,1],s=25, c="crimson", marker="o", zorder=3)

        # make lines invisible
        parts['cmeans'].set_visible(False)

    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(15, 15))

    parts = ax1.violinplot(msg_propagation_times, showmeans=True)
    ax1.set_title('Popagation Time (per message)')
    ax1.set_ylabel('Propagation Time (ms)')
    ax1.spines[['right', 'top']].set_visible(False)
    ax1.axes.xaxis.set_visible(False)
    style_violin(parts, ax1)

    parts = ax2.violinplot(cpu_usage, showmeans=True)
    ax2.set_title('Peak CPU Usage (per node)')
    ax2.set_ylabel('CPU Usage (%)')
    ax2.spines[['right', 'top']].set_visible(False)
    ax2.axes.xaxis.set_visible(False)
    style_violin(parts, ax2)

    parts = ax3.violinplot(memory_usage, showmeans=True)
    ax3.set_title('Peak Memory Usage (per node)')
    ax3.set_ylabel('Memory (MBytes)')
    ax3.spines[['right', 'top']].set_visible(False)
    ax3.axes.xaxis.set_visible(False)
    style_violin(parts, ax3)

    parts = ax4.violinplot([network_usage['rx_mbytes'], network_usage['tx_mbytes']], showmeans=True)
    ax4.set_title('Total Netowrk IO (per node)')
    ax4.set_ylabel('Bandwidth (MBytes)')
    ax4.spines[['right', 'top']].set_visible(False)
    ax4.set_xticks([1, 2])
    ax4.set_xticklabels(['Received (Rx)', 'Sent (Tx)'])
    style_violin(parts, ax4)

    parts = ax5.violinplot(injection_times, showmeans=True)
    ax5.set_title('Injection Time (per message)')
    ax5.set_ylabel('Milliseconds (ms)')
    ax5.spines[['right', 'top']].set_visible(False)
    ax5.axes.xaxis.set_visible(False)
    style_violin(parts, ax5)

    parts = ax6.violinplot([disk_usage['disk_read_mbytes'], disk_usage['disk_write_mbytes']], showmeans=True)
    ax6.set_title('Peak Disk IO (per node)')
    ax6.set_ylabel('Disk IO (MBytes)')
    ax6.spines[['right', 'top']].set_visible(False)
    ax6.set_xticks([1, 2])
    ax6.set_xticklabels(['Read', 'Write'])
    style_violin(parts, ax6)

    fig.suptitle('Wakurtosis Simulation Analysis \n(%d nodes, %d topic(s), Rate: %d msg/s, Time: %.2f s. Sampling Rate: %.2f samples/s.)\n' %(simulation_summary['num_nodes'], \
    simulation_summary['num_topics'], simulation_config['wsl']['message_rate'], simulation_summary['simulation_time_ms'] / 1000.0, \
    simulation_summary['metrics']['esr']), fontsize=20)

    plt.tight_layout()

    figure_path = G_DEFAULT_NODES_FIG_FILENAME
    plt.savefig(figure_path, format="pdf", bbox_inches="tight")

    G_LOGGER.info('Nodes analysis figure saved in %s' %figure_path)

def plot_figure(msg_propagation_times, cpu_usage, memory_usage, bandwith_in, bandwith_out):

    fig, (ax1, ax2, ax3, ax4, ax5) = plt.subplots(1, 5, figsize=(15, 10))
    
    if msg_propagation_times:
        ax1.violinplot(msg_propagation_times, showmedians=True)
        ax1.set_title('Message propagation times \n(sample size: %d messages)' %len(msg_propagation_times))
        ax1.set_ylabel('Propagation Time (ms)')
        ax1.spines[['right', 'top']].set_visible(False)
        ax1.axes.xaxis.set_visible(False)

    if cpu_usage:
        ax2.violinplot(cpu_usage, showmedians=True)
        ax2.set_title('Maximum CPU usage per Waku node \n(sample size: %d nodes)' %len(cpu_usage))
        ax2.set_ylabel('CPU Cycles')
        ax2.spines[['right', 'top']].set_visible(False)
        ax2.axes.xaxis.set_visible(False)

    if memory_usage:
        ax3.violinplot(memory_usage, showmedians=True)
        ax3.set_title('Maximum memory usage per Waku node \n(sample size: %d nodes)' %len(memory_usage))
        ax3.set_ylabel('Bytes')
        ax3.spines[['right', 'top']].set_visible(False)
        ax3.axes.xaxis.set_visible(False)

    if bandwith_in:
        ax4.violinplot(bandwith_in, showmedians=True)
        ax4.set_title('Bandwith IN usage per Waku node \n(sample size: %d nodes)' %len(memory_usage))
        ax4.set_ylabel('Bytes')
        ax4.spines[['right', 'top']].set_visible(False)
        ax4.axes.xaxis.set_visible(False)
    
    if bandwith_out:
        ax5.violinplot(bandwith_out, showmedians=True)
        ax5.set_title('Bandwith IN usage per Waku node \n(sample size: %d nodes)' %len(memory_usage))
        ax5.set_ylabel('Bytes')
        ax5.spines[['right', 'top']].set_visible(False)
        ax5.axes.xaxis.set_visible(False)
    
    plt.tight_layout()

    figure_path = '%s/%s' %(G_DEFAULT_SIMULATION_PATH, G_DEFAULT_CONTAINER_FIG_FILENAME)
    plt.savefig(figure_path, format="pdf", bbox_inches="tight")

    G_LOGGER.info('Figure saved in %s' %figure_path)


def connect_to_prometheus():
    prometheus = subprocess.check_output("kurtosis enclave inspect wakurtosis | grep '\\<prometheus\\>' | awk '{print $6}'", shell=True)
    url = f'http://{prometheus[:-1].decode("utf-8") }'

    try:
        G_LOGGER.debug('Connecting to Prometheus server in %s' %url)
        prometheus = PrometheusConnect(url, disable_ssl=True)
        # print(prometheus)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        return None

    return prometheus


def fetch_cadvisor_stats_from_prometheus(prometheus, container_ip, start_ts, end_ts):

    metrics = prometheus.get_label_values("__name__")
    # print(metrics)
    start_timestamp = datetime.utcfromtimestamp(start_ts / 1e9)
    end_timestamp = datetime.fromtimestamp(end_ts / 1e9)

    # container_network_transmit_bytes_total{container_label_com_kurtosistech_private_ip = "212.209.64.2"}
    kurtosis_ip_template = "container_label_com_kurtosistech_private_ip"

    cpu = prometheus.custom_query_range(f"container_cpu_load_average_10s{{{kurtosis_ip_template} "
                                        f"= '{container_ip}'}}", start_time=start_timestamp,
                                        end_time=end_timestamp, step="1s")
    cpu = [float(cpu[0]['values'][i][1]) for i in range(len(cpu[0]['values']))]

    mem = prometheus.custom_query_range(f"container_memory_usage_bytes{{{kurtosis_ip_template} "
                                        f"= '{container_ip}'}}", start_time=start_timestamp,
                                        end_time=end_timestamp, step="1s")
    mem = [int(mem[0]['values'][i][1]) for i in range(len(mem[0]['values']))]

    net_in = prometheus.custom_query_range(f"container_network_receive_bytes_total{{{kurtosis_ip_template}"
                                           f"= '{container_ip}'}}", start_time=start_timestamp,
                                           end_time=end_timestamp, step="1s")
    net_in = [int(net_in[0]['values'][i][1]) for i in range(len(net_in[0]['values']))]

    net_out = prometheus.custom_query_range(f"container_network_transmit_bytes_total{{{kurtosis_ip_template} "
                                            f"= '{container_ip}'}}", start_time=start_timestamp,
                                            end_time=end_timestamp, step="1s")
    net_out = [int(net_out[0]['values'][i][1]) for i in range(len(net_out[0]['values']))]

    return {'cpu_usage': cpu, 'memory_usage': mem, 'bandwidth_in': net_in, 'bandwidth_out': net_out}


def _load_topics(node_info, nodes, node):
    topics = None
    with open("config/topology_generated/" + node_info["node_config"], mode='rb') as read_file:
        toml_config = tomllib.load(read_file)
        if node_info["image"] == "nim-waku":
            topics = list(toml_config["topics"].split(" "))
        elif node_info["image"] == "go-waku":
            topics = toml_config["topics"]
        else:
            raise ValueError("Unknown image type")
    # Load topics into topology for easier access
    nodes[node]["topics"] = topics


def load_topics_into_topology(topology):
    """ Load Topics """
    nodes = topology["nodes"]
    for node, node_info in nodes.items():
        try:
            _load_topics(node_info, nodes, node)
        except ValueError as e:
            G_LOGGER.error('%s: %s' % (e.__doc__, e))
            sys.exit()

    G_LOGGER.info('Loaded nodes topics from toml files')


def load_topology(topology_file):
    """ Load topology """
    with open(topology_file, 'r') as read_file:
        topology = json.load(read_file)

    G_LOGGER.debug(topology)
    G_LOGGER.info('Topology loaded')

    return topology


def load_messages(simulation_path):
    try:
        with open(f'{simulation_path}/messages.json', 'r') as f:
            injected_msgs_dict = json.load(f)
    except OSError as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    G_LOGGER.info(f'Loaded {len(injected_msgs_dict)} messages.')

    return injected_msgs_dict


def compare_tss(tss, min_tss, max_tss):
    if tss < min_tss:
        min_tss = tss
    elif tss > max_tss:
        max_tss = tss

    return min_tss, max_tss


def _innit_logger():
    global G_LOGGER

    """ Init Logging """
    G_LOGGER = logging.getLogger(G_APP_NAME)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    G_LOGGER.addHandler(handler)

    tqdm_logging.set_level(logging.INFO)

    # Set loglevel from config
    G_LOGGER.setLevel(G_LOG_LEVEL)
    handler.setLevel(G_LOG_LEVEL)

    G_LOGGER.info('Started')


def _parse_args():
    """ Parse command line args """
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--simulation_path", help="Simulation results path",
                        default=G_DEFAULT_SIMULATION_PATH)
    args = parser.parse_args()

    simulation_path = args.simulation_path

    return simulation_path


def get_relay_line_info(log_line):
    msg_topics = re.search(r'topics="([^"]+)"', log_line).group(1)
    msg_topic = re.search(r'pubsubTopic=([^ ]+)', log_line).group(1)
    msg_hash = re.search(r'hash=([^ ]+)', log_line).group(1)
    msg_peer_id = re.search(r'peerId=([^ ]+)', log_line).group(1)

    return msg_topics, msg_topic, msg_hash, msg_peer_id


def analyze_published(log_line, node_logs, msgs_dict, msg_publishTime):
    msg_topics, msg_topic, msg_hash, msg_peer_id = get_relay_line_info(log_line)

    node_logs[msg_peer_id]['published'].append([msg_publishTime, msg_topics, msg_topic, msg_hash])

    if msg_hash not in msgs_dict:
        msgs_dict[msg_hash] = {'published': [{'ts': msg_publishTime, 'peer_id': msg_peer_id}],
                               'received': []}
    else:
        msgs_dict[msg_hash]['published'].append(
            {'ts': msg_publishTime, 'peer_id': msg_peer_id})


def analyze_received(log_line, node_logs, msgs_dict, msg_receivedTime):
    msg_topics, msg_topic, msg_hash, msg_peer_id = get_relay_line_info(log_line)
    node_logs[msg_peer_id]['received'].append([msg_receivedTime, msg_topics, msg_topic, msg_hash])

    if msg_hash not in msgs_dict:
        msgs_dict[msg_hash] = {'published': [], 'received': [
            {'ts': msg_receivedTime, 'peer_id': msg_peer_id}]}
    else:
        msgs_dict[msg_hash]['received'].append(
            {'ts': msg_receivedTime, 'peer_id': msg_peer_id})


def parse_lines_in_file(file, node_logs, msgs_dict, min_tss, max_tss):
    for log_line in file:
        if 'waku.relay' in log_line:
            if 'published' in log_line:
                msg_publishTime = int(re.search(r'publishTime=([\d]+)', log_line).group(1))

                analyze_published(log_line, node_logs, msgs_dict, msg_publishTime)

                min_tss, max_tss = compare_tss(msg_publishTime, min_tss, max_tss)

            elif 'received' in log_line:
                msg_receivedTime = int(re.search(r'receivedTime=([\d]+)', log_line).group(1))

                analyze_received(log_line, node_logs, msgs_dict, msg_receivedTime)

                min_tss, max_tss = compare_tss(msg_receivedTime, min_tss, max_tss)

    return min_tss, max_tss


def open_file(folder):
    try:
        file = open(f'{folder[0]}/output.log', mode='r')
    except OSError as e:
        G_LOGGER.error(f'{e.__doc__}: {e}')
        sys.exit()

    return file


def prepare_node_in_logs(node_pbar, topology, node_logs, container_name):
    for node in node_pbar:
        node_info = topology["nodes"][node]
        peer_id = node_info["peer_id"][:3] + "*" + node_info["peer_id"][-6:]
        node_logs[peer_id] = {'published': [], 'received': [],
                              'container_name': container_name, 'peer_id': node}


def analyze_containers(topology, simulation_path):
    node_logs = {}
    msgs_dict = {}
    max_tss = -sys.maxsize - 1
    min_tss = sys.maxsize

    print(topology["containers"])

    for container_name, container_info in topology["containers"].items():
                
        node_pbar = tqdm(container_info["nodes"])

        node_pbar.set_description(f"Parsing log of container {container_name}")

        prepare_node_in_logs(node_pbar, topology, node_logs, container_name)

        folder = glob.glob(f'{simulation_path}/{container_name}--*')
        if len(folder) > 1:
            raise RuntimeError(f"Error: Multiple containers with same name: {folder}")

        file = open_file(folder)
        min_tss, max_tss = parse_lines_in_file(file, node_logs, msgs_dict, min_tss, max_tss)
        file.close()

    return node_logs, msgs_dict, min_tss, max_tss


def compute_message_latencies(msgs_dict):
    # Compute message latencies and propagation times througout the network
    pbar = tqdm(msgs_dict.items())
    for msg_id, msg_data in pbar:
        # NOTE: Carefull here as I am assuming that every message is published once ...
        if len(msg_data['published']) > 1:
            G_LOGGER.warning('Several publishers of message %s')

        published_ts = int(msg_data['published'][0]['ts'])
        peer_id = msg_data['published'][0]['peer_id']

        pbar.set_description('Computing latencies of message %s' % msg_id)

        # Compute latencies
        latencies = []
        for received_data in msg_data['received']:
            # Skip self
            if received_data['peer_id'] == peer_id:
                continue
            # NOTE: We are getting some negative latencies meaning that the message appears to be received before it was sent ...
            # I assume this must be because those are the nodes that got the message injected in the first place
            #  TLDR: Should be safe to ignore all the negative latencies
            latency = int(received_data['ts']) - published_ts
            peer_id = msg_data['published'][0]['peer_id']
            latencies.append(latency)

        msgs_dict[msg_id]['latencies'] = latencies


def compute_propagation_times(msgs_dict):
    msg_propagation_times = []
    pbar = tqdm(msgs_dict.items())

    for msg_id, msg_data in pbar:
        pbar.set_description('Computing propagation time of message %s' % msg_id)
        msg_propagation_times.append(round(max(msg_data['latencies']) / 1000000))

    return msg_propagation_times


def compute_injection_times(injected_msgs_dict):
    return [msg['injection_time'] for msg in injected_msgs_dict.values() if msg['status'] == 200]


def get_hardware_metrics(topology, node_logs, min_tss, max_tss):
    # Fetch Hardware metrics from Node containers
    cpu_usage = []
    memory_usage = []
    bandwith_in = []
    bandwith_out = []
    node_container_ips = [info["kurtosis_ip"] for info in topology["containers"].values()]
    pbar = tqdm(node_container_ips)

    prometheus = connect_to_prometheus()

    for container_ip in pbar:
        
        pbar.set_description(f'Fetching hardware stats from container {container_ip}')
        
        try:
            container_stats = fetch_cadvisor_stats_from_prometheus(prometheus, container_ip, min_tss, max_tss)
        except Exception as e:
            G_LOGGER.error('%s: %s' % (e.__doc__, e))
            continue 
            
        # NOTE: Here we could also choose a different statistic such as mean or average instead of max
        cpu_usage.append(max(container_stats['cpu_usage']))
        memory_usage.append(max(container_stats['memory_usage']))
        bandwith_in.append(max(container_stats['bandwidth_in']))
        bandwith_out.append(max(container_stats['bandwidth_out']))

    return cpu_usage, memory_usage, bandwith_in, bandwith_out


def compute_message_delivery(msgs_dict, injected_msgs_dict):
    
    # Compute message delivery
    total_messages = len(injected_msgs_dict)
    delivered_messages = len(msgs_dict)
    lost_messages = total_messages - delivered_messages
    delivery_rate = delivered_messages * 100 / total_messages

    G_LOGGER.info(f'{delivered_messages} of {total_messages} messages delivered. '
                  f'Lost: {lost_messages}. Delivery rate {delivery_rate}')


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
                        metrics_dict[node_id] = {'samples' : [sample]}
            
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    G_LOGGER.info('Loaded metrics for %d nodes.' %len(metrics_dict))

    return metrics_dict, info


def build_summary(metrics_info, simulation_config, msgs_dict, node_logs, topics, min_tss, max_tss, avg_samples_per_node):

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

    # Load Simulation Parameters
    try:
        with open(G_DEFAULT_CONFIG_FILE, "r") as read_file:
            simulation_summary['parameters'] = json.load(read_file)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        
    return simulation_summary


def compute_process_level_metrics():

    """ Load Metrics """
    node_metrics, metrics_info = load_process_level_metrics(G_DEFAULT_METRICS_FILENAME)
    
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
        
        # This accumulated 
        total_network_usage['rx_mbytes'].append(sum(obj['NetStats']['all']['total_received'] for obj in node_obj['samples']) / (1024*1024))
        total_network_usage['tx_mbytes'].append(sum(obj['NetStats']['all']['total_sent'] for obj in node_obj['samples']) / (1024*1024))

        # Peak values
        max_disk_usage['disk_read_mbytes'].append(max(obj['DiskIORChar'] for obj in node_obj['samples']) / (1024*1024))
        max_disk_usage['disk_write_mbytes'].append(max(obj['DiskIOWChar'] for obj in node_obj['samples']) / (1024*1024))
    
    avg_samples_per_node = statistics.mean(num_samples)
   
    return metrics_info, max_cpu_usage, max_memory_usage, total_network_usage, max_disk_usage, avg_samples_per_node

# todo change timestamps
# todo cpu load zero
# todo merge branch


def main():

    _innit_logger()
    simulation_path = _parse_args()
        
    """ Load Topics Structure """
    topology = load_topology(simulation_path + "/network_data.json")
    load_topics_into_topology(topology)

    """ Load Simulation Messages """
    injected_msgs_dict = load_messages(simulation_path)

    node_logs, msgs_dict, min_tss, max_tss = analyze_containers(topology, simulation_path)

    # Compute simulation time window
    simulation_time_ms = round((max_tss - min_tss) / 1000000)
    G_LOGGER.info(f'Simulation started at {min_tss}, ended at {max_tss}. '
                  f'Effective simulation time was {simulation_time_ms} ms.')
    
    compute_message_delivery(msgs_dict, injected_msgs_dict)
    compute_message_latencies(msgs_dict)
    msg_propagation_times = compute_propagation_times(msgs_dict)
    msg_injection_times = compute_injection_times(injected_msgs_dict)
    
    # Pull hardware metrics from cAdvisor at a container level
    cpu_usage, memory_usage, bandwith_in, bandwith_out = get_hardware_metrics(topology, node_logs, min_tss, max_tss)

    # Generate Figure
    # plot_figure(msg_propagation_times, cpu_usage, memory_usage, bandwith_in, bandwith_out)
    total_network_usage = {'rx_mbytes' : bandwith_in, 'tx_mbytes' : bandwith_out}
    plot_figure_ex(msg_propagation_times, cpu_usage, memory_usage, total_network_usage, max_disk_usage,
                   msg_injection_times, summary['general'], summary['parameters'])
    # Pull metrics from process level monitoring
    if os.path.exists(G_DEFAULT_METRICS_FILENAME):
        metrics_info, max_cpu_usage, max_memory_usage, total_network_usage, max_disk_usage, avg_samples_per_node = compute_process_level_metrics()
        
        # Build simulation summary
        summary = build_summary(metrics_info, topology, msgs_dict, node_logs, [], min_tss, max_tss, avg_samples_per_node)
        
        # Plot figure
        plot_figure_ex(msg_propagation_times, max_cpu_usage, max_memory_usage, total_network_usage, max_disk_usage, 
                       msg_injection_times, summary['general'], summary['parameters'])
        
        # Generate summary
        summary_path = '%s/%s' %(G_DEFAULT_SIMULATION_PATH, G_DEFAULT_SUMMARY_FILENAME)
        with open(summary_path, 'w') as fp:
            json.dump(summary, fp, indent=4)
        G_LOGGER.info('Analsysis sumnmary saved in  %s' %summary_path)
    else:
        G_LOGGER.info('No metrics file found. Skipping process level metrics.')
    
    """ We are done """
    G_LOGGER.info('Ended')


if __name__ == "__main__":
    main()
