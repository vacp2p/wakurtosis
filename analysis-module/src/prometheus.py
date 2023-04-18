# Python Imports
from datetime import datetime
import subprocess
from tqdm import tqdm
from prometheus_api_client import PrometheusConnect

# Project Imports
from src import analysis_logger


def connect_to_prometheus(port):
    #prometheus = subprocess.check_output("kurtosis enclave inspect wakurtosis | grep '\\<prometheus\\>' | awk '{print $6}'", shell=True)
    #url = f'http://{prometheus[:-1].decode("utf-8") }'
    url = f"http://127.0.0.1:{port}"
    try:
        analysis_logger.G_LOGGER.debug('Connecting to Prometheus server in %s' %url)
        prometheus = PrometheusConnect(url, disable_ssl=True)
        # print(prometheus)
    except Exception as e:
        analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
        return None

    return prometheus


def get_hardware_metrics(topology, min_tss, max_tss, prom_port):
    # Fetch Hardware metrics from Node containers
    cpu_usage = []
    memory_usage = []
    bandwith_in = []
    bandwith_out = []
    node_container_ips = [info["kurtosis_ip"] for info in topology["containers"].values()]
    pbar = tqdm(node_container_ips)

    prometheus = connect_to_prometheus(prom_port)

    for container_ip in pbar:

        pbar.set_description(f'Fetching hardware stats from container {container_ip}')

        try:
            container_stats = fetch_cadvisor_stats_from_prometheus(prometheus, container_ip, min_tss, max_tss)
        except Exception as e:
            analysis_logger.G_LOGGER.error('%s: %s' % (e.__doc__, e))
            continue

            # NOTE: Here we could also choose a different statistic such as mean or average instead of max
        cpu_usage.append(max(container_stats['cpu_usage']))
        memory_usage.append(max(container_stats['memory_usage']))
        bandwith_in.append(max(container_stats['bandwidth_in']))
        bandwith_out.append(max(container_stats['bandwidth_out']))

    return cpu_usage, memory_usage, bandwith_in, bandwith_out


def fetch_cadvisor_stats_from_prometheus(prom, container_ip, start_ts, end_ts):
    metrics = prom.get_label_values("__name__")
    # print(metrics)
    start_timestamp = datetime.utcfromtimestamp(start_ts / 1e9)
    end_timestamp = datetime.fromtimestamp(end_ts / 1e9)

    # container_network_transmit_bytes_total{container_label_com_kurtosistech_private_ip = "212.209.64.2"}
    kurtosis_ip_template = "container_label_com_kurtosistech_private_ip"

    cpu = prom.custom_query_range(f"container_cpu_load_average_10s{{{kurtosis_ip_template} "
                                        f"= '{container_ip}'}}", start_time=start_timestamp,
                                  end_time=end_timestamp, step="1s")
    cpu = [float(cpu[0]['values'][i][1]) for i in range(len(cpu[0]['values']))]

    mem = prom.custom_query_range(f"container_memory_usage_bytes{{{kurtosis_ip_template} "
                                        f"= '{container_ip}'}}", start_time=start_timestamp,
                                  end_time=end_timestamp, step="1s")
    mem = [int(mem[0]['values'][i][1]) for i in range(len(mem[0]['values']))]

    net_in = prom.custom_query_range(f"container_network_receive_bytes_total{{{kurtosis_ip_template}"
                                           f"= '{container_ip}'}}", start_time=start_timestamp,
                                     end_time=end_timestamp, step="1s")
    net_in = [int(net_in[0]['values'][i][1]) for i in range(len(net_in[0]['values']))]

    net_out = prom.custom_query_range(f"container_network_transmit_bytes_total{{{kurtosis_ip_template} "
                                            f"= '{container_ip}'}}", start_time=start_timestamp,
                                      end_time=end_timestamp, step="1s")
    net_out = [int(net_out[0]['values'][i][1]) for i in range(len(net_out[0]['values']))]

    return {'cpu_usage': cpu, 'memory_usage': mem, 'bandwidth_in': net_in, 'bandwidth_out': net_out}
