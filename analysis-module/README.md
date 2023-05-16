

Mount:

1 - Logs folder (/simulation_data)

Example:

- docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ --add-host=host.docker.internal:host-gateway <image> <script> -p <prometheus_port>


To run tests:

- docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ --add-host=host.docker.internal:host-gateway <image> -m unittest discover -s tests -p "*.py"