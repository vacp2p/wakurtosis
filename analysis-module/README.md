

Mount:

1 - Logs folder (/simulation_data)

2 - Tomls (/tomls)

Example:

- docker run <image name> --net="host" -v wakurtosis_logs:/simulation_data/ topology_generated:/tomls/ -p <prometheus_port>
