# Python Imports
import argparse
import hashlib
import random
import sys
import time
import tomllib
import asyncio
import os

# Project Imports
from src.utils import wls_logger
from src.utils import waku_messaging
from src.utils import payloads
from src.utils import files

""" Globals """
G_DEFAULT_CONFIG_FILE = 'config.json'
G_DEFAULT_TOPOLOGY_FILE = 'topology_generated/network_data.json'


def parse_cli(args):
    """ Parse command line args. """
    parser = argparse.ArgumentParser()
    parser.add_argument("-cfg", "--config_file", type=str, help="Config file",
                        default=G_DEFAULT_CONFIG_FILE)
    parser.add_argument("-t", "--topology_file", type=str, help="Topology file",
                        default=G_DEFAULT_TOPOLOGY_FILE)

    parsed_args = parser.parse_args(args)

    return parsed_args


def _load_topics(node_info, nodes, node):
    topics = None
    with open("tomls/" + node_info["node_config"], mode='rb') as read_file:
        toml_config = tomllib.load(read_file)
        if node_info["image"] == "nim-waku":
            topics = list(toml_config["topics"].split(" "))
        elif node_info["image"] == "go-waku":
            topics = toml_config["topics"]
        else:
            raise ValueError("Unknown image type")
    # Load topics into topology for easier access
    nodes[node]["topics"] = topics


def load_topics_into_topology(topology):
    """ Load Topics """
    nodes = topology["nodes"]
    for node, node_info in nodes.items():
        try:
            _load_topics(node_info, nodes, node)
        except ValueError as e:
            wls_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
            sys.exit()

    wls_logger.G_LOGGER.info('Loaded nodes topics from toml files')


def get_random_emitters(topology, wls_config):
    nodes = topology["nodes"]
    """ Define the subset of emitters """
    num_emitters = int(len(nodes) * wls_config["emitters_fraction"])

    if num_emitters == 0 or num_emitters > len(nodes):
        wls_logger.G_LOGGER.error(
            'The number of emitters must be greater than zero and less or equals than one.')
        sys.exit()

    random_emitters = dict(random.sample(list(nodes.items()), num_emitters))
    wls_logger.G_LOGGER.info('Selected %d emitters out of %d total nodes' % (len(random_emitters), len(nodes)))

    return random_emitters


def _is_simulation_finished(start_time, wls_config, msgs_dict):
    # Check end condition
    elapsed_s = time.time() - start_time

    if elapsed_s >= wls_config['simulation_time']:
        wls_logger.G_LOGGER.info(f"Simulation ended. Sent {len(msgs_dict)} messages in {elapsed_s}.")
        return True

    return False


def _select_emitter_with_topic(random_emitters):
    # Pick an emitter at random from the emitters list
    random_emitter, random_emitter_info = random.choice(list(random_emitters.items()))
    emitter_address = f"http://{random_emitter_info['ip_address']}:" \
                      f"{random_emitter_info['ports']['rpc-' + random_emitter][0]}/"
    emitter_topics = random_emitter_info["topics"]
    # Pick a topic at random from the topics supported by the emitter
    emitter_topic = random.choice(emitter_topics)

    wls_logger.G_LOGGER.info(f"Injecting message of topic {emitter_topic} to network "
                  f"through Waku node {emitter_address} ...")

    return emitter_address, emitter_topic


async def _inject_message_async(emitter_address, emitter_topic, msgs_dict, msgs_dict_lock, wls_config):
    payload, size = payloads.make_payload_dist(dist_type=wls_config['dist_type'].lower(),
                                               min_size=wls_config['min_packet_size'],
                                               max_size=wls_config['max_packet_size'])

    response, elapsed, waku_msg, ts = await waku_messaging.send_msg_to_node_async(emitter_address,
                                                                      topic=emitter_topic,
                                                                      payload=payload,
                                                                      nonce=len(msgs_dict))

    msg_hash = hashlib.sha256(waku_msg.encode('utf-8')).hexdigest()
    async with msgs_dict_lock:
        
        if msg_hash in msgs_dict:
            wls_logger.G_LOGGER.error(f"Hash collision. {msg_hash} already exists in dictionary")
            return
        
        # Update the messages dictionary
        msgs_dict[msg_hash] = {'ts': ts, 'injection_point': emitter_address, 'status' : response,
                               'nonce': len(msgs_dict), 'topic': emitter_topic,
                               'payload': payload, 'payload_size': size, 'injection_time': elapsed}


async def start_traffic_injection_async(wls_config, random_emitters):
    """ Start simulation """
    start_time = time.time()
    next_time_to_msg = 0
    msgs_dict = {}
    msgs_dict_lock = asyncio.Lock()
    tasks = []
    nonce = 0

    wls_logger.G_LOGGER.info(f"Starting a simulation of {wls_config['simulation_time']} seconds...")

    while True:
        if _is_simulation_finished(start_time, wls_config, msgs_dict):
            break

        emitter_address, emitter_topic = _select_emitter_with_topic(random_emitters)

        task = asyncio.create_task(_inject_message_async(emitter_address, emitter_topic, msgs_dict, msgs_dict_lock, wls_config))
        tasks.append(task)

        nonce += 1

        # Compute the time to next message
        next_time_to_msg = waku_messaging.get_next_time_to_msg(wls_config['inter_msg_type'],
                                                            wls_config['message_rate'],
                                                            wls_config['simulation_time'])

        # Wait for the specified time before sending the next message
        wls_logger.G_LOGGER.info('Next message will be injected in %d ms.' % (next_time_to_msg * 1000.0))
        await asyncio.sleep(next_time_to_msg)

    # Wait for all the tasks to complete
    await asyncio.gather(*tasks)
    
    return msgs_dict


async def main():
    args = parse_cli(sys.argv[1:])

    config_file = args.config_file
    topology_file = args.topology_file
        
    config = files.load_config_file(config_file)
    
    # Set loglevel from config
    wls_config = config['wls']

    wls_logger.configure_logging(wls_logger.G_LOGGER, wls_logger.handler, wls_config, config_file)

    # Set RPNG seed from config
    random.seed(config['general']['prng_seed'])

    topology = files.load_topology(topology_file)

    load_topics_into_topology(topology)

    random_emitters = get_random_emitters(topology, wls_config)

    # Wait for signal to start
    # while not os.path.exists('/wls/start.signal'):
    #     wls_logger.G_LOGGER.info('Waiting for signal to start ...')
    #     asyncio.sleep(1)

    # Start the siulation
    msgs_dict = await start_traffic_injection_async(wls_config, random_emitters)

    files.save_messages_to_json(msgs_dict)

    # Delete de signal file just in case
    if os.path.exists('/wls/start.signal'):
        os.remove('/wls/start.signal')


if __name__ == "__main__":
    asyncio.run(main())
