# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(system_variables.FILE_HELPERS_MODULE)


def send_json_rpc(service_id, port_id, method, params, extract={}):
    recipe = struct(
        service_id=service_id,
        port_id=port_id,
        endpoint="",
        method="POST",
        content_type="application/json",
        body='{ "jsonrpc": "2.0", "method": "' + method + '", "params": [' + params + '], "id": 1}',
        extract=extract
    )

    response = wait(recipe=recipe,
                    field="code",
                    assertion="==",
                    target_value=200)

    return response


def get_wakunode_peer_id(service_id, port_id):
    extract = {"peer_id": '.result.listenAddresses | .[0] | split("/") | .[-1]'}

    response = send_json_rpc(service_id, port_id,
                             system_variables.GET_WAKU_INFO_METHOD, "", extract)

    return response["extract.peer_id"]


def create_waku_id(waku_service_information):
    waku_service = waku_service_information["service_info"]

    ip = waku_service.ip_address
    port = waku_service.ports[system_variables.WAKU_LIBP2P_PORT_ID].number
    waku_node_id = waku_service_information["peer_id"]

    return '"/ip4/' + str(ip) + '/tcp/' + str(port) + '/p2p/' + waku_node_id + '"'


def _merge_peer_ids(peer_ids):
    return "[" + ",".join(peer_ids) + "]"


def connect_wakunode_to_peers(service_id, port_id, peer_ids):
    method = system_variables.CONNECT_TO_PEER_METHOD
    params = _merge_peer_ids(peer_ids)

    response = send_json_rpc(service_id, port_id, method, params)

    print(response)


def post_waku_v2_relay_v1_message(service_id, topic):
    waku_message = '{"payload": "0x1a2b3c4d5e6f", "timestamp": 1626813243}'
    params = '"' + topic + '"' + ", " + waku_message

    response = send_json_rpc(service_id, system_variables.WAKU_RPC_PORT_ID,
                                  system_variables.POST_RELAY_MESSAGE, params)

    print(response)


def get_wakunode_id(service_id, port_id):
    extract = {"waku_id": '.result.listenAddresses | .[0] | split("/") | .[-1]'}

    response = send_json_rpc(service_id, port_id, system_variables.GET_WAKU_INFO_METHOD, "",
                                  extract)

    return response["extract.waku_id"]


def make_service_wait(service_id, time):
    exec_recipe = struct(
        service_id=service_id,
        command=["sleep", time]
    )
    exec(exec_recipe)


def get_waku_peers(waku_service_id):
    response = send_json_rpc(waku_service_id, system_variables.WAKU_RPC_PORT_ID,
                                  system_variables.GET_PEERS_METHOD, "")

    print(response)

    return response


def send_test_messages(topology_information, number_of_messages, time_between_message):
    for wakunode_name in topology_information.keys():
        for i in range(number_of_messages):
            make_service_wait(wakunode_name,
                              time_between_message)  # todo check if this stops wakunode
            post_waku_v2_relay_v1_message(wakunode_name, "test")


def interconnect_waku_nodes(topology_information, services):
    # Interconnect them
    for waku_service_id in topology_information.keys():
        peers = topology_information[waku_service_id]["static_nodes"]

        peer_ids = [create_waku_id(services[peer]) for peer in peers]

        connect_wakunode_to_peers(waku_service_id, system_variables.WAKU_RPC_PORT_ID, peer_ids)


