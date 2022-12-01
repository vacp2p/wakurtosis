
IMAGE_NAME = "wakunode"
PORT_ID = "rpc"
TCP_PORT = 8545

GET_WAKU_INFO_METHOD = "get_waku_v2_debug_v1_info"
CONNECT_TO_PEER_METHOD = "post_waku_v2_admin_v1_peers"

def send_json_rpc(service_id, port_id, method, params):

    recipe = struct(
        service_id=service_id,
        port_id=port_id,
        endpoint="",
        method="POST",
        content_type="application/json",
        body='{ "jsonrpc": "2.0", "method": "' + method + '", "params": [' + params + ']}, "id": 1}'
    )

    response = get_value(recipe=recipe)


def run(args):
    contents = read_file(src="github.com/logos-co/wakurtosis/kurtosis-module/starlark/waku_test_topology.json")

    decoded = json.decode(contents)

    services = {}

    # Get up all waku nodes
    for wakunode_name in decoded.keys():
        waku_service = add_service(
            service_id=wakunode_name,
            config=struct(
                image=IMAGE_NAME,
                ports={ PORT_ID: struct(number=TCP_PORT, protocol="TCP")},
                entrypoint=[
                    "/usr/bin/wakunode", "--rpc-address=0.0.0.0"
                ],
                cmd=[
                    "--topics='" + decoded[wakunode_name]["topics"] + "'", '--rpc-admin=true', '--keep-alive=true'
                ]
            )
        )

        services[wakunode_name] = waku_service

    break
    # Interconnect them
    # for wakunode_name in decoded.keys():
    #     peers = decoded[wakunode_name]["static_nodes"]

