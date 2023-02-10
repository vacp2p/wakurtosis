#!/usr/bin/env python3
"""
Description: Wakurtosis simulation analysis

"""

""" Dependencies """
import sys, logging, yaml, json, time, random, os, argparse, tomllib, glob, csv

""" Globals """
G_APP_NAME = 'WLS-ANALYSE'
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
    G_LOGGER.debug(topics)
    G_LOGGER.debug(nodes_topics)

    """ Load Simulation Messages """
    msgs_dict = None
    try:
        with open('%s/messages.json' %simulation_path, 'r') as f:
            msgs_dict = json.load(f)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    G_LOGGER.info('Loaded %d messages.' %len(msgs_dict))
    # G_LOGGER.debug(msgs_dict)

    """ Load node level logs """
    node_logs = {}
    try:
        services_log_paths = glob.glob('%s/*--user-service--*' %simulation_path)
        
        for log_path in services_log_paths:
            with open('%s/spec.json' %log_path, mode='r') as f:
                spec_json = json.load(f)
                if spec_json['Path'] == '/usr/bin/wakunode':
                    node_id = spec_json['Config']['Labels']['com.kurtosistech.id']
                    node_logs[node_id] = []
                    with open('%s/output.log' %log_path, mode='r') as f:
                        node_log_reader = csv.reader(f, delimiter=" ")
                        # Check and extract if the log entry is relevant to us
                        for log_line in node_log_reader:
                            # if 'waku.relay received' in log_line:
                            #     print(log_line)
                            # elif 'waku.relay received' in log_line:
                            #     print(log_line)
                            if 'subscribe' in log_line:
                                node_logs[node_id].append(log_line)
                        G_LOGGER.info('Parsed node \"%s\" log in %s/output.log' %(node_id, log_path))
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    G_LOGGER.debug(node_logs.keys())
    # G_LOGGER.debug(node_logs)
    
    ### Statistics we want to compute:
    # 1 - Make sure that all messages have been delivered to their respective peers (x topic)
    # 2 - Calculate the latency of every message at every peer wrt injection time
    # 3 - Summarise/Visualise latencies per node / per topic / per message size?
    # 4 - Reconstruct the path of the messages throughout the network where edge weight is latency
    # 5 - Calculate propagation times per message (time for injection to last node)

    """ We are done """
    G_LOGGER.info('Ended')
    
if __name__ == "__main__":
    
    main()
