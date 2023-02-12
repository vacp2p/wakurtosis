# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(vars.WAKU_MODULE)
node_builders = import_module(vars.NODE_BUILDERS_MODULE)


# We have to encapsulate all tests into one function, so we can use the same service for all tests,
# instead having to create one for each test, and in order to create a node we need access to "plan"
# parameter, so we cannot have it as a global variable as it was intended.
def test_waku_methods(plan):

    # Another file because kurtosis artifact clashes
    topology_for_test_file = vars.TEST_FILES_LOCATION + "test_network_data_2.json"
    topology = read_file(src=topology_for_test_file)
    topology = json.decode(topology)

    services_info = node_builders.instantiate_services(plan, topology, True)
    expected_ids = {
        "nwaku_0_2": "16Uiu2HAm7ZPmRY3ECVz7fAJQdxEDrBw3ToneYgUryKDJPtz25R2n",
        "nwaku_1_2": "16Uiu2HAmV7KPdL24S9Lztu6orfWuHypA9F6NUR4GkBDvWg8U4B5Z"
    }

    for test_node in services_info.keys():
        test_send_json_rpc(plan, test_node)
        test_get_wakunode_peer_id(plan, test_node, expected_ids)
        test_connect_wakunode_to_peers(plan, test_node)
        test_post_waku_v2_relay_v1_message(plan, test_node)

    test_create_waku_id(plan)
    test__merge_peer_ids(plan)
    test_get_waku_peers(plan, topology)
    test_interconnect_waku_nodes(plan, topology, services_info)
    test_get_waku_peers_after(plan, topology)

    for service_name in services_info.keys():
        plan.remove_service(service_name)


def test_send_json_rpc(plan, service_name):
    waku_message = '{"payload": "0x1a2b3c4d5e6f", "timestamp": 1626813243}'
    params = "test, " + waku_message

    # Automatically waits for 200
    waku.send_json_rpc(plan, service_name, vars.WAKU_RPC_PORT_ID,
                       vars.POST_RELAY_MESSAGE_METHOD, params)


def test_get_wakunode_peer_id(plan, service_name, expected_ids):
    peer_id = waku.get_wakunode_peer_id(plan, service_name, vars.WAKU_RPC_PORT_ID)

    plan.assert(value=peer_id, assertion="==",
            target_value=expected_ids[service_name])


def test_create_waku_id(plan):
    service_struct = struct(ip_address="1.1.1.1",
                            ports={vars.WAKU_LIBP2P_PORT_ID: PortSpec(number=1234)})
    services_example = {"service_info": service_struct, "peer_id": "ASDFGHJKL"}

    waku_id = waku.create_waku_id(services_example)

    plan.assert(value=waku_id, assertion="==", target_value='"/ip4/1.1.1.1/tcp/1234/p2p/ASDFGHJKL"')


def test__merge_peer_ids(plan):
    waku_ids = ["/ip4/1.1.1.1/tcp/1234/p2p/ASDFGHJKL", "/ip4/2.2.2.2/tcp/1234/p2p/QWERTYUIOP"]

    ids = waku._merge_peer_ids(waku_ids)

    plan.assert(value=ids,
            assertion="==",
            target_value="[/ip4/1.1.1.1/tcp/1234/p2p/ASDFGHJKL,/ip4/2.2.2.2/tcp/1234/p2p/QWERTYUIOP]")


def test_connect_wakunode_to_peers(plan, service_name):
    # It will print an error but 200 code
    waku.connect_wakunode_to_peers(plan, service_name, vars.WAKU_RPC_PORT_ID, ["asd"])

def test_post_waku_v2_relay_v1_message(plan, service_name):
    waku.post_waku_v2_relay_v1_message_test(plan, service_name, "test")


def test_get_waku_peers(plan, test_topology):
    for test_node in test_topology.keys():
        num_peers = waku.get_waku_peers(plan, test_node)

        plan.assert(value=num_peers, assertion="==", target_value=0)

def test_get_waku_peers_after(plan, test_topology):
    for test_node in test_topology.keys():
        num_peers = waku.get_waku_peers(plan, test_node)

        plan.assert(value=num_peers, assertion="==", target_value=1)

def test_interconnect_waku_nodes(plan, test_topology, node_test_services):

    waku.interconnect_waku_nodes(plan, test_topology, node_test_services)

    for service_name in node_test_services:
        neighbours = waku.get_waku_peers(plan, service_name)
        plan.assert(value=neighbours, assertion="==", target_value=1)
