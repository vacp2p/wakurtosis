#! /usr/bin/env python3

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

import random, math
import sys, os, shutil
import json, ast
from collections import defaultdict

from pathlib import Path

import time, tracemalloc
import string
import typer

from enum import Enum, EnumMeta

# Enums & Consts

class MetaEnum(EnumMeta):
    def __contains__(cls, item):
        try:
            cls(item)
        except ValueError:
            return False
        return True

class BaseEnum(Enum, metaclass=MetaEnum):
    pass

class Trait(BaseEnum):
    NWAKU   =	"nwaku"
    GOWAKU  =	"gowaku"
    DISCV5  =	"discv5"
    DNSDISC =	"dnsdisc"
    DNS     =    "dns"
    FLTER   =	"flter"
    LIGHTPUSH = "lightpush"
    METRICS =	"metrics"
    NODE    =	"node"
    PEER    =	"peer"
    PEERXCHNG = "peerxchng"
    RELAY   =	"relay"
    REST    =	"rest"
    RLN     =	"rln"
    RPC     =	"rpc"
    STORE   =	"store"
    SWAP    =	"swap"
    WEBSOCKET = "websocket"

# To add a new node type, add appropriate entries to the nodeType and nodeTypeToDocker
class nodeType(BaseEnum):
    NWAKU = "nwaku"     # waku desktop config
    GOWAKU = "gowaku"   # waku mobile config

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
    NOMOSTREE = "nomostree"  # balanced binary tree with even # of leaves
    STAR = "star"  # spof
    REGULAR = "regular"  # gossip-sub / waku


NW_DATA_FNAME = "network_data.json"
NODES_JSON, NODE_PREFIX, SUBNET_PREFIX, CONTAINERS_JSON, CONTAINER_PREFIX = \
    "nodes", "node", "subnetwork", "containers", "containers"
ID_STR_SEPARATOR = "-"

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
def draw_network(dirname, H):
    fname = os.path.join(dirname, NW_DATA_FNAME)
    fig, axes = plt.subplots(1, 2, layout='constrained', sharey=False)
    fig.set_figwidth(12)
    fig.set_figheight(10)
    axes[0].set_title("The Generated Network")
    nx.draw(H, ax=axes[0], pos=nx.kamada_kawai_layout(H), with_labels=True)
    degree_sequence = sorted((d for n, d in H.degree()), reverse=True)
    axes[1].bar(*np.unique(degree_sequence, return_counts=True), align='center',
            width=0.9975, edgecolor='k', facecolor='green', alpha=0.5)
    axes[1].set_xticks(range(max(degree_sequence)+1))
    axes[1].set_title("Normalised Degree Histogram")
    axes[1].set_xlabel("Degree")
    axes[1].set_ylabel("% of Nodes")
    plt.savefig(f'{os.path.splitext(fname)[0]}.pdf', format="pdf", bbox_inches="tight")
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

# remove mkdir
def make_empty_dir(dirname):
    if os.path.isdir(dirname):
        shutil.rmtree(dirname)
    os.makedirs(dirname, exist_ok=True)

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

# |G| = n
def generate_config_model(ctx):
    n = ctx.params["num_nodes"]
    # degrees = nx.random_powerlaw_tree_sequence(n, tries=10000)
    degrees = [random.randint(1, n) for i in range(n)]
    if (sum(degrees)) % 2 != 0:  # adjust the degree to be even
        degrees[-1] += 1
    return nx.configuration_model(degrees)  # generate the graph


# |G| = n
def generate_scalefree_graph(ctx):
    n = ctx.params["num_nodes"]
    return nx.scale_free_graph(n)


# |G| = n; n must be larger than k=D=3
def generate_newmanwattsstrogatz_graph(ctx):
    n = ctx.params["num_nodes"]
    fanout = ctx.params["fanout"]
    return nx.newman_watts_strogatz_graph(n, fanout, 0.5)


# |G| = n (if odd); n+1 (if even)
def generate_barbell_graph(ctx):
    n = ctx.params["num_nodes"]
    return nx.barbell_graph(int(n / 2), 1)


# |G| > fanout^{\floor{log_n} + 1}
def generate_balanced_tree(ctx):
    n = ctx.params["num_nodes"]
    fanout = ctx.params["fanout"]
    height = int(math.log(n) / math.log(fanout))
    return nx.balanced_tree(fanout, height)


# nomostree is a balanced binary tree with even number of leaves
# |G| = n (if odd); n+1 (if even)
def generate_nomos_tree(ctx):
    n = ctx.params["num_nodes"]
    fanout = ctx.params["fanout"]
    # nomos currently insists on binary trees
    assert(fanout == 2)
    height = int(math.log(n) / math.log(fanout))
    G = nx.balanced_tree(fanout, height)
    i, diff = 0, G.number_of_nodes() - n
    leaves = [x for x in G.nodes() if G.degree(x) == 1]
    nleaves = len(leaves)
    if (nleaves - diff) % 2 != 0:
        diff -= 1
    for node in leaves:
        if i == diff:
            break
        G.remove_node(node)
        i += 1
    G = nx.convert_node_labels_to_integers(G)
    return G


# |G| = n
def generate_star_graph(ctx):
    n = ctx.params["num_nodes"]
    return nx.star_graph(n-1)

# |G| = n, n*d must be even
def generate_regular_graph(ctx):
    d = ctx.params["fanout"]
    n = ctx.params["num_nodes"]
    return nx.random_regular_graph(d, n)

networkTypeSwitch = {
    networkType.CONFIGMODEL: generate_config_model,
    networkType.SCALEFREE: generate_scalefree_graph,
    networkType.NEWMANWATTSSTROGATZ: generate_newmanwattsstrogatz_graph,
    networkType.BARBELL: generate_barbell_graph,
    networkType.BALANCEDTREE: generate_balanced_tree,
    networkType.NOMOSTREE: generate_nomos_tree,
    networkType.STAR: generate_star_graph,
    networkType.REGULAR: generate_regular_graph
}


# Generate the network from nw type
def generate_network(ctx):
    network_type = networkType(ctx.params["network_type"])
    return postprocess_network(networkTypeSwitch.get(network_type)(ctx))


# Label the generated network with prefix
def postprocess_network(G):
    G = nx.Graph(G)  # prune out parallel/multi edges
    G.remove_edges_from(nx.selfloop_edges(G))  # remove the self-loops
    mapping = {i : f"{NODE_PREFIX}{ID_STR_SEPARATOR}{i}" for i in range(len(G))}
    return nx.relabel_nodes(G, mapping)  # label the nodes


def generate_subnets(G, num_subnets):
    n = len(G.nodes)
    if num_subnets == n:  # if num_subnets == size of the network
        return {f"{NODE_PREFIX}{ID_STR_SEPARATOR}{i}" : f"{SUBNET_PREFIX}_{i}" for i in range(n)}

    # Permute the node indices; this makes sure that the nodes are assigned randomly to subnets
    lst = list(range(n))
    random.shuffle(lst)

    # Select (without replacement) a num_subnets - 1 of offsets; make sure final offset is n-1.
    # Each offset demarcates a subnet boundary
    offsets = sorted(random.sample(range(0, n), num_subnets - 1))
    offsets.append(n - 1)   # we have num_subnets offsets

    start, subnet_id, node2subnet = 0, 0, {}
    for end in offsets:
        # Build a node2subnet map as follows
        # From the permuted lst, pick nodes whose indices are in the closed interval [start, end].
        # Remember, these are *sorted* offsets in the range of 0..n and without replacement; so 
        # they will all index correctly.
        # Finally, assign all these node to the current subnet.
        for i in range(start, end + 1):
            node2subnet[f"{NODE_PREFIX}{ID_STR_SEPARATOR}{lst[i]}"] = f"{SUBNET_PREFIX}_{subnet_id}"
            #node2subnet[lst[i]] = subnet_id
        start = end     # roll over the start to the end of the last offset
        subnet_id += 1  # increment the subnet_id 
    return node2subnet


### file format related fns ###########################################################
# Generate per node toml configs
def generate_toml(traits_dir, topics, traits_list):
    topics, node_type, tomls = get_random_sublist(topics), traits_list[0], ""
    if node_type == nodeType.GOWAKU:    # comma separated list of quoted topics
        topic_str = ", ".join(f"\"{t}\"" for t in topics)
        topic_str = f"[{topic_str}]"
    else:                               # space separated topics
        topic_str = " ".join(topics)
        topic_str = f"\"{topic_str}\""

    for trait in traits_list[1:]:       # skip the first trait as it is docker/node selector.
        toml = f'#{trait}\n'
        tomlf = f"{traits_dir}/{trait}.toml"
        if not os.path.isfile(tomlf):
             raise ValueError(f"traits: missing trait file {tomlf}")
        with open(tomlf, 'rb') as f:
            strlines = [l.decode("utf-8").strip() for l in f if not len(l.split()) == 0]
            toml += ''.join([f'{l}\n' for l in strlines if not l.startswith('#')])
        tomls += toml + '\n'
    return f"{tomls}#topics\ntopics = {topic_str}\n"


# Convert a dict to pair of arrays
def dict_to_arrays(dic):
    keys, vals = zip(*dic.items())
    return keys, vals


# Check for range failures in a list
def range_fails(lst, min=0, max=100):
    return any(x < min or x > max for x in lst)


# Check for sum failures in a list
def sum_fails(lst, sum_expected=100):
    return not sum(lst) == sum_expected


# Construct the nodeType from the trait
def traits_to_nodeType(s):
    return nodeType(s.split(':')[0])


# Validate the traits distribution (stick to percentages: num nodes may vary post generation)
def validate_traits_distribution(traits_dir, traits_distribution):
    traits, traits_freq = dict_to_arrays(traits_distribution)
    if range_fails(traits_freq, max=100):
        raise ValueError(f"{traits_distribution} : invalid percentage (>{100} or <0)")
    if sum_fails(traits_freq, sum_expected=100):
        raise ValueError(f"{traits_distribution} : percentages do not sum to {100}")
    if not os.path.exists(traits_dir):
        raise ValueError(f"{traits_dir} : trait directory does not exist!")
    for s in traits:
        traits_list = s.split(":")
        if traits_list[0] not in nodeType:
            raise ValueError(f"{traits_distribution} : unknown node type {traits_list[0]} in {s}")
        for t in traits_list[1:]:
            if t not in Trait and not os.path.exists(f"{traits_dir}/{t}.toml"):
                raise ValueError(f"{traits_distribution} : unknown trait {t} in {s}")


# Generate a list of nodeType enums that respects the node type distribution
def generate_traits_distribution(node_type_distribution, G):
    num_nodes = G.number_of_nodes()
    nodes, node_percentage = dict_to_arrays(node_type_distribution)
    traits_distribution = []
    for i, n in enumerate(nodes):
       traits_distribution +=  [nodes[i]] * math.ceil(node_percentage[i] * num_nodes/100)
    random.shuffle(traits_distribution)
    return traits_distribution


# Inverts a dictionary of lists (of lists/tuples) 
def invert_dict_of_list(d, idx=0):
    inv = defaultdict(list)
    for key, val in d.items():
        inv[val[idx]].append(key)
    return inv


# TODO: reduce container packer memory consumption
# Packs the nodes into container in a subnet aware manner : optimal
# Number of containers = 
#   $$ O(\sum_{i=0}^{num_subnets} log_{container_size}(#Nodes_{numsubnets}) + num_subnets)
def pack_nodes(container_size, node2subnet):
    subnet2nodes = invert_dict_of_list(node2subnet)
    port_shift, cid, node2container = 0, 0, {}
    for subnet in subnet2nodes:
        for node in subnet2nodes[subnet]:
            if port_shift >= container_size:
                port_shift, cid = 0, cid+1
            node2container[node] = (port_shift, f"{CONTAINER_PREFIX}_{cid}")
            port_shift += 1
    return node2container


# Generates network-wide json and per-node toml and writes them
def generate_and_write_files(ctx: typer, G):
    topics = generate_topics(ctx.params["num_topics"])
    node2subnet = generate_subnets(G, ctx.params["num_subnets"])
    traits_distribution = generate_traits_distribution(ctx.params["node_type_distribution"], G)
    node2container = pack_nodes(ctx.params["container_size"], node2subnet)
    container2nodes = invert_dict_of_list(node2container, 1)

    json_dump, json_dump[CONTAINERS_JSON], json_dump[NODES_JSON] = {}, {}, {}
    for container, nodes in container2nodes.items():
        json_dump[CONTAINERS_JSON][container] = nodes

    i, traits_dir = 0,  ctx.params["traits_dir"]
    for node in G.nodes:
        # write the per node toml for the i^ith node of appropriate type
        traits_list, i = traits_distribution[i].split(":"),  i+1
        node_type = nodeType(traits_list[0])
        write_toml(ctx.params["output_dir"], node, generate_toml(traits_dir, topics, traits_list))
        json_dump[NODES_JSON][node] = {}
        json_dump[NODES_JSON][node]["static_nodes"] = []
        for edge in G.edges(node):
            json_dump[NODES_JSON][node]["static_nodes"].append(edge[1])
        json_dump[NODES_JSON][node][SUBNET_PREFIX] = node2subnet[node]
        json_dump[NODES_JSON][node]["image"] = nodeTypeToDocker.get(node_type)
            # the per node tomls will continue for now as they include topics
        json_dump[NODES_JSON][node]["node_config"] = f"{node}.toml"
            # logs ought to continue as they need to be unique
        json_dump[NODES_JSON][node]["node_log"] = f"{node}.log"
        port_shift, cid = node2container[node]
        json_dump[NODES_JSON][node]["port_shift"] = port_shift
        json_dump[NODES_JSON][node]["container_id"] = cid
    write_json(ctx.params["output_dir"], json_dump)  # network wide json


# sanity check : valid json with "gennet" config
def _config_file_callback(ctx: typer.Context, param: typer.CallbackParam, cfile: str):
    if cfile:
        typer.echo(f"Loading config file: {os.path.basename(cfile)}")
        ctx.default_map = ctx.default_map or {}  # Init the default map
        try:
            with open(cfile, 'r') as f:  # Load config file
                conf = json.load(f)
                if "gennet" not in conf:
                    print(
                        f"Gennet configuration not found in {cfile}. Skipping network generation.")
                    sys.exit(0)
                if "general" in conf and "prng_seed" in conf["general"]:
                    conf["gennet"]["prng_seed"] = conf["general"]["prng_seed"]
                # TODO : type-check and sanity-check the values in config.json
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
            f"num_subnets must be <= num_nodes : num_subnets={num_subnets}, num_nodes={1}")
    return num_subnets


def main(ctx: typer.Context,

        benchmark: bool = typer.Option(False,
            help="Measure CPU/Mem usage of Gennet"),
         draw: bool = typer.Option(False,
             help="Draw the generated network"),
         container_size: int =  typer.Option(1,
             help="Set the number of nodes per container"),
         output_dir: str = typer.Option("network_data",
             help="Set the output directory for Gennet generated files"),
         prng_seed: int = typer.Option(1,
             help="Set the random seed"),
         num_nodes: int = typer.Option(4,
             help="Set the number of nodes"),
         num_topics: int = typer.Option(1,
             help="Set the number of topics"),
         fanout: int = typer.Option(3,
             help="Set the arity for trees, d-regular graphs & newmanwattsstrogatz"),
         node_type_distribution: str = typer.Argument("{\"nwaku\" : 100 }",
             callback=ast.literal_eval, help="Set the node type distribution"),
         network_type: networkType = typer.Option(networkType.REGULAR.value,
             help="Set the node type"),
         num_subnets: int = typer.Option(1, callback=_num_subnets_callback,
             help="Set the number of subnets"),
         num_partitions: int = typer.Option(1, callback=_num_partitions_callback,
             help="Set the number of network partitions"),
         config_file: str = typer.Option("", callback=_config_file_callback, is_eager=True,
             help="Set the input config file (JSON)"),
         traits_dir: Path = typer.Option("./traits", exists=True, file_okay=False,
             dir_okay=True, readable=True, resolve_path=True, help="Set the traits directory")):

    # Benchmarking: record start time and start tracing mallocs
    if benchmark:
        tracemalloc.start()
    start = time.time()

    # set the random seed : networkx uses numpy.random as well
    print("Setting the random seed to ", prng_seed)
    random.seed(prng_seed)
    np.random.seed(prng_seed)

    # validate node type distribution
    validate_traits_distribution(ctx.params["traits_dir"], node_type_distribution)

    # Generate the network
    # G = generate_network(num_nodes, networkType(network_type), tree_arity)
    G = generate_network(ctx)

    # Do not complain if the folder already exists
    make_empty_dir(output_dir)

    # Generate file format specific data structs and write the files
    generate_and_write_files(ctx, G)

    # Draw the graph if need be
    if draw:
        draw_network(output_dir, G)

    end = time.time()
    time_took = end - start
    print(f'For {G.number_of_nodes()}/{num_nodes} nodes, network generation took {time_took} secs.')
    print(f'The generated network ({network_type.value}) is under ./{output_dir}')

    # Benchmarking. Record finish time and stop the malloc tracing
    if benchmark:
        mem_curr, mem_max = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"STATS: For {num_nodes} nodes, time took is {time_took} secs, peak memory usage is {mem_max/(1024*1024)} MBs\n")


if __name__ == "__main__":
    typer.run(main)
