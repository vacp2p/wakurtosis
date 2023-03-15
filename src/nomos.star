# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)
call_protocols = import_module(vars.CALL_PROTOCOLS)


def get_nomos_peer_id(plan, service_name, port_id):
    extract = {"peer_id": '.peer_id'}

    response = call_protocols.send_http_get_req(plan, service_name, port_id, vars.NOMOS_NET_INFO_URL, extract)

    plan.assert(value=response["code"], assertion="==", target_value = 200)

    return response["extract.peer_id"]


def create_node_multiaddress(node_id, node_information):
    ip = node_information[vars.IP_KEY]
    port = node_information[vars.PORTS_KEY][vars.NOMOS_LIBP2P_PORT_ID + "_" + node_id][0]
    nomos_node_id = node_information[vars.PEER_ID_KEY]

    return '"/ip4/' + str(ip) + '/tcp/' + str(port) + '/p2p/' + nomos_node_id + '"'


def _merge_peer_ids(peer_ids):
    return "[" + ",".join(peer_ids) + "]"


def connect_nomos_to_peers(plan, service_name, node_id, port_id, peer_ids):
    body = _merge_peer_ids(peer_ids)
    port_id = port_id + vars.ID_STR_SEPARATOR + node_id

    response = call_protocols.send_http_post_req(plan, service_name, port_id, vars.NOMOS_NET_CONN_URL, body) 

    plan.assert(value=response["code"], assertion="==", target_value = 200)

    plan.print(response)


def make_service_wait(plan,service_id, time):
    exec_recipe = struct(
        service_id=service_id,
        command=["sleep", time]
    )
    plan.exec(exec_recipe)


def interconnect_nomos_nodes(plan, topology_information, interconnection_batch):
    # Interconnect them
    nodes_in_topology = topology_information[vars.GENNET_NODES_KEY]

    for node_id in nodes_in_topology.keys():
        peers = nodes_in_topology[node_id][vars.GENNET_STATIC_NODES_KEY]

        for i in range(0, len(peers), interconnection_batch):
            peer_ids = [create_node_multiaddress(peer, nodes_in_topology[peer])
                        for peer in peers[i:i + interconnection_batch]]

            connect_nomos_to_peers(plan, nodes_in_topology[node_id][vars.GENNET_NODE_CONTAINER_KEY],
                                      node_id, vars.RPC_PORT_ID, peer_ids)


