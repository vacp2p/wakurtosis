# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku_builder = import_module(vars.WAKU_BUILDER_MODULE)


def prepare_gowaku_service(gowakunode_name, all_services, config_files, artifact_ids, service_id):
    prepared_ports = waku_builder.prepare_waku_ports_in_service(gowakunode_name)
    prepared_files = waku_builder.prepare_waku_config_files_in_service(gowakunode_name, artifact_ids)
    prepared_cmd = _prepare_gowaku_cmd_in_service(gowakunode_name, config_files)

    add_service_config = ServiceConfig(
        image=vars.GOWAKU_IMAGE,
        ports=prepared_ports,
        files=prepared_files,
        entrypoint=vars.GENERAL_ENTRYPOINT,
        cmd=prepared_cmd
    )

    all_services[service_id] = add_service_config


def _prepare_gowaku_cmd_in_service(gowakunode_names, config_files):
    prepared_cmd = ""
    for i in range(len(gowakunode_names)):
        prepared_cmd += vars.GOWAKU_ENTRYPOINT + " "
        prepared_cmd += vars.WAKUNODE_CONFIGURATION_FILE_FLAG + \
                        vars.CONTAINER_NODE_CONFIG_FILE_LOCATION + \
                        gowakunode_names[i] + "/" + config_files[i] + " "
        prepared_cmd += vars.WAKUNODE_PORT_SHIFT_FLAG + str(i)
        if i != len(gowakunode_names) - 1:
            prepared_cmd += " & "

    return [prepared_cmd]