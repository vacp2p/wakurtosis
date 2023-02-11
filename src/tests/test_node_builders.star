# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
node_builders = import_module(system_variables.NODE_BUILDERS_MODULE)
waku = import_module(system_variables.WAKU_MODULE)


def test_prepare_nwaku_service(plan):
    test_dict = {}
    node_builders.prepare_nwaku_service(plan, "test", "nwaku_test", test_dict, False)

    # hasattr doesn't work in dicts?
    plan.assert(value=str(test_dict.get("test")),
        assertion="!=", target_value="None")
    plan.assert(value=test_dict["test"].image,
        assertion="==", target_value=system_variables.NWAKU_IMAGE)
    plan.assert(value=str(test_dict["test"].ports[system_variables.WAKU_RPC_PORT_ID].number),
        assertion="==", target_value=str(system_variables.WAKU_TCP_PORT))
    plan.assert(value=str(test_dict["test"].ports[system_variables.PROMETHEUS_PORT_ID].number),
        assertion="==", target_value=str(system_variables.PROMETHEUS_TCP_PORT))
    plan.assert(value=str(test_dict["test"].ports[system_variables.WAKU_LIBP2P_PORT_ID].number),
            assertion="==", target_value=str(system_variables.WAKU_LIBP2P_PORT))
    plan.assert(value=test_dict["test"].files[system_variables.CONTAINER_NODE_CONFIG_FILE_LOCATION],
            assertion="==", target_value="nwaku_test")
    # Only way to assert lists?
    for i in range(len(test_dict["test"].entrypoint)):
        plan.assert(value=test_dict["test"].entrypoint[i],
                assertion="==", target_value=system_variables.NWAKU_ENTRYPOINT[i])
    plan.assert(value=test_dict["test"].cmd[0],
            assertion="==", target_value=system_variables.NODE_CONFIGURATION_FILE_FLAG +
            system_variables.CONTAINER_NODE_CONFIG_FILE_LOCATION +
            "/test.toml")


def test_prepare_gowaku_service(plan):
    test_dict = {}
    node_builders.prepare_gowaku_service(plan, "test", "gowaku_test", test_dict, False)

    # hasattr doesn't work in dicts?
    plan.assert(value=str(test_dict.get("test")),
        assertion="!=", target_value="None")
    plan.assert(value=test_dict["test"].image,
        assertion="==", target_value=system_variables.GOWAKU_IMAGE)
    plan.assert(value=str(test_dict["test"].ports[system_variables.WAKU_RPC_PORT_ID].number),
        assertion="==", target_value=str(system_variables.WAKU_TCP_PORT))
    plan.assert(value=str(test_dict["test"].ports[system_variables.PROMETHEUS_PORT_ID].number),
        assertion="==", target_value=str(system_variables.PROMETHEUS_TCP_PORT))
    plan.assert(value=str(test_dict["test"].ports[system_variables.WAKU_LIBP2P_PORT_ID].number),
            assertion="==", target_value=str(system_variables.WAKU_LIBP2P_PORT))
    plan.assert(value=test_dict["test"].files[system_variables.CONTAINER_NODE_CONFIG_FILE_LOCATION],
            assertion="==", target_value="gowaku_test")
    # Only way to assert lists?
    for i in range(len(test_dict["test"].entrypoint)):
        plan.assert(value=test_dict["test"].entrypoint[i],
                assertion="==", target_value=system_variables.GOWAKU_ENTRYPOINT[i])
    plan.assert(value=test_dict["test"].cmd[0],
            assertion="==", target_value=system_variables.NODE_CONFIGURATION_FILE_FLAG +
            system_variables.CONTAINER_NODE_CONFIG_FILE_LOCATION +
            "/test.toml")


def test_instantiate_services(plan):
    topology = read_file(src=system_variables.TOPOLOGIES_LOCATION +
                             system_variables.DEFAULT_TOPOLOGY_FILE_DEFAULT_ARGUMENT_VALUE)
    topology = json.decode(topology)

    node_test_services = node_builders.instantiate_services(plan, topology, True)

    waku.interconnect_waku_nodes(plan, topology, node_test_services)
    _test_node_neighbours(plan, node_test_services)
    _test__add_waku_service_information(plan, node_test_services)

    for node_id in node_test_services.keys():
        plan.remove_service(node_id)


def _test_node_neighbours(plan, topology_information):
    for node_name in topology_information.keys():
        peers = waku.get_waku_peers(plan, node_name)
        plan.assert(value=peers, assertion="==", target_value=1)


def _test__add_waku_service_information(plan, node_test_services):
    # Already done in instantiate_services, so here just checking data is correct

    plan.assert(value=str(len(node_test_services)), assertion="==", target_value="2")
    plan.assert(value=str(node_test_services.get("test_waku_0")),
        assertion="!=", target_value="None")
    plan.assert(value=str(node_test_services.get("test_waku_1")),
        assertion="!=", target_value="None")

