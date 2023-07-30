Mount:

1 - Logs folder (/simulation_data)

Run:
- `docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ --add-host=host.docker.internal:host-gateway <image> <script> -p <prometheus_port> -i <infra_type>`

Example:
- `docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ --add-host=host.docker.internal:host-gateway analysis ./src/main.py -i container-proc`
- `docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ --add-host=host.docker.internal:host-gateway analysis ./src/main.py -i cadvisor -p 123456`

To run tests:

- `docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/
  --add-host=host.docker.internal:host-gateway <image> -m unittest discover -s tests -p "*.py"`

## Plotting configuration

The configuration is set in `config.json`, inside "plotting" keyword.

The name of the metric should be the same metric that lives inside Prometheus. This is, any cAdvisor and Waku exposed metric.

```json
{
  "plotting": {
    "by_node": [
      "container_cpu_load_average_10s",
      "container_memory_usage_bytes",
      "container_network_receive_bytes_total",
      "container_network_transmit_bytes_total",
      "container_fs_reads_bytes_total",
      "container_fs_writes_bytes_total"
    ]
  }
}
```

`by_node`: This means that the metric will be gathered for each node, getting the distribution of the maximum values in the entire simulation.

`by simulation`: This means that we will get an accumulated value across the entire simulation. **deprecated**
