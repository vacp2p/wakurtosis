# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(system_variables.FILE_HELPERS_MODULE)
templates = import_module(system_variables.TEMPLATES_MODULE)

def create_config(num_nodes, num_topics, node_type, network_type, num_partitions, num_subnets):
    
    template_data = {"num_nodes": num_nodes, "num_topics" : num_topics, "node_type" : node_type, 
                    "network_type" : network_type, "num_partitions" : num_partitions, "num_subnets" : num_subnets}

    # Traffic simulation parameters
    gennet_yml_template = templates.get_gennet_template()

    artifact_id = render_templates(
        config={
            system_variables.CONTAINER_GENNET_CONFIGURATION_FILE_NAME: struct(
                template=gennet_yml_template,
                data=template_data,
            )
        }
    )
    
    return artifact_id

def init(num_nodes, num_topics, node_type, network_type, num_partitions, num_subnets):
    
    # Generate simulation config
    gennet_config = create_config(num_nodes, num_topics, node_type, network_type, num_partitions, num_subnets)

    gennet_service = add_service(
        service_id=system_variables.GENNET_SERVICE_ID,
        config=struct(
            image=system_variables.GENNET_IMAGE,
            ports={},
            files={
                system_variables.GENNET_CONFIG_PATH : gennet_config,
            },
        
            cmd=["python3", "gennet.py"]

        )
    )

    return gennet_service

