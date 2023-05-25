# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")


def prepare_waku_ports_in_service(node_names, network_topology, discovery):
    prepared_ports = {}

    for node_name in node_names:
        port_shift = network_topology[vars.GENNET_NODES_KEY][node_name][vars.GENNET_PORT_SHIFT_KEY]
        prepare_single_node_waku_ports(prepared_ports, node_name, port_shift, discovery)

    return prepared_ports


def prepare_single_node_waku_ports(prepared_ports, node_name, port_shift, discovery):
    prepared_ports[vars.WAKU_RPC_PORT_ID + vars.ID_STR_SEPARATOR + node_name] = \
        PortSpec(number=vars.WAKU_RPC_PORT_NUMBER + port_shift,
                 transport_protocol=vars.WAKU_RPC_PORT_PROTOCOL)

    prepared_ports[vars.PROMETHEUS_PORT_ID + vars.ID_STR_SEPARATOR + node_name] = \
        PortSpec(number=vars.PROMETHEUS_PORT_NUMBER + port_shift,
                 transport_protocol=vars.PROMETHEUS_PORT_PROTOCOL)

    prepared_ports[vars.WAKU_LIBP2P_PORT_ID + vars.ID_STR_SEPARATOR + node_name] = \
        PortSpec(number=vars.WAKU_LIBP2P_PORT + port_shift,
                 transport_protocol=vars.WAKU_LIBP2P_PORT_PROTOCOL)

    if discovery:
        prepared_ports[vars.WAKU_DISCV5_PORT_ID + vars.ID_STR_SEPARATOR + node_name] = \
            PortSpec(number=vars.WAKU_DISCV5_PORT_NUMBER + port_shift,
                     transport_protocol=vars.WAKU_DISCV5_PORT_PROTOCOL)


def prepare_waku_config_files_in_service(node_names, artifact_ids):
    prepared_files = {}

    for i in range(len(node_names)):
        prepared_files[vars.CONTAINER_NODE_CONFIG_FILE_LOCATION + node_names[i]] = artifact_ids[i]

    return prepared_files


def add_waku_ports_info_to_topology(network_topology, all_services_information, node_info, node_id):
    waku_rpc_port_id = vars.WAKU_RPC_PORT_ID + vars.ID_STR_SEPARATOR + node_id
    libp2p_port_id = vars.WAKU_LIBP2P_PORT_ID + vars.ID_STR_SEPARATOR + node_id
    prometheus_port_id = vars.PROMETHEUS_PORT_ID + vars.ID_STR_SEPARATOR + node_id

    network_topology[vars.GENNET_NODES_KEY][node_id][vars.PORTS_KEY] = {}
    _add_waku_port(network_topology, all_services_information, node_id, node_info, waku_rpc_port_id)
    _add_waku_port(network_topology, all_services_information, node_id, node_info, libp2p_port_id)
    _add_waku_port(network_topology, all_services_information, node_id, node_info,
                   prometheus_port_id)


def _add_waku_port(network_topology, all_services_information, node_id, node_info, port_id):
    network_topology[vars.GENNET_NODES_KEY][node_id][vars.PORTS_KEY][port_id] = \
        (all_services_information[node_info[vars.GENNET_NODE_CONTAINER_KEY]].ports[
             port_id].number,
         all_services_information[node_info[vars.GENNET_NODE_CONTAINER_KEY]].ports[
             port_id].transport_protocol)
