# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
node_builders = import_module(vars.NODE_BUILDERS_MODULE)
waku = import_module(vars.WAKU_MODULE)


def test_prepare_nwaku_service(plan):
    test_dict = {}
    node_builders.prepare_nwaku_service("test", test_dict, "test.toml", "id_1")

    # hasattr doesn't work in dicts?
    plan.assert(value=str(test_dict.get("test")),
        assertion="!=", target_value="None")
    plan.assert(value=test_dict["test"].image,
        assertion="==", target_value=vars.NWAKU_IMAGE)
    plan.assert(value=str(test_dict["test"].ports[vars.WAKU_RPC_PORT_ID].number),
        assertion="==", target_value=str(vars.WAKU_RPC_PORT_NUMBER))
    plan.assert(value=str(test_dict["test"].ports[vars.PROMETHEUS_PORT_ID].number),
        assertion="==", target_value=str(vars.PROMETHEUS_PORT_NUMBER))
    plan.assert(value=str(test_dict["test"].ports[vars.WAKU_LIBP2P_PORT_ID].number),
            assertion="==", target_value=str(vars.WAKU_LIBP2P_PORT))
    plan.assert(value=test_dict["test"].files[vars.CONTAINER_NODE_CONFIG_FILE_LOCATION],
            assertion="==", target_value="id_1")
    # Only way to assert lists?
    for i in range(len(test_dict["test"].entrypoint)):
        plan.assert(value=test_dict["test"].entrypoint[i],
                assertion="==", target_value=vars.NWAKU_ENTRYPOINT[i])
    plan.assert(value=test_dict["test"].cmd[0],
            assertion="==", target_value=vars.NODE_CONFIGURATION_FILE_FLAG +
            vars.CONTAINER_NODE_CONFIG_FILE_LOCATION +
            "test.toml")



def test_prepare_gowaku_service(plan):
    test_dict = {}
    node_builders.prepare_gowaku_service("test", test_dict, "test.toml", "id_2")

    # hasattr doesn't work in dicts?
    plan.assert(value=str(test_dict.get("test")),
        assertion="!=", target_value="None")
    plan.assert(value=test_dict["test"].image,
        assertion="==", target_value=vars.GOWAKU_IMAGE)
    plan.assert(value=str(test_dict["test"].ports[vars.WAKU_RPC_PORT_ID].number),
        assertion="==", target_value=str(vars.WAKU_RPC_PORT_NUMBER))
    plan.assert(value=str(test_dict["test"].ports[vars.PROMETHEUS_PORT_ID].number),
        assertion="==", target_value=str(vars.PROMETHEUS_PORT_NUMBER))
    plan.assert(value=str(test_dict["test"].ports[vars.WAKU_LIBP2P_PORT_ID].number),
            assertion="==", target_value=str(vars.WAKU_LIBP2P_PORT))
    plan.assert(value=test_dict["test"].files[vars.CONTAINER_NODE_CONFIG_FILE_LOCATION],
            assertion="==", target_value="id_2")
    # Only way to assert lists?
    for i in range(len(test_dict["test"].entrypoint)):
        plan.assert(value=test_dict["test"].entrypoint[i],
                assertion="==", target_value=vars.GOWAKU_ENTRYPOINT[i])
    plan.assert(value=test_dict["test"].cmd[0],
            assertion="==", target_value=vars.NODE_CONFIGURATION_FILE_FLAG +
            vars.CONTAINER_NODE_CONFIG_FILE_LOCATION + "test.toml")


def test_instantiate_services(plan):
    topology = read_file(src=vars.TEST_FILES_LOCATION +
                             vars.DEFAULT_TOPOLOGY_FILE_DEFAULT_ARGUMENT_VALUE)
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
    plan.assert(value=str(node_test_services.get("nwaku_0")),
        assertion="!=", target_value="None")
    plan.assert(value=str(node_test_services.get("nwaku_1")),
        assertion="!=", target_value="None")

