# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku_builder = import_module(vars.WAKU_BUILDER_MODULE)
files = import_module(vars.FILE_HELPERS_MODULE)


def prepare_nwaku_service(nwakunode_names, all_services, config_files, artifact_ids, run_artifact_id,
                          service_id, network_topology, discovery):
    prepared_ports = waku_builder.prepare_waku_ports_in_service(nwakunode_names, network_topology,
                                                                discovery)
    prepared_files = waku_builder.prepare_waku_config_files_in_service(nwakunode_names,
                                                                       artifact_ids, run_artifact_id)
    prepared_cmd = _prepare_nwaku_cmd_in_service(nwakunode_names, config_files, network_topology)

    add_service_config = ServiceConfig(
        image=vars.NWAKU_IMAGE,
        ports=prepared_ports,
        files=prepared_files,
        entrypoint=vars.GENERAL_ENTRYPOINT,
        cmd=prepared_cmd
    )

    all_services[service_id] = add_service_config


def _prepare_nwaku_cmd_in_service(nwakunode_names, config_files, network_topology):
    prepared_cmd = ""

    for i in range(len(nwakunode_names)):
        prepared_cmd += vars.CONTAINER_NODE_SCRIPT_RUN_LOCATION + vars.NWAKU_SCRIPT_ENTRYPOINT + " "

        prepared_cmd += vars.CONTAINER_NODE_CONFIG_FILE_LOCATION + nwakunode_names[i] + "/" + config_files[i] + " "

        prepared_cmd += str(network_topology[vars.GENNET_NODES_KEY][nwakunode_names[i]][vars.GENNET_PORT_SHIFT_KEY])

        if i != len(nwakunode_names) - 1:
            prepared_cmd += " & "

    return [prepared_cmd]
