# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")


def get_toml_configuration_artifact(wakunode_name, same_toml_configuration, artifact_id=""):
    if same_toml_configuration:
        artifact_id = upload_files(
            src=system_variables.GENERAL_TOML_CONFIGURATION_PATH,
            artifact_id=artifact_id
        )
        file_name = system_variables.GENERAL_TOML_CONFIGURATION_NAME
    else:
        artifact_id = upload_files(
            src=system_variables.WAKU_CONFIGURATION_FILES_LOCATION +
                wakunode_name +
                system_variables.WAKU_CONFIGURATION_FILE_EXTENSION,
            artifact_id=artifact_id
        )
        file_name = wakunode_name + system_variables.WAKU_CONFIGURATION_FILE_EXTENSION

    return artifact_id, file_name


def generate_template_targets_with_port(services, port_id):
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
