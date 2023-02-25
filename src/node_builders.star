# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(vars.WAKU_MODULE)
nomos = import_module(vars.NOMOS_MODULE)
files = import_module(vars.FILE_HELPERS_MODULE)


def prepare_nwaku_service(plan, nwakunode_name, all_services, use_general_configuration):
    artifact_id, configuration_file = files.get_toml_configuration_artifact(plan, nwakunode_name,
                                                                            use_general_configuration,
                                                                            nwakunode_name)

    plan.print("Configuration being used file is " + configuration_file)

    add_service_config = ServiceConfig(
        image=system_variables.NWAKU_IMAGE,
        ports={
            system_variables.WAKU_RPC_PORT_ID: PortSpec(number=system_variables.WAKU_TCP_PORT,
                                                        transport_protocol="TCP"),
            system_variables.PROMETHEUS_PORT_ID: PortSpec(
                number=system_variables.PROMETHEUS_TCP_PORT,
                transport_protocol="TCP"),
            system_variables.WAKU_LIBP2P_PORT_ID: PortSpec(
                number=system_variables.WAKU_LIBP2P_PORT,
                transport_protocol="TCP"),
        },
        files={
            system_variables.CONTAINER_NODE_CONFIG_FILE_LOCATION: artifact_id
        },
        entrypoint=system_variables.NWAKU_ENTRYPOINT,
        cmd=[
            "--config-file=" + system_variables.CONTAINER_NODE_CONFIG_FILE_LOCATION + "/" + configuration_file
        ]
    )

    all_services[nwakunode_name] = add_service_config



def prepare_gowaku_service(plan, gowakunode_name, all_services, use_general_configuration):
    artifact_id, configuration_file = files.get_toml_configuration_artifact(plan, gowakunode_name,
                                                                            use_general_configuration,
                                                                            gowakunode_name)

    plan.print("Configuration being used file is " + configuration_file)
    plan.print("Entrypoint is "+ str(system_variables.GOWAKU_ENTRYPOINT))

    add_service_config = ServiceConfig(
        image=system_variables.GOWAKU_IMAGE,
        ports={
            system_variables.WAKU_RPC_PORT_ID: PortSpec(number=system_variables.WAKU_TCP_PORT,
                                                        transport_protocol="TCP"),
            system_variables.PROMETHEUS_PORT_ID: PortSpec(
                number=system_variables.PROMETHEUS_TCP_PORT,
                transport_protocol="TCP"),
            system_variables.WAKU_LIBP2P_PORT_ID: PortSpec(
                number=system_variables.WAKU_LIBP2P_PORT,
                transport_protocol="TCP"),
        },
        files={
            system_variables.CONTAINER_NODE_CONFIG_FILE_LOCATION: artifact_id
        },
        entrypoint=system_variables.GOWAKU_ENTRYPOINT,
        cmd=[
            "--config-file=" + system_variables.CONTAINER_NODE_CONFIG_FILE_LOCATION + "/" + configuration_file
        ]
    )

    all_services[gowakunode_name] = add_service_config


def prepare_nomos_service(node_name, all_services, config_file, artifact_id):
    nomos_service_config = ServiceConfig(
	image=vars.NOMOS_IMAGE,
	ports={
	    vars.NOMOS_HTTP_PORT_ID: PortSpec(number=vars.NOMOS_HTTP_PORT,
	    					    transport_protocol="TCP"),
	    vars.PROMETHEUS_PORT_ID: PortSpec(
	        number=vars.PROMETHEUS_TCP_PORT,
	        transport_protocol="TCP"),
	    vars.NOMOS_LIBP2P_PORT_ID: PortSpec(
	        number=vars.NOMOS_LIBP2P_PORT,
	        transport_protocol="TCP"),
	},
	files={
	    vars.CONTAINER_NODE_CONFIG_FILE_LOCATION: artifact_id
	},
	entrypoint=vars.NOMOS_ENTRYPOINT,
	cmd=[
	    vars.NOMOS_CONTAINER_CONFIG_FILE_LOCATION 
	]
    )

    all_services[node_name] = nomos_service_config


def interconnect_nodes(plan, topology_information, services, interconnection_batch):
    for waku_service_name in services.keys():
        peers = topology_information[waku_service_name]["static_nodes"]

        for i in range(0, len(peers), interconnection_batch):
            x = i
            image = services[waku_service_name]["image"]
            create_id = service_dispatcher[image].create_id
            connect_peers = service_dispatcher[image].connect_peers
            peer_ids = [create_id(services[peer]) for peer in peers[x:x + interconnection_batch]]

            connect_peers(plan, waku_service_name, vars.WAKU_RPC_PORT_ID, peer_ids)


def instantiate_services(plan, network_topology, testing):
    """
    As we will need to access for the service information later, the structure is the following:

    services = {
        "nwaku_0": {
            "peer_id" : peer id of the node, as string,
            "service_info": Kurtosis service struct, that has
                "ip": ip of the service that is running the node,
                "ports": Kurtosis PortSpec, that you can access with their respective identifier
        },
        "nwaku_1": {...},
        "gowaku_": {...}

    }

    Example:

    service_peer_id = services["nwaku_0"]["peer_id"]
    service_ip = services["nwaku_0"]["service_info"].ip_address
    rpc_node_number = services["nwaku_0"]["service_info"].ports["your_rpc_identifier"].number
    rpc_node_protocol = services["nwaku_0"]["service_info"].ports["your_rpc_identifier"].protocol
    """

    all_services = {}

    # Get up all nodes
    for service_name in network_topology.keys():
        image = network_topology[service_name]["image"]

        service_builder = service_dispatcher[image].prepare_service

        service_builder(plan, service_name, all_services, use_general_configuration)

    all_services_information = plan.add_services(
        configs = all_services
    )
    services_information = add_service_information(plan, all_services_information, network_topology)

    return services_information


def add_service_information(plan, all_services_information, network_topology):
    new_services_information = {}

    for service_name in all_services_information:
        image = network_topology[service_name]["image"]
        info_getter = service_dispatcher[image].add_service_information
	service_info = all_services_information[service_name]
	new_service_info = info_getter(plan, service_name, service_info)
	new_service_info["image"] = image
	new_services_information[service_name] = new_service_info

    return new_services_information


def _add_waku_service_information(plan, service_name, service_info):
    node_peer_id = waku.get_wakunode_peer_id(plan, service_name, vars.WAKU_RPC_PORT_ID)
    new_service_info = {}
    new_service_info["peer_id"] = node_peer_id
    new_service_info["service_info"] = service_info

    return new_service_info


def _add_nomos_service_information(plan, service_name, service_info):
    node_peer_id = nomos.get_nomos_peer_id(plan, service_name, vars.NOMOS_HTTP_PORT_ID)
    new_service_info = {}
    new_service_info["peer_id"] = node_peer_id
    new_service_info["service_info"] = service_info

    return new_service_info


service_dispatcher = {
    "go-waku": struct(
        prepare_service = prepare_gowaku_service,
        add_service_information = _add_waku_service_information,
        create_id = waku.create_waku_id,
        connect_peers = waku.connect_wakunode_to_peers
    ),
    "nim-waku": struct(
        prepare_service = prepare_gowaku_service,
        add_service_information = _add_waku_service_information,
        create_id = waku.create_waku_id,
        connect_peers = waku.connect_wakunode_to_peers
    ),
    "nomos": struct(
        prepare_service = prepare_nomos_service,
        add_service_information = _add_nomos_service_information,
        create_id = nomos.create_nomos_id,
        connect_peers = nomos.connect_nomos_to_peers
    ),
}
