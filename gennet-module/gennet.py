#! /usr/bin/env python3

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

import random, math
import sys, os
import json, ast

import time, tracemalloc
import string
import typer

from enum import Enum


# Enums & Consts

# To add a new node type, add appropriate entries to the nodeType and nodeTypeSwitch
class nodeType(Enum):
    NWAKU = "nwaku"     # waku desktop config
    GOWAKU = "gowaku"   # waku mobile config


nodeTypeToToml = {
    nodeType.NWAKU: "rpc-admin = true\nkeep-alive = true\nmetrics-server = true\n",
    nodeType.GOWAKU: "rpc-admin = true\nmetrics-server = true\nrpc = true\n"
}

nodeTypeToDocker = {
    nodeType.NWAKU: "nim-waku",
    nodeType.GOWAKU: "go-waku"
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
NODE_PREFIX, SUBNET_PREFIX, CONTAINER_PREFIX = "node", "subnetwork", "container"

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

    start, subnet_id, node2subnet = 0, 0, {}
    for end in offsets:
        l = []
        for i in range(start, end + 1):
            node2subnet[f"{NODE_PREFIX}_{lst[i]}"] = f"{SUBNET_PREFIX}_{subnet_id}"
            #node2subnet[lst[i]] = subnet_id
        start = end
        subnet_id += 1
    return node2subnet


### file format related fns ###########################################################
# Generate per node toml configs
def generate_toml(topics, node_type=nodeType.NWAKU):
    topics = get_random_sublist(topics)
    if node_type == nodeType.GOWAKU:    # comma separated list of quoted topics
        topic_str = ", ".join(f"\"{t}\"" for t in topics)
        topic_str = f"[{topic_str}]"
    else:                               # space separated topics
        topic_str = " ".join(topics)  
        topic_str = f"\"{topic_str}\""
    return f"{nodeTypeToToml.get(node_type)}topics = {topic_str}\n"


# Convert a dict to pair of arrays
def dict_to_arrays(dic):
    keys, vals = list(dic.keys()), []
    for k in keys :
        vals.append(dic[k])
    return keys, vals


# Generate a list of nodeType enums that respects the node type distribution
def generate_node_types(node_type_distribution, G):
    num_nodes = G.number_of_nodes()
    nodes, node_probs = dict_to_arrays(node_type_distribution)
    node_types_str = random.choices(nodes, weights=node_probs, k=num_nodes)
    node_types_enum = [nodeType(s) for s in node_types_str]
    return node_types_enum

# Inverts a dictionary of lists
def invert_dict_of_list(d):
    inv = {} 
    for key, val in d.items(): 
        if val not in inv: 
            inv[val] = [key] 
        else: 
            inv[val].append(key) 
    return inv


# Packs the nodes into container in a subnet aware manner : optimal
# Number of containers = 
#   $$ O(\sum_{i=0}^{num_subnets} log_{container_size}(#Nodes_{numsubnets}) + num_subnets)
def pack_nodes(container_size, node2subnet, G):
    subnet2node = invert_dict_of_list(node2subnet)
    port_shift, cid, node2container = 0, 0, {}
    for subnet in subnet2node:
        for node in subnet2node[subnet]:
            if port_shift >= container_size :
                port_shift, cid = 0, cid+1
            node2container[node] = (port_shift, f"{CONTAINER_PREFIX}_{cid}")
            port_shift += 1
    return node2container


# Generates network-wide json and per-node toml and writes them
def generate_and_write_files(ctx: typer, G):
    topics = generate_topics(ctx.params["num_topics"])
    node2subnet = generate_subnets(G, ctx.params["num_subnets"])
    node_types_enum = generate_node_types(ctx.params["node_type_distribution"], G)
    node2container = pack_nodes(ctx.params["container_size"], node2subnet, G)

    json_dump = {}
    json_dump[CONTAINER_PREFIX] = {}
    inv = {} 
    for key, val in node2container.items(): 
        if val[1] not in inv: 
            inv[val[1]] = [key]
        else: 
            inv[val[1]].append(key)
    for container, nodes in inv.items():
        json_dump[CONTAINER_PREFIX][container] = nodes

    i = 0
    for node in G.nodes:
        # package container_size nodes per container

        # write the per node toml for the i^ith node of appropriate type
        node_type, i = node_types_enum[i], i+1
        write_toml(ctx.params["output_dir"], node, generate_toml(topics, node_type))
        json_dump[node] = {}
        json_dump[node]["static_nodes"] = []
        for edge in G.edges(node):
            json_dump[node]["static_nodes"].append(edge[1])
        json_dump[node][SUBNET_PREFIX] = node2subnet[node]
        json_dump[node]["image"] = nodeTypeToDocker.get(node_type)
            # the per node tomls will continue for now as they include topics
        json_dump[node]["node_config"] = f"{node}.toml" 
            # logs ought to continue as they need to be unique
        json_dump[node]["node_log"] = f"{node}.log"
        port_shift, cid = node2container[node]
        json_dump[node]["port_shift"] = port_shift
        json_dump[node]["container_id"] = cid
    write_json(ctx.params["output_dir"], json_dump)  # network wide json


# sanity check : valid json with "gennet" config
def conf_callback(ctx: typer.Context, param: typer.CallbackParam, cfile: str):
    if cfile:
        typer.echo(f"Loading config file: {cfile.split('/')[-1]}")
        ctx.default_map = ctx.default_map or {}  # Init the default map
        try:
            with open(cfile, 'r') as f:  # Load config file
                conf = json.load(f)
                if "gennet" not in conf:
                    print(f"Gennet configuration not found in {cfile}. Skipping topology generation.")
                    sys.exit(1)
                if "general" in conf and "prng_seed" in conf["general"]:
                    conf["gennet"]["prng_seed"] = conf["general"]["prng_seed"]
                # TODO : type-check and sanity-check the config.json
                #print(conf)
            ctx.default_map.update(conf["gennet"])  # Merge config and default_map
        except Exception as ex:
            raise typer.BadParameter(str(ex))
    return cfile


# sanity check : num_partitions == 1
def _num_partitions_callback(num_partitions: int):
    if num_partitions > 1:
        raise ValueError(
            f"--num-partitions {num_partitions}, Sorry, we do not yet support partitions")
    return num_partitions


# sanity check :  num_subnets < num_nodes
def _num_subnets_callback(ctx: typer, Context, num_subnets: int):
    num_nodes = ctx.params["num_nodes"]
    if num_subnets == -1:
        num_subnets = num_nodes
    if num_subnets > num_nodes:
        raise ValueError(
            f"num_subnets must be <= num_nodes: num_subnets={num_subnets}, num_nodes={1}")
    return num_subnets


def main(ctx: typer.Context,
         benchmark: bool = False,
         container_size: int = 1,   # TODO: reduce container packer memory consumption
         output_dir: str = "network_data",
         prng_seed: int = 3,
         num_nodes: int = 4,
         num_topics: int = 1,
         node_type_distribution: str = typer.Argument("{\"nwaku\" : 100 }" ,callback=ast.literal_eval),
         network_type: networkType = networkType.NEWMANWATTSSTROGATZ.value,
         num_subnets: int = typer.Option(1, callback=_num_subnets_callback),
         num_partitions: int = typer.Option(1, callback=_num_partitions_callback),
         config_file: str = typer.Option("", callback=conf_callback, is_eager=True)):

    # Benchmarking: record start time and start tracing mallocs
    if benchmark :
        tracemalloc.start()
    start = time.time()

    # re-read the conf file to set node_type_distribution -- no cli equivalent
    conf = {}
    if config_file != "" :
        with open(config_file, 'r') as f:  # Load config file
            conf = json.load(f)
        #print(conf)

    # set the random seed : networkx uses numpy.random as well
    print("Setting the random seed to", prng_seed)
    random.seed(prng_seed)
    np.random.seed(prng_seed)
   
    # leaving it for now should any json parsing issues pops up
    # Extract the node type distribution from config.json or use the default
    # no cli equivalent for node type distribution (NTD)
    # if "gennet" in conf  and "node_type_distribution" in conf ["gennet"]:
    #     node_type_distribution = conf["gennet"]["node_type_distribution"]
    # else:
    #    node_type_distribution = { "nwaku" : 100 }  # default NTD is all nwaku


    # Generate the network
    G = generate_network(num_nodes, networkType(network_type))

    # Do not complain if folder exists already
    os.makedirs(output_dir, exist_ok=True)

    # Generate file format specific data structs and write the files
    generate_and_write_files(ctx, G)
    #generate_and_write_files(output_dir, num_topics, num_subnets, node_type_distribution, G)
    #draw(G, outpur_dir)
    end = time.time()
    time_took = end - start
    print(f"For {num_nodes} nodes, network generation took {time_took} secs.\nThe generated network is under ./{output_dir}")

    # Benchmarking. Record finish time and stop the malloc tracing
    if benchmark :
        mem_curr, mem_max = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"STATS: For {num_nodes} nodes, time took is {time_took} secs, peak memory usage is {mem_max/(1024*1024)} MBs\n")


if __name__ == "__main__":
    typer.run(main)
