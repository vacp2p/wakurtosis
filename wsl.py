#!/usr/bin/env python3
"""
Description: Wakurtosis load simulator

"""

""" Dependencies """
import sys, logging, yaml, json, time, random, os
import requests
# from pathlib import Path
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# import cloudpickle as pickle

""" Globals """
G_APP_NAME = 'WLS'
G_LOG_LEVEL = 'INFO'
G_CONFIG_FILE = './wsl.yml'
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

    # Size in bytes, supposed to be hexa, 2 hexa digits per byte
    payload = ''.join('00' * int(size))

    payload = '0x%s' %payload 

    G_LOGGER.debug('Payload of size %d bytes: %s' %(size, payload))

    return payload

def make_payload_dist(dist_type, min_size, max_size):

    if dist_type == 'uniform':
        size = random.uniform(min_size, max_size)
        return make_payload(size)

    # TODO: Normal in [a,b]

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
    
    """ Load config file """
    try:
        with open(G_CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()
    G_LOGGER.info('Configuration loaded from %s' %G_CONFIG_FILE)

    # Set loglevel from config
    G_LOGGER.setLevel(config['general']['debug_level'])
    handler.setLevel(config['general']['debug_level'])

    # Set RPNG seed from config
    random.seed(config['general']['prng_seed'])
    
    """ Dump enclave info """
    # Delete previous dump
    os.system('rm -rf %s' %config['general']['enclave_dump_path'])
    # Generate new dump
    os.system('kurtosis enclave dump %s %s' %(config['general']['enclave_name'], config['general']['enclave_dump_path']))

    """ Parse targets """
    targets = parse_targets(config['general']['enclave_dump_path'])
    
    """ Check all nodes are reachable """
    for i, target in enumerate(targets):
        if not check_waku_node('http://%s/' %target):
            G_LOGGER.error('Node %d (%s) is not online. Aborted.' %(i, target))
            sys.exit(1)
    G_LOGGER.info('All %d Waku nodes are reachable.' %len(targets))

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
            G_LOGGER.info('Simulation ended. Sent %d messages (%d bytes) in %d at an avg. bandwitdth of %d Bps' %(msg_cnt, bytes_cnt, elapsed_s, bytes_cnt / elapsed_s))
            break

        # Send message
        # BUG: There is a constant discrepancy. The average number of messages sent by time interval is slightly less than expected
        msg_elapsed = time.time() - last_msg_time
        if msg_elapsed <= next_time_to_msg:
            continue
        
        # Reference: https://rfc.vac.dev/spec/16/#get_waku_v2_relay_v1_messages
        node_address = 'http://%s/' %random.choice(targets)

        G_LOGGER.info('Injecting message to network through Waku node %s ...' %node_address)
        
        payload = make_payload_dist(dist_type='uniform', min_size=config['general']['min_packet_size'], max_size=config['general']['max_packet_size'])
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

        # Sampling inter-message times from a Poisson distribution)
        next_time_to_msg = poisson_interval(config['general']['msg_rate'])
        last_msg_time = time.time()
        
        msg_cnt += 1
        bytes_cnt += len(payload) / 2 - 2
        
    # Pull messages 
    # get_waku_v2_relay_v1_messagesget_waku_v2_relay_v1_messages
    
    """ We are done """
    G_LOGGER.info('Ended')
    
if __name__ == "__main__":
    
    main()
