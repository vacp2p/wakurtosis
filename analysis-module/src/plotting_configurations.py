plotting_config = {
    "container_cpu_load_average_10s": {
        "title": "Peak CPU Usage (per node)",
        "y_label": "CPU Usage (%)",
        "statistic": "max",
        "toMB": False
    },
    "container_memory_usage_bytes": {
        "title": "Peak Memory Usage (per node)",
        "y_label": "Memory (MBytes)",
        "statistic": "max",
        "toMB": True
    },
    "cpu": {
        "title": "Peak CPU Usage (per node)",
        "y_label": "CPU Usage (%)",
        "metric_name": "container_cpu_load_average_10s",
        "statistic": "max",
        "toMB": False
    },
    "memory": {
        "title": "Peak Memory Usage (per node)",
        "y_label": "Memory (MBytes)",
        "metric_name": "container_memory_usage_bytes",
        "statistic": "max",
        "toMB": True
    },
    "bandwith": {
        "title": "Total Netowrk IO (per node)",
        "y_label": "Bandwidth (MBytes)",
        "metric_name": [
            "container_network_receive_bytes_total",
            "container_network_transmit_bytes_total"
        ],
        "xtic_labels": [
            "Received (Rx)",
            "Sent (Tx)"
        ],
        "toMB": True
    },
    "disk": {
        "title": "Peak Disk IO (per node)",
        "y_label": "Disk IO (MBytes)",
        "metric_name": [
            "container_fs_reads_bytes_total",
            "container_fs_writes_bytes_total"
        ],
        "xtic_labels": [
            "Read",
            "Write"
        ],
        "toMB": True
    }
}