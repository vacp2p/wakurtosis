# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)
templates = import_module(vars.TEMPLATES_MODULE)

def upload_config(plan, config_file, artifact_name):
    config_artifact = plan.upload_files(
        src=config_file,
        name=artifact_name
    )

    return config_artifact

def create_new_topology_information(plan, network_topology, network_artifact_name):
    template = """
        {{.information}}
    """
    info = {}
    info["information"] = json.encode(network_topology)

    artifact_id = plan.render_templates(
        config={
            vars.CONTAINER_TOPOLOGY_FILE_NAME_WLS: struct(
                template=template,
                data=info,
            )
        },
        name=network_artifact_name
    )

    return artifact_id


def create_cmd(config_file, prometheus_service):
    cmd = []
    config_file_name = config_file.split("/")[-1]

    cmd.append(vars.WLS_CONFIG_FILE_FLAG)
    cmd.append(vars.WLS_CONFIG_PATH + config_file_name)
    cmd.append(vars.WLS_TOPOLOGY_FILE_FLAG)
    cmd.append(vars.WLS_TOPOLOGY_PATH + vars.CONTAINER_TOPOLOGY_FILE_NAME_WLS)
    cmd.append("--prometheus-ip")
    cmd.append(prometheus_service.ip_address)
    cmd.append("--prometheus-port")
    cmd.append(str(prometheus_service.ports[vars.PROMETHEUS_PORT_ID].number))

    return cmd

def init(plan, network_topology, config_file, prometheus_service):
    
    # Generate simulation config
    config_artifact = upload_config(plan, config_file, vars.WLS_CONFIG_ARTIFACT_NAME)

    tomls_artifact = plan.upload_files(
        src = vars.NODE_CONFIG_FILE_LOCATION,
        name = vars.WLS_TOMLS_ARTIFACT_NAME,
    )

    # Get complete network topology information
    wls_topology = create_new_topology_information(plan, network_topology,
                                                   vars.WLS_TOPOLOGY_ARTIFACT_NAME)

    wls_cmd = create_cmd(config_file, prometheus_service)

    add_service_config = ServiceConfig(
        image=vars.WLS_IMAGE,
        ports={},
        files={
            vars.WLS_CONFIG_PATH: config_artifact,
            vars.WLS_TOMLS_PATH: tomls_artifact,
            vars.WLS_TOPOLOGY_PATH: wls_topology
        },
        cmd=wls_cmd
    )
    wls_service = plan.add_service(
        service_name=vars.WLS_SERVICE_NAME,
        config=add_service_config
    )

    return wls_service
