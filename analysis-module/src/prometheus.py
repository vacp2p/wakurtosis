# Python Imports
import builtins
from datetime import datetime
import subprocess
from tqdm import tqdm
from prometheus_api_client import PrometheusConnect

# Project Imports
from src import analysis_logger


def connect_to_prometheus(port):
    url = f"http://host.docker.internal:{port}"
    try:
        analysis_logger.G_LOGGER.debug('Connecting to Prometheus server in %s' %url)
        prometheus = PrometheusConnect(url, disable_ssl=True)
    except Exception as e:
        analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
        return None

    return prometheus


def get_hardware_metrics_2(topology, min_tss, max_tss, prom_port):
    # Fetch Hardware metrics from Node containers
    cpu_usage = []
    memory_usage = []
    bandwith_in = []
    bandwith_out = []
    max_disk_usage = {'disk_read_mbytes': [], 'disk_write_mbytes': []}

    node_container_ips = [info["kurtosis_ip"] for info in topology["containers"].values()]
    pbar = tqdm(node_container_ips)

    prometheus = connect_to_prometheus(prom_port)

    for container_ip in pbar:
        pbar.set_description(f'Fetching hardware stats from container {container_ip}')
        try:
            fetch_cadvisor_stats_from_prometheus(prometheus, container_ip, min_tss, max_tss)
        except Exception as e:
            analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
            continue

        # NOTE: Here we could also choose a different statistic such as mean or average instead of max
        cpu_usage.append(max(container_stats['cpu_usage']))
        memory_usage.append(max(container_stats['memory_usage']))
        bandwith_in.append(max(container_stats['bandwidth_in']))
        bandwith_out.append(max(container_stats['bandwidth_out']))
        max_disk_usage['disk_read_mbytes'].append(max(container_stats['disk_read']))
        max_disk_usage['disk_write_mbytes'].append(max(container_stats['disk_write']))

    return cpu_usage, memory_usage, bandwith_in, bandwith_out, max_disk_usage


def get_hardware_metrics(metrics, topology, min_tss, max_tss, prom_port):
    node_container_ips = [info["kurtosis_ip"] for info in topology["containers"].values()]
    pbar = tqdm(node_container_ips)

    prometheus = connect_to_prometheus(prom_port)

    for container_ip in pbar:
        pbar.set_description(f'Fetching hardware stats from container {container_ip}')
        try:
            fetch_cadvisor_stats_from_prometheus(metrics, prometheus, container_ip, min_tss, max_tss)
        except Exception as e:
            analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
            continue


def fetch_cadvisor_stats_from_prometheus(metrics, prom, container_ip, start_ts, end_ts):
    # Prometheus query example:
    # container_network_transmit_bytes_total{container_label_com_kurtosistech_private_ip = "212.209.64.2"}
    start_timestamp = datetime.utcfromtimestamp(start_ts / 1e9)
    end_timestamp = datetime.fromtimestamp(end_ts / 1e9)

    for metric in metrics["to_query"].values():
        if type(metric["metric_name"]) is list:
            if "values" not in metric.keys():
                metric["values"] = [[] for _ in range(len(metric["metric_name"]))]
            for i, submetric in enumerate(metric["metric_name"]):
                values = fetch_metric(prom, submetric, container_ip, start_timestamp, end_timestamp,
                                      metric["toMB"])
                stat_function = vars(builtins)[metric["statistic"]]
                metric["values"][i].append(stat_function(values))
        else:
            values = fetch_metric(prom, metric["metric_name"], container_ip, start_timestamp, end_timestamp,
                                  metric["toMB"])
            stat_function = vars(builtins)[metric["statistic"]]
            metric.setdefault("values", []).append(stat_function(values))


def fetch_cadvisor_stats_from_prometheus_2(prom, container_ip, start_ts, end_ts):
    # Prometheus query example:
    # container_network_transmit_bytes_total{container_label_com_kurtosistech_private_ip = "212.209.64.2"}
    start_timestamp = datetime.utcfromtimestamp(start_ts / 1e9)
    end_timestamp = datetime.fromtimestamp(end_ts / 1e9)

    cpu = fetch_metric(prom, "container_cpu_load_average_10s", container_ip, start_timestamp, end_timestamp)
    mem = fetch_metric(prom, "container_memory_usage_bytes", container_ip, start_timestamp, end_timestamp, True)
    net_in = fetch_metric(prom, "container_network_receive_bytes_total", container_ip, start_timestamp, end_timestamp, True)
    net_out = fetch_metric(prom, "container_network_transmit_bytes_total", container_ip, start_timestamp, end_timestamp, True)
    disk_r = fetch_metric(prom, "container_fs_reads_bytes_total", container_ip, start_timestamp, end_timestamp, True)
    disk_w = fetch_metric(prom, "container_fs_writes_bytes_total", container_ip, start_timestamp, end_timestamp, True)

    return {'cpu_usage': cpu, 'memory_usage': mem, 'bandwidth_in': net_in, 'bandwidth_out': net_out,
            'disk_read': disk_r, 'disk_write': disk_w}


def fetch_metric(prom, metric, ip, start_timestamp, end_timestamp, to_mbytes=False):
    metric_result = prom.custom_query_range(f"{metric}{{container_label_com_kurtosistech_private_ip = '{ip}'}}",
                                  start_time=start_timestamp, end_time=end_timestamp, step="1s")
    print(metric_result)
    metric_values = [float(metric_result[0]['values'][i][1]) for i in range(len(metric_result[0]['values']))]
    if to_mbytes:
        metric_values = [value/(1024*1024) for value in metric_values]

    return metric_values
