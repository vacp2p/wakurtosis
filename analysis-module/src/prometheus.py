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
                print(f"{submetric} is: {values}")
                stat_function = vars(builtins)[metric["statistic"]]
                metric["values"][i].append(stat_function(values))
        else:
            values = fetch_metric(prom, metric["metric_name"], container_ip, start_timestamp, end_timestamp,
                                  metric["toMB"])
            print(f"{metric['metric_name']} is: {values}")
            stat_function = vars(builtins)[metric["statistic"]]
            metric.setdefault("values", []).append(stat_function(values))


def fetch_metric(prom, metric, ip, start_timestamp, end_timestamp, to_mbytes=False):
    metric_result = prom.custom_query_range(f"{metric}{{container_label_com_kurtosistech_private_ip = '{ip}'}}",
                                  start_time=start_timestamp, end_time=end_timestamp, step="1s")
    print(metric_result)
    metric_values = [float(metric_result[0]['values'][i][1]) for i in range(len(metric_result[0]['values']))]
    if to_mbytes:
        metric_values = [value/(1024*1024) for value in metric_values]
    print(metric_values)

    return metric_values
