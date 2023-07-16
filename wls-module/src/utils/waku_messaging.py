# Python Imports
import time
import json
import requests
import sys
import random
import base64
import aiohttp

# Project Imports
from src.utils import wls_logger


def _poisson_interval(rate):
    # Generate a random interval using a Poisson distribution
    return random.expovariate(rate)


def _get_waku_payload(nonce, payload):
    my_payload = {
        'nonce': nonce,
        'ts': time.time_ns(),
        'payload': payload
    }

    return my_payload


def _create_waku_msg(payload):
    waku_msg = {
        'payload':  base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
    }

    return waku_msg


def _create_waku_rpc_data(topic, waku_msg, node_address):
    data = {
        'jsonrpc': '2.0',
        'method': 'post_waku_v2_relay_v1_message',
        'id': 1,
        'params': [topic, waku_msg]
    }

    wls_logger.G_LOGGER.debug(f"Waku RPC: {data['method']} from {node_address} Topic: {topic}")

    return data

def _send_waku_rpc(data, node_address):
    s_time = time.time()

    json_data = json.dumps(data)

    response = requests.post(node_address, data=json_data,
                             headers={'content-type': 'application/json'})

    elapsed_ms = (time.time() - s_time) * 1000

    response_obj = response.json()

    wls_logger.G_LOGGER.debug(f"Response from {node_address}: {response_obj} [{elapsed_ms:.4f} ms.]")

    return response_obj, elapsed_ms

async def _send_waku_rpc_async(data, node_address):
    s_time = time.time()

    json_data = json.dumps(data)

    async with aiohttp.ClientSession() as session:
        async with session.post(node_address, data=json_data, headers={'content-type': 'application/json'}) as response:
            elapsed_ms = (time.time() - s_time) * 1000
            wls_logger.G_LOGGER.debug(f"Response from {node_address}: {response.status} [{elapsed_ms:.4f} ms.]")

            return response.status, elapsed_ms


### get peer

# build a fresh RPC buffer
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
async def _send_get_peers_async(data, node_address):
    json_data = json.dumps(data)
    start = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.post(node_address, data=json_data,
                headers={'content-type': 'application/json'}) as res:
            elapsed = time.time() - start
            response = await res.json(content_type='text/html') # yield when parsing
            #wls_logger.G_LOGGER.debug(f"get_peers : {node_address}: {response} [{elapsed}]")
            return response, elapsed

# create the buffer, start the call
async def send_get_peers_to_node_async(node_address):
    # do NOT lift : need fresh rpc buffer for correct operation!
    data = _create_get_peers_rpc(node_address)  # get a new buffer every time: do NOT reuse!
    response_obj, elapsed = await _send_get_peers_async(data, node_address) # yield when waiting
    return response_obj, elapsed

###

def send_msg_to_node(node_address, topic, payload, nonce=1):
    my_payload = _get_waku_payload(nonce, payload)
    waku_msg = _create_waku_msg(my_payload)
    data = _create_waku_rpc_data(topic, waku_msg, node_address)

    response_obj, elapsed_ms = _send_waku_rpc(data, node_address)

    return response_obj, elapsed_ms, json.dumps(waku_msg), my_payload['ts']

async def send_msg_to_node_async(node_address, topic, payload, nonce=1):
    my_payload = _get_waku_payload(nonce, payload)
    waku_msg = _create_waku_msg(my_payload)
    data = _create_waku_rpc_data(topic, waku_msg, node_address)

    response_obj, elapsed_ms = await _send_waku_rpc_async(data, node_address)

    return response_obj, elapsed_ms, json.dumps(waku_msg), my_payload['ts']

def get_next_time_to_msg(inter_msg_type, msg_rate, simulation_time):
    if inter_msg_type == 'poisson':
        return _poisson_interval(msg_rate)

    if inter_msg_type == 'uniform':
        return simulation_time / (msg_rate * simulation_time)

    wls_logger.G_LOGGER.error(f'{inter_msg_type} is not a valid inter_msg_type. Aborting.')
    sys.exit(1)
