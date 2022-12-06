IMAGE_NAME = "wakunode"
WAKU_RPC_PORT_ID = "rpc"
TCP_PORT = 8545

GET_WAKU_INFO_METHOD = "get_waku_v2_debug_v1_info"
CONNECT_TO_PEER_METHOD = "post_waku_v2_admin_v1_peers"



def create_waku_id(other_node_info):
    ip = other_node_info["service"].ip_address
    port = other_node_info["service"].ports["rpc"].number
    node_id = other_node_info["id"]

    return "/ip4/" + str(ip) + "/tcp/" + str(port) + "/p2p/" + node_id


def connect_wakunode_to_peer(service_id, port_id, other_node_info):

    method = CONNECT_TO_PEER_METHOD

    params = create_waku_id(other_node_info)

    response = send_json_rpc(service_id, port_id, method, params)

    print(response)

def send_json_rpc(service_id, port_id, method, params):
    recipe = struct(
        service_id=service_id,
        port_id=port_id,
        endpoint="",
        method="POST",
        content_type="application/json",
        body='{ "jsonrpc": "2.0", "method": "' + method + '", "params": [' + params + '], "id": 1}'
    )

    response = get_value(recipe=recipe)

    return response


def get_wakunode_id(service_id, port_id):
    response = send_json_rpc(service_id, port_id, GET_WAKU_INFO_METHOD, "")

    result = extract(response.body, ".result.listenAddresses")
    wakunode_id = result[:-1].split("/")[-1]

    return wakunode_id


def run(args):
    contents = read_file(src="github.com/logos-co/wakurtosis/kurtosis-module/starlark/waku_test_topology.json")

    # decoded = json.decode(contents)

    decoded = {
        "waku_0": {
            "ports_shift": 0,
            "topics": "test",
            "static_nodes": [
                "waku_1",
            ]
        },
        "waku_1": {
            "ports_shift": 1,
            "topics": "test",
            "static_nodes": [
                "waku_0"
            ]
        },
    }

    services = {}

    # Get up all waku nodes
    for wakunode_name in decoded.keys():
        waku_service = add_service(
            service_id=wakunode_name,
            config=struct(
                image=IMAGE_NAME,
                ports={WAKU_RPC_PORT_ID: struct(number=TCP_PORT, protocol="TCP")},
                entrypoint=[
                    "/usr/bin/wakunode", "--rpc-address=0.0.0.0"
                ],
                cmd=[
                    "--topics='" + decoded[wakunode_name]["topics"] + "'", '--rpc-admin=true', '--keep-alive=true'
                ]
            )
        )

        waku_info = {}
        id = get_wakunode_id(wakunode_name, WAKU_RPC_PORT_ID)
        waku_info["id"] = id
        waku_info["service"] = waku_service

        services[wakunode_name] = waku_info

        # exec(wakunode_name, ["sleep", "30"])


    # Interconnect them
    for wakunode_name in decoded.keys():
        peers = decoded[wakunode_name]["static_nodes"]

        for peer in peers:
            connect_wakunode_to_peer(wakunode_name, WAKU_RPC_PORT_ID, services[peer])
