# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")


def prepare_waku_ports_in_service(wakunode_names):
    prepared_ports = {}
    for i in range(len(wakunode_names)):
        prepared_ports[vars.RPC_PORT_ID + "_" + wakunode_names[i]] = \
            PortSpec(number=vars.WAKU_RPC_PORT_NUMBER + i,
                     transport_protocol=vars.WAKU_RPC_PORT_PROTOCOL)

        prepared_ports[vars.PROMETHEUS_PORT_ID + "_" + wakunode_names[i]] = \
            PortSpec(number=vars.PROMETHEUS_PORT_NUMBER + i,
                transport_protocol=vars.PROMETHEUS_PORT_PROTOCOL)

        prepared_ports[vars.WAKU_LIBP2P_PORT_ID + "_" + wakunode_names[i]] = \
            PortSpec(number=vars.WAKU_LIBP2P_PORT + i,
                transport_protocol=vars.WAKU_LIBP2P_PORT_PROTOCOL)

    return prepared_ports


def _add_waku_ports_info_to_topology(network_topology, all_services_information, node_info, node_id):
    waku_rpc_port_id = vars.RPC_PORT_ID + "_" + node_id
    libp2p_port_id = vars.WAKU_LIBP2P_PORT_ID + "_" + node_id
    prometheus_port_id = vars.PROMETHEUS_PORT_ID + "_" + node_id

    _add_waku_port(network_topology, all_services_information, node_id, node_info, waku_rpc_port_id)
    _add_waku_port(network_topology, all_services_information, node_id, node_info, libp2p_port_id)
    _add_waku_port(network_topology, all_services_information, node_id, node_info, prometheus_port_id)


def _add_waku_port(network_topology, all_services_information, node_id, node_info, port_id):
    network_topology[vars.GENNET_NODES_KEY][node_id][vars.TOPOLOGY_PORTS_KEY] = {}
    network_topology[vars.GENNET_NODES_KEY][node_id][vars.TOPOLOGY_PORTS_KEY][port_id] = \
        (all_services_information[node_info[vars.GENNET_NODE_CONTAINER_KEY]].ports[
             port_id].number,
         all_services_information[node_info[vars.GENNET_NODE_CONTAINER_KEY]].ports[
             port_id].transport_protocol)