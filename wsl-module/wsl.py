#!/usr/bin/env python3
"""
Description: Wakurtosis load simulator

"""

""" Dependencies """
import sys, logging, yaml, json, time, random, os, argparse
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
g_DEFAULT_CONFIG_FILE = './config/wsl.yml'
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

def check_waku_node(node_address):

    data = {
        'jsonrpc': '2.0',
        # 'method': 'get_waku_v2_debug_v1_info',
        'method' : 'get_waku_v2_debug_v1_version',
        'id': 1,
        'params' : []}

    G_LOGGER.info('Waku RPC: %s from %s' %(data['method'], node_address))
    
    try:
        response = requests.post(node_address, data=json.dumps(data), headers={'content-type': 'application/json'})
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

def send_waku_msg(node_address, topic, payload, nonce=1):

    waku_msg = {
        'nonce' : nonce,
        'timestamp' : time.time_ns(),
        'payload' : payload}

    data = {
        'jsonrpc': '2.0',
        'method': 'post_waku_v2_relay_v1_message',
        'id': 1,
        'params' : [topic, waku_msg]}

    G_LOGGER.debug('Waku RPC: %s from %s' %(data['method'], node_address))
    
    s_time = time.time()
    
    response = requests.post(node_address, data=json.dumps(data), headers={'content-type': 'application/json'})

    elapsed_ms =(time.time() - s_time) * 1000

    response_obj = response.json()

    G_LOGGER.debug('Response from %s: %s [%.4f ms.]' %(node_address, response_obj, elapsed_ms))
    
    return response_obj, elapsed_ms

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
    parser.add_argument("-cfg", "--config_file", help="Config file", action="store_true", default=g_DEFAULT_CONFIG_FILE)
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
        if not check_waku_node('http://%s/' %target):
            G_LOGGER.error('Node %d (%s) is not online. Aborted.' %(i, target))
            sys.exit(1)
    G_LOGGER.info('All %d Waku nodes are reachable.' %len(targets))

    """ Define the subset of emitters """
    num_emitters = int(len(targets) * config['general']['emitters_fraction'])
    if num_emitters == 0:
        G_LOGGER.error('The number of emitters must be greater than zero. Try increasing the fraction of emitters.')
        sys.exit()

    emitters = random.sample(targets, num_emitters)
    G_LOGGER.info('Selected %d emitters out of %d total nodes' %(len(emitters), len(targets)))

    """ Start simulation """
    stats = {}
    msg_cnt = 0
    bytes_cnt = 0
    s_time = time.time()
    last_msg_time = 0
    next_time_to_msg = 0

    G_LOGGER.info('Starting a simulation of %d seconds ...' %config['general']['simulation_time'])

    while True:
        
        # Check end condition
        elapsed_s = time.time() - s_time
        if  elapsed_s >= config['general']['simulation_time']:
            G_LOGGER.info('Simulation ended. Sent %d messages (%d bytes) in %ds.' %(msg_cnt, bytes_cnt, elapsed_s))
            break

        # Send message
        # BUG: There is a constant discrepancy. The average number of messages sent by time interval is slightly less than expected
        msg_elapsed = time.time() - last_msg_time
        if msg_elapsed <= next_time_to_msg:
            continue

        G_LOGGER.debug('Time Δ: %.6f ms.' %((msg_elapsed - next_time_to_msg) * 1000.0))
        
        # Reference: https://rfc.vac.dev/spec/16/#get_waku_v2_relay_v1_messages
        node_address = 'http://%s/' %random.choice(emitters)

        G_LOGGER.info('Injecting message to network through Waku node %s ...' %node_address)
        
        payload = make_payload_dist(dist_type=config['general']['dist_type'].lower(), min_size=config['general']['min_packet_size'], max_size=config['general']['max_packet_size'])
        response, elapsed = send_waku_msg(node_address, topic='test', payload=payload)

        # # Keep track of basic stats
        # if response['result']:
        #     if node_address in stats:
        #         stats[node_address]['msg_cnt'] += 1
        #         stats[node_address]['msg_sent'] += 1
        #     else:
        #         stats[node_address] = { 'msg_cnt' = 1 }
        #         stats[node_address]['msg_sent'] += 1
        
        # else:
        #     G_LOGGER.error('RPC Message failed to node_address')

        # Compute the time to next message
        # NOTE: Shall we pack this into a function?
        if config['general']['inter_msg_type'] == 'poisson':
            next_time_to_msg = poisson_interval(config['general']['msg_rate']) 
        elif config['general']['inter_msg_type'] == 'uniform':
            next_time_to_msg = config['general']['simulation_time'] / config['general']['msg_rate']
        else:
            G_LOGGER.error('%s is not a valid inter_msg_type. Aborting.' %config['general']['inter_msg_type'])
            sys.exit()

        G_LOGGER.debug('Next message will happen in %d ms.' %(next_time_to_msg * 1000.0))
        
        last_msg_time = time.time()
        
        msg_cnt += 1 
        
    # Pull messages 
    # get_waku_v2_relay_v1_messagesget_waku_v2_relay_v1_messages
    
    """ We are done """
    G_LOGGER.info('Ended')
    
if __name__ == "__main__":
    
    main()
