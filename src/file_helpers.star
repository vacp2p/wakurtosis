# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")


def get_toml_configuration_artifact(plan, config_file, name, testing):
    plan.print("Configuration being used file is " + config_file)

    if testing:
        artifact_id = plan.upload_files(
            src=vars.TEST_FILES_LOCATION + config_file,
            name=name
        )
    else:
        artifact_id = plan.upload_files(
            src=vars.NODE_CONFIG_FILE_LOCATION + config_file,
            name=name
        )

    return artifact_id


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
        prometheus_service.ports[vars.PROMETHEUS_PORT_ID].number)
    prometheus_info = {"prometheus_url": prometheus_url}

    return prometheus_info


def prepare_artifact_files_grafana(plan, artifact_config_name, artifact_customization_name,
                                   artifact_dashboard_name):
    config_id = plan.upload_files(
        src=vars.GRAFANA_CONFIGURATION_PATH,
        name=artifact_config_name
    )
    customization_id = plan.upload_files(
        src=vars.GRAFANA_CUSTOMIZATION_PATH,
        name=artifact_customization_name
    )
    dashboard_id = plan.upload_files(
        src=vars.GRAFANA_DASHBOARD_PATH,
        name=artifact_dashboard_name
    )

    return config_id, customization_id, dashboard_id
