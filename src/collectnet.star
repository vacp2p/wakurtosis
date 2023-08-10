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
            vars.CONTAINER_COLLECTNET_NETDATA_FILE_NAME : struct(
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

    cmd.append(vars.COLLECTNET_CONFIG_FILE_FLAG)
    cmd.append(vars.COLLECTNET_CONFIG_PATH + config_file_name)
    cmd.append(vars.COLLECTNET_NETDATA_FILE_FLAG)
    cmd.append(vars.COLLECTNET_NETDATA_PATH + vars.COLLECTNET_NETDATA_FILE_NAME)
    cmd.append("--prometheus-ip")
    cmd.append(prometheus_service.ip_address)
    cmd.append("--prometheus-port")
    cmd.append(str(prometheus_service.ports[vars.PROMETHEUS_PORT_ID].number))

    return cmd

def init(plan, network_topology, config_file, prometheus_service):
    # Generate simulation config
    config_artifact = upload_config(plan, config_file, vars.COLLECTNET_CONFIG_ARTIFACT_NAME)

    tomls_artifact = plan.upload_files(
        src = vars.NODE_CONFIG_FILE_LOCATION,
        #name = vars.COLLECTNET_TOMLS_ARTIFACT_NAME,
    )

    # Get complete network topology information
    collectnet_netdata = create_new_topology_information(plan, network_topology,
                                                   vars.COLLECTNET_NETDATA_ARTIFACT_NAME)

    collectnet_cmd = create_cmd(config_file, prometheus_service)

    add_service_config = ServiceConfig(
        image=vars.COLLECTNET_IMAGE,
        ports={},
        files={
            vars.COLLECTNET_CONFIG_PATH: config_artifact,
            #vars.COLLECTNET_TOMLS_PATH: tomls_artifact,
            vars.COLLECTNET_NETDATA_PATH: collectnet_netdata
        },
        cmd=collectnet_cmd
    )
    collectnet_service = plan.add_service(
        service_name=vars.COLLECTNET_SERVICE_NAME,
        config=add_service_config
    )

    return collectnet_service