# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")


def prepare_nomos_service(node_name, all_services, config_files, artifact_ids, service_id):
    prepared_ports = _prepare_nomos_ports_in_service(node_name)
    prepared_files = _prepare_nomos_config_files_in_service(node_name, artifact_ids)
    prepared_cmd = _prepare_nomos_cmd_in_service(node_name, config_files)

    add_service_config = ServiceConfig(
        image=vars.NOMOS_IMAGE,
        ports=prepared_ports,
        files=prepared_files,
        entrypoint=vars.GENERAL_ENTRYPOINT,
        cmd=prepared_cmd
    )

    all_services[service_id] = add_service_config


def _prepare_nomos_cmd_in_service(nomos_names, config_files):
    prepared_cmd = ""
    for i in range(len(nomos_names)):
        prepared_cmd += vars.NOMOS_ENTRYPOINT + " "
        prepared_cmd += vars.NOMOS_CONTAINER_CONFIG_FILE_LOCATION + " "
        # prepared_cmd += vars.NOMOS_PORT_SHIFT_FLAG + str(i)
        if i != len(nomos_names) - 1:
            prepared_cmd += " & "

    return [prepared_cmd]


def _prepare_nomos_ports_in_service(node_names):
    prepared_ports = {}
    for i in range(len(node_names)):
        prepared_ports[vars.RPC_PORT_ID + "_" + node_names[i]] = \
            PortSpec(number=vars.NOMOS_RPC_PORT_NUMBER + i,
                     transport_protocol=vars.NOMOS_RPC_PORT_PROTOCOL)

        prepared_ports[vars.PROMETHEUS_PORT_ID + "_" + node_names[i]] = \
            PortSpec(number=vars.PROMETHEUS_PORT_NUMBER + i,
                transport_protocol=vars.PROMETHEUS_PORT_PROTOCOL)

        prepared_ports[vars.NOMOS_LIBP2P_PORT_ID + "_" + node_names[i]] = \
            PortSpec(number=vars.NOMOS_LIBP2P_PORT + i,
                transport_protocol=vars.NOMOS_LIBP2P_PORT_PROTOCOL)

    return prepared_ports


def _prepare_nomos_config_files_in_service(node_names, artifact_ids):
    prepared_files = {}

    for i in range(len(node_names)):
        prepared_files[vars.CONTAINER_NODE_CONFIG_FILE_LOCATION + node_names[i]] = artifact_ids[i]

    return prepared_files


def add_nomos_ports_info_to_topology(network_topology, all_services_information, node_info, node_id):
    nomos_rpc_port_id = vars.RPC_PORT_ID + "_" + node_id
    libp2p_port_id = vars.NOMOS_LIBP2P_PORT_ID + "_" + node_id
    prometheus_port_id = vars.PROMETHEUS_PORT_ID + "_" + node_id

    network_topology[vars.GENNET_NODES_KEY][node_id][vars.PORTS_KEY] = {}
    _add_nomos_port(network_topology, all_services_information, node_id, node_info, nomos_rpc_port_id)
    _add_nomos_port(network_topology, all_services_information, node_id, node_info, libp2p_port_id)
    _add_nomos_port(network_topology, all_services_information, node_id, node_info, prometheus_port_id)


def _add_nomos_port(network_topology, all_services_information, node_id, node_info, port_id):
    network_topology[vars.GENNET_NODES_KEY][node_id][vars.PORTS_KEY][port_id] = \
        (all_services_information[node_info[vars.GENNET_NODE_CONTAINER_KEY]].ports[
             port_id].number,
         all_services_information[node_info[vars.GENNET_NODE_CONTAINER_KEY]].ports[
             port_id].transport_protocol)
