# Python Imports
import argparse
import hashlib
import json
import random
import sys
import time
import tomllib

# Project Imports
from utils import logger
from utils import waku_messaging
from utils import payloads
from utils import files

""" Globals """
G_DEFAULT_CONFIG_FILE = './config/config.json'
G_DEFAULT_TOPOLOGY_FILE = './network_topology/network_data.json'
G_LOGGER, handler = logger.innit_logging()


def parse_cli():
    """ Parse command line args. """
    parser = argparse.ArgumentParser()
    parser.add_argument("-cfg", "--config_file", help="Config file", action="store_true",
                        default=G_DEFAULT_CONFIG_FILE)
    parser.add_argument("-t", "--topology_file", help="Topology file", action="store_true",
                        default=G_DEFAULT_TOPOLOGY_FILE)

    args = parser.parse_args()

    return args


def load_topics_into_topology(topology):
    """ Load Topics """
    nodes = topology["nodes"]
    for node, node_info in nodes.items():
        try:
            with open("tomls/" + node_info["node_config"], mode='rb') as read_file:
                toml_config = tomllib.load(read_file)
                if node_info["image"] == "nim-waku":
                    topics = list(toml_config["topics"].split(" "))
                elif node_info["image"] == "go-waku":
                    topics = toml_config["topics"]

                # Load topics into topology for easier access
                nodes[node]["topics"] = topics
        except Exception as e:
            G_LOGGER.error('%s: %s' % (e.__doc__, e))
            sys.exit()

    G_LOGGER.info('Loaded nodes topics from toml files')


def get_random_emitters(topology, wls_config):
    nodes = topology["nodes"]
    """ Define the subset of emitters """
    num_emitters = int(len(nodes) * wls_config["emitters_fraction"])

    if num_emitters == 0:
        G_LOGGER.error(
            'The number of emitters must be greater than zero. Try increasing the fraction of emitters.')
        sys.exit()

    random_emitters = dict(random.sample(list(nodes.items()), num_emitters))
    G_LOGGER.info('Selected %d emitters out of %d total nodes' % (len(random_emitters), len(nodes)))

    return random_emitters


def start_traffic_inyection(wls_config, random_emitters):
    """ Start simulation """
    s_time = time.time()
    last_msg_time = 0
    next_time_to_msg = 0
    msgs_dict = {}

    G_LOGGER.info('Starting a simulation of %d seconds ...' % wls_config['simulation_time'])

    while True:
        # Check end condition
        elapsed_s = time.time() - s_time

        if elapsed_s >= wls_config['simulation_time']:
            G_LOGGER.info(
                'Simulation ended. Sent %d messages in %ds.' % (len(msgs_dict), elapsed_s))
            break

        # Send message
        # BUG: There is a constant discrepancy. The average number of messages sent by time interval is slightly less than expected
        msg_elapsed = time.time() - last_msg_time
        if msg_elapsed <= next_time_to_msg:
            continue

        G_LOGGER.debug('Time Δ: %.6f ms.' % ((msg_elapsed - next_time_to_msg) * 1000.0))

        # Pick an emitter at random from the emitters list
        random_emitter, random_emitter_info = random.choice(list(random_emitters.items()))

        emitter_address = f"http://{random_emitter_info['ip_address']}:{random_emitter_info['ports']['rpc_' + random_emitter][0]}/"
        emitter_topics = random_emitter_info["topics"]

        # Pick a topic at random from the topics supported by the emitter
        emitter_topic = random.choice(emitter_topics)

        G_LOGGER.info('Injecting message of topic %s to network through Waku node %s ...' % (
        emitter_topic, emitter_address))

        payload, size = payloads.make_payload_dist(dist_type=wls_config['dist_type'].lower(),
                                          min_size=wls_config['min_packet_size'],
                                          max_size=wls_config['max_packet_size'])
        response, elapsed, waku_msg, ts = waku_messaging.send_msg_to_node(emitter_address, topic=emitter_topic,
                                                           payload=payload, nonce=len(msgs_dict))

        if response['result']:
            msg_hash = hashlib.sha256(waku_msg.encode('utf-8')).hexdigest()
            if msg_hash in msgs_dict:
                G_LOGGER.error('Hash collision. %s already exists in dictionary' % msg_hash)
                continue
            msgs_dict[msg_hash] = {'ts': ts, 'injection_point': emitter_address,
                                   'nonce': len(msgs_dict), 'topic': emitter_topic,
                                   'payload': payload, 'payload_size': size}

        # Compute the time to next message
        next_time_to_msg = waku_messaging.get_next_time_to_msg(wls_config['inter_msg_type'],
                                                wls_config['message_rate'],
                                                wls_config['simulation_time'])
        G_LOGGER.debug('Next message will happen in %d ms.' % (next_time_to_msg * 1000.0))

        last_msg_time = time.time()

    elapsed_s = time.time() - s_time

    return msgs_dict


def save_messages(msgs_dict):
    # Save messages for further analysis
    with open('./messages.json', 'w') as f:
        f.write(json.dumps(msgs_dict, indent=4))

    """ We are done """
    G_LOGGER.info('Ended')


def main():
    args = parse_cli()

    config_file = args.config_file
    topology_file = args.topology_file
        
    config = files.load_config_file(config_file)
    
    # Set loglevel from config
    wls_config = config['wls']

    logger.configure_logging(G_LOGGER, handler, wls_config, config_file)

    # Set RPNG seed from config
    random.seed(config['general']['prng_seed'])

    topology = files.load_topology(topology_file)

    load_topics_into_topology(topology)

    random_emitters = get_random_emitters(topology, wls_config)

    msgs_dict = start_traffic_inyection(wls_config, random_emitters)

    save_messages(msgs_dict)


if __name__ == "__main__":
    main()
