

Mount:

1 - Logs folder (/simulation_data)

2 - Tomls (/tomls)

Example:

- docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ --add-host=host.docker.internal:host-gateway <image> -p <prometheus_port>
