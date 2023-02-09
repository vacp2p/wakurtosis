# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")


def get_toml_configuration_artifact(plan, wakunode_name, same_toml_configuration, name):
    if same_toml_configuration:
        artifact_id = plan.upload_files(
            src=system_variables.GENERAL_TOML_CONFIGURATION_PATH,
            name=name
        )
        file_name = system_variables.GENERAL_TOML_CONFIGURATION_NAME
    else:
        artifact_id = plan.upload_files(
            src=system_variables.NODE_CONFIG_FILE_LOCATION +
                wakunode_name +
                system_variables.NODE_CONFIGURATION_FILE_EXTENSION,
            name=name
        )
        file_name = wakunode_name + system_variables.NODE_CONFIGURATION_FILE_EXTENSION

    return artifact_id, file_name


def generate_template_node_targets(services, port_id):
    template_data = {}
    targets_data = []
    for service_name in services.keys():
        service_ip = services[service_name]["service_info"].ip_address
        service_port_number = str(services[service_name]["service_info"].ports[port_id].number)
        targets_data.append('"' + service_ip + ":" + service_port_number + '"')

    data_as_string = ",".join(targets_data)
    targets_payload = "[" + data_as_string + "]"
    template_data["targets"] = targets_payload

    return template_data


def generate_template_prometheus_url(prometheus_service):
    prometheus_url = prometheus_service.ip_address + ":" + str(
        prometheus_service.ports[system_variables.PROMETHEUS_PORT_ID].number)
    prometheus_info = {"prometheus_url": prometheus_url}

    return prometheus_info


def prepare_artifact_files_grafana(plan, artifact_config_name, artifact_customization_name,
                                   artifact_dashboard_name):
    config_id = plan.upload_files(
        src=system_variables.GRAFANA_CONFIGURATION_PATH,
        name=artifact_config_name
    )
    customization_id = plan.upload_files(
        src=system_variables.GRAFANA_CUSTOMIZATION_PATH,
        name=artifact_customization_name
    )
    dashboard_id = plan.upload_files(
        src=system_variables.GRAFANA_DASHBOARD_PATH,
        name=artifact_dashboard_name
    )

    return config_id, customization_id, dashboard_id


def prepare_artifact_folders_cadvisor(plan):
    root_id = plan.upload_files(
        src=system_variables.CONTAINER_ROOT_CADVISOR,
        #name=root_name
        name="root_name"
    )
    varrun_id = plan.upload_files(
        src=system_variables.CONTAINER_VARRUN_CADVISOR,
        name="varrun_name"
    )
    varlibdocker = plan.upload_files(
        src=system_variables.CONTAINER_VARLIBDOCKER_CADVISOR,
        name="varlibdocker_name"
    )
    devdisk_id = plan.upload_files(
        src=system_variables.CONTAINER_DEVDISK_CADVISOR,
        name="devdisk_name"
    )
    sys_id = plan.upload_files(
        src=system_variables.CONTAINER_SYS_CADVISOR,
        name="sys_name"
    )
    machineid_id = plan.upload_files(
        src=system_variables.CONTAINER_MACHINEID_CADVISOR,
        name="machineid_name"
    )
    wsl_id = plan.upload_files(
        src=system_variables.CADVISOR_WSL,
        name="wsl_name"
    )

    return root_id, varrun_id, varlibdocker, devdisk_id, sys_id, machineid_id, wsl_id