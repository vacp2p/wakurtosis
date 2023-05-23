# Python Imports
import sys
import json

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

# Project Imports
from src import analysis_logger
from src import vars


def _load_topics(node_info, nodes, node, tomls_folder):
    topics = None
    with open(tomls_folder + node_info["node_config"], mode='rb') as read_file:
        toml_config = tomllib.load(read_file)
        if node_info["image"] == vars.G_NWAKU_IMAGE_NAME:
            topics = list(toml_config["topics"].split(" "))
        elif node_info["image"] == vars.G_GOWAKU_IMAGE_NAME:
            topics = toml_config["topics"]
        else:
            raise ValueError("Unknown image type")
    # Load topics into topology for easier access
    nodes[node]["topics"] = topics


def load_topics_into_topology(topology, tomls_folder):
    nodes = topology["nodes"]
    for node, node_info in nodes.items():
        try:
            _load_topics(node_info, nodes, node, tomls_folder)
        except ValueError as e:
            analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
            sys.exit()

    analysis_logger.G_LOGGER.info('Loaded nodes topics from toml files')


def load_json(json_file):
    with open(json_file, 'r') as read_file:
        jfile = json.load(read_file)

    analysis_logger.G_LOGGER.debug(jfile)
    analysis_logger.G_LOGGER.info(f'{json_file} loaded')

    return jfile
