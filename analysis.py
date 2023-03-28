#!/usr/bin/env python3
"""
Description: Wakurtosis simulation analysis
"""

""" Dependencies """
import sys, logging, json, argparse, tomllib, glob, re, requests
from datetime import datetime
from tqdm_loggable.auto import tqdm
from tqdm_loggable.tqdm_logging import tqdm_logging
import matplotlib.pyplot as plt

from prometheus_api_client import PrometheusConnect

""" Globals """
G_APP_NAME = 'WLS-ANALYSIS'
G_LOG_LEVEL = 'DEBUG'
G_DEFAULT_CONFIG_FILE = './config/config.json'
G_DEFAULT_CONFIG_FILE = './config/config.json'
G_DEFAULT_TOPOLOGY_PATH = './config/topology_generated'
G_DEFAULT_SIMULATION_PATH = './wakurtosis_logs'
G_DEFAULT_FIG_FILENAME = 'analysis.pdf'
G_DEFAULT_SUMMARY_FILENAME = 'summary.json'
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


def plot_figure(msg_propagation_times, cpu_usage, memory_usage):

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 10))
    
    ax1.violinplot(msg_propagation_times, showmedians=True)
    ax1.set_title('Message propagation times \n(sample size: %d messages)' %len(msg_propagation_times))
    ax1.set_ylabel('Propagation Time (ms)')
    ax1.spines[['right', 'top']].set_visible(False)
    ax1.axes.xaxis.set_visible(False)

    ax2.violinplot(cpu_usage, showmedians=True)
    ax2.set_title('Maximum CPU usage per Waku node \n(sample size: %d nodes)' %len(cpu_usage))
    ax2.set_ylabel('CPU Cycles')
    ax2.spines[['right', 'top']].set_visible(False)
    ax2.axes.xaxis.set_visible(False)

    ax3.violinplot(memory_usage, showmedians=True)
    ax3.set_title('Maximum memory usage per Waku node \n(sample size: %d nodes)' %len(memory_usage))
    ax3.set_ylabel('Bytes')
    ax3.spines[['right', 'top']].set_visible(False)
    ax3.axes.xaxis.set_visible(False)
    
    plt.tight_layout()

    figure_path = '%s/%s' %(G_DEFAULT_SIMULATION_PATH, G_DEFAULT_FIG_FILENAME)
    plt.savefig(figure_path, format="pdf", bbox_inches="tight")

    G_LOGGER.info('Figure saved in %s' %figure_path)


def fetch_cadvisor_stats_from_container_2(container_id, start_ts, end_ts, prometheus_port=52118):
    url='http://localhost:%d' %52118

    try:
        G_LOGGER.debug('Connecting to Prometheus server in %s' %url)
        prometheus = PrometheusConnect(url, disable_ssl=True,
                                       container_label="container_label_com_docker_container_id=%s" %container_id)
        print(prometheus)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        return None

    metrics = prometheus.get_label_values("__name__")
    print(metrics)
    try:
        # query = '100 - (avg by(instance) (irate(container_cpu_usage_seconds_total{container_label_com_docker_container_id="<%s>"}[5m])) * 100)' %container_id
        # query = "container_file_descriptors{process_cpu_seconds_total=\"<%s>\"}" %container_id
        # result = prometheus.query(query)
        query = 'process_cpu_seconds_total'
        result = prometheus.custom_query(query)
        G_LOGGER.debug('Querying: %s' %query)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        return None

    print('--->', result)
    return {'cpu_usage' : 0, 'memory_usage' : 0, 'bandwidth_in' : 0, 'bandwidth_out' : 0}


def fetch_cadvisor_summary_from_container(container_id):
    
    # cAdvisor API URL endpoint
    url = 'http://localhost:8080/api/v2.1/summary/docker/%s' %container_id
    # Note: We can also use the endpoint /stats instead of summary to get timepoints
    G_LOGGER.debug('Fetching summary stats from %s ...' %url)
    
    # Make an HTTP request to the cAdvisor API to get the summary stats of the container
    try:
        response = requests.get(url)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        return
    
    # Parse the response as JSON
    summary_stats = json.loads(response.text)
    # G_LOGGER.debug(summary_stats)

    return summary_stats


def fetch_cadvisor_stats_from_container(container_id, start_ts, end_ts):
    
    # cAdvisor API URL endpoint
    url = 'http://localhost:8080/api/v2.1/stats/docker/%s?count=1000' %(container_id)
    # Note: We can also use the endpoint /stats instead of summary to get timepoints
    G_LOGGER.debug('Fetching cAdvisor stats from %s ...' %url)
    
    # Make an HTTP request to the cAdvisor API to get the summary stats of the container
    try:
        response = requests.get(url)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        return
    
    # Parse the response as JSON
    stats_dict = json.loads(response.text)
    
    cpu_usage = []
    memory_usage = [] 
    for stats_obj in stats_dict.values():
        
        for data_point in stats_obj['stats']:
            
            # Only take into account data points wihtin the simulation time
            datetime_str = data_point['timestamp']
            # print(datetime_str)
            datetime_obj = datetime.fromisoformat(datetime_str[:-1])
            # print(datetime_obj)
            # timestamp_ns = int(datetime_obj.timestamp() * 1e9)
            # Calculate the total number of seconds and microseconds since the Unix epoch
            unix_seconds = (datetime_obj - datetime(1970, 1, 1)).total_seconds()
            microseconds = datetime_obj.microsecond

            # Convert to nanoseconds
            timestamp_ns = int((unix_seconds * 1e9) + (microseconds * 1e3))

            # if timestamp_ns < start_ts or timestamp_ns > end_ts:
            #     G_LOGGER.debug('Data point %d out of the time window [%d-%d]' %(timestamp_ns, start_ts, end_ts))
            #     continue

            G_LOGGER.debug('Data point %d' %(timestamp_ns))
            
            # print(data_point['timestamp'])
            # NOTE: This is comes empty. Check in Ubuntu
            # print(data_point['diskio'])
            # print('CPU:', data_point['cpu']['usage']['user'])
            # print('Memory:', data_point['memory']['usage'])
            cpu_usage.append(data_point['cpu']['usage']['user'])
            memory_usage.append(data_point['memory']['usage'])

    print(len(cpu_usage))

    return {'cpu_usage' : cpu_usage, 'memory_usage' : memory_usage}


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

    for container_name, nodes_in_container in topology["containers"].items():
        node_pbar = tqdm(nodes_in_container)

        node_pbar.set_description(f"Parsing log of container {container_name}")

        prepare_node_in_logs(node_pbar, topology, node_logs, container_name)

        folder = glob.glob(f'{simulation_path}/{container_name}*')
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


def get_hardware_metrics(node_logs, min_tss, max_tss):
    # Fetch Hardware metrics from Node containers
    cpu_usage = []
    memory_usage = []
    pbar = tqdm(node_logs.items())
    for node in pbar:
        pbar.set_description(
            'Fetching hardware stats from container %s' % node[1]['container_name'])
        container_stats = fetch_cadvisor_stats_from_container(node[1]['container_name'], min_tss,
                                                              max_tss)
        # NOTE: Here we could also chose a different statistic such as mean or average instead of max
        cpu_usage.append(max(container_stats['cpu_usage']))
        memory_usage.append(max(container_stats['memory_usage']))

    return cpu_usage, memory_usage


def compute_message_delivery(msgs_dict, injected_msgs_dict):
    # Compute message delivery
    total_messages = len(injected_msgs_dict)
    delivered_messages = len(msgs_dict)
    lost_messages = total_messages - delivered_messages
    delivery_rate = delivered_messages * 100 / total_messages

    G_LOGGER.info(f'{delivered_messages} of {total_messages} messages delivered. '
                  f'Lost: {lost_messages}. Delivery rate {delivery_rate}')


def main():
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
    cpu_usage, memory_usage = get_hardware_metrics(node_logs, min_tss, max_tss)

    # Generate Figure
    plot_figure(msg_propagation_times, cpu_usage, memory_usage)
    
    """ We are done """
    G_LOGGER.info('Ended')


if __name__ == "__main__":
    main()
