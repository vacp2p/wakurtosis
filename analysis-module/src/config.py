# Python Imports
import sys
import json

# Project Imports
from src import analysis_logger
from src import vars

def load_config(simulation_path):

    config_path = f'{simulation_path}/config/config.json' 

    try:
        with open(config_path, "r") as read_file:
            config = json.load(read_file)
    except Exception as e:
        analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    return config