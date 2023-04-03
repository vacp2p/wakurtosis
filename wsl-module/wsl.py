#!/usr/bin/env python3
"""
Description: Wakurtosis load simulator

"""

""" Dependencies """
import sys, logging, yaml, json, time, random, os, argparse, tomllib, glob, hashlib
import requests
import rtnorm
import asyncio
import aiohttp
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

def check_waku_node(node_address):

    data = {
        'jsonrpc': '2.0',
        'method': 'get_waku_v2_debug_v1_info',
        # 'method' : 'get_waku_v2_debug_v1_version',
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

def get_waku_msgs(node_address, topic, cursor=None):

    data = {
        'jsonrpc': '2.0',
        'method': 'get_waku_v2_store_v1_messages',
        'id': 1,
        'params' : [topic, None, None, None, {"pageSize": 100, "cursor": cursor,"forward": True}]
    }

    G_LOGGER.debug('Waku RPC: %s from %s' %(data['method'], node_address))
    
    s_time = time.time()
    
    response = requests.post(node_address, data=json.dumps(data), headers={'content-type': 'application/json'})

    elapsed_ms =(time.time() - s_time) * 1000

    response_obj = response.json()

    # G_LOGGER.debug('Response from %s: %s [%.4f ms.]' %(node_address, response_obj, elapsed_ms))
    
    return response_obj, elapsed_ms

# https://rfc.vac.dev/spec/16/#get_waku_v2_relay_v1_messages
def get_last_waku_msgs(node_address, topic):

    data = {
        'jsonrpc': '2.0',
        'method': 'get_waku_v2_relay_v1_messages',
        'id': 1,
        'params' : [topic]}

    G_LOGGER.debug('Waku RPC: %s from %s' %(data['method'], node_address))
    
    s_time = time.time()
    
    response = requests.post(node_address, data=json.dumps(data), headers={'content-type': 'application/json'})

    elapsed_ms =(time.time() - s_time) * 1000

    response_obj = response.json()

    # G_LOGGER.debug('Response from %s: %s [%.4f ms.]' %(node_address, response_obj, elapsed_ms))
    
    return response_obj, elapsed_ms

async def send_waku_msg(node_address, topic, payload, payload_size, nonce=1):

    # waku_msg = {
    #     'nonce' : nonce,
    #     'timestamp' : time.time_ns(),
    #     'payload' : payload}

    my_payload = {
        'nonce' : nonce,
        'ts' : time.time_ns(),
        'payload' : payload
    }

    waku_msg = {
        'payload' : json.dumps(my_payload).encode('utf-8').hex()
    }

    data = {
        'jsonrpc': '2.0',
        'method': 'post_waku_v2_relay_v1_message',
        'id': 1,
        'params' : [topic, waku_msg]}

    G_LOGGER.debug('Waku RPC: %s from %s Topic: %s' %(data['method'], node_address, topic))
    
    s_time = time.time()

    json_data = json.dumps(data)
    
    # response = requests.post(node_address, data=json_data, headers={'content-type': 'application/json'})
    
    async with aiohttp.ClientSession() as session:
        async with session.post(node_address, data=json_data, headers={'content-type': 'application/json'}) as response:
            elapsed_ms =(time.time() - s_time) * 1000
            
            G_LOGGER.debug('Response from %s: %s [%.4f ms.]' %(node_address, response.status, elapsed_ms))
    
            return response.status, elapsed_ms, json.dumps(waku_msg), my_payload['ts'], node_address, topic, payload, payload_size, nonce

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
        return make_payload(min_size), min_size

    # Payload sizes are even integers uniformly distributed in [min_size, max_size] 
    if dist_type == 'uniform':
        size = int(random.uniform(min_size, max_size))
        
        # Reject non even sizes
        while(size % 2) != 0:
            size = int(random.uniform(min_size, max_size))
            
        return make_payload(size), size

    # Payload sizes are even integers ~"normally" distributed in [min_size, max_size] 
    if dist_type == 'gaussian':
        σ = (max_size - min_size) / 5.
        μ = (max_size - min_size) / 2.
        size = int(rtnorm.rtnorm(min_size, max_size, sigma=σ, mu=μ, size=1))
        
        # Reject non even sizes
        while(size % 2) != 0:
            size = int(rtnorm.rtnorm(min_size, max_size, sigma=σ, mu=μ, size=1))

        return make_payload(size), size

    G_LOGGER.error('Unknown distribution type %s')

    return '0x00', 0

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
        return simulation_time / (msg_rate * simulation_time)
        
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

async def simulate(config, emitters, emitters_indices, emitters_topics):
    
    G_LOGGER.info('Starting a simulation of %d seconds ...' %config['general']['simulation_time'])

    s_time = time.time()
    
    last_msg_time = 0
    next_time_to_msg = 0
    msgs_dict = {}
    tasks = []
    nonce = 0

    while True:
        
        # Check end condition
        elapsed_s = time.time() - s_time
        if  elapsed_s >= config['general']['simulation_time']:
            G_LOGGER.info('Simulation ended. Sent %d messages in %ds.' %(len(msgs_dict), elapsed_s))
            break

        # Send message
        # BUG: There is a constant discrepancy. The average number of messages sent by time interval is slightly less than expected
        msg_elapsed = time.time() - last_msg_time
        # if msg_elapsed <= next_time_to_msg:
        # continue

        G_LOGGER.debug('Time Δ: %.6f ms.' %((msg_elapsed - next_time_to_msg) * 1000.0))
        
        # Pick an emitter at random from the emitters list
        emitter_idx = random.choice(emitters_indices)
        
        node_address = 'http://%s/' %emitters[emitter_idx]

        emitter_topics = emitters_topics[emitter_idx]

        # Pick a topic at random from the topics supported by the emitter
        emitter_topic = random.choice(emitter_topics)

        G_LOGGER.info('Injecting message of topic %s to network through Waku node %s ...' %(emitter_topic, node_address))
        
        # Build the payload
        payload, payload_size = make_payload_dist(dist_type=config['general']['dist_type'].lower(), min_size=config['general']['min_packet_size'], max_size=config['general']['max_packet_size'])
        
        # Inject the message
        # response, elapsed_injection, waku_msg, ts = asyncio.create_task(send_waku_msg(node_address, topic=emitter_topic, payload=payload, nonce=len(msgs_dict)))

        task = asyncio.create_task(send_waku_msg(node_address, topic=emitter_topic, payload=payload, payload_size=payload_size, nonce=nonce))
        tasks.append(task)

        nonce += 1

        # Compute the time to next message
        next_time_to_msg = get_next_time_to_msg(config['general']['inter_msg_type'], config['general']['msg_rate'], config['general']['simulation_time']) 
        G_LOGGER.debug('Next message will happen in %d ms.' %(next_time_to_msg * 1000.0))
        
        last_msg_time = time.time()

        await asyncio.sleep(next_time_to_msg)

    elapsed_s = time.time() - s_time

    # Gather results from tasks
    results = await asyncio.gather(*tasks)
    return results
    
async def main(): 

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
        if not check_waku_node('http://%s/' %target):
            G_LOGGER.error('Node %d (%s) is not online. Aborted.' %(i, target))
            sys.exit(1)
    G_LOGGER.info('All %d Waku nodes are reachable.' %len(targets))

    """ Load Topics """
    topics = []
    try:
        tomls = glob.glob('./tomls/*.toml')
        tomls.sort()
        for toml_file in tomls:
            with open(toml_file, mode='rb') as read_file:
                toml_config = tomllib.load(read_file)
                node_topics_str = toml_config['topics']
                
                # Make sure we are tokenising the topics depending if Nim-Waku or Go-Waku
                # Ideally we should also pass the network_data.json so we can check directly the type of node
                if isinstance(node_topics_str, list):
                
                    # Parses Go Waku style topics list: ["topic_a", "topic_b"]
                    topics.append(node_topics_str)
                else:
                    # Parses Nim Waku style topics list: "topic_a" "topic_b"
                    topics.append(list(node_topics_str.split(' ')))

    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    # Dictionary to count messages of every topic being sent
    topics_msg_cnt = {}
    for node_topics in topics:
        for topic in node_topics:
            topics_msg_cnt[topic] = 0
    
    G_LOGGER.info('Loaded nodes topics from toml files: %s' %topics_msg_cnt.keys())

    """ Define the subset of emitters """
    num_emitters = int(len(targets) * config['general']['emitters_fraction'])
    if num_emitters == 0:
        G_LOGGER.error('The number of emitters must be greater than zero. Try increasing the fraction of emitters.')
        sys.exit()

    """ NOTE: Emitters will only inject topics they are subscribed to """
    emitters_indices = random.sample(range(len(targets)), num_emitters)
    emitters = [targets[i] for i in emitters_indices]
    emitters_topics = [topics[i] for i in emitters_indices]
    G_LOGGER.info('Selected %d emitters out of %d total nodes' %(len(emitters), len(targets)))

    """ Wait for signal to start """
    while not os.path.exists('/wsl/start.signal'):
        G_LOGGER.info('Waiting for signal to start ...')
        print(os.listdir('/wsl'))
        time.sleep(0.5)

    """ Start simulation """
    results = await simulate(config, emitters, emitters_indices, emitters_topics)

    """ Process results and build messages dictionary """
    msgs_dict = {}
    for result in results:
        
        response_status, injection_time, waku_msg, ts, node_address, topic, payload, payload_size, nonce = result
        
        msg_hash = hashlib.sha256(waku_msg.encode('utf-8')).hexdigest()
        if msg_hash in msgs_dict:
            G_LOGGER.error('Hash collision. %s already exists in dictionary' %msg_hash)
            continue
        
        msgs_dict[msg_hash] = {'statsus' : response_status, 'ts' : ts, 'injection_point' : node_address, 'injection_time' : injection_time, 'nonce' : nonce, 'topic' : topic, 'payload' : payload, 'payload_size' : payload_size}
    
    """ Save messages for further analysis """
    with open('./messages.json', 'w') as f:
        f.write(json.dumps(msgs_dict, indent=4))

    # Delete de signal file just in case
    if os.path.exists('/tmp/start.signal'):
        os.remove('/tmp/start.signal')

    """ We are done """
    G_LOGGER.info('Ended')
    
if __name__ == "__main__":
    asyncio.run(main())
