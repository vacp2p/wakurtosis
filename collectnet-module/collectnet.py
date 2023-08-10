# Python Imports
import argparse
import hashlib
import random
import os
import sys
import time
import asyncio
import os
import json
import typer
import logging as log
from pathlib import Path
import aiohttp

def load_json(fname):
    with open(fname, 'r') as f:
        dic = json.load(f)
    return dic


def save_json(fname, dic):
   with open(fname, 'w') as f:
        f.write(json.dumps(dic, indent=4))


def _create_get_peers_rpc(node_address):
    data = {
        'jsonrpc': '2.0',
        'method': 'get_waku_v2_admin_v1_peers',
        'id': 1,
        'params': []
    }
    #wls_logger.G_LOGGER.debug(f"Waku RPC: {data['method']} from {node_address}")
    return data


# post the RPC, collect the result, and parse it to a json
async def send_get_peers_async(rpc_cmd, node_address):
    json_data = json.dumps(rpc_cmd)
    start = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.post(node_address, data=json_data,
                headers={'content-type': 'application/json'}) as res:
            elapsed = time.time() - start
            response = await res.json(content_type='text/html') # yield when parsing
            #wls_logger.G_LOGGER.debug(f"get_peers : {node_address}: {response} [{start}:{elapsed}]")
            #print(response, elapsed)
            return response, elapsed

'''
# create the buffer, start the call
async def send_get_peers_to_node_async(node_address):
    # do NOT lift : need fresh rpc buffer for correct operation!
    data = _create_get_peers_rpc(node_address)  # get a new buffer every time: do NOT reuse!
    response_obj, elapsed = await _send_get_peers_async(data, node_address) # yield when waiting
    #print(response_obj, elapsed)
    return response_obj, elapsed
'''


node2addr, peerid2node, collector, count, debugfh = {}, {}, {}, 0, None
# the event handler for peer collection
async def collect_peers():
    #global node2addr, peerid2node, collector, count
    ctime = time.time()
    tasks, collector[ctime]  = [], {}
    for name, addr in node2addr.items(): # yield between each iterations
        rpc_cmd = _create_get_peers_rpc(addr)  # get a new buffer every time: do NOT reuse!
        task = asyncio.create_task(send_get_peers_async(rpc_cmd, addr))
        tasks.append(task)
        #response, elapsed = await send_get_peers_to_node_async(addr)
        #log.info(f"get_peers : {name}={addr} -> {response} = {elapsed}")
        #collector[name] = (response, elapsed)
    collected_replies, i = await asyncio.gather(*tasks), 0
    for name, addr in node2addr.items():
        results, relay_peers = collected_replies[i], []
        for res in results[0]["result"]:
            if res["protocol"] == "/vac/waku/relay/2.0.0" and res["connected"]:
                peerid = res["multiaddr"].split("/")[6]
                if peerid not in peerid2node:
                    print(f'adding discv5 server ({peerid}) as peer')
                    peerid2node[peerid] = "discv5-server"
                    continue
                relay_peers.append(peerid2node[peerid])
        collector[ctime][name] = relay_peers
        i += 1
    if debugfh != None:
        debugfh.write(f'\t{ctime} : {{{collected_replies}}},\n')


# pre-compute the addresses
def precompute_node_maps(network_data):
    #global  node2addr, peerid2node
    for node, info in network_data["nodes"].items():
        node2addr[node] = f"http://{info['ip_address']}:{info['ports']['rpc-' + node][0]}/"
       # if network_data["nodes"][node]["peer_id"] in peerid2node:
        peerid2node[network_data["nodes"][node]["peer_id"]] = node
    log.debug(f"get_peers: {node2addr}")
    print(f"get_peers: {node2addr}, {peerid2node}")
    return node2addr, peerid2node


async def start_topology_collector_async(wls_config,
        network_data, sampling_interval, output_file, debug):
    #global node2addr, peerid2node, collector, count, debugfh
    start_time = time.time()
    log.info(f"Starting topology collection")
    precompute_node_maps(network_data)
    count, collector = 0, {}
    if debug:
        global debugfh
        debugfh = open(f'debug-{os.path.basename(output_file)}', "w")
        debugfh.write("{\n")
    while True:
        await collect_peers()
        count +=1
        print(f'Next topology collection {count} will be done in {sampling_interval} secs')
        log.debug(f'Next topology collection {count} will be done in {sampling_interval} secs')
        # Wait for all the tasks to complete
        await asyncio.sleep(sampling_interval)
    #return collector


def main(ctx: typer.Context,
        config_file: Path = typer.Option("config.json",
                exists=True, file_okay=True, readable=True,
                help="Set the config file"),
        network_data_file: Path = typer.Option("topology_generated/network_data.json",
                exists=True, file_okay=True, readable=True,
                help="Set the network data file"),
        output_file: Path = typer.Option("observed_network.json", exists=False, resolve_path=True,
                help="Set the output file"),
        sampling_interval: int = typer.Option(5,
                help="Set the sampling interval"),
        debug: int = typer.Option(True,
                help="Set debug")
        ):

    config = load_json(config_file)
    network_data = load_json(network_data_file)

    # Set loglevel from config
    wls_config = config['wls']

    # Set RPNG seed from config
    random.seed(config['general']['prng_seed'])

    log.info("Starting topology generator")


    loop = asyncio.get_event_loop()
    task = loop.create_task(
            start_topology_collector_async(
                wls_config, network_data, sampling_interval, output_file, debug))
    loop.call_later(wls_config['simulation_time'], task.cancel)

    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass

    save_json(output_file, collector)
    if debugfh != None:
        debugfh.write("\n}")

if __name__ == "__main__":
    typer.run(main)
