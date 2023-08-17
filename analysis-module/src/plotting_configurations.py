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
    "container_network_receive_bytes_total": {
        "title": "Total Netowrk IO (per node)",
        "y_label": "Bandwidth (MBytes)",
        "xtic_labels": [
            "Received (Rx)"
        ],
        "statistic": "max",
        "toMB": True
    },
    "container_network_transmit_bytes_total": {
        "title": "Total Netowrk IO (per node)",
        "y_label": "Bandwidth (MBytes)",
        "metric_name": [
            "container_network_transmit_bytes_total"
        ],
        "xtic_labels": [
            "Sent (Tx)"
        ],
        "statistic": "max",
        "toMB": True
    },
    "container_fs_reads_bytes_total": {
        "title": "Peak Disk IO (per node)",
        "y_label": "Disk IO (MBytes)",
        "metric_name": [
            "container_fs_reads_bytes_total"
        ],
        "xtic_labels": [
            "Read"
        ],
        "statistic": "max",
        "toMB": True
    },
    "container_fs_writes_bytes_total": {
        "title": "Peak Disk IO (per node)",
        "y_label": "Disk IO (MBytes)",
        "metric_name": [
            "container_fs_writes_bytes_total"
        ],
        "xtic_labels": [
            "Write"
        ],
        "statistic": "max",
        "toMB": True
    }
}
