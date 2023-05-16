

Mount:

1 - Logs folder (/simulation_data)

Run:
- docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ --add-host=host.docker.internal:host-gateway <image> <script> -p <prometheus_port> -i <infra_type>

Example:
- docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ --add-host=host.docker.internal:host-gateway analysis ./src/main.py -i container-proc
- docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ --add-host=host.docker.internal:host-gateway analysis ./src/main.py -i cadvisor -p 123456

To run tests:

- docker run --network "host" -v $(pwd)/wakurtosis_logs:/simulation_data/ --add-host=host.docker.internal:host-gateway <image> -m unittest discover -s tests -p "*.py"