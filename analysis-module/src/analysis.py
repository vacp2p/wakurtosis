# Python Imports
import re
import sys
import glob
from tqdm_loggable.auto import tqdm

# Project Imports
from src import analysis_logger
from src import log_parser


def update_min_max_tss(tss, min_tss, max_tss):
    if tss < min_tss:
        min_tss = tss
    elif tss > max_tss:
        max_tss = tss

    return min_tss, max_tss


def get_relay_line_info(log_line):
    msg_topics = re.search(r'topics="([^"]+)"', log_line).group(1)
    msg_topic = re.search(r'pubsubTopic=([^ ]+)', log_line).group(1)
    msg_hash = re.search(r'hash=([^ ]+)', log_line).group(1)
    msg_peer_id = re.search(r'peerId=([^ ]+)', log_line).group(1)

    return msg_topics, msg_topic, msg_hash, msg_peer_id


def compute_injection_times(injected_msgs_dict):
    return [msg['injection_time'] for msg in injected_msgs_dict.values() if msg['status'] == 200]


def analyze_published(log_line, node_logs, msgs_dict, msg_publishTime):
    msg_topics, msg_topic, msg_hash, msg_peer_id = get_relay_line_info(log_line)
    node_logs[msg_peer_id]['published'].append([msg_publishTime, msg_topics, msg_topic, msg_hash])

    if msg_hash not in msgs_dict:
        msgs_dict[msg_hash] = {'published': [{'ts': msg_publishTime, 'peer_id': msg_peer_id}],
                               'received': []}
    else:
        msgs_dict[msg_hash]['published'].append(
            {'ts': msg_publishTime, 'peer_id': msg_peer_id})


def analyze_received(log_line, node_logs, msgs_dict, msg_receivedTime):
    msg_topics, msg_topic, msg_hash, msg_peer_id = get_relay_line_info(log_line)
    node_logs[msg_peer_id]['received'].append([msg_receivedTime, msg_topics, msg_topic, msg_hash])

    if msg_hash not in msgs_dict:
        msgs_dict[msg_hash] = {'published': [], 'received': [
            {'ts': msg_receivedTime, 'peer_id': msg_peer_id}]}
    else:
        msgs_dict[msg_hash]['received'].append(
            {'ts': msg_receivedTime, 'peer_id': msg_peer_id})


def parse_lines_in_file(file, node_logs, msgs_dict, min_tss, max_tss):
    for log_line in file:
        if 'waku.relay' in log_line:
            if 'published' in log_line:
                msg_publishTime = int(re.search(r'publishTime=([\d]+)', log_line).group(1))

                analyze_published(log_line, node_logs, msgs_dict, msg_publishTime)

                min_tss, max_tss = update_min_max_tss(msg_publishTime, min_tss, max_tss)

            elif 'received' in log_line:
                msg_receivedTime = int(re.search(r'receivedTime=([\d]+)', log_line).group(1))

                analyze_received(log_line, node_logs, msgs_dict, msg_receivedTime)

                min_tss, max_tss = update_min_max_tss(msg_receivedTime, min_tss, max_tss)

    return min_tss, max_tss


def compute_message_latencies(msgs_dict):
    # Compute message latencies and propagation times throughout the network
    pbar = tqdm(msgs_dict.items())
    for msg_hash, msg_data in pbar:
        # NOTE: Careful here as I am assuming that every message is published once ...
        if len(msg_data['published']) > 1:
            analysis_logger.G_LOGGER.warning('Several publishers of message %s')

        published_ts = int(msg_data['published'][0]['ts'])
        peer_id = msg_data['published'][0]['peer_id']

        pbar.set_description('Computing latencies of message %s' % msg_hash)

        # Compute latencies
        latencies = []
        for received_data in msg_data['received']:
            # Skip self
            if received_data['peer_id'] == peer_id:
                analysis_logger.G_LOGGER.warning('Message %s received by the same node that published it' % msg_hash)
                continue
            # NOTE: We are getting some negative latencies meaning that the message appears to be received before it was sent ...
            # I assume this must be because those are the nodes that got the message injected in the first place
            #  TLDR: Should be safe to ignore all the negative latencies
            latency = int(received_data['ts']) - published_ts
            peer_id = msg_data['published'][0]['peer_id']
            latencies.append(latency)

        msgs_dict[msg_hash]['latencies'] = latencies


def compute_propagation_times(msgs_dict):
    msg_propagation_times = []
    pbar = tqdm(msgs_dict.items())

    for msg_hash, msg_data in pbar:
        pbar.set_description('Computing propagation time of message %s' % msg_hash)
        # todo check Why do we round here
        # msg_propagation_times.append(round(max(msg_data['latencies']) / 1000000))
        msg_propagation_times.append(max(msg_data['latencies']) / 1000000)

    return msg_propagation_times


def compute_message_delivery(msgs_dict, injected_msgs_dict):
    # Compute message delivery
    total_messages = len(injected_msgs_dict)
    delivered_messages = len(msgs_dict)
    lost_messages = total_messages - delivered_messages
    delivery_rate = delivered_messages * 100 / total_messages

    analysis_logger.G_LOGGER.info(f'{delivered_messages} of {total_messages} messages delivered. '
                                  f'Lost: {lost_messages}. Delivery rate {delivery_rate}')

    return delivery_rate


def analyze_containers(topology, simulation_path):
    node_logs = {}
    msgs_dict = {}
    max_tss = -sys.maxsize - 1
    min_tss = sys.maxsize

    for container_name, container_info in topology["containers"].items():
        node_pbar = tqdm(container_info["nodes"])

        node_pbar.set_description(f"Parsing log of container {container_name}")

        log_parser.prepare_node_in_logs(node_pbar, topology, node_logs, container_name)

        folder = glob.glob(f'{simulation_path}/{container_name}--*')
        if len(folder) > 1:
            raise RuntimeError(f"Error: Multiple containers with same name: {folder}")

        file = log_parser.open_file(folder)
        min_tss, max_tss = parse_lines_in_file(file, node_logs, msgs_dict, min_tss, max_tss)
        file.close()

    return node_logs, msgs_dict, min_tss, max_tss


def inject_metric_in_dict(metrics, key_name, title, y_label, metric_name, values):
    metrics[key_name] = {}
    metrics[key_name]["title"] = title
    metrics[key_name]["y_label"] = y_label
    metrics[key_name]["metric_name"] = metric_name
    metrics[key_name]["values"] = values
