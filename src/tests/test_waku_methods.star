# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(system_variables.WAKU_MODULE)
node_builders = import_module(system_variables.NODE_BUILDERS_MODULE)


# We have to encapsulate all tests into one function, so we can use the same service for all tests,
# instead having to create one for each test, and in order to create a node we need access to "plan"
# parameter, so we cannot have it as a global variable as it was intented.
def test_waku_methods(plan):
    NWAKU_TEST_SERVICE_NAME = "nwaku_global_test"
    NWAKU_TEST_SERVICE_NAME_2 = "nwaku_test_2"
    NWAKU_TEST_SERVICE = node_builders.prepare_nwaku_service(plan, NWAKU_TEST_SERVICE_NAME, False)
    NWAKU_TEST_SERVICE_2 = node_builders.prepare_nwaku_service(plan, NWAKU_TEST_SERVICE_NAME_2, False)

    test_send_json_rpc(plan, NWAKU_TEST_SERVICE_NAME)
    test_get_wakunode_peer_id(plan, NWAKU_TEST_SERVICE_NAME)
    test_create_waku_id(plan)
    test__merge_peer_ids(plan)
    test_connect_wakunode_to_peers(plan, NWAKU_TEST_SERVICE_NAME)
    test_post_waku_v2_relay_v1_message(plan, NWAKU_TEST_SERVICE_NAME)
    test_get_waku_peers(plan)
    test_interconnect_waku_nodes(plan)

    plan.remove_service(NWAKU_TEST_SERVICE_NAME)
    plan.remove_service(NWAKU_TEST_SERVICE_NAME_2)

def test_send_json_rpc(plan, service_name):
    waku_message = '{"payload": "0x1a2b3c4d5e6f", "timestamp": 1626813243}'
    params = "test, " + waku_message

    # Automatically waits for 200
    waku.send_json_rpc(plan, service_name, system_variables.WAKU_RPC_PORT_ID,
                       system_variables.POST_RELAY_MESSAGE_METHOD, params)


def test_get_wakunode_peer_id(plan, service_name):
    peer_id = waku.get_wakunode_peer_id(plan, service_name, system_variables.WAKU_RPC_PORT_ID)
    plan.print(peer_id)
    plan.assert(value=peer_id, assertion="==",
            target_value="16Uiu2HAm7ZPmRY3ECVz7fAJQdxEDrBw3ToneYgUryKDJPtz25R2n")


def test_create_waku_id(plan):
    service_struct = struct(ip_address="1.1.1.1",
                            ports={system_variables.WAKU_LIBP2P_PORT_ID: PortSpec(number=1234)})
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
    waku.connect_wakunode_to_peers(plan, service_name, system_variables.WAKU_RPC_PORT_ID, ["asd"])

def test_post_waku_v2_relay_v1_message(plan, service_name):
    waku.post_waku_v2_relay_v1_message_test(plan, service_name, "test")


def test_get_waku_peers(plan):
    num_peers = waku.get_waku_peers(plan, "nwaku_global_test")

    plan.assert(value=num_peers, assertion="==", target_value=0)

def test_interconnect_waku_nodes(plan):
    topology = read_file(src=system_variables.TOPOLOGIES_LOCATION +
                                  system_variables.TOPOLOGY_FOR_TESTS)
    topology = json.decode(topology)

    node_test_services = node_builders.instantiate_services(plan, topology, True)

    waku.interconnect_waku_nodes(plan, topology, node_test_services)

    for service_name in topology:
        neighbours = waku.get_waku_peers(plan, service_name)
        plan.assert(value=neighbours, assertion="==", target_value=1)

    for service_name in topology:
        plan.remove_service(service_name)
