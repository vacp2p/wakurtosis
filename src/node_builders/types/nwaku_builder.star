# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku_builder = import_module(vars.WAKU_BUILDER_MODULE)
files = import_module(vars.FILE_HELPERS_MODULE)


def prepare_nwaku_service(nwakunode_names, all_services, config_files, artifact_ids, service_id,
                          network_topology):
    prepared_ports = waku_builder.prepare_waku_ports_in_service(nwakunode_names, network_topology)
    prepared_files = waku_builder.prepare_waku_config_files_in_service(nwakunode_names,
                                                                       artifact_ids)
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
        prepared_cmd += vars.NWAKU_ENTRYPOINT + " "
        prepared_cmd += vars.WAKUNODE_CONFIGURATION_FILE_FLAG + \
                        vars.CONTAINER_NODE_CONFIG_FILE_LOCATION + \
                        nwakunode_names[i] + "/" + config_files[i] + " "
        prepared_cmd += vars.WAKUNODE_PORT_SHIFT_FLAG + \
                        str(network_topology[vars.GENNET_NODES_KEY][nwakunode_names[i]][
                                vars.GENNET_PORT_SHIFT_KEY])
        if i != len(nwakunode_names) - 1:
            prepared_cmd += " & "

    return [prepared_cmd]


def instantiate_bootstrap_nwaku(plan, node_name, config_file, testing):
    prepared_ports = {}
    prepared_ports[vars.WAKU_RPC_PORT_ID + vars.ID_STR_SEPARATOR + node_name] = \
        PortSpec(number=vars.WAKU_RPC_PORT_NUMBER,
                 transport_protocol=vars.WAKU_RPC_PORT_PROTOCOL)

    prepared_ports[vars.PROMETHEUS_PORT_ID + vars.ID_STR_SEPARATOR + node_name] = \
        PortSpec(number=vars.PROMETHEUS_PORT_NUMBER,
                 transport_protocol=vars.PROMETHEUS_PORT_PROTOCOL)

    prepared_ports[vars.WAKU_LIBP2P_PORT_ID + vars.ID_STR_SEPARATOR + node_name] = \
        PortSpec(number=vars.WAKU_LIBP2P_PORT,
                 transport_protocol=vars.WAKU_LIBP2P_PORT_PROTOCOL)

    prepared_ports[vars.WAKU_DISCV5_PORT_ID + vars.ID_STR_SEPARATOR + node_name] = \
        PortSpec(number=vars.WAKU_DISCV5_PORT_NUMBER,
                 transport_protocol=vars.WAKU_DISCV5_PORT_PROTOCOL)

    artifact_id = files.get_toml_configuration_artifact(plan, config_file, "bootstrap-toml", testing)
    prepared_files = waku_builder.prepare_waku_config_files_in_service([node_name],
                                                                       [artifact_id])
    prepared_cmd = ""
    prepared_cmd += vars.NWAKU_ENTRYPOINT + " "
    # todo Change invalid address in discv5
    #prepared_cmd += vars.WAKUNODE_CONFIGURATION_FILE_FLAG + \
    #                vars.CONTAINER_NODE_CONFIG_FILE_LOCATION + node_name + "/" + config_file

    add_service_config = ServiceConfig(
        image=vars.NWAKU_IMAGE,
        ports=prepared_ports,
        files=prepared_files,
        entrypoint=vars.GENERAL_ENTRYPOINT,
        cmd=[prepared_cmd]
    )

    service = plan.add_service(
        service_name="node-bootstrap",
        config=add_service_config
    )

    return service

