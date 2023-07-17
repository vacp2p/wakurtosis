# Python Imports
import json
from prometheus_api_client import PrometheusConnect


def connect_to_prometheus(ip, port):
    print(f"Connecting to {ip}:{port}")
    url = f"http://{ip}:{port}"
    try:
        prometheus = PrometheusConnect(url, disable_ssl=True)
    except Exception as e:
        print("Cannot connect to Prometheus Service")
        print(e)
        return None

    return prometheus


def dump_prometheus(config, prometheus_ip, prometheus_port):
    to_query = config["plotting"]["by_node"]

    to_query = "|".join(to_query)

    print(to_query)

    prometheus_connection = connect_to_prometheus(prometheus_ip, prometheus_port)

    query = f"{{__name__=~\"{to_query}\"}}"
    print(query)

    metrics = prometheus_connection.custom_query(query)

    with open("/wls/prometheus_data.json", "w") as out_file:
        json.dump(metrics, out_file)
