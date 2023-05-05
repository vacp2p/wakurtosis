

Mount:

1 - Logs folder (/simulation_data)

2 - Tomls (/tomls)

Example:

For Cadvisor infra:
- docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ -v $(pwd)/config/topology_generated:/tomls/ --add-host=host.docker.internal:host-gateway <image> -i=cadvisor -p <prometheus_port>

For container-proc infra:
- docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ -v $(pwd)/config/topology_generated:/tomls/ --add-host=host.docker.internal:host-gateway <image> -i=container-proc