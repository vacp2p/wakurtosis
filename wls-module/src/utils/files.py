# Python Imports
import json

# Project Imports
from src.utils import wls_logger


def load_config_file(config_file):
    """ Load config file """
    with open(config_file, 'r') as f:
        config = json.load(f)

    return config


def load_topology(topology_file):
    """ Load topology """
    with open(topology_file, 'r') as read_file:
        topology = json.load(read_file)

    wls_logger.G_LOGGER.debug(topology)
    wls_logger.G_LOGGER.info('Topology loaded')

    return topology


def save_messages_to_json(msgs_dict):
    # Save messages for further analysis
    with open('./messages.json', 'w') as f:
        f.write(json.dumps(msgs_dict, indent=4))

    """ We are done """
    wls_logger.G_LOGGER.info('Ended')
