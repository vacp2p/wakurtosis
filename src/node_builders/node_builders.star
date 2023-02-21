# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(vars.WAKU_MODULE)
files = import_module(vars.FILE_HELPERS_MODULE)
waku_builder = import_module(vars.WAKU_BUILDER_MODULE)
nwaku_builder = import_module(vars.NWAKU_BUILDER_MODULE)
gowaku_builder = import_module(vars.GOWAKU_BUILDER_MODULE)


service_builder_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: gowaku_builder.prepare_gowaku_service,
    vars.GENNET_NWAKU_IMAGE_VALUE: nwaku_builder.prepare_nwaku_service
    # nomos: nomos_builder.prepare_nomos_service
}

ports_dispatcher = {
    vars.GENNET_GOWAKU_IMAGE_VALUE: waku_builder._add_waku_ports_info_to_topology,
    vars.GENNET_NWAKU_IMAGE_VALUE: waku_builder._add_waku_ports_info_to_topology
    # nomos: nomos_builder._add_nomos_ports_info_to_topology
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


def _add_service_info_to_topology(plan, all_services_information, network_topology):
    for node_id, node_info in network_topology[vars.GENNET_NODES_KEY].items():
        node_rpc_port_id = vars.RPC_PORT_ID + "_" + node_id

        node_peer_id = waku.get_wakunode_peer_id(plan, node_info[vars.GENNET_NODE_CONTAINER_KEY],
                                                 node_rpc_port_id)

        network_topology[vars.GENNET_NODES_KEY][node_id][vars.PEER_ID_KEY] = node_peer_id

        network_topology[vars.GENNET_NODES_KEY][node_id][vars.IP_KEY] = \
            all_services_information[node_info[vars.GENNET_NODE_CONTAINER_KEY]].ip_address

        ports_adder = ports_dispatcher[node_info[vars.GENNET_IMAGE_KEY]]
        ports_adder(network_topology, all_services_information, node_info, node_id)
