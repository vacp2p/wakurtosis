# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
node_builders = import_module(vars.NODE_BUILDERS_MODULE)
waku = import_module(vars.WAKU_MODULE)


def test_instantiate_services(plan):
    topology = read_file(src=vars.TEST_FILES_LOCATION +
                             vars.DEFAULT_TOPOLOGY_FILE_DEFAULT_ARGUMENT_VALUE)
    topology = json.decode(topology)

    node_builders.instantiate_services(plan, topology, True)

    for node_info in topology["nodes"].values():
        plan.assert(value="peer_id", assertion="IN", target_value=node_info.keys())
        plan.assert (value="ip_address", assertion="IN", target_value=node_info.keys())
        plan.assert (value="ports", assertion="IN", target_value=node_info.keys())

    node_builders.interconnect_nodes(plan, topology, 1)
    _test_node_neighbours(plan, topology)

    for node_id in topology["containers"].keys():
        plan.remove_service(node_id)


def _test_node_neighbours(plan, topology):
    for node_name, node_info in topology["nodes"].items():
        peers = waku.get_waku_peers(plan, node_info["container_id"], node_name)
        plan.assert(value=peers, assertion="==", target_value=1)


