# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(vars.WAKU_MODULE)
nomos = import_module(vars.NOMOS_MODULE)
files = import_module(vars.FILE_HELPERS_MODULE)
waku_builder = import_module(vars.WAKU_BUILDER_MODULE)
nwaku_builder = import_module(vars.NWAKU_BUILDER_MODULE)
gowaku_builder = import_module(vars.GOWAKU_BUILDER_MODULE)
nomos_builder = import_module(vars.NOMOS_BUILDER_MODULE)


service_builder_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: gowaku_builder.prepare_gowaku_service,
    vars.GENNET_NWAKU_IMAGE_VALUE: nwaku_builder.prepare_nwaku_service,
    vars.GENNET_NOMOS_IMAGE_VALUE: nomos_builder.prepare_nomos_service
}

service_info_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: waku.get_wakunode_peer_id,
    vars.GENNET_NWAKU_IMAGE_VALUE: waku.get_wakunode_peer_id,
    vars.GENNET_NOMOS_IMAGE_VALUE: nomos.get_nomos_peer_id
}

service_multiaddr_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: waku.create_node_multiaddress,
    vars.GENNET_NWAKU_IMAGE_VALUE: waku.create_node_multiaddress,
    vars.GENNET_NOMOS_IMAGE_VALUE: nomos.create_node_multiaddress
}

service_connect_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: waku.connect_wakunode_to_peers,
    vars.GENNET_NWAKU_IMAGE_VALUE: waku.connect_wakunode_to_peers,
    vars.GENNET_NOMOS_IMAGE_VALUE: nomos.connect_nomos_to_peers
}

ports_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: waku_builder._add_waku_ports_info_to_topology,
    vars.GENNET_NWAKU_IMAGE_VALUE: waku_builder._add_waku_ports_info_to_topology,
    vars.GENNET_NOMOS_IMAGE_VALUE: nomos_builder._add_nomos_ports_info_to_topology
}

def instantiate_services(plan, network_topology, testing):
    """
    As we will need to access for the service information later, we are adding Starlark info into
    the network topology.:

    network_topology = {
        "containers": [...],
        "nodes": {
            "node_0": {
                standard_gennet_info...,
                "peer_id" : peer id of the node, as string,
                "ip_address": ip of the container that has the node, as string
                "ports": {
                    "waku_rpc_node_0": (port_number, port_protocol)
                    "libp2p_node_0": (port_number, port_protocol),
                    "prometheus_node_0": (port_number, port_protocol)
                }
            },
            "node_1": {...}
        }

    }
    """
    all_services_configuration = {}

    for service_id, nodes_in_service in network_topology[vars.GENNET_ALL_CONTAINERS_KEY].items():
        image = network_topology[vars.GENNET_NODES_KEY][nodes_in_service[0]][vars.GENNET_IMAGE_KEY]
        service_builder = service_builder_dispatcher[image]

        # Get all config file names needed
        config_file_names = [network_topology[vars.GENNET_NODES_KEY][node][vars.GENNET_CONFIG_KEY]
                             for node in nodes_in_service]

        config_files_artifact_ids = [
            files.get_toml_configuration_artifact(plan, config_file_name, service_name, testing)
            for config_file_name, service_name
            in zip(config_file_names, nodes_in_service)
        ]

        service_builder(nodes_in_service, all_services_configuration, config_file_names,
                        config_files_artifact_ids, service_id)

    all_services_information = plan.add_services(
        configs=all_services_configuration
    )

    _add_service_info_to_topology(plan, all_services_information, network_topology)


def interconnect_nodes(plan, topology_information, interconnection_batch):
    # Interconnect them
    nodes_in_topology = topology_information[vars.GENNET_NODES_KEY]

    for node_id in nodes_in_topology.keys():
        image = nodes_in_topology[node_id][vars.GENNET_IMAGE_KEY]
        peers = nodes_in_topology[node_id][vars.GENNET_STATIC_NODES_KEY]
        create_node_multiaddress = service_multiaddr_dispatcher[image]
        connect_node_to_peers = service_connect_dispatcher[image]

        for i in range(0, len(peers), interconnection_batch):
            peer_ids = [create_node_multiaddress(peer, nodes_in_topology[peer])
                        for peer in peers[i:i + interconnection_batch]]

            connect_node_to_peers(plan, nodes_in_topology[node_id][vars.GENNET_NODE_CONTAINER_KEY],
                                      node_id, vars.RPC_PORT_ID, peer_ids)



def _add_service_info_to_topology(plan, all_services_information, network_topology):
    for node_id, node_info in network_topology[vars.GENNET_NODES_KEY].items():
        node_rpc_port_id = vars.RPC_PORT_ID + vars.ID_STR_SEPARATOR + node_id

        image = network_topology[vars.GENNET_NODES_KEY][node_id][vars.GENNET_IMAGE_KEY]
        peer_id_getter = service_info_dispatcher[image]
        node_peer_id = peer_id_getter(plan, node_info[vars.GENNET_NODE_CONTAINER_KEY],
                                                 node_rpc_port_id)

        network_topology[vars.GENNET_NODES_KEY][node_id][vars.PEER_ID_KEY] = node_peer_id

        network_topology[vars.GENNET_NODES_KEY][node_id][vars.IP_KEY] = \
            all_services_information[node_info[vars.GENNET_NODE_CONTAINER_KEY]].ip_address

        ports_adder = ports_dispatcher[node_info[vars.GENNET_IMAGE_KEY]]
        ports_adder(network_topology, all_services_information, node_info, node_id)
