# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)
dispatchers = import_module(vars.DISPATCHERS_MODULE)

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
                    "rpc-node_0": (port_number, port_protocol)
                    "libp2p-node_0": (port_number, port_protocol),
                    "prometheus-node_0": (port_number, port_protocol)
                }
            },
            "node_1": {...}
        }
    }
    """
    all_services_configuration = {}

    for service_id, nodes_in_service in network_topology[vars.GENNET_ALL_CONTAINERS_KEY].items():
        image = network_topology[vars.GENNET_NODES_KEY][nodes_in_service[0]][vars.GENNET_IMAGE_KEY]
        service_builder = dispatchers.service_builder_dispatcher[image]

        # Get all config file names needed
        config_file_names = [network_topology[vars.GENNET_NODES_KEY][node][vars.GENNET_CONFIG_KEY]
                             for node in nodes_in_service]

        config_files_artifact_ids = [
            files.get_toml_configuration_artifact(plan, config_file_name, service_name, testing)
            for config_file_name, service_name
            in zip(config_file_names, nodes_in_service)
        ]

        service_builder(nodes_in_service, all_services_configuration, config_file_names,
                        config_files_artifact_ids, service_id, network_topology)

    all_services_information = plan.add_services(
        configs=all_services_configuration
    )

    plan.print("Subnets: Greetings...")
    subnets = network_topology[vars.GENNET_SUBNETS_KEY].keys()
    plan.print(subnets)

    i = 0
    for src in subnets:
        src_dict = network_topology[vars.GENNET_SUBNETS_KEY][src]
        plan.print(src_dict)
        for dst in src_dict.keys():
            skip = False
            QoS_spec = network_topology[vars.GENNET_SUBNETS_KEY][dst][src]
            i = i + 1
            s = src + ":" + dst + "->" + QoS_spec
            QoS_lst = QoS_spec.split(":")
            packet_loss_perc, dist, delay = float(QoS_lst[0]), QoS_lst[1], int(QoS_lst[2])
            plan.print(s + " = " + str(len(QoS_lst)))
            if dist == "Uniform":
                delay_distribution = UniformPacketDelayDistribution(ms=delay)
            elif dist == "Normal":
                mean, std_dev, corr = delay, int(QoS_lst[3]), float(QoS_lst[4])
                delay_distribution = NormalPacketDelayDistribution(
                        mean_ms=delay, std_dev_ms=std_dev, correlation=corr)
            elif dist == "None":
                skip = True
            else:
                plan.print("Subnets: Invalid delay distribution: "+dist)
                plan.exit()
            if not skip:
                connection_config = ConnectionConfig(packet_loss_perc, delay_distribution)
                plan.set_connection(
                    subnetworks = (src, dst),
                    config = connection_config,
                )
    _add_service_info_to_topology(plan, all_services_information, network_topology)


def interconnect_nodes(plan, topology_information, interconnection_batch):
    # Interconnect them
    nodes_in_topology = topology_information[vars.GENNET_NODES_KEY]

    for node_id in nodes_in_topology.keys():
        image = nodes_in_topology[node_id][vars.GENNET_IMAGE_KEY]
        peers = nodes_in_topology[node_id][vars.GENNET_STATIC_NODES_KEY]
        create_node_multiaddress = dispatchers.service_multiaddr_dispatcher[image]
        connect_node_to_peers = dispatchers.service_connect_dispatcher[image]

        for i in range(0, len(peers), interconnection_batch):
            peer_ids = [create_node_multiaddress(peer, nodes_in_topology[peer])
                        for peer in peers[i:i + interconnection_batch]]

            connect_node_to_peers(plan, nodes_in_topology[node_id][vars.GENNET_NODE_CONTAINER_KEY],
                                      node_id, vars.RPC_PORT_ID, peer_ids)



def _add_service_info_to_topology(plan, all_services_information, network_topology):
    for node_id, node_info in network_topology[vars.GENNET_NODES_KEY].items():
        node_rpc_port_id = vars.RPC_PORT_ID + vars.ID_STR_SEPARATOR + node_id

        image = network_topology[vars.GENNET_NODES_KEY][node_id][vars.GENNET_IMAGE_KEY]
        peer_id_getter = dispatchers.service_info_dispatcher[image]
        node_peer_id = peer_id_getter(plan, node_info[vars.GENNET_NODE_CONTAINER_KEY],
                                                 node_rpc_port_id)

        network_topology[vars.GENNET_NODES_KEY][node_id][vars.PEER_ID_KEY] = node_peer_id

        network_topology[vars.GENNET_NODES_KEY][node_id][vars.IP_KEY] = \
            all_services_information[node_info[vars.GENNET_NODE_CONTAINER_KEY]].ip_address

        ports_adder = dispatchers.ports_dispatcher[node_info[vars.GENNET_IMAGE_KEY]]
        ports_adder(network_topology, all_services_information, node_info, node_id)

    for container_id, container_info in network_topology[vars.GENNET_ALL_CONTAINERS_KEY].items():
        nodes = container_info
        ip = network_topology[vars.GENNET_NODES_KEY][nodes[0]][vars.IP_KEY]
        network_topology[vars.GENNET_ALL_CONTAINERS_KEY][container_id] = {}
        network_topology[vars.GENNET_ALL_CONTAINERS_KEY][container_id][vars.GENNET_NODES_KEY] = nodes
        network_topology[vars.GENNET_ALL_CONTAINERS_KEY][container_id][vars.KURTOSIS_IP_KEY] = ip
