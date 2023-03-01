# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)
templates = import_module(vars.TEMPLATES_MODULE)

def upload_config(plan, config_file):
    config_artifact = plan.upload_files(
        src=config_file,
        name="config_file"
    )

    return config_artifact

def create_targets(plan, services):
    
    # Get private ip and ports of all nodes
    template_data = files.generate_template_node_targets(services, vars.RPC_PORT_ID, "targets")

    # Template
    template = """
        {{.targets}}
    """

    artifact_id = plan.render_templates(
        config={
            vars.CONTAINER_TARGETS_FILE_NAME_WLS: struct(
                template=template,
                data=template_data,
            )
        },
        name="wls_targets"
    )

    return artifact_id

def create_new_topology_information(plan, network_topology):
    template = """
        {{.information}}
    """
    info = {}
    info["information"] = network_topology

    artifact_id = plan.render_templates(
        config={
            vars.CONTAINER_TOPOLOGY_FILE_NAME_WLS: struct(
                template=template,
                data=info,
            )
        },
        name="wls_topology"
    )

    return artifact_id


def init(plan, network_topology, config_file):
    
    # Generate simulation config
    config_artifact = upload_config(plan, config_file)

    tomls_artifact = plan.upload_files(
        src = vars.NODE_CONFIG_FILE_LOCATION,
        name = "tomls_artifact",
    )

    # Get complete network topology information
    wls_topology = create_new_topology_information(plan, network_topology)

    add_service_config = ServiceConfig(
        image=vars.WLS_IMAGE,
        ports={},
        files={
            vars.WLS_CONFIG_PATH: config_artifact,
            vars.WLS_TOMLS_PATH: tomls_artifact,
            vars.WLS_TOPOLOGY_PATH: wls_topology
        },
        cmd=vars.WLS_CMD
    )
    wls_service = plan.add_service(
        service_name=vars.WLS_SERVICE_NAME,
        config=add_service_config
    )

    return wls_service

