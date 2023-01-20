# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(system_variables.FILE_HELPERS_MODULE)
templates = import_module(system_variables.TEMPLATES_MODULE)

def create_wsl_config(simulation_time, message_rate, min_packet_size, max_packet_size, inter_msg_type, dist_type, emitters_fraction):
    
    template_data = {"simulation_time": simulation_time, "message_rate" : message_rate, "min_packet_size" : min_packet_size, 
                    "max_packet_size" : max_packet_size, "dist_type" : dist_type, "emitters_fraction" : emitters_fraction, "inter_msg_type" : inter_msg_type}

    # Traffic simulation parameters
    wsl_yml_template = templates.get_wsl_template()

    artifact_id = render_templates(
        config={
            system_variables.CONTAINER_WSL_CONFIGURATION_FILE_NAME: struct(
                template=wsl_yml_template,
                data=template_data,
            )
        }
    )
    
    return artifact_id

def create_targets(services):
    
    # Get private ip and ports of all nodes
    template_data = files.generate_template_node_targets(services, system_variables.WAKU_RPC_PORT_ID)

    # Template
    template = """
        {{.targets}}
    """

    artifact_id = render_templates(
        config={
            system_variables.CONTAINER_TARGETS_FILE_NAME_WSL: struct(
                template=template,
                data=template_data,
            )
        }
    )

    return artifact_id

def init(services, simulation_time, message_rate, min_packet_size, max_packet_size, inter_msg_type, dist_type, emitters_fraction):
    
    # Generate simulation config
    wsl_config = create_config(simulation_time, message_rate, min_packet_size, max_packet_size, inter_msg_type, dist_type, emitters_fraction)

    # Create targets.json
    wsl_targets = create_targets(services)

    wsl_service = add_service(
        service_id=system_variables.WSL_SERVICE_ID,
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

    return wsl_service

