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
                simulation_time : {{.simulation_time}} 

                # Message rate in messages per second
                msg_rate : {{.message_rate}} 

                # Packet size in bytes
                min_packet_size : {{.min_packet_size}} 
                max_packet_size : {{.max_packet_size}} 

                # Packe size distribution
                # Values: uniform and gaussian
                dist_type : {{.dist_type}} 

                # Fraction (of the total number of nodes) that inject traffic
                # Values: [0., 1.]
                emitters_fraction : {{.emitters_fraction}} 

                # Inter-message times
                # Values: uniform and poisson
                inter_msg_type : {{.inter_msg_type}} 
            """

    return wsl_yml_template