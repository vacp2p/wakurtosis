#!/usr/bin/env python3
"""
Description: Wakurtosis load simulator

"""

""" Dependencies """
import sys, logging, yaml, json, time, random, os, argparse, tomllib, glob
import requests
import rtnorm
# from pathlib import Path
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# import cloudpickle as pickle

""" Globals """
G_APP_NAME = 'WLS'
G_LOG_LEVEL = 'DEBUG'
G_DEFAULT_CONFIG_FILE = './config/wsl.yml'
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

def check_nomos_node(node_address):
    url = node_address + "network/info"
    
    try:
        response = requests.get(url)
    except Exception as e:
        G_LOGGER.debug('%s: %s' % (e.__doc__, e))
        return False

    try:
        response_obj = response.json()
    except Exception as e:
        G_LOGGER.debug('%s: %s' % (e.__doc__, e))
        return False

    G_LOGGER.debug('Response from %s: %s' %(node_address, response_obj))
    
    return True

def add_nomos_tx(node_address, tx):
    url = node_address + "mempool/addtx"

    try:
        response = requests.post(url, data=json.dumps(tx), headers={'content-type': 'application/json'})
    except Exception as e:
        G_LOGGER.debug('%s: %s' % (e.__doc__, e))
        return False

    G_LOGGER.debug('Response from %s: %s' %(url, response.text))
    
    return True

def get_nomos_mempool_metrics(node_address):
    url = node_address + "mempool/metrics"

    try:
        response = requests.get(url)
    except Exception as e:
        G_LOGGER.debug('%s: %s' % (e.__doc__, e))
        return False

    try:
        response_obj = response.json()
    except Exception as e:
        G_LOGGER.debug('%s: %s' % (e.__doc__, e))
        return False

    G_LOGGER.debug('Response from %s: %s' %(node_address, response_obj))
    
    return True


# Generate a random interval using a Poisson distribution
def poisson_interval(rate):
    return random.expovariate(rate)

def make_payload(size):
    payload = hex(random.getrandbits(4*size))     
    G_LOGGER.debug('Payload of size %d bytes: %s' %(size, payload))
    return payload

def make_payload_dist(dist_type, min_size, max_size):

    # Check if min and max packet sizes are the same
    if min_size == max_size:
        G_LOGGER.warning('Packet size is constant: min_size=max_size=%d' %min_size)
        return make_payload(min_size)

    # Payload sizes are even integers uniformly distributed in [min_size, max_size] 
    if dist_type == 'uniform':
        size = int(random.uniform(min_size, max_size))
        
        # Reject non even sizes
        while(size % 2) != 0:
            size = int(random.uniform(min_size, max_size))
            
        return make_payload(size)

    # Payload sizes are even integers ~"normally" distributed in [min_size, max_size] 
    if dist_type == 'gaussian':
        σ = (max_size - min_size) / 5.
        μ = (max_size - min_size) / 2.
        size = int(rtnorm.rtnorm(min_size, max_size, sigma=σ, mu=μ, size=1))
        
        # Reject non even sizes
        while(size % 2) != 0:
            size = int(rtnorm.rtnorm(min_size, max_size, sigma=σ, mu=μ, size=1))

        return make_payload(size)

    G_LOGGER.error('Unknown distribution type %s')

    return '0x00'

def parse_targets(enclave_dump_path, waku_port=8545):

    targets = []

    G_LOGGER.info('Extracting Waku node addresses from Kurtosus enclance dump in %s' %enclave_dump_path)            

    for path_obj in os.walk(enclave_dump_path):
        if 'waku_' in path_obj[0]:
            with open(path_obj[0] + '/spec.json', "r") as read_file:
                spec_obj = json.load(read_file)
                network_settings = spec_obj['NetworkSettings']
                waku_address = network_settings['Ports']['%d/tcp' %waku_port]
                targets.append('%s:%s' %(waku_address[0]['HostIp'], waku_address[0]['HostPort']))

    G_LOGGER.info('Parsed %d Waku nodes' %len(targets))            

    return targets

def get_next_time_to_msg(inter_msg_type, msg_rate, simulation_time):
    
    if inter_msg_type == 'poisson':
        return poisson_interval(msg_rate) 
    
    if inter_msg_type == 'uniform':
        return simulation_time / msg_rate
        
    G_LOGGER.error('%s is not a valid inter_msg_type. Aborting.' %inter_msg_type)
    sys.exit()

def get_all_messages_from_node_from_topic(node_address, topic):

    page_cnt = 0
    msg_cnt = 0

    # Retrieve the first page
    response, elapsed = get_waku_msgs(node_address, topic)
    if 'error' in response:
        G_LOGGER.error(response['error'])
        return 0
    
    messages = response['result']['messages']
    msg_cnt += len(messages)
    G_LOGGER.debug('Got page %d with %d messages from node %s and topic: %s' %(page_cnt, len(messages), node_address, topic))

    for msg_idx, msg in enumerate(messages):
        # Decode the payload
        payload_obj = json.loads(''.join(map(chr, msg['payload'])))
        
    # Retrieve further pages
    while(response['result']['pagingOptions']):
        page_cnt += 1
        cursor = response['result']['pagingOptions']['cursor']
        index = {"digest" : cursor['digest'], "receivedTime" : cursor['receiverTime']}
        response, elapsed = get_waku_msgs(node_address, topic, cursor)
        if 'error' in response:
            G_LOGGER.error(response['error'])
            break

        messages = response['result']['messages']
        msg_cnt += len(messages)
        G_LOGGER.debug('Got page %d with %d messages from node %s and topic: %s' %(page_cnt, len(messages), node_address, topic))

        for msg_idx, msg in enumerate(messages):
            # Decode the payload
            payload_obj = json.loads(''.join(map(chr, msg['payload'])))
    
    return msg_cnt

def main(): 

    global G_LOGGER
    
    """ Init Logging """
    G_LOGGER = logging.getLogger(G_APP_NAME)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    G_LOGGER.addHandler(handler)
    
    G_LOGGER.info('Started')

    """ Parse command line args. """
    parser = argparse.ArgumentParser()
    parser.add_argument("-cfg", "--config_file", help="Config file", action="store_true", default=G_DEFAULT_CONFIG_FILE)
    args = parser.parse_args()

    config_file = args.config_file
        
    """ Load config file """
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()
    
    # Set loglevel from config
    G_LOGGER.setLevel(config['general']['debug_level'])
    handler.setLevel(config['general']['debug_level'])

    G_LOGGER.debug(config)
    G_LOGGER.info('Configuration loaded from %s' %config_file)

    # Set RPNG seed from config
    random.seed(config['general']['prng_seed'])
    
    """ Load targets """
    try:
        with open(config['general']['targets_file'], 'r') as read_file:
            targets = json.load(read_file)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    if len(targets) == 0:
        G_LOGGER.error('Cannot find valid targets. Aborting.')
        sys.exit(1)

    G_LOGGER.debug(targets)
    G_LOGGER.info('%d targets loaded' %len(targets))
    
    """ Check all nodes are reachable """
    for i, target in enumerate(targets):
        if not check_nomos_node('http://%s/' %target):
            G_LOGGER.error('Node %d (%s) is not online. Aborted.' %(i, target))
            sys.exit(1)
    G_LOGGER.info('All %d Waku nodes are reachable.' %len(targets))

    G_LOGGER.info('Tx addition start time: %d' %int(time.time()))
    """ Add new transaction to every node """
    for i, target in enumerate(targets):
        if not add_nomos_tx('http://%s/' %target, 'tx%s' %i):
            G_LOGGER.error('Unable to add new tx. Node %d (%s).' %(i, target))

    """ Collect mempool metrics from nodes """
    for i, target in enumerate(targets):
        if not get_nomos_mempool_metrics('http://%s/' %target):
            G_LOGGER.error('Unable to add new tx. Node %d (%s).' %(i, target))

    """ We are done """
    G_LOGGER.info('Ended')
    
if __name__ == "__main__":
    
    main()
