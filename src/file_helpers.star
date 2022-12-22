# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")


def get_toml_configuration_artifact(wakunode_name, same_toml_configuration):
    if same_toml_configuration:
        artifact_id = upload_files(
            src=system_variables.GENERAL_TOML_CONFIGURATION_PATH
        )
        file_name = system_variables.GENERAL_TOML_CONFIGURATION_NAME
    else:
        artifact_id = upload_files(
            src="github.com/logos-co/wakurtosis/config/waku_config_files/" + wakunode_name + ".toml"
        )
        file_name = wakunode_name + ".toml"

    return artifact_id, file_name


def generate_template_data(services):
    template_data = {}
    node_data = []
    for wakunode_name in services.keys():
        node_data.append(
            '"' + services[wakunode_name]["service_info"].ip_address + ":" + str(
                services[wakunode_name]["service_info"].ports[
                    system_variables.PROMETHEUS_PORT_ID].number) + '"')

    data_as_string = ",".join(node_data)
    test = "[" + data_as_string + "]"

    template_data["targets"] = test

    return template_data
