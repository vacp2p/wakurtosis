# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku_builder = import_module(vars.WAKU_BUILDER_MODULE)


def prepare_nwaku_service(nwakunode_names, all_services, config_files, artifact_ids, service_id):
    prepared_ports = waku_builder.prepare_waku_ports_in_service(nwakunode_names)
    prepared_files = waku_builder.prepare_waku_config_files_in_service(nwakunode_names, artifact_ids)
    prepared_cmd = _prepare_nwaku_cmd_in_service(nwakunode_names, config_files)

    add_service_config = ServiceConfig(
        image=vars.NWAKU_IMAGE,
        ports=prepared_ports,
        files=prepared_files,
        entrypoint=vars.GENERAL_ENTRYPOINT,
        cmd=prepared_cmd
    )

    all_services[service_id] = add_service_config


def _prepare_nwaku_cmd_in_service(nwakunode_names, config_files):
    prepared_cmd = ""
    for i in range(len(nwakunode_names)):
        prepared_cmd += vars.NWAKU_ENTRYPOINT + " "
        prepared_cmd += vars.WAKUNODE_CONFIGURATION_FILE_FLAG + \
                        vars.CONTAINER_NODE_CONFIG_FILE_LOCATION + \
                        nwakunode_names[i] + "/" + config_files[i] + " "
        prepared_cmd += vars.WAKUNODE_PORT_SHIFT_FLAG + str(i)
        if i != len(nwakunode_names) - 1:
            prepared_cmd += " & "

    return [prepared_cmd]
