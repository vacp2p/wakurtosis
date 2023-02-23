#!/usr/bin/env python3
"""
Description: Wakurtosis simulation analysis

"""

""" Dependencies """
import sys, logging, yaml, json, time, random, os, argparse, tomllib, glob, re, requests
import matplotlib.pyplot as plt
from scipy import stats

""" Globals """
G_APP_NAME = 'WLS-ANALYSIS'
G_LOG_LEVEL = 'DEBUG'
G_DEFAULT_CONFIG_FILE = './config/config.json'
G_DEFAULT_CONFIG_FILE = './config/config.json'
G_DEFAULT_TOPOLOGY_PATH = './config/topology_generated'
G_DEFAULT_SIMULATION_PATH = './wakurtosis_logs'
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

def fetch_cadvisor_stats_from_container(container_id):
    
    # cAdvisor API URL endpoint
    url = 'http://localhost:8080/api/v2.1/stats/docker/%s' %container_id
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
        # print(stats_obj['spec'])
        for data_point in stats_obj['stats']:
            # print(data_point['timestamp'])
            # NOTE: This is comes empty. Check in Ubuntu
            # print(data_point['diskio'])
            # print('CPU:', data_point['cpu']['usage']['user'])
            # print('Memory:', data_point['memory']['usage'])
            cpu_usage.append(data_point['cpu']['usage']['user'])
            memory_usage.append(data_point['memory']['usage'])

    return {'cpu_usage' : cpu_usage, 'memory_usage' : memory_usage}

def main(): 

    global G_LOGGER
    
    """ Init Logging """
    G_LOGGER = logging.getLogger(G_APP_NAME)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    G_LOGGER.addHandler(handler)

    # Set loglevel from config
    G_LOGGER.setLevel(G_LOG_LEVEL)
    handler.setLevel(G_LOG_LEVEL)
    
    G_LOGGER.info('Started')

    """ Parse command line args """
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--simulation_path", help="Simulation results path", action="store_true", default=G_DEFAULT_SIMULATION_PATH)
    args = parser.parse_args()

    simulation_path = args.simulation_path
        
    """ Load Topics Structure """
    topics = set()
    nodes_topics = [] 
    try:
        tomls = glob.glob('%s/*.toml' %G_DEFAULT_TOPOLOGY_PATH)
        # Index is the node id
        tomls.sort()
        for toml_file in tomls:
            
            with open(toml_file, mode='rb') as read_file:
                toml_config = tomllib.load(read_file)
                node_topics_str = toml_config['topics']
                topics_list = list(node_topics_str.split(' '))
                nodes_topics.append(topics_list)
                topics.update(topics_list)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    G_LOGGER.info('Loaded topic structure with %d topic(s) and %d node(s).' %(len(topics), len(nodes_topics)))
    # G_LOGGER.debug(topics)
    # G_LOGGER.debug(nodes_topics)

    """ Load Simulation Messages """
    msgs_dict = {}
    # try:
    #     with open('%s/messages.json' %simulation_path, 'r') as f:
    #         msgs_dict = json.load(f)
    # except Exception as e:
    #     G_LOGGER.error('%s: %s' % (e.__doc__, e))
    #     sys.exit()

    # G_LOGGER.info('Loaded %d messages.' %len(msgs_dict))
    # G_LOGGER.debug(msgs_dict)

    """ Load node level logs """
    node_logs = {}
    # try:
    services_log_paths = glob.glob('%s/*--user-service--*' %simulation_path)
    
    for log_path in services_log_paths:
        with open('%s/spec.json' %log_path, mode='r') as f:
            spec_json = json.load(f)
            if spec_json['Path'] == '/usr/bin/wakunode':
                node_id = spec_json['Config']['Labels']['com.kurtosistech.id']
                # container_id = spec_json['Name'][1:]
                container_id = spec_json['Id']
                node_logs[node_id] = {'published' : [], 'received' : [], 'container_id' : container_id}
                
                with open('%s/output.log' %log_path, mode='r') as f:
                    
                    # Process log line by line as a text string
                    for log_line in f:
                        # At this stage we only care about Waku Relay protocol
                        if 'waku.relay' in log_line:
                            
                            msg_topics = re.search(r'topics="([^"]+)"', log_line).group(1)
                            msg_topic = re.search(r'pubsubTopic=([^ ]+)', log_line).group(1)
                            msg_hash = re.search(r'hash=([^ ]+)', log_line).group(1)

                            if 'published' in log_line:
                                msg_publishTime = re.search(r'publishTime=([\d]+)', log_line).group(1)
                                node_logs[node_id]['published'].append([msg_publishTime, msg_topics, msg_topic, msg_hash])
                                
                                if msg_hash not in msgs_dict:
                                    msgs_dict[msg_hash] = {'published' : [{'ts' : msg_publishTime, 'node_id' : node_id}], 'received' : []}
                                else:
                                    msgs_dict[msg_hash]['published'].append({'ts' : msg_publishTime, 'node_id' : node_id})
                                
                                    # G_LOGGER.debug('Published by %s: %s %s %s %s' %(node_id, msg_publishTime, msg_hash, msg_topic, msg_topics))

                            elif 'received' in log_line: 
                                msg_receivedTime = re.search(r'receivedTime=([\d]+)', log_line).group(1)
                                node_logs[node_id]['received'].append([msg_receivedTime, msg_topics, msg_topic, msg_hash])
                                
                                if msg_hash not in msgs_dict:
                                    msgs_dict[msg_hash] = {'published' : [], 'received' : [{'ts' : msg_receivedTime, 'node_id' : node_id}]}
                                else:
                                    msgs_dict[msg_hash]['received'].append({'ts' : msg_receivedTime, 'node_id' : node_id})
                                
                                # G_LOGGER.debug('Received in node %s: %s %s %s %s' %(node_id, msg_receivedTime, msg_hash, msg_topic, msg_topics))
                                
                        
                G_LOGGER.info('Parsed node \"%s\" log in %s/output.log' %(node_id, log_path))
    # except Exception as e:
    #     G_LOGGER.error('%s: %s' % (e.__doc__, e))
    #     sys.exit()

    # G_LOGGER.debug(node_logs.keys())
    # G_LOGGER.debug(node_logs)
    # for item in node_logs.items():
    #     print(item[0], len(item[1]['published']), len(item[1]['received']))

    # Calculate tota propagation times, ie time for a messafe to reach all the nodes
    # Easiest way is likely to sort the reception time stamps and get the oldest for a specific message within the node
    
    for _, msg_data in msgs_dict.items():
        # NOTE: Carefull here as I am assuming that every message is published once ...
        published_ts = int(msg_data['published'][0]['ts'])
        node_id = msg_data['published'][0]['node_id']
        
        # Compute latencies
        latencies = []
        for received_data in msg_data['received']:
            # Skip self
            if received_data['node_id'] == node_id:
                continue
            # NOTE: We are getting some negative latencies meaning that the message appears to be received before it was sent ... I assume this must be because those are the nodes that got the message injected in the first place
            #  TLDR: Should be safe to ignore all the negative latencies
            latency = int(received_data['ts']) - published_ts
            node_id = msg_data['published'][0]['node_id']
            latencies.append(latency)
                    
        msgs_dict[_]['latencies'] = latencies
            
    msg_propagation_times = []
    for msg_hash, msg_data in msgs_dict.items():
        msg_propagation_times.append(round(max(msg_data['latencies'])/1000000))
    
    print(stats.describe(msg_propagation_times))

    # fig, ax = plt.subplots()
    # ax.violinplot(msg_propagation_times, showmedians=True)
    # ax.set_title('Message propagation times (sample size: %d messages)' %len(msg_propagation_times))
    # ax.set_ylabel('Milliseconds (ms)')
    # ax.spines[['right', 'top']].set_visible(False)
    # ax.axes.xaxis.set_visible(False)
    # plt.tight_layout()
    # plt.savefig("propagation.pdf", format="pdf", bbox_inches="tight")
    # plt.show()

    ### Statistics we want to compute:
    # 1 - Make sure that all messages have been delivered to their respective peers (x topic)
    # 2 - Calculate the latency of every message at every peer wrt injection time
    # 3 - Summarise/Visualise latencies per node / per topic / per message size?
    # 4 - Reconstruct the path of the messages throughout the network where edge weight is latency
    # 5 - Calculate propagation times per message (time for injection to last node)
    # 6 - Pull statistics from cCadvisor using API (memory, CPU, badnwitdh per node)
    # Pull networking info from prometheus/grafana

    # Fetch Hardware metrics from Node containers 
    cpu_usage = []
    memory_usage = []
    for node in node_logs.items():
        container_stats = fetch_cadvisor_stats_from_container(node[1]['container_id'])
        # NOTE: Here we could also chose a different statistic such as mean or average instead of max
        cpu_usage.append(max(container_stats['cpu_usage']))
        memory_usage.append(max(container_stats['memory_usage']))

    # Generate plots
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 10))
    
    ax1.violinplot(msg_propagation_times, showmedians=True)
    ax1.set_title('Message propagation times \n(sample size: %d messages)' %len(msg_propagation_times))
    ax1.set_ylabel('Milliseconds (ms)')
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
    plt.savefig("analysis.pdf", format="pdf", bbox_inches="tight")
    # plt.show()

    """ We are done """
    G_LOGGER.info('Ended')
    
if __name__ == "__main__":
    
    main()
