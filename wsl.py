#!/usr/bin/env python3
"""
Description: Wakurtosis load simulator

"""

""" Dependencies """
import sys, logging, yaml, json, time, random
import requests

# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# import cloudpickle as pickle

""" Globals """
G_APP_NAME = 'WLS'
G_LOG_LEVEL = logging.INFO
G_CONFIG_FILE = './wsl.yml'

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

def ping_waku_node(node_address):

    data = {
        'jsonrpc': '2.0',
        # 'method': 'get_waku_v2_debug_v1_info',
        'method' : 'get_waku_v2_debug_v1_version',
        'id': 1,
        'params' : []}

    logger.info('Waku RPC: %s from %s' %(data['method'], node_address))
    
    response = requests.post(node_address, data=json.dumps(data), headers={'content-type': 'application/json'})

    response_obj = response.json()

    logger.debug('Response from %s: %s' %(node_address, response_obj))
    
    return response_obj

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

    logger.debug('Waku RPC: %s from %s' %(data['method'], node_address))
    
    s_time = time.time()
    
    response = requests.post(node_address, data=json.dumps(data), headers={'content-type': 'application/json'})

    elapsed_ms =(time.time() - s_time) * 1000

    response_obj = response.json()

    logger.debug('Response from %s: %s [%.4f ms.]' %(node_address, response_obj, elapsed_ms))
    
    return response_obj, elapsed_ms

# Generate a random interval using a Poisson distribution
def poisson_interval(rate):
    return random.expovariate(rate)

def make_payload(size):

    # Size in bytes, supposed to be hexa, 2 hexa digits per byte
    payload = ''.join('00' * int(size))

    payload = '0x%s' %payload 

    logger.debug('Payload of size %d bytes: %s' %(size, payload))

    return payload

def make_payload_dist(dist_type, min_size, max_size):

    if dist_type == 'uniform':
        size = random.uniform(min_size, max_size)
        return make_payload(size)

    # TODO: Normal in [a,b]

    logger.error('Unknown distribution type %s')

    return '0x00'

def main():
    
    logger = logging.getLogger(G_APP_NAME)
    logger.info('Started')
    
    """ Load config file """
    try:
        with open(G_CONFIG_FILE, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        logger.error('%s: %s' % (e.__doc__, e))
        sys.exit()
    logger.info('Configuration loaded from %s' %G_CONFIG_FILE)

    random.seed(config['general']['prng_seed'])
    
    """ Load targets """
    try:
        with open(config['general']['targets']) as f:
            targets_obj = json.load(f)
            targets = targets_obj[0]['rpc_targets']
    except Exception as e:
        logger.error('%s: %s' % (e.__doc__, e))
        sys.exit()
    logger.info('Targets loaded: %s' %targets)
    
    """ Ping all nodes """
    for i, target in enumerate(targets):
        ping_waku_node('http://%s/' %target)
    
    """ Start simulation """
    stats = {}
    msg_cnt = 0
    bytes_cnt = 0
    s_time = time.time()
    last_msg_time = 0
    next_time_to_msg = 0

    logger.info('Starting a simulation of %d seconds ...' %config['general']['simulation_time'])

    while True:
        
        # Check end condition
        elapsed_s = time.time() - s_time
        if  elapsed_s >= config['general']['simulation_time']:
            logger.info('Simulation ended. Sent %d messages (%d bytes) in %d at an avg. bandwitdth of %d Bps' %(msg_cnt, bytes_cnt, elapsed_s, bytes_cnt / elapsed_s))
            break

        # Send message
        # BUG: There is a constant discrepancy. The average number of messages sent by time interval is slightly less than expected
        msg_elapsed = time.time() - last_msg_time
        if msg_elapsed <= next_time_to_msg:
            continue
        
        # Reference: https://rfc.vac.dev/spec/16/#get_waku_v2_relay_v1_messages
        node_address = 'http://%s/' %random.choice(targets)
        
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
        #     logger.error('RPC Message failed to node_address')

        # Sampling inter-message times from a Poisson distribution)
        next_time_to_msg = poisson_interval(config['general']['msg_rate'])
        last_msg_time = time.time()
        
        msg_cnt += 1
        bytes_cnt += len(payload) / 2 - 2
        
    # Pull messages so we can verify latency
    # get_waku_v2_relay_v1_messagesget_waku_v2_relay_v1_messages
    
    """ We are done """
    logger.info('Ended')
    
if __name__ == "__main__":
    
    # Init Logging
    logger = logging.getLogger(G_APP_NAME)
    logger.setLevel(G_LOG_LEVEL)
    handler = logging.StreamHandler(sys.stdout)

    handler.setLevel(G_LOG_LEVEL)
    handler.setFormatter(CustomFormatter())
    logger.addHandler(handler)
        
    main()
