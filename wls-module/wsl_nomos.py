#!/usr/bin/env python3
"""
Description: Wakurtosis load simulator

"""

""" Dependencies """
import sys, logging, yaml, json, time, random, os, argparse, tomllib, glob
import requests
import rtnorm
import nomos
# from pathlib import Path
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# import cloudpickle as pickle

""" Globals """
G_APP_NAME = 'WLS'
G_LOG_LEVEL = 'DEBUG'
G_DEFAULT_CONFIG_FILE = './config/wsl.yml'
G_DEFAULT_TOPOLOGY_FILE = './tomls/network_data.json'
G_LOGGER = None

""" Custom logging formatter """
class CustomFormatter(logging.Formatter):
    
    # Set different formats for every logging level
    time_name_stamp = "[%(asctime)s.%(msecs)03d] [" + G_APP_NAME + "]"
    FORMATS = {
        logging.ERROR: time_name_stamp + " ERROR in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.WARNING: time_name_stamp + " WARNING - %(msg)s",
        logging.CRITICAL: time_name_stamp + " CRITICAL in %(module)s.py %(funcName)s() %(lineno)d - %(msg)s",
        logging.INFO:  time_name_stamp + " %(msg)s",
        logging.DEBUG: time_name_stamp + " %(funcName)s() %(msg)s",
        'DEFAULT': time_name_stamp + " %(msg)s",
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self.FORMATS['DEFAULT'])
        formatter = logging.Formatter(log_fmt, '%d-%m-%Y %H:%M:%S')
        return formatter.format(record)

def check_nomos_node(node_address):
    url = node_address + "network/info"
    
    try:
        response = requests.get(url)
    except Exception as e:
        G_LOGGER.debug('%s: %s' % (e.__doc__, e))
        return False

    try:
        response_obj = response.json()
    except Exception as e:
        G_LOGGER.debug('%s: %s' % (e.__doc__, e))
        return False

    G_LOGGER.debug('Response from %s: %s' %(node_address, response_obj))
    
    return True

def add_nomos_tx(node_address, tx):
    url = node_address + "mempool/addtx"

    try:
        response = requests.post(url, data=json.dumps(tx), headers={'content-type': 'application/json'})
    except Exception as e:
        G_LOGGER.debug('%s: %s' % (e.__doc__, e))
        return False

    if len(response.text) > 0:
        G_LOGGER.debug('Response from %s: %s' %(url, response.text))
        return False
    
    return True

def get_nomos_mempool_metrics(node_address, iteration_s):
    url = node_address + "mempool/metrics"

    try:
        response = requests.get(url)
    except Exception as e:
        G_LOGGER.debug('%s: %s' % (e.__doc__, e))
        return "error", -1

    try:
        response_obj = response.json()
    except Exception as e:
        G_LOGGER.debug('%s: %s' % (e.__doc__, e))
        return "error", -1
    G_LOGGER.debug('Response from %s: %s' %(node_address, response_obj))
    time_e = int(time.time() * 1000)
    
    return response_obj, time_e - iteration_s

def main(): 

    global G_LOGGER
    
    """ Init Logging """
    G_LOGGER = logging.getLogger(G_APP_NAME)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(CustomFormatter())
    G_LOGGER.addHandler(handler)
    
    G_LOGGER.info('Started')

    """ Parse command line args. """
    parser = argparse.ArgumentParser()
    parser.add_argument("-cfg", "--config_file", help="Config file", action="store_true", default=G_DEFAULT_CONFIG_FILE)
    parser.add_argument("-topo", "--topology_file", help="Topology file", action="store_true", default=G_DEFAULT_TOPOLOGY_FILE)
    args = parser.parse_args()

    config_file = args.config_file
    topology_file = args.topology_file
        
    """ Load config file """
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()
    
    # Set loglevel from config
    G_LOGGER.setLevel(config['general']['debug_level'])
    handler.setLevel(config['general']['debug_level'])

    G_LOGGER.debug(config)
    G_LOGGER.info('Configuration loaded from %s' %config_file)

    # Set RPNG seed from config
    random.seed(config['general']['prng_seed'])
    
    """ Load targets """
    try:
        with open(config['general']['targets_file'], 'r') as read_file:
            targets = json.load(read_file)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    try:
        with open(topology_file) as read_file:
            topology = json.load(read_file)
    except Exception as e:
        G_LOGGER.error('%s: %s' % (e.__doc__, e))
        sys.exit()

    if len(targets) == 0:
        G_LOGGER.error('Cannot find valid targets. Aborting.')
        sys.exit(1)

    G_LOGGER.debug(targets)
    G_LOGGER.info('%d targets loaded' %len(targets))

    """ Check all nodes are reachable """
    for i, target in enumerate(targets):
        if not check_nomos_node('http://%s/' %target):
            G_LOGGER.error('Node %d (%s) is not online. Aborted.' %(i, target))
            sys.exit(1)
    G_LOGGER.info('All %d Waku nodes are reachable.' %len(targets))

    """ Start simulation """
    msg_cnt = 0
    failed_addtx_cnt = 0
    failed_metrics_cnt = 0
    bytes_cnt = 0
    s_time = time.time()
    last_msg_time = 0
    next_time_to_msg = 0
    failed_dissemination_cnt = 0
    batch_size = 40 
    iterations = []
    tx_id = 0

    G_LOGGER.info('Tx addition start time: %d' %int(round(time.time() * 1000)))
    """ Add new transaction to every node """
    for i, target in enumerate(targets):
        iteration_s = int(time.time() * 1000)
        last_tx_sent = iteration_s

        tx_id = tx_id + msg_cnt+failed_addtx_cnt+1
        for j in range(batch_size):
            tx_id += j
            tx_target = random.choice(targets)
            G_LOGGER.debug('sending tx_id: %s to target: %s' %(tx_id, tx_target))

            if not add_nomos_tx('http://%s/' %tx_target, 'tx%s' %tx_id):
                G_LOGGER.error('Unable to add new tx. Node %s.' %(tx_target))
                failed_addtx_cnt += 1
                continue

            last_tx_sent = int(time.time() * 1000)
            msg_cnt += 1

        time.sleep(1.5)

        results = []
        """ Collect mempool metrics from nodes """
        for n, target in enumerate(targets):
            res, t = get_nomos_mempool_metrics('http://%s/' %target, iteration_s)
            if 'error' in res:
                G_LOGGER.error('Unable to pull metrics. Node %d (%s).' %(n, target))
                failed_metrics_cnt += 1
                continue

            is_ok = True
            delta = res['last_tx'] - last_tx_sent
            start_finish = res['last_tx'] - iteration_s

            # Tolerate one second difference between finish and start times.
            if -1000 < delta < 0:
                delta = 0

            if delta < 0:
                G_LOGGER.error('delta should be gt that zero: %d' %delta)
                delta = -1

            G_LOGGER.debug('should be %s' %msg_cnt)
            if res['pending_tx'] != msg_cnt:
                delta = -1
                is_ok = False
                failed_dissemination_cnt += 1

            results.append({
                "node": n,
                "is_ok": is_ok,
                "delta": delta,
                "start_finish": start_finish
            })

        iterations.append({
            "iteration": iteration_s,
            "results": results
        })

    stats = {
        "msg_cnt": msg_cnt,
        "failed_addtx_cnt": failed_addtx_cnt,
        "failed_metrics_cnt": failed_metrics_cnt,
        "failed_dissemination_cnt": failed_dissemination_cnt,
        "batch_size": batch_size,
        "bytes_cnt": bytes_cnt,
        "s_time": s_time,
        "last_msg_time": last_msg_time,
        "next_time_to_msg": next_time_to_msg,
        "iterations": iterations,
    }

    G_LOGGER.info("Results: %s" %json.dumps(stats))

    with open('./summary.json', 'w') as summary_file:
        summary_file.write(json.dumps(stats, indent=4))

    nomos.network_graph("1.png", topology)
    nomos.hist_delta("2.png", stats['iterations'])
    nomos.concat_images("collage.png", ["1.png", "2.png"])

    """ We are done """
    G_LOGGER.info('Ended')
    
if __name__ == "__main__":
    
    main()
