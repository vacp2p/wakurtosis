#! /usr/bin/env python3

import matplotlib.pyplot as plt
import yaml
import networkx as nx
import random, math
import json
import sys, os
import string
import typer
from enum import Enum


# Enums & Consts

# To add a new node type, add appropriate entries to the nodeType and nodeTypeSwitch
class nodeType(Enum):
    DESKTOP = "desktop"  # waku desktop config
    MOBILE = "mobile"  # waku mobile config


nodeTypeSwitch = {
    nodeType.DESKTOP: "rpc-admin = true\nkeep-alive = true\n",
    nodeType.MOBILE: "rpc-admin = true\nkeep-alive = true\n"
}


# To add a new network type, add appropriate entries to the networkType and networkTypeSwitch
# the networkTypeSwitch is placed before generate_network(): fwd declaration mismatch with typer/python :/
class networkType(Enum):
    CONFIGMODEL = "configmodel"
    SCALEFREE = "scalefree"  # power law
    NEWMANWATTSSTROGATZ = "newmanwattsstrogatz"  # mesh, smallworld
    BARBELL = "barbell"  # partition
    BALANCEDTREE = "balancedtree"  # committees?
    STAR = "star"  # spof


NW_DATA_FNAME = "network_data.json"
NODE_PREFIX = "waku"
SUBNET_PREFIX = "subnetwork"


### I/O related fns ##############################################################

# Dump to a json file
def write_json(dirname, json_dump):
    fname = os.path.join(dirname, NW_DATA_FNAME)
    with open(fname, "w") as f:
        json.dump(json_dump, f, indent=2)


def write_toml(dirname, node_name, toml):
    fname = os.path.join(dirname, f"{node_name}.toml")
    with open(fname, "w") as f:
        f.write(toml)


# Draw the network and output the image to a file; does not account for subnets yet
def draw(dirname, H):
    nx.draw(H, pos=nx.kamada_kawai_layout(H), with_labels=True)
    fname = os.path.join(dirname, NW_DATA_FNAME)
    plt.savefig(f"{os.path.splitext(fname)[0]}.png", format="png")
    plt.show()


# Has trouble with non-integer/non-hashable keys 
def read_json(fname):
    with open(fname) as f:
        jdata = json.load(f)
    return nx.node_link_graph(jdata)


# check if the required dir can be created
def exists_or_nonempty(dirname):
    if not os.path.exists(dirname):
        return False
    elif not os.path.isfile(dirname) and os.listdir(dirname):
        print(f"{dirname}: exists and not empty")
        return True
    elif os.path.isfile(dirname):
        print(f"{dirname}: exists but not a directory")
        return True
    else:
        return False


### topics related fns #############################################################

# Generate a random string of upper case chars
def generate_random_string(n):
    return "".join(random.choice(string.ascii_uppercase) for _ in range(n))


# Generate the topics - topic followed by random UC chars - Eg, topic_XY"
def generate_topics(num_topics):
    topic_len = int(math.log(num_topics) / math.log(26)) + 1  # base is 26 - upper case letters
    topics = {i: f"topic_{generate_random_string(topic_len)}" for i in range(num_topics)}
    return topics


# Get a random sub-list of topics
def get_random_sublist(topics):
    n = len(topics)
    lo = random.randint(0, n - 1)
    hi = random.randint(lo + 1, n)
    sublist = []
    for i in range(lo, hi):
        sublist.append(topics[i])
    return sublist


### network processing related fns #################################################

# Network Types
def generate_config_model(n):
    # degrees = nx.random_powerlaw_tree_sequence(n, tries=10000)
    degrees = [random.randint(1, n) for i in range(n)]
    if (sum(degrees)) % 2 != 0:  # adjust the degree to be even
        degrees[-1] += 1
    return nx.configuration_model(degrees)  # generate the graph


def generate_scalefree_graph(n):
    return nx.scale_free_graph(n)


# n must be larger than k=D=3
def generate_newmanwattsstrogatz_graph(n):
    return nx.newman_watts_strogatz_graph(n, 3, 0.5)


def generate_barbell_graph(n):
    return nx.barbell_graph(int(n / 2), 1)


def generate_balanced_tree(n, fanout=3):
    height = int(math.log(n) / math.log(fanout))
    return nx.balanced_tree(fanout, height)


def generate_star_graph(n):
    return nx.star_graph(n)


networkTypeSwitch = {
    networkType.CONFIGMODEL: generate_config_model,
    networkType.SCALEFREE: generate_scalefree_graph,
    networkType.NEWMANWATTSSTROGATZ: generate_newmanwattsstrogatz_graph,
    networkType.BARBELL: generate_barbell_graph,
    networkType.BALANCEDTREE: generate_balanced_tree,
    networkType.STAR: generate_star_graph
}


# Generate the network from nw type
def generate_network(n, network_type):
    return postprocess_network(networkTypeSwitch.get(network_type)(n))


# Label the generated network with prefix
def postprocess_network(G):
    G = nx.Graph(G)  # prune out parallel/multi edges
    G.remove_edges_from(nx.selfloop_edges(G))  # remove the self-loops
    mapping = {i: f"{NODE_PREFIX}_{i}" for i in range(len(G))}
    return nx.relabel_nodes(G, mapping)  # label the nodes


def generate_subnets(G, num_subnets):
    n = len(G.nodes)
    if num_subnets == n:  # if num_subnets == size of the network
        return {f"{NODE_PREFIX}_{i}": f"{SUBNET_PREFIX}_{i}" for i in range(n)}

    lst = list(range(n))
    random.shuffle(lst)
    offsets = sorted(random.sample(range(0, n), num_subnets - 1))
    offsets.append(n - 1)

    start = 0
    subnets = {}
    subnet_id = 0
    for end in offsets:
        for i in range(start, end + 1):
            subnets[f"{NODE_PREFIX}_{lst[i]}"] = f"{SUBNET_PREFIX}_{subnet_id}"
        start = end
        subnet_id += 1
    return subnets


### file format related fns ###########################################################
# Generate per node toml configs
def generate_toml(topics, node_type=nodeType.DESKTOP):
    topic_str = " ".join(get_random_sublist(topics))  # space separated topics
    return f"{nodeTypeSwitch.get(node_type)}topics = \"{topic_str}\"\n"


# Generates network-wide json and per-node toml and writes them 
def generate_and_write_files(dirname, num_topics, num_subnets, G):
    topics = generate_topics(num_topics)
    subnets = generate_subnets(G, num_subnets)
    json_dump = {}
    for node in G.nodes:
        write_toml(dirname, node, generate_toml(topics))  # per node toml
        json_dump[node] = {}
        json_dump[node]["static_nodes"] = []
        for edge in G.edges(node):
            json_dump[node]["static_nodes"].append(edge[1])
        json_dump[node][SUBNET_PREFIX] = subnets[node]
    write_json(dirname, json_dump)  # network wide json


def conf_callback(ctx: typer.Context, param: typer.CallbackParam, value: str):
    if value:
        typer.echo(f"Loading config file: {value}")
        try:
            with open(value, 'r') as f:  # Load config file
                conf = json.load(f)
                conf = conf["gennet"]
            ctx.default_map = ctx.default_map or {}  # Initialize the default map
            ctx.default_map.update(conf)  # Merge the config dict into default_map
        except Exception as ex:
            raise typer.BadParameter(str(ex))
    return value


# Sanity checks
def _num_partitions_callback(num_partitions: int):
    if num_partitions > 1:
        raise ValueError(
            f"--num-partitions {num_partitions}, Sorry, we do not yet support partitions")

    return num_partitions


def _num_subnets_callback(ctx: typer, Context, num_subnets: int):
    num_nodes = ctx.params["num_nodes"]
    if num_subnets > num_nodes:
        raise ValueError(
            f"num_subnets must be <= num_nodes: num_subnets={num_subnets}, num_nodes={1}")
    if num_subnets == -1:
        num_subnets = num_nodes

    return num_subnets


def main(output_dir: str = "topology_generated",
         num_nodes: int = 4,
         num_topics: int = 1,
         network_type: networkType = networkType.NEWMANWATTSSTROGATZ.value,
         node_type: nodeType = nodeType.DESKTOP.value,
         num_subnets: int = typer.Option(-1, callback=_num_subnets_callback),
         num_partitions: int = typer.Option(1, callback=_num_partitions_callback),
         config_file: str = typer.Option("", callback=conf_callback, is_eager=True)):

    # Generate the network
    G = generate_network(num_nodes, networkType(network_type))

    # Do not complain if folder exists already
    os.makedirs(output_dir, exist_ok=True)

    # Generate file format specific data structs and write the files
    generate_and_write_files(output_dir, num_topics, num_subnets, G)


if __name__ == "__main__":
    typer.run(main)
