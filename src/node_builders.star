# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(vars.WAKU_MODULE)
files = import_module(vars.FILE_HELPERS_MODULE)


def prepare_nwaku_service(nwakunode_names, all_services, config_files, artifact_ids, container):

    # TODO MAKE SURE THEY MATCH
    prepared_ports = {}
    for i in range(len(nwakunode_names)):
        prepared_ports[vars.WAKU_RPC_PORT_ID+"_"+nwakunode_names[i]] = PortSpec(number=vars.WAKU_TCP_PORT + i,
                                            transport_protocol="TCP")
        prepared_ports[vars.PROMETHEUS_PORT_ID+"_"+nwakunode_names[i]] = PortSpec(
                number=vars.PROMETHEUS_TCP_PORT + i,
                transport_protocol="TCP")
        prepared_ports[vars.WAKU_LIBP2P_PORT_ID+"_"+nwakunode_names[i]] = PortSpec(
                number=vars.WAKU_LIBP2P_PORT + i,
                transport_protocol="TCP")

    prepared_files = {}
    for i in range(len(nwakunode_names)):
        prepared_files[vars.CONTAINER_NODE_CONFIG_FILE_LOCATION+nwakunode_names[i]] = artifact_ids[i]

    prepared_cmd = ""
    for i in range(len(nwakunode_names)):
        prepared_cmd += vars.NWAKU_ENTRYPOINT + " "
        prepared_cmd += vars.NODE_CONFIGURATION_FILE_FLAG + vars.CONTAINER_NODE_CONFIG_FILE_LOCATION +\
                        nwakunode_names[i] + "/" + config_files[i] + " "
        prepared_cmd += "--ports-shift="+str(i)
        if i != len(nwakunode_names) - 1:
            prepared_cmd += " & "

    add_service_config = ServiceConfig(
        image=vars.NWAKU_IMAGE,
        ports=prepared_ports,
        files=prepared_files,
        entrypoint=["/bin/sh", "-c"],
        cmd=[prepared_cmd]
    )

    all_services[container] = add_service_config


def prepare_gowaku_service(gowakunode_name, all_services, config_file, artifact_id):
    add_service_config = ServiceConfig(
        image=vars.GOWAKU_IMAGE,
        ports={
            vars.WAKU_RPC_PORT_ID: PortSpec(number=vars.WAKU_TCP_PORT,
                                            transport_protocol="TCP"),
            vars.PROMETHEUS_PORT_ID: PortSpec(
                number=vars.PROMETHEUS_TCP_PORT,
                transport_protocol="TCP"),
            vars.WAKU_LIBP2P_PORT_ID: PortSpec(
                number=vars.WAKU_LIBP2P_PORT,
                transport_protocol="TCP"),
        },
        files={
            vars.CONTAINER_NODE_CONFIG_FILE_LOCATION: artifact_id
        },
        entrypoint=vars.GOWAKU_ENTRYPOINT,
        cmd=[
            vars.NODE_CONFIGURATION_FILE_FLAG +
            vars.CONTAINER_NODE_CONFIG_FILE_LOCATION + config_file
        ]
    )

    all_services[gowakunode_name] = add_service_config


def prepare_nomos_service(plan, test, test2):
    plan.print("nomos")


def instantiate_services(plan, network_topology, testing):
    """
    todo refactor this
    As we will need to access for the service information later, the structure is the following:

    services = {
        "nwaku_0": {
            "hostname": service hostname
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
    service_hostname = services["nwaku_0"]["service_info"].hostname
    service_ip = services["nwaku_0"]["service_info"].ip_address
    rpc_node_number = services["nwaku_0"]["service_info"].ports["your_rpc_identifier"].number
    rpc_node_protocol = services["nwaku_0"]["service_info"].ports["your_rpc_identifier"].transport_protocol
    """

    all_services_configuration = {}

    for service_id, nodes_in_service in network_topology["containers"].items():
        image = network_topology["nodes"][nodes_in_service[0]]["image"]
        service_builder = service_dispatcher[image]

        # Get all config file names needed
        config_file_names = [network_topology["nodes"][node]["node_config"] for node in nodes_in_service]

        config_files_artifact_ids = [
            files.get_toml_configuration_artifact(plan, config_file_name,service_name, testing)
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

    for node_id, node_info in network_topology["nodes"].items():
        waku_port_id = vars.WAKU_RPC_PORT_ID + "_" + node_id
        libp2p_port_id = vars.WAKU_LIBP2P_PORT_ID + "_" + node_id
        prometheus_port_id = vars.PROMETHEUS_PORT_ID + "_" + node_id

        node_peer_id = waku.get_wakunode_peer_id(plan, node_info["container_id"], waku_port_id)

        network_topology["nodes"][node_id]["peer_id"] = node_peer_id
        network_topology["nodes"][node_id]["ip_address"] = \
            all_services_information[node_info["container_id"]].ip_address

        network_topology["nodes"][node_id]["ports"] = {}
        network_topology["nodes"][node_id]["ports"][waku_port_id] = \
            (all_services_information[node_info["container_id"]].ports[waku_port_id].number,
             all_services_information[node_info["container_id"]].ports[waku_port_id].transport_protocol)

        network_topology["nodes"][node_id]["ports"][libp2p_port_id] = \
            (all_services_information[node_info["container_id"]].ports[libp2p_port_id].number,
             all_services_information[node_info["container_id"]].ports[libp2p_port_id].transport_protocol)

        network_topology["nodes"][node_id]["ports"][prometheus_port_id] = \
            (all_services_information[node_info["container_id"]].ports[prometheus_port_id].number,
             all_services_information[node_info["container_id"]].ports[prometheus_port_id].transport_protocol)


service_dispatcher = {
    "go-waku": prepare_gowaku_service,
    "nim-waku": prepare_nwaku_service,
    "nomos": prepare_nomos_service
}
