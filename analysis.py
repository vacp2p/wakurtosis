#!/usr/bin/env python3
"""
Description: Wakurtosis simulation analysis

"""

""" Dependencies """
import sys, logging, yaml, json, time, random, os, argparse, tomllib, glob, re, requests

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

def fetch_hw_metrics_from_container(container_id):
    
    # cAdvisor API URL endpoint
    url = 'http://localhost:8080/api/v2.1/summary/docker/%s' %container_id
    G_LOGGER.debug('Fetching summary stats from %s ...' %url)
    
    # Make an HTTP request to the cAdvisor API to get the summary stats of the container
    try:
        response = requests.get(url)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        return
    
    # Parse the response as JSON
    summary_stats = json.loads(response.text)
    G_LOGGER.debug(summary_stats)

    return summary_stats

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
                                    msgs_dict[msg_hash] = {'published_ts' : [msg_publishTime], 'received_ts' : []}
                                else:
                                    msgs_dict[msg_hash]['published_ts'].append(msg_publishTime)
                                
                                    # G_LOGGER.debug('Published by %s: %s %s %s %s' %(node_id, msg_publishTime, msg_hash, msg_topic, msg_topics))

                            elif 'received' in log_line: 
                                msg_receivedTime = re.search(r'receivedTime=([\d]+)', log_line).group(1)
                                node_logs[node_id]['received'].append([msg_receivedTime, msg_topics, msg_topic, msg_hash])
                                
                                if msg_hash not in msgs_dict:
                                    msgs_dict[msg_hash] = {'published_ts' : [], 'received_ts' : [msg_receivedTime]}
                                else:
                                    msgs_dict[msg_hash]['received_ts'].append(msg_receivedTime)
                                
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
    for msg in msgs_dict.items():
        published_ts = msg[1]['published_ts'][0]
        msg[1]['latencies'] = []
        for received_ts in msg[1]['received_ts']:
            latency = int(received_ts) - int(published_ts)
            msg[1]['latencies'].append(latency)
            # print(msg[0], msg[1]['published_ts'], received_ts, latency)
        msg[1]['max_latency'] = max(msg[1]['latencies'])
        msg[1]['min_latency'] = min(msg[1]['latencies'])

    # print(msgs_dict)
    ### Statistics we want to compute:
    # 1 - Make sure that all messages have been delivered to their respective peers (x topic)
    # 2 - Calculate the latency of every message at every peer wrt injection time
    # 3 - Summarise/Visualise latencies per node / per topic / per message size?
    # 4 - Reconstruct the path of the messages throughout the network where edge weight is latency
    # 5 - Calculate propagation times per message (time for injection to last node)
    # 6 - Pull statistics from cCadvisor using API (memory, CPU, badnwitdh per node)

    # Fetch Hardware metrics from Node containers 
    for node in node_logs.items():
        node_logs[node[0]]['hw_stats'] = fetch_hw_metrics_from_container(node[1]['container_id'])
        
    # Do Some plotting?


    
    """ We are done """
    G_LOGGER.info('Ended')
    
if __name__ == "__main__":
    
    main()
