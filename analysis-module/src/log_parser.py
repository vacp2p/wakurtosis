# Python Imports
import sys
import json

# Project Imports
from src import analysis_logger


def load_messages(simulation_path):
    try:
        with open(f'{simulation_path}/messages.json', 'r') as f:
            injected_msgs_dict = json.load(f)
    except OSError as e:
        analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    analysis_logger.G_LOGGER.info(f'Loaded {len(injected_msgs_dict)} messages.')

    return injected_msgs_dict


def prepare_node_in_logs(node_pbar, topology, node_logs, container_name):
    for node in node_pbar:
        node_info = topology["nodes"][node]
        peer_id = node_info["peer_id"][:3] + "*" + node_info["peer_id"][-6:]
        node_logs[peer_id] = {'published': [], 'received': [],
                              'container_name': container_name, 'peer_id': node}


def open_file(folder):
    try:
        file = open(f'{folder[0]}/output.log', mode='r')
    except OSError as e:
        analysis_logger.G_LOGGER.error(f'{e.__doc__}: {e}')
        sys.exit()

    return file


