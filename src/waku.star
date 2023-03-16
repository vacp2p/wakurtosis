# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)
call_protocols = import_module(vars.CALL_PROTOCOLS)


def get_wakunode_peer_id(plan, service_name, port_id):
    extract = {"peer_id": '.result.listenAddresses | .[0] | split("/") | .[-1]'}

    response = call_protocols.send_json_rpc(plan, service_name, port_id,
                             vars.GET_WAKU_INFO_METHOD, "", extract)

    plan.assert(value=response["code"], assertion="==", target_value = 200)

    return response["extract.peer_id"]


def create_node_multiaddress(node_id, node_information):
    ip = node_information[vars.IP_KEY]
    port = node_information[vars.PORTS_KEY][vars.WAKU_LIBP2P_PORT_ID + vars.ID_STR_SEPARATOR + node_id][0]
    waku_node_id = node_information[vars.PEER_ID_KEY]

    return '"/ip4/' + str(ip) + '/tcp/' + str(port) + '/p2p/' + waku_node_id + '"'


def _merge_peer_ids(peer_ids):
    return "[" + ",".join(peer_ids) + "]"


def connect_wakunode_to_peers(plan, service_name, node_id, port_id, peer_ids):
    method = vars.CONNECT_TO_PEER_METHOD
    params = _merge_peer_ids(peer_ids)
    port_id = port_id + vars.ID_STR_SEPARATOR + node_id

    response = call_protocols.send_json_rpc(plan, service_name, port_id, method, params)

    plan.assert(value=response["code"], assertion="==", target_value = 200)

    plan.print(response)


def make_service_wait(plan, service_name, time):
    exec_recipe = struct(
        service_name=service_name,
        command=["sleep", time]
    )
    plan.exec(exec_recipe)


def get_waku_peers(plan, waku_service_container, node_name):
    extract = {"peers": '.result | length'}
    port_name = vars.RPC_PORT_ID + vars.ID_STR_SEPARATOR + node_name

    response = call_protocols.send_json_rpc(plan, waku_service_container, port_name,
                                            vars.GET_PEERS_METHOD, "", extract)

    plan.assert(value=response["code"], assertion="==", target_value=200)

    return response["extract.peers"]


def interconnect_waku_nodes(plan, topology_information, interconnection_batch):
    # Interconnect them
    nodes_in_topology = topology_information[vars.GENNET_NODES_KEY]

    for node_id in nodes_in_topology.keys():
        peers = nodes_in_topology[node_id][vars.GENNET_STATIC_NODES_KEY]

        for i in range(0, len(peers), interconnection_batch):
            peer_ids = [create_node_multiaddress(peer, nodes_in_topology[peer])
                        for peer in peers[i:i + interconnection_batch]]

            connect_wakunode_to_peers(plan, nodes_in_topology[node_id][vars.GENNET_NODE_CONTAINER_KEY],
                                      node_id, vars.RPC_PORT_ID, peer_ids)


