#!/usr/bin/env python3
"""
Description: Wakurtosis simulation analysis

"""

""" Dependencies """
import sys, logging, json, argparse, tomllib, glob, re, requests, statistics, os
from datetime import datetime
from pathlib import Path
from tqdm_loggable.auto import tqdm
from tqdm_loggable.tqdm_logging import tqdm_logging
import matplotlib.pyplot as plt
from scipy import stats

# from prometheus_api_client import PrometheusConnect

""" Globals """
G_APP_NAME = 'WLS-ANALYSIS'
G_LOG_LEVEL = 'INFO'
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

def plot_figure(msg_propagation_times, cpu_usage, memory_usage, network_usage, simulation_summary, simulation_config):

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 15))
    
    ax1.violinplot(msg_propagation_times, showmedians=True)
    ax1.set_title('Message propagation times')
    ax1.set_ylabel('Propagation Time (ms)')
    ax1.spines[['right', 'top']].set_visible(False)
    ax1.axes.xaxis.set_visible(False)

    ax2.violinplot(cpu_usage, showmedians=True)
    ax2.set_title('Maximum CPU usage per Waku node')
    ax2.set_ylabel('CPU Cycles')
    ax2.spines[['right', 'top']].set_visible(False)
    ax2.axes.xaxis.set_visible(False)

    ax3.violinplot(memory_usage, showmedians=True)
    ax3.set_title('Maximum memory usage per Waku node')
    ax3.set_ylabel('Memory (MBytes)')
    ax3.spines[['right', 'top']].set_visible(False)
    ax3.axes.xaxis.set_visible(False)

    ax4.violinplot([network_usage['rx_mbytes'], network_usage['tx_mbytes']], showmedians=True)
    # ax4.violinplot(network_usage['tx_mbytes'], showmedians=True)
    ax4.set_title('Bandwidth per Waku node')
    ax4.set_ylabel('Bandwidth (MBytes)')
    ax4.spines[['right', 'top']].set_visible(False)
    ax4.set_xticks([1, 2])
    ax4.set_xticklabels(['Received (Rx)', 'Sent (Tx)'])
    
    fig.suptitle('Simulation Analisys \n(%d nodes, %d topic(s), Rate: %d msg/s, Time: %.2f s.)' %(simulation_summary['num_nodes'], \
    simulation_summary['num_topics'], simulation_config['wsl']['message_rate'], simulation_summary['simulation_time_ms'] / 1000.0, ), fontsize=20)
    
    plt.tight_layout()

    figure_path = '%s/%s' %(G_DEFAULT_SIMULATION_PATH, G_DEFAULT_FIG_FILENAME)
    plt.savefig(figure_path, format="pdf", bbox_inches="tight")

    G_LOGGER.info('Figure saved in %s' %figure_path)

# def fetch_cadvisor_stats_from_container(container_id, start_ts, end_ts, prometheus_port=52118):

#     url='http://localhost:%d' %52118
    
#     try:
#         G_LOGGER.debug('Connecting to Prometheus server in %s' %url)
#         prometheus = PrometheusConnect(url, disable_ssl=True, container_label="container_label_com_docker_container_id=%s" %container_id)
#         print(prometheus)
#     except Exception as e:
#         G_LOGGER.error('%s: %s' % (e.__doc__, e))
#         return None
    
#     metrics = prometheus.get_label_values("__name__")
#     print(metrics)

#     try:
#         # query = '100 - (avg by(instance) (irate(container_cpu_usage_seconds_total{container_label_com_docker_container_id="<%s>"}[5m])) * 100)' %container_id
#         # query = "container_file_descriptors{process_cpu_seconds_total=\"<%s>\"}" %container_id
#         # result = prometheus.query(query)
#         query = 'process_cpu_seconds_total'
#         result = prometheus.custom_query(query)
#         G_LOGGER.debug('Querying: %s' %query)
#     except Exception as e:
#         G_LOGGER.error('%s: %s' % (e.__doc__, e))
#         return None

    

#     print('--->', result)

#     return {'cpu_usage' : 0, 'memory_usage' : 0, 'bandwidth_in' : 0, 'bandwidth_out' : 0}

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
    network_usage = {'rx_mbytes' : [], 'tx_mbytes' : []}
    for stats_obj in stats_dict.values():
        for data_point in stats_obj['stats']:
            
            # Only take into account data points wihtin the simulation time
            datetime_str = data_point['timestamp']
            datetime_obj = datetime.fromisoformat(datetime_str[:-1])
            unix_seconds = (datetime_obj - datetime(1970, 1, 1)).total_seconds()
            microseconds = datetime_obj.microsecond

            # Convert to nanoseconds
            timestamp_ns = int((unix_seconds * 1e9) + (microseconds * 1e3))

            # if timestamp_ns < start_ts or timestamp_ns > end_ts:
            #     G_LOGGER.debug('Data point %d out of the time window [%d-%d]' %(timestamp_ns, start_ts, end_ts))
            #     continue

            G_LOGGER.debug('Data point %d' %(timestamp_ns))
            cpu_usage.append(data_point['cpu']['usage']['user'])
            memory_usage.append(data_point['memory']['usage'] / 1024 / 1024)
            network_usage['rx_mbytes'].append(data_point['network']['interfaces'][0]['rx_bytes'] / 1024 / 1024)
            network_usage['tx_mbytes'].append(data_point['network']['interfaces'][0]['tx_bytes'] /1024 / 1024)

    G_LOGGER.debug('Aggregated %d data points' %len(cpu_usage))

    return {'cpu_usage' : cpu_usage, 'memory_usage' : memory_usage, 'network_usage' : network_usage}

def main(): 

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

    """ Parse command line args """
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--simulation_path", help="Simulation results path", action="store_true", default=G_DEFAULT_SIMULATION_PATH)
    args = parser.parse_args()

    G_LOGGER.info(args)

    simulation_path = args.simulation_path

    """ Load Simulation Parameters """
    try:
        with open(G_DEFAULT_CONFIG_FILE, "r") as read_file:
            simulation_config = json.load(read_file)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    G_LOGGER.info('Loaded simulation configuration from %s' %G_DEFAULT_CONFIG_FILE)
    
    """ Load Topics Structure """
    topics = set()
    nodes_topics = {}
    try:
        tomls = glob.glob('%s/*.toml' %G_DEFAULT_TOPOLOGY_PATH)
        # Index is the node id
        tomls.sort()
        for toml_file in tomls:
            
            with open(toml_file, mode='rb') as read_file:
                toml_config = tomllib.load(read_file)
                node_id = Path(toml_file).stem
                node_topics_str = toml_config['topics']
                topics_list = list(node_topics_str.split(' '))
                nodes_topics[node_id] = topics_list
                topics.update(topics_list)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    G_LOGGER.info('Loaded topic structure with %d topic(s) and %d node(s).' %(len(topics), len(nodes_topics)))
   
    """ Load Simulation Messages """
    injected_msgs_dict = {}
    try:
        with open('%s/messages.json' %simulation_path, 'r') as f:
            injected_msgs_dict = json.load(f)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    G_LOGGER.info('Loaded %d messages.' %len(injected_msgs_dict))
    # G_LOGGER.debug(injected_msgs_dict)

    node_logs = {}
    msgs_dict = {}
    
    # Helper list with all the timestamps
    tss = []
    try:
        services_log_paths = glob.glob('%s/*--user-service--*' %simulation_path)
    
        pbar = tqdm(services_log_paths)
        for log_path in pbar:
            with open('%s/spec.json' %log_path, mode='r') as f:
                spec_json = json.load(f)
                if spec_json['Path'] == '/usr/bin/wakunode':
                    node_id = spec_json['Config']['Labels']['com.kurtosistech.id']
                    
                    # container_id = spec_json['Name'][1:]
                    container_id = spec_json['Id']
                    node_logs[node_id] = {'published' : [], 'received' : [], 'container_id' : container_id}
                    
                    pbar.set_description("Parsing log of node %s" %node_id)

                    with open('%s/output.log' %log_path, mode='r') as f:
                        
                        # Process log line by line as a text string
                        for log_line in f:
                            
                            # At this stage we only care about Waku Relay protocol
                            if 'waku.relay' in log_line:
                                
                                msg_topics = re.search(r'topics="([^"]+)"', log_line).group(1)
                                msg_topic = re.search(r'pubsubTopic=([^ ]+)', log_line).group(1)
                                msg_hash = re.search(r'hash=([^ ]+)', log_line).group(1)

                                if 'published' in log_line:
                                    msg_publishTime = int(re.search(r'publishTime=([\d]+)', log_line).group(1))
                                    tss.append(msg_publishTime)

                                    node_logs[node_id]['published'].append([msg_publishTime, msg_topics, msg_topic, msg_hash])
                                    
                                    if msg_hash not in msgs_dict:
                                        msgs_dict[msg_hash] = {'published' : [{'ts' : msg_publishTime, 'node_id' : node_id, 'topic' : msg_topic}], 'received' : []}
                                    else:
                                        msgs_dict[msg_hash]['published'].append({'ts' : msg_publishTime, 'node_id' : node_id, 'topic' : msg_topic})
                                    
                                elif 'received' in log_line: 
                                    msg_receivedTime = int(re.search(r'receivedTime=([\d]+)', log_line).group(1))
                                    tss.append(msg_receivedTime)
                                    
                                    node_logs[node_id]['received'].append([msg_receivedTime, msg_topics, msg_topic, msg_hash])
                                    
                                    if msg_hash not in msgs_dict:
                                        msgs_dict[msg_hash] = {'published' : [], 'received' : [{'ts' : msg_receivedTime, 'node_id' : node_id, 'topic' : msg_topic}]}
                                    else:
                                        msgs_dict[msg_hash]['received'].append({'ts' : msg_receivedTime, 'node_id' : node_id, 'topic' : msg_topic})
                                                                    
                    G_LOGGER.debug('Parsed node \"%s\" log in %s/output.log' %(node_id, log_path))
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    simulation_summary = {'general' : {}, 'nodes' : {}, 'messages' : {}, 'simulation parameters' : simulation_config}
    simulation_summary['general']['datetime'] = datetime.now().isoformat()
    simulation_summary['general']['num_messages'] = len(msgs_dict)
    simulation_summary['general']['num_nodes'] = len(node_logs)
    simulation_summary['general']['num_topics'] = len(topics)
    simulation_summary['general']['topics'] = list(topics)

    # Compute effective simulation time window
    simulation_start_ts = min(tss)
    simulation_end_ts = max(tss)
    simulation_time_ms = round((simulation_end_ts - simulation_start_ts) / 1000000)
    simulation_summary['general']['simulation_start_ts'] = simulation_start_ts
    simulation_summary['general']['simulation_end_ts'] = simulation_end_ts
    simulation_summary['general']['simulation_time_ms'] = simulation_time_ms
    G_LOGGER.info('Simulation started at %d, ended at %d Effective simulation time was %d ms. ' %(simulation_start_ts, simulation_end_ts, simulation_time_ms))
        
    # Compute message delivery (node centric)
    simulation_summary['nodes'] = {}
    for node_id, node in node_logs.items():
        simulation_summary['nodes'][node_id] = {'published_msgs' : len(node['published']), 'received_msgs' : len(node['received']), 'topics' : nodes_topics[node_id]}
        
    # Compute message delivery (message centric)
    total_messages = len(injected_msgs_dict)
    delivered_messages = 0
    for msg_id, msg in msgs_dict.items():
        
        if len(msg['received']) > 0:
            delivered_messages += 1
        
        simulation_summary['messages'][msg_id] = {'published' : len(msg['published']), 'received' : len(msg['received'])}

    lost_messages = total_messages - delivered_messages
    lost_pct = 100.0 - (delivered_messages * 100 / total_messages)

    simulation_summary['general']['msgs_total'] = total_messages
    simulation_summary['general']['msgs_delivered'] = delivered_messages
    simulation_summary['general']['msgs_lost'] = lost_messages
    simulation_summary['general']['msgs_lost_pct'] = lost_pct
    
    G_LOGGER.info('%d of %d messages delivered. Lost: %d Lost %% %.2f%%' %(delivered_messages, total_messages, lost_messages, lost_pct))

    # Compute message latencies and propagation times througout the network
    pbar = tqdm(msgs_dict.items())
    for msg_id, msg_data in pbar:
        # NOTE: Carefull here as I am assuming that every message is published once ...
        if len(msg_data['published']) > 1:
            G_LOGGER.warning('Several publishers of message %s')
        
        published_ts = msg_data['published'][0]['ts']
        node_id = msg_data['published'][0]['node_id']
        topic = msg_data['published'][0]['topic']

        simulation_summary['messages'][msg_id]['published_by'] = node_id
        simulation_summary['messages'][msg_id]['published_at'] = published_ts
        simulation_summary['messages'][msg_id]['topic'] = topic
        
        pbar.set_description('Computing latencies of message %s' %msg_id)

        # Compute latencies
        latencies = []
        for received_data in msg_data['received']:
            # Skip self
            if received_data['node_id'] == node_id:
                continue
            # NOTE: We are getting some negative latencies meaning that the message appears to be received before it was sent ... I assume this must be because those are the nodes that got the message injected in the first place
            #  TLDR: Should be safe to ignore all the negative latencies
            latency_ms = (received_data['ts'] - published_ts) / 1e6
            node_id = msg_data['published'][0]['node_id']
            latencies.append(latency_ms)
                    
        msgs_dict[msg_id]['latencies'] = latencies
        if len(latencies):
            simulation_summary['messages'][msg_id]['avg_latency_ms'] = statistics.mean(latencies)
        else:
            G_LOGGER.warning('Message %s hasn\'t been received by any node' %msg_id)
            simulation_summary['messages'][msg_id]['avg_latency_ms'] = None

    msg_propagation_times = []
    pbar = tqdm(msgs_dict.items())
    for msg_id, msg_data in pbar:
        pbar.set_description('Computing propagation time of message %s' %msg_id)
        if len(msg_data['latencies']):
            msg_propagation_times.append(max(msg_data['latencies']))
            simulation_summary['messages'][msg_id]['avg_propagation_ms'] = statistics.mean(msg_data['latencies'])
        else:
            simulation_summary['messages'][msg_id]['avg_propagation_ms'] = None

    # Fetch Hardware metrics from Node containers 
    cpu_usage = []
    memory_usage = []
    network_usage = {'rx_mbytes' : [], 'tx_mbytes' : []}
    pbar = tqdm(node_logs.items())
    for node in pbar:
        pbar.set_description('Fetching hardware stats from container %s' %node[1]['container_id'])
        container_stats = fetch_cadvisor_stats_from_container(node[1]['container_id'], simulation_start_ts, simulation_end_ts)
        
        # NOTE: Here we could also chose a different statistic such as mean or average instead of max
        max_cpu_usage = max(container_stats['cpu_usage'])
        cpu_usage.append(max_cpu_usage)
        simulation_summary['nodes'][node[0]]['max_cpu_usage_cycles'] = max_cpu_usage
        
        max_memory_usage = max(container_stats['memory_usage'])
        memory_usage.append(max_memory_usage)
        simulation_summary['nodes'][node[0]]['max_memory_usage_mbytes'] = max_memory_usage
        
        rx_mbytes = max(container_stats['network_usage']['rx_mbytes'])
        network_usage['rx_mbytes'].append(rx_mbytes)
        simulation_summary['nodes'][node[0]]['max_rx_mbytes'] = rx_mbytes
        
        tx_mbytes = max(container_stats['network_usage']['tx_mbytes'])
        network_usage['tx_mbytes'].append(tx_mbytes)
        simulation_summary['nodes'][node[0]]['max_tx_mbytes'] = tx_mbytes

    # Generate Figure
    plot_figure(msg_propagation_times, cpu_usage, memory_usage, network_usage, simulation_summary['general'], simulation_config)

    # Generate summary
    summary_path = '%s/%s' %(G_DEFAULT_SIMULATION_PATH, G_DEFAULT_SUMMARY_FILENAME)
    with open(summary_path, 'w') as fp:
        json.dump(simulation_summary, fp, indent=4)
    G_LOGGER.info('Analsysis sumnmary saved in  %s' %summary_path)

    """ We are done """
    G_LOGGER.info('Ended')
    
if __name__ == "__main__":
    
    main()
