# Python Imports
import builtins
from datetime import datetime
from tqdm import tqdm
from prometheus_api_client import PrometheusConnect

# Project Imports
from src import analysis_logger
from src import plotting_configurations


def connect_to_prometheus(port):
    url = f"http://host.docker.internal:{port}"
    try:
        analysis_logger.G_LOGGER.debug('Connecting to Prometheus server in %s' % url)
        prometheus = PrometheusConnect(url, disable_ssl=True)
    except Exception as e:
        analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
        return None

    return prometheus


def get_hardware_metrics(metrics, topology, min_tss, max_tss, prom_port):
    container_ips = [info["kurtosis_ip"] for info in topology["containers"].values()]
    pbar = tqdm(container_ips)
    prometheus = connect_to_prometheus(prom_port)

    for container_ip in pbar:
        pbar.set_description(f'Fetching hardware stats from container {container_ip}')
        try:
            fetch_cadvisor_stats_from_prometheus_by_node(metrics, prometheus, container_ip, min_tss,
                                                         max_tss)
        except Exception as e:
            analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
            continue

    #fetch_cadvisor_stats_from_prometheus_by_simulation(metrics, prometheus, container_ips, min_tss,
    #                                                   max_tss)


def fetch_cadvisor_stats_from_prometheus_by_simulation(metrics, prom, container_ips, start_ts,
                                                       end_ts):
    start_timestamp = datetime.utcfromtimestamp(start_ts / 1e9)
    end_timestamp = datetime.fromtimestamp(end_ts / 1e9)

    for metric in metrics["by_simulation"]:
        plotting_config = plotting_configurations.plotting_config[metric]
        plotting_config.setdefault("values", []).append(
            fetch_accumulated_metric_for_all_nodes(prom, metric, container_ips,
                                                   start_timestamp,
                                                   end_timestamp, plotting_config["toMB"]))


def fetch_cadvisor_stats_from_prometheus_by_node(metrics, prom, container_ip, start_ts, end_ts):
    # Prometheus query example:
    # container_network_transmit_bytes_total{container_label_com_kurtosistech_private_ip = "212.209.64.2"}
    start_timestamp = datetime.utcfromtimestamp(start_ts / 1e9)
    end_timestamp = datetime.fromtimestamp(end_ts / 1e9)

    for metric in metrics["by_node"]:
        plotting_config = plotting_configurations.plotting_config[metric]
        stat_function = function_dispatcher[plotting_config["statistic"]]
        values = fetch_metric(prom, metric, container_ip, start_timestamp, end_timestamp,
                              plotting_config["toMB"])
        plotting_config.setdefault("values", []).append(stat_function(values))


def fetch_accumulated_metric_for_all_nodes(prom, metric, container_ips, start_timestamp,
                                           end_timestamp,
                                           to_mbytes=False):
    result = {}
    for ip in container_ips:
        values = fetch_metric_with_timestamp(prom, metric, ip, start_timestamp, end_timestamp)
        for item in values:
            timestamp, value = item
            value = int(value)
            if to_mbytes:
                value = value / (1024 * 1024)
            if timestamp in result:
                result[timestamp] += value
            else:
                result[timestamp] = value

    result_list = [value for value in result.values()]

    return result_list


def fetch_metric(prom, metric, ip, start_timestamp, end_timestamp, to_mbytes=False):
    metric_result = prom.custom_query_range(
        f"{metric}{{container_label_com_kurtosistech_private_ip = '{ip}'}}",
        start_time=start_timestamp, end_time=end_timestamp, step="1s")
    if not metric_result:
        analysis_logger.G_LOGGER.error(f"{metric} returns no data. Adding zero.")
        return [0]
    metric_values = [float(metric_result[0]['values'][i][1]) for i in
                     range(len(metric_result[0]['values']))]
    if to_mbytes:
        metric_values = [value / (1024 * 1024) for value in metric_values]

    return metric_values


def fetch_metric_with_timestamp(prom, metric, ip, start_timestamp, end_timestamp):
    metric_result = prom.custom_query_range(
        f"{metric}{{container_label_com_kurtosistech_private_ip = '{ip}'}}",
        start_time=start_timestamp, end_time=end_timestamp, step="1s")

    if not metric_result:
        analysis_logger.G_LOGGER.error(f"{metric} returns no data. Adding zero.")
        return [[0, 0]]

    return metric_result[0]['values']


function_dispatcher = {
    "max": max,
    "min": min,
    "average": lambda x: sum(x) / len(x)
}
