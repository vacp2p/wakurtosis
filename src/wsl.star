# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(system_variables.FILE_HELPERS_MODULE)

def create_wsl_config(simulation_time=300, message_rate=50, min_packet_size=1, max_packet_size=1024, inter_msg_type='uniform', dist_type='uniform', emitters_fraction=0.5):
    
    template_data = {"simulation_time": simulation_time, "message_rate" : message_rate, "min_packet_size" : min_packet_size, 
                    "max_packet_size" : max_packet_size, "dist_type" : dist_type, "emitters_fraction" : emitters_fraction, "inter_msg_type" : inter_msg_type}

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

    artifact_id = render_templates(
        config={
            "wsl.yml": struct(
                template=wsl_yml_template,
                data=template_data,
            )
        }
    )
    
    return artifact_id

def create_wsl_targets(services):
    
    # Get private ip and ports of all nodes
    template_data = files.generate_template_targets_with_port(services, system_variables.WAKU_RPC_PORT_ID)

    # Template
    template = """
        {{.targets}}
    """

    artifact_id = render_templates(
        config={
            "targets.json": struct(
                template=template,
                data=template_data,
            )
        }
    )

    return artifact_id

def set_up_wsl(services, simulation_time, message_rate, min_packet_size, max_packet_size, inter_msg_type, dist_type, emitters_fraction):
    
    # Generate simulation config
    wsl_config = create_wsl_config(simulation_time, message_rate, min_packet_size, max_packet_size, inter_msg_type, dist_type, emitters_fraction)

    # Create targets.json
    wsl_targets = create_wsl_targets(services)

    wsl_service = add_service(
        service_id="wsl",
        config=struct(
            image=system_variables.WSL_IMAGE,
            ports={},
            files={
                system_variables.WSL_CONFIG_PATH : wsl_config,
                system_variables.WSL_TARGETS_PATH : wsl_targets,
            },
        
            cmd=["python3", "wsl.py"]

        )
    )

    print('kurtosis service logs wakurtosis SERVICE-GUID')
    
    return wsl_service