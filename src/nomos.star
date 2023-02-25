# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)


def get_req(plan, service_name, port_id, endpoint, extract={}):
    recipe = GetHttpRequestRecipe(
        service_name=service_name,
        port_id=port_id,
        endpoint=endpoint,
        extract=extract
    )

    response = plan.wait(recipe=recipe,
                    field="code",
                    assertion="==",
                    target_value=200)

    return response


def post_req(plan, service_name, port_id, endpoint, body, extract={}):
    recipe = PostHttpRequestRecipe(
        service_name=service_name,
        port_id=port_id,
        endpoint=endpoint,
        content_type="application/json",
        body=body,
        extract=extract
    )

    response = plan.wait(recipe=recipe,
                    field="code",
                    assertion="==",
                    target_value=200)

    return response


def get_nomos_peer_id(plan, service_name, port_id):
    extract = {"peer_id": '.peer_id'}

    response = get_req(plan, service_name, port_id, vars.NOMOS_NET_INFO_URL, extract)

    plan.assert(value=response["code"], assertion="==", target_value = 200)

    return response["extract.peer_id"]


def create_nomos_id(nomos_service_information):
    nomos_service = nomos_service_information["service_info"]

    ip = nomos_service.ip_address
    port = nomos_service.ports[vars.NOMOS_LIBP2P_PORT_ID].number
    nomos_node_id = nomos_service_information["peer_id"]

    return '"/ip4/' + str(ip) + '/tcp/' + str(port) + '/p2p/' + nomos_node_id + '"'


def _merge_peer_ids(peer_ids):
    return "[" + ",".join(peer_ids) + "]"


def connect_nomos_to_peers(plan, service_id, port_id, peer_ids):
    body = _merge_peer_ids(peer_ids)

    response = post_req(plan, service_id, port_id, vars.NOMOS_NET_CONN_URL, body) 

    plan.assert(value=response["code"], assertion="==", target_value = 200)

    plan.print(response)


def make_service_wait(plan,service_id, time):
    exec_recipe = struct(
        service_id=service_id,
        command=["sleep", time]
    )
    plan.exec(exec_recipe)


def interconnect_nomos_nodes(plan, topology_information, services):
    # Interconnect them
    for nomos_service_id in services.keys():
        peers = topology_information[nomos_service_id]["static_nodes"]

        peer_ids = [create_nomos_id(services[peer]) for peer in peers]

        connect_nomos_to_peers(plan, nomos_service_id, vars.NOMOS_HTTP_PORT_ID, peer_ids)
