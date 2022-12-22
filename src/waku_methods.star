system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")
files = import_module("github.com/logos-co/wakurtosis/src/file_helpers.star")

def send_waku_json_rpc(service_id, port_id, method, params, extract={}):
    recipe = struct(
        service_id=service_id,
        port_id=port_id,
        endpoint="",
        method="POST",
        content_type="application/json",
        body='{ "jsonrpc": "2.0", "method": "' + method + '", "params": [' + params + '], "id": 1}',
        extract=extract
    )

    response = request(recipe=recipe)

    return response


def create_waku_id(waku_service_information):
    waku_service = waku_service_information["service_info"]

    ip = waku_service.ip_address
    port = waku_service.ports[system_variables.WAKU_LIBP2P_PORT_ID].number
    waku_node_id = waku_service_information["id"]

    return '"/ip4/' + str(ip) + '/tcp/' + str(port) + '/p2p/' + waku_node_id + '"'


def _merge_peer_ids(peer_ids):
    return "[" + ",".join(peer_ids) + "]"


def connect_wakunode_to_peers(service_id, port_id, peer_ids):
    method = system_variables.CONNECT_TO_PEER_METHOD
    params = _merge_peer_ids(peer_ids)

    response = send_waku_json_rpc(service_id, port_id, method, params)

    print(response)


def post_waku_v2_relay_v1_message(service_id, topic):
    waku_message = '{"payload": "0x1a2b3c4d5e6f", "timestamp": 1626813243}'
    params = '"' + topic + '"' + ", " + waku_message

    response = send_waku_json_rpc(service_id, system_variables.WAKU_RPC_PORT_ID, system_variables.POST_RELAY_MESSAGE, params)

    print(response)


def get_wakunode_id(service_id, port_id):
    extract = {"waku_id": '.result.listenAddresses | .[0] | split("/") | .[-1]'}

    response = send_waku_json_rpc(service_id, port_id, system_variables.GET_WAKU_INFO_METHOD, "", extract)

    return response["extract.waku_id"]


def add_waku_service(wakunode_name, use_general_configuration):
    artifact_id, configuration_file = files.get_toml_configuration_artifact(wakunode_name, use_general_configuration)

    print("Configuration being used file is " + configuration_file)

    waku_service = add_service(
        service_id=wakunode_name,
        config=struct(
            image=system_variables.WAKU_IMAGE,
            ports={
                system_variables.WAKU_RPC_PORT_ID: PortSpec(number=system_variables.WAKU_TCP_PORT,
                                                            transport_protocol="TCP"),
                system_variables.PROMETHEUS_PORT_ID: PortSpec(number=system_variables.PROMETHEUS_TCP_PORT,
                                                              transport_protocol="TCP"),
                system_variables.WAKU_LIBP2P_PORT_ID: PortSpec(number=system_variables.WAKU_LIBP2P_PORT,
                                                               transport_protocol="TCP"),
            },
            files={
                system_variables.WAKU_CONFIG_FILE_LOCATION: artifact_id
            },
            entrypoint=system_variables.WAKU_ENTRYPOINT,
            cmd=[
                "--config-file=" + system_variables.WAKU_CONFIG_FILE_LOCATION + "/" + configuration_file
            ]
        )
    )

    return waku_service


def make_service_wait(service_id, time):
    exec_recipe = struct(
        service_id=service_id,
        command=["sleep", time]
    )
    exec(exec_recipe)


def add_waku_service_information(services, waku_service_id, waku_service):
    """
    As we will need to access for the service information later, the structure is the following:

    services = {
        "waku_0": {
            "id" : id of the node, as string,
            "service_info": Kurtosis service struct, that has
                "ip": ip of the node,
                "ports": Kurtosis PortSpec, that you can access with their respective identifier
        },
        "waku_1": {...}
    }

    Example:

    node_id = services["waku_0"]["id"]
    node_ip = services["waku_0"]["service_info"].ip_address
    rpc_node_number = services["waku_0"]["service_info"].ports["your_rpc_identifier"].number
    rpc_node_protocol = services["waku_0"]["service_info"].ports["your_rpc_identifier"].protocol
    """
    waku_info = {}

    waku_node_id = get_wakunode_id(waku_service_id, system_variables.WAKU_RPC_PORT_ID)

    waku_info["id"] = waku_node_id
    waku_info["service_info"] = waku_service

    services[waku_service_id] = waku_info


def instantiate_waku_nodes(network_topology, use_general_configuration):
    waku_services_information = {}

    # Get up all waku nodes
    for waku_service_id in network_topology.keys():
        waku_service = add_waku_service(waku_service_id, use_general_configuration)

        make_service_wait(waku_service_id, system_variables.WAKU_SETUP_WAIT_TIME)
        add_waku_service_information(waku_services_information, waku_service_id, waku_service)

    return waku_services_information


def get_waku_peers(waku_service_id):
    response = send_waku_json_rpc(waku_service_id, system_variables.WAKU_RPC_PORT_ID,
                                  system_variables.GET_PEERS_METHOD, "")

    print(response)

    return response


def send_test_messages(topology_information, number_of_messages, time_between_message):
    for wakunode_name in topology_information.keys():
        for i in range(number_of_messages):
            make_service_wait(wakunode_name, time_between_message) # todo check if this stops wakunode
            post_waku_v2_relay_v1_message(wakunode_name, "test")


def interconnect_waku_nodes(topology_information, services):
    # Interconnect them
    for waku_service_id in topology_information.keys():
        peers = topology_information[waku_service_id]["static_nodes"]

        peer_ids = [create_waku_id(services[peer]) for peer in peers]

        connect_wakunode_to_peers(waku_service_id, system_variables.WAKU_RPC_PORT_ID, peer_ids)
