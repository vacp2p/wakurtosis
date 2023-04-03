#!/usr/bin/env python3
"""
Description: Wakurtosis simulation analysis

"""

""" Dependencies """
import sys, logging, json, argparse, tomllib, glob, re, statistics
from datetime import datetime
from pathlib import Path
from tqdm_loggable.auto import tqdm
from tqdm_loggable.tqdm_logging import tqdm_logging
import matplotlib.pyplot as plt
import numpy as np

""" Globals """
G_APP_NAME = 'WLS-ANALYSIS'
G_LOG_LEVEL = 'INFO'
G_DEFAULT_CONFIG_FILE = './config/config.json'
G_DEFAULT_TOPOLOGY_PATH = './config/topology_generated'
G_DEFAULT_SIMULATION_PATH = './wakurtosis_logs'
G_DEFAULT_NODES_FIG_FILENAME = './monitoring/nodes_analysis.pdf'
G_DEFAULT_MSGS_FIG_FILENAME = './monitoring/msg_distributions.pdf'
G_DEFAULT_SUMMARY_FILENAME = './monitoring/summary.json'
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

def extract_node_id(s: str) -> str:
    pattern = r"node_(\d+)\.toml"
    match = re.search(pattern, s)
    if match:
        return f"node_{match.group(1)}"
    else:
        return None

def load_metrics(metrics_file_path: str):
    
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
                    pid = process['pid']
                    container_nodes[pid] = node_id  
                
                # Parse samples for each node
                for sample in container_data['samples']:

                    node_id = container_nodes[sample['PID']]
                    if node_id in metrics_dict:
                        metrics_dict[node_id]['samples'].append(sample)
                    else:
                        metrics_dict[node_id] = {'samples' : [sample]}
            
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    G_LOGGER.info('Loaded metrics for %d nodes.' %len(metrics_dict))

    return metrics_dict, info

# def plot_msg_distributions(messages, simulation_config):

#     # msg_sizes_bytes = []
#     # for msg in messages.values():
#     #     print(msg)
#     #     msg_sizes_bytes.append(msg['payload_size'])
    
#     msg_sizes_bytes = [msg['payload_size'] for msg in messages.values()]

#     fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 15))
#     ax1.hist(msg_sizes_bytes, 1000, density = 1, color ='blue', alpha = 0.7)
    
#     plt.tight_layout()

#     figure_path = '%s/%s' %(G_DEFAULT_SIMULATION_PATH, G_DEFAULT_MSGS_FIG_FILENAME)
#     plt.savefig(figure_path, format="pdf", bbox_inches="tight")

#     G_LOGGER.info('Messages distribution figure saved in %s' %figure_path)

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

    # Gather injection times and message sizes
    injection_times = [msg['injection_time'] for msg in injected_msgs_dict.values()]
    injection_sizes = [(msg['injection_time'], msg['payload_size']) for msg in injected_msgs_dict.values()]

    node_logs = {}
    msgs_dict = {}
    
    # Helper list with all the timestamps
    tss = []
    try:
        services_log_paths = glob.glob('%s/*--user-service--*' %simulation_path)
        if len(services_log_paths) == 0:
            G_LOGGER.error('No services logs found in %s' %simulation_path)
            sys.exit()  

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
    total_messages = len(msgs_dict)
    delivered_messages = 0
    lost_messages = 0
    for msg_id, msg in msgs_dict.items():
        
        # Carefull here, we are asuming a single topic, ie every message must be delivered to everynode. For multiple topics we will have to take into accoun the number 
        # of nodes subscribed to each topic for each message
        if len(msg['received']) == len(node_logs):
            delivered_messages += 1
        else:
            # Message hasnt been delivered to all nodes
            lost_messages += 1  
        
        simulation_summary['messages'][msg_id] = {'published' : len(msg['published']), 'received' : len(msg['received'])}

    # lost_messages = total_messages - delivered_messages
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

    """ Load Metrics """
    node_metrics, metrics_info = load_metrics(G_DEFAULT_METRICS_FILENAME)
    simulation_summary['general']['metrics'] = metrics_info

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
    
    # Calculate the effective sampling rate (esr)
    simulation_summary['general']['metrics']['avg_samples_per_node'] = statistics.mean(num_samples)
    simulation_summary['general']['metrics']['esr'] = simulation_summary['general']['metrics']['avg_samples_per_node'] / (simulation_summary['general']['simulation_time_ms'] / 1000.0)

    # Generate Figures
    plot_stats(msg_propagation_times, max_cpu_usage, max_memory_usage, total_network_usage, max_disk_usage, injection_times, simulation_summary['general'], simulation_config)
    # plot_msg_distributions(injected_msgs_dict, simulation_config)

    # Generate summary
    summary_path = G_DEFAULT_SUMMARY_FILENAME
    with open(summary_path, 'w') as fp:
        json.dump(simulation_summary, fp, indent=4)
    G_LOGGER.info('Analsysis sumnmary saved in  %s' %summary_path)

    """ We are done """
    G_LOGGER.info('Ended')
    
if __name__ == "__main__":
    
    main()
