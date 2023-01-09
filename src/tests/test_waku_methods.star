# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(system_variables.WAKU_MODULE)


def test_network_creation():

    waku_topology = read_file(src=system_variables.TOPOLOGIES_LOCATION +
                                  system_variables.DEFAULT_TOPOLOGY_FILE_DEFAULT_ARGUMENT_VALUE)
    waku_topology = json.decode(waku_topology)

    waku_test_services = waku.instantiate_waku_nodes(waku_topology, True)

    waku.interconnect_waku_nodes(waku_topology, waku_test_services)
    waku.send_test_messages(waku_test_services, system_variables.NUMBER_TEST_MESSAGES,
                            system_variables.DELAY_BETWEEN_TEST_MESSAGE)
    _test_node_neighbours(waku_test_services)


def _test_node_neighbours(topology_information):
    for wakunode_name in topology_information.keys():
        peers = waku.get_waku_peers(wakunode_name)
        assert(value=peers, assertion="==", target_value=2)


def test_create_waku_id():
    service_struct = struct(ip_address="1.1.1.1",
                            ports={system_variables.WAKU_LIBP2P_PORT_ID: PortSpec(number=1234)})
    services_example = {"service_info": service_struct, "id": "ASDFGHJKL"}

    waku_id = waku.create_waku_id(services_example)

    assert (value=waku_id, assertion="==", target_value='"/ip4/1.1.1.1/tcp/1234/p2p/ASDFGHJKL"')


def test__merge_peer_ids():
    waku_ids = ["/ip4/1.1.1.1/tcp/1234/p2p/ASDFGHJKL", "/ip4/2.2.2.2/tcp/1234/p2p/QWERTYUIOP"]

    ids = waku._merge_peer_ids(waku_ids)

    assert (value=ids,
            assertion="==",
            target_value="[/ip4/1.1.1.1/tcp/1234/p2p/ASDFGHJKL,/ip4/2.2.2.2/tcp/1234/p2p/QWERTYUIOP]")


def test__add_information():
    service_struct = struct(ip_address="1.1.1.1",
                            ports={system_variables.WAKU_LIBP2P_PORT_ID: PortSpec(number=1234)})

    services = {}

    waku._add_information(services, {}, "IDTEST", service_struct, "waku_test")

    assert(value=str(len(services)), assertion="==", target_value="1")
    assert(value="waku_test", assertion="IN", target_value=services.keys())
    assert(value=services["waku_test"]["id"], assertion="==", target_value="IDTEST")
    assert(value=services["waku_test"]["service_info"].ip_address,
            assertion="==", target_value="1.1.1.1")
    assert(value=str(services["waku_test"]["service_info"].ports[system_variables.WAKU_LIBP2P_PORT_ID].number),
            assertion="==", target_value="1234")
    assert(value=services["waku_test"]["service_info"].ports[system_variables.WAKU_LIBP2P_PORT_ID].transport_protocol,
            assertion="==", target_value="TCP")
