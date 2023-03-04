# Python Imports
import argparse
import hashlib
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
            'The number of emitters must be greater than zero. '
            'Try increasing the fraction of emitters.')
        sys.exit()

    random_emitters = dict(random.sample(list(nodes.items()), num_emitters))
    G_LOGGER.info('Selected %d emitters out of %d total nodes' % (len(random_emitters), len(nodes)))

    return random_emitters


def _is_simulation_finished(start_time, wls_config, msgs_dict):
    # Check end condition
    elapsed_s = time.time() - start_time

    if elapsed_s >= wls_config['simulation_time']:
        G_LOGGER.info(f"Simulation ended. Sent {len(msgs_dict)} messages in {elapsed_s}.")
        return True

    return False


def _time_to_send_next_message(last_msg_time, next_time_to_msg):
    # Send message
    # BUG: There is a constant discrepancy.
    # The average number of messages sent by time interval is slightly less than expected
    msg_elapsed = time.time() - last_msg_time

    if msg_elapsed <= next_time_to_msg:
        return False

    G_LOGGER.debug(f"Time Δ: {(msg_elapsed - next_time_to_msg) * 1000.0:6f}ms.")

    return True


def _select_emitter_and_topic(random_emitters):
    # Pick an emitter at random from the emitters list
    random_emitter, random_emitter_info = random.choice(list(random_emitters.items()))
    emitter_address = f"http://{random_emitter_info['ip_address']}:" \
                      f"{random_emitter_info['ports']['rpc_' + random_emitter][0]}/"
    emitter_topics = random_emitter_info["topics"]
    # Pick a topic at random from the topics supported by the emitter
    emitter_topic = random.choice(emitter_topics)

    G_LOGGER.info(f"Injecting message of topic {emitter_topic} to network "
                  f"through Waku node {emitter_address} ...")

    return emitter_address, emitter_topic


def _inyect_message(emitter_address, emitter_topic, msgs_dict, wls_config):
    payload, size = payloads.make_payload_dist(dist_type=wls_config['dist_type'].lower(),
                                               min_size=wls_config['min_packet_size'],
                                               max_size=wls_config['max_packet_size'])

    response, elapsed, waku_msg, ts = waku_messaging.send_msg_to_node(emitter_address,
                                                                      topic=emitter_topic,
                                                                      payload=payload,
                                                                      nonce=len(msgs_dict))

    if response['result']:
        msg_hash = hashlib.sha256(waku_msg.encode('utf-8')).hexdigest()
        if msg_hash in msgs_dict:
            G_LOGGER.error(f"Hash collision. {msg_hash} already exists in dictionary")
            raise RuntimeWarning

        msgs_dict[msg_hash] = {'ts': ts, 'injection_point': emitter_address,
                               'nonce': len(msgs_dict), 'topic': emitter_topic,
                               'payload': payload, 'payload_size': size}


def start_traffic_inyection(wls_config, random_emitters):
    """ Start simulation """
    start_time = time.time()
    last_msg_time = 0
    next_time_to_msg = 0
    msgs_dict = {}

    G_LOGGER.info(f"Starting a simulation of {wls_config['simulation_time']} seconds...")

    while True:
        if _is_simulation_finished(start_time, wls_config, msgs_dict):
            break

        if not _time_to_send_next_message(last_msg_time, next_time_to_msg):
            continue

        emitter_address, emitter_topic = _select_emitter_and_topic(random_emitters)

        try:
            _inyect_message(emitter_address, emitter_topic, msgs_dict, wls_config)
        except RuntimeWarning:
            continue

        # Compute the time to next message
        next_time_to_msg = waku_messaging.get_next_time_to_msg(wls_config['inter_msg_type'],
                                                               wls_config['message_rate'],
                                                               wls_config['simulation_time'])
        G_LOGGER.debug('Next message will happen in %d ms.' % (next_time_to_msg * 1000.0))

        last_msg_time = time.time()

    return msgs_dict


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

    files.save_messages_to_json(msgs_dict)


if __name__ == "__main__":
    main()
