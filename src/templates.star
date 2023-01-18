# GRAFANA
def get_prometheus_template_content_for_grafana():
    # template
    prometheus_template = """
        apiVersion: 1
        datasources:
            - name: Prometheus
              type: prometheus
              access: proxy
              org_id: 1
              url: http://{{.prometheus_url}}
              is_default: true
              version: 1
              editable: true
    """

    return prometheus_template

# PROMETHEUS
def  get_prometheus_template():
    # template
    template = """
    [
        {
            "labels": {
                "job": 
                "wakurtosis"
            }, 
            "targets" : {{.targets}} 
        }
    ]
    """

    return template

# WSL
def get_wsl_template():
    # Traffic simulation parameters
    wsl_yml_template = """
            general:

                debug_level : "DEBUG"

                targets_file : "./targets/targets.json"

                prng_seed : 0

                # Simulation time in seconds
                simulation_time : 1000

                # Message rate in messages per second
                msg_rate : 10

                # Packet size in bytes
                min_packet_size : 2
                max_packet_size : 1024

                # Packe size distribution
                # Values: uniform and gaussian
                dist_type : "gaussian"

                # Fraction (of the total number of nodes) that inject traffic
                # Values: [0., 1.]
                emitters_fraction : 0.5

                # Inter-message times
                # Values: uniform and poisson
                inter_msg_type : "uniform"
        """

    return wsl_yml_template
