# Python Imports
import json
import sys

# Project Imports
import logger

G_LOGGER, handler = logger.innit_logging()


def load_config_file(config_file):
    """ Load config file """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    return config


def load_topology(topology_file):
    """ Load topology """
    try:
        with open(topology_file, 'r') as read_file:
            topology = json.load(read_file)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    if len(topology) == 0:
        G_LOGGER.error('Cannot find valid topology. Aborting.')
        sys.exit(1)

    G_LOGGER.debug(topology)
    G_LOGGER.info('%d topology loaded' % len(topology))

    return topology


def save_messages_to_json(msgs_dict):
    # Save messages for further analysis
    with open('./messages.json', 'w') as f:
        f.write(json.dumps(msgs_dict, indent=4))

    """ We are done """
    G_LOGGER.info('Ended')
