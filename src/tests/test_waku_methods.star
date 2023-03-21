# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(vars.WAKU_MODULE)
node_builders = import_module(vars.NODE_BUILDERS_MODULE)
call_protocols = import_module(vars.CALL_PROTOCOLS)


# We have to encapsulate all tests into one function, so we can use the same service for all tests,
# instead having to create one for each test, and in order to create a node we need access to "plan"
# parameter, so we cannot have it as a global variable as it was intended.
def test_waku_methods(plan):

    # Another file because kurtosis artifact clashes
    topology_for_test_file = vars.TEST_FILES_LOCATION + "test_network_data_2.json"
    topology = read_file(src=topology_for_test_file)
    topology = json.decode(topology)

    node_builders.instantiate_services(plan, topology, True)
    expected_ids = {
        "nwaku_0_2": "16Uiu2HAm7ZPmRY3ECVz7fAJQdxEDrBw3ToneYgUryKDJPtz25R2n",
        "nwaku_1_2": "16Uiu2HAmV7KPdL24S9Lztu6orfWuHypA9F6NUR4GkBDvWg8U4B5Z"
    }

    for test_node, test_node_info in topology["nodes"].items():
        test_send_json_rpc(plan, test_node, test_node_info)
        test_get_wakunode_peer_id(plan, test_node, test_node_info, expected_ids)

    test_create_node_multiaddress(plan)
    test__merge_peer_ids(plan)
    test_get_waku_peers(plan, topology, 0)
    waku.interconnect_waku_nodes(plan, topology, 1)
    test_get_waku_peers(plan, topology, 1)

    for service_name in topology["containers"].keys():
        plan.remove_service(service_name)


def test_send_json_rpc(plan, test_node, test_node_info):
    waku_message = '{"payload": "0x1a2b3c4d5e6f", "timestamp": 1626813243}'
    params = "test, " + waku_message
    service_id = test_node_info[vars.GENNET_NODE_CONTAINER_KEY]

    # Automatically waits for 200
    call_protocols.send_json_rpc(plan, service_id, vars.RPC_PORT_ID+vars.ID_STR_SEPARATOR+test_node,
                       vars.POST_RELAY_MESSAGE_METHOD, params)


def test_get_wakunode_peer_id(plan, test_node, test_node_info, expected_ids):
    service_id = test_node_info[vars.GENNET_NODE_CONTAINER_KEY]
    peer_id = waku.get_wakunode_peer_id(plan, service_id, vars.RPC_PORT_ID+vars.ID_STR_SEPARATOR+test_node)
    plan.print("Peer ID for " + test_node + ": " + peer_id)
    plan.assert(value=peer_id, assertion="==", target_value=expected_ids[test_node])


def test_create_node_multiaddress(plan):
    node_id = "test"
    node_information = {"ip_address": "1.1.1.1", "ports": {"libp2p-test": (1234, 'tcp')},
                        "peer_id": "ASDFGHJKL"}

    waku_id = waku.create_node_multiaddress(node_id, node_information)

    plan.assert(value=waku_id, assertion="==", target_value='"/ip4/1.1.1.1/tcp/1234/p2p/ASDFGHJKL"')


def test__merge_peer_ids(plan):
    waku_ids = ["/ip4/1.1.1.1/tcp/1234/p2p/ASDFGHJKL", "/ip4/2.2.2.2/tcp/1234/p2p/QWERTYUIOP"]

    ids = waku._merge_peer_ids(waku_ids)

    plan.assert(value=ids,
            assertion="==",
            target_value="[/ip4/1.1.1.1/tcp/1234/p2p/ASDFGHJKL,/ip4/2.2.2.2/tcp/1234/p2p/QWERTYUIOP]")


def test_get_waku_peers(plan, test_topology, expected):
    for test_node, test_node_info in test_topology["nodes"].items():
        num_peers = waku.get_waku_peers(plan, test_node_info["container_id"], test_node)

        plan.assert(value=num_peers, assertion="==", target_value=expected)
