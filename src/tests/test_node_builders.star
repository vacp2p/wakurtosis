# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
node_builders = import_module(system_variables.NODE_BUILDERS_MODULE)
waku = import_module(system_variables.WAKU_MODULE)


def test_add_nwaku_service(plan):
    nwaku_test_service = node_builders.add_nwaku_service(plan, "nwaku_test", False)

    test__add_waku_service_information(plan, nwaku_test_service)

    plan.assert(value=str(nwaku_test_service.ports[system_variables.WAKU_RPC_PORT_ID].number),
            assertion="==", target_value=str(system_variables.WAKU_TCP_PORT))
    plan.assert(value=str(nwaku_test_service.ports[system_variables.PROMETHEUS_PORT_ID].number),
            assertion="==", target_value=str(system_variables.PROMETHEUS_TCP_PORT))
    plan.assert(value=str(nwaku_test_service.ports[system_variables.WAKU_LIBP2P_PORT_ID].number),
            assertion="==", target_value=str(system_variables.WAKU_LIBP2P_PORT))

    plan.remove_service("nwaku_test")


def test_add_gowaku_service(plan):
    gowaku_test_service = node_builders.add_gowaku_service(plan, "gowaku_test", False)

    plan.assert(value=str(gowaku_test_service.ports[system_variables.WAKU_RPC_PORT_ID].number),
            assertion="==", target_value=str(system_variables.WAKU_TCP_PORT))
    plan.assert(value=str(gowaku_test_service.ports[system_variables.PROMETHEUS_PORT_ID].number),
            assertion="==", target_value=str(system_variables.PROMETHEUS_TCP_PORT))
    plan.assert(value=str(gowaku_test_service.ports[system_variables.WAKU_LIBP2P_PORT_ID].number),
            assertion="==", target_value=str(system_variables.WAKU_LIBP2P_PORT))

    plan.remove_service("gowaku_test")


def test_instantiate_services(plan):
    topology = read_file(src=system_variables.TOPOLOGIES_LOCATION +
                             system_variables.DEFAULT_TOPOLOGY_FILE_DEFAULT_ARGUMENT_VALUE)
    topology = json.decode(topology)

    node_test_services = node_builders.instantiate_services(plan, topology, False)

    waku.interconnect_waku_nodes(plan, topology, node_test_services)
    _test_node_neighbours(plan, node_test_services)

    for node_id in node_test_services.keys():
        plan.remove_service(node_id)


def _test_node_neighbours(plan, topology_information):
    for node_name in topology_information.keys():
        peers = waku.get_waku_peers(plan, node_name)
        plan.assert(value=peers, assertion="==", target_value=2)


def test__add_waku_service_information(plan, test_service):

    services = {}

    node_builders._add_waku_service_information(plan, services, "nwaku_test", test_service)

    plan.print(services["nwaku_test"]["peer_id"])

    plan.assert(value=str(len(services)), assertion = "==", target_value = "1")
    plan.assert(value="nwaku_test", assertion="IN", target_value=services.keys())
    plan.assert(value=services["nwaku_test"]["peer_id"], assertion="==",
            target_value="16Uiu2HAm7ZPmRY3ECVz7fAJQdxEDrBw3ToneYgUryKDJPtz25R2n")
    plan.assert(value=str(services["nwaku_test"]["service_info"].ports[system_variables.WAKU_LIBP2P_PORT_ID].number),
            assertion="==", target_value = str(system_variables.WAKU_LIBP2P_PORT))
    plan.assert(value=services["nwaku_test"]["service_info"].ports[system_variables.WAKU_LIBP2P_PORT_ID].transport_protocol,
            assertion="==", target_value="TCP")
