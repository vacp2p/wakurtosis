import requests
import time
import json
import random
import matplotlib.pyplot as plt
import networkx as nx
import statistics
from PIL import Image

LOGGER = None

# Histogram of time delta in millis of tx being sent
# and received by all nodes.

def hist_delta(name, iterations):
    results = []
    for iteration in iterations:
        iteration_results = [result["delta"] for result in iteration["results"]]
        results.extend(iteration_results)

    plt.hist(results, bins=30, color="#000000")
    plt.xlabel("Delta time (milliseconds)", fontsize=12)
    plt.ylabel("Frequency", fontsize=12)
    plt.title("TX dissemination over network", fontsize=14)

    plt.savefig(name, dpi=200)
    plt.close()

def network_graph(name, topology):
    G = nx.DiGraph()
    for node_name, node_data in topology.items():
        G.add_node(node_name)
    for node_name, node_data in topology.items():
        for connection in node_data["static_nodes"]:
            G.add_edge(node_name, connection)

    pos = nx.spring_layout(G, seed=1)
    node_size = 100
    font_size = 8

    nx.draw(G, pos, with_labels=False, node_size=node_size, font_size=font_size, node_color='white', edge_color='black')
    shift_amount = 0.07
    label_pos = {k: (v[0], v[1]+shift_amount) for k, v in pos.items()}
    nx.draw_networkx_labels(G, label_pos, font_size=font_size)
    nx.draw_networkx_nodes(G, pos, node_size=node_size, node_color='black', edgecolors='white')

    plt.savefig(name, dpi=200)
    plt.close()

def concat_images(name, images):
    images = [Image.open(image) for image in images]

    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)
    max_height = max(heights)

    collage = Image.new('RGB', (total_width, max_height))

    x_offset = 0
    for image in images:
        collage.paste(image, (x_offset, 0))
        x_offset += image.size[0]

    collage.save(name)

def check_nomos_node(node_address):
    url = node_address + "network/info"
 
    try:
        response = requests.get(url)
    except Exception as e:
        LOGGER.debug('%s: %s' % (e.__doc__, e))
        return False

    try:
        response_obj = response.json()
    except Exception as e:
        LOGGER.debug('%s: %s' % (e.__doc__, e))
        return False

    LOGGER.debug('Response from %s: %s' %(node_address, response_obj))
 
    return True

def add_nomos_tx(node_address, tx):
    url = node_address + "mempool/addtx"

    try:
        response = requests.post(url, data=json.dumps(tx), headers={'content-type': 'application/json'})
    except Exception as e:
        LOGGER.debug('%s: %s' % (e.__doc__, e))
        return False

    if len(response.text) > 0:
        LOGGER.debug('Response from %s: %s' %(url, response.text))
        return False
 
    return True

def get_nomos_mempool_metrics(node_address, iteration_s):
    url = node_address + "mempool/metrics"

    try:
        response = requests.get(url)
    except Exception as e:
        LOGGER.debug('%s: %s' % (e.__doc__, e))
        return "error", -1

    try:
        response_obj = response.json()
    except Exception as e:
        LOGGER.debug('%s: %s' % (e.__doc__, e))
        return "error", -1
    LOGGER.debug('Response from %s: %s' %(node_address, response_obj))
    time_e = int(time.time() * 1000)
 
    return response_obj, time_e - iteration_s

def run_tests(logger, config, targets, topology):
    global LOGGER
    LOGGER = logger

    """ Check all nodes are reachable """
    for i, target in enumerate(targets):
        if not check_nomos_node('http://%s/' %target):
            LOGGER.error('Node %d (%s) is not online. Aborted.' %(i, target))
            sys.exit(1)
    LOGGER.info('All %d Waku nodes are reachable.' %len(targets))

    """ Start simulation """
    msg_cnt = 0
    failed_addtx_cnt = 0
    failed_metrics_cnt = 0
    s_time = time.time()
    failed_dissemination_cnt = 0
    batch_size = 40
    iterations = []
    tx_id = 0
    all_response_deltas = []

    LOGGER.info('Tx addition start time: %d' %int(round(time.time() * 1000)))
    """ Add new transaction to every node """
    for i, target in enumerate(targets):
        iteration_s = int(time.time() * 1000)
        last_tx_sent = iteration_s

        tx_id = tx_id + msg_cnt+failed_addtx_cnt+1
        for j in range(batch_size):
            tx_id += j
            tx_target = random.choice(targets)
            LOGGER.debug('sending tx_id: %s to target: %s' %(tx_id, tx_target))

            if not add_nomos_tx('http://%s/' %tx_target, 'tx%s' %tx_id):
                LOGGER.error('Unable to add new tx. Node %s.' %(tx_target))
                failed_addtx_cnt += 1
                continue

            last_tx_sent = int(time.time() * 1000)
            msg_cnt += 1

        time.sleep(1)

        results = []
        """ Collect mempool metrics from nodes """
        for n, target in enumerate(targets):
            res, t = get_nomos_mempool_metrics('http://%s/' %target, iteration_s)
            if 'error' in res:
                LOGGER.error('Unable to pull metrics. Node %d (%s).' %(n, target))
                failed_metrics_cnt += 1
                continue

            is_ok = True
            delta = res['last_tx'] - last_tx_sent
            start_finish = res['last_tx'] - iteration_s

            # Tolerate one second difference between finish and start times.
            if -1000 < delta < 0:
                delta = 0

            if delta < 0:
                LOGGER.error('delta should be gt that zero: %d' %delta)
                delta = -1

            LOGGER.debug('should be %s' %msg_cnt)
            if res['pending_tx'] != msg_cnt:
                delta = -1
                is_ok = False
                failed_dissemination_cnt += 1

            if delta >= 0:
                all_response_deltas.append(delta)

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
        "s_time": s_time,
        "median_response_delta": statistics.median(all_response_deltas),
        "iterations": iterations,
    }

    with open('./topology.json', 'w') as summary_file:
        summary_file.write(json.dumps(topology, indent=4))

    with open('./summary.json', 'w') as summary_file:
        summary_file.write(json.dumps(stats, indent=4))

    network_graph("1.png", topology)
    hist_delta("2.png", stats['iterations'])
    concat_images("collage.png", ["1.png", "2.png"])

    """ We are done """
    LOGGER.info('Ended')
