# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(system_variables.WAKU_MODULE)
files = import_module(system_variables.FILE_HELPERS_MODULE)


def add_nwaku_service(nwakunode_name, use_general_configuration):
    artifact_id, configuration_file = files.get_toml_configuration_artifact(nwakunode_name,
                                                                            use_general_configuration)

    print("Configuration being used file is " + configuration_file)

    nwaku_service = add_service(
        service_id=nwakunode_name,
        config=struct(
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
                system_variables.NODE_CONFIG_FILE_LOCATION: artifact_id
            },
            entrypoint=system_variables.NWAKU_ENTRYPOINT,
            cmd=[
                "--config-file=" + system_variables.NODE_CONFIG_FILE_LOCATION + "/" + configuration_file
            ]
        )
    )

    return nwaku_service


def add_gowaku_service(gowakunode_name, use_general_configuration):
    artifact_id, configuration_file = files.get_toml_configuration_artifact(gowakunode_name,
                                                                            use_general_configuration)

    print("Configuration being used file is " + configuration_file)
    print("Entrypoint is "+ str(system_variables.GOWAKU_ENTRYPOINT))

    gowaku_service = add_service(
        service_id=gowakunode_name,
        config=struct(
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
                system_variables.NODE_CONFIG_FILE_LOCATION: artifact_id
            },
            entrypoint=system_variables.GOWAKU_ENTRYPOINT,
            cmd=[
                "--config-file=" + system_variables.NODE_CONFIG_FILE_LOCATION + "/" + configuration_file
            ]
        )
    )

    return gowaku_service

def add_jswaku_service(test, test2):
    print("jswaku")

def add_nomos_service(test, test2):
    print("nomos")


def instantiate_services(network_topology, use_general_configuration):
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

    services_information = {}

    # Get up all nodes
    for service_id in network_topology.keys():
        image = network_topology[service_id]["image"]

        service_builder, information_builder = service_dispatcher[image]

        service_information = service_builder(service_id, use_general_configuration)

        information_builder(services_information, service_id, service_information)

    return services_information


def _add_waku_service_information(services_information, new_service_id, service_information):

    new_service_information = {}

    wakunode_peer_id = waku.get_wakunode_peer_id(new_service_id, system_variables.WAKU_RPC_PORT_ID)

    new_service_information["peer_id"] = wakunode_peer_id
    new_service_information["service_info"] = service_information

    services_information[new_service_id] = new_service_information


service_dispatcher = {
    "go-waku": (add_gowaku_service, _add_waku_service_information),
    "nim-waku": (add_nwaku_service, _add_waku_service_information),
    "js-waku": (add_jswaku_service, _add_waku_service_information),
    "nomos": (add_nomos_service, "test")
}
