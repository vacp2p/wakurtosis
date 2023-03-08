# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku_builders = import_module(vars.WAKU_BUILDER_MODULE)


def test_prepare_waku_ports_in_service(plan):
    topology = {"nodes":{"test1": {vars.GENNET_PORT_SHIFT_KEY : 0},
                         "test2": {vars.GENNET_PORT_SHIFT_KEY : 1}}}
    ports = waku_builders.prepare_waku_ports_in_service(["test1", "test2"], topology)

    for node_name in ["test1", "test2"]:
        plan.assert(value=str(ports[vars.RPC_PORT_ID+"_"+node_name].number),
            assertion="==", target_value = str(vars.WAKU_RPC_PORT_NUMBER +
                                           topology["nodes"][node_name][vars.GENNET_PORT_SHIFT_KEY]))
        plan.assert(value=str(ports[vars.PROMETHEUS_PORT_ID+"_"+node_name].number),
            assertion="==", target_value=str(vars.PROMETHEUS_PORT_NUMBER +
                                             topology["nodes"][node_name][vars.GENNET_PORT_SHIFT_KEY]))
        plan.assert(value=str(ports[vars.WAKU_LIBP2P_PORT_ID+"_"+node_name].number),
                assertion="==", target_value=str(vars.WAKU_LIBP2P_PORT +
                                             topology["nodes"][node_name][vars.GENNET_PORT_SHIFT_KEY]))

def test_prepare_waku_config_files_in_service(plan):
    names = ["test1", "test2"]
    artifact_ids = ["a1", "a2"]

    files = waku_builders.prepare_waku_config_files_in_service(names, artifact_ids)

    for name, artif_id in zip(names, artifact_ids):
        plan.assert(value=files[vars.CONTAINER_NODE_CONFIG_FILE_LOCATION+name],
                    assertion="==", target_value=artif_id)

def test_add_waku_ports_info_to_topology(plan):
    network_topology = {"nodes": {"test1": {}, "test2": {}}}
    service_struct_1 = struct(ports={vars.RPC_PORT_ID+"_test1": PortSpec(number=1),
                                     vars.WAKU_LIBP2P_PORT_ID+"_test1": PortSpec(number=2),
                                     vars.PROMETHEUS_PORT_ID+"_test1": PortSpec(number=3)})

    node_info1 = {vars.GENNET_NODE_CONTAINER_KEY: "cid1"}

    services = {"cid1": service_struct_1}

    waku_builders.add_waku_ports_info_to_topology(network_topology, services, node_info1, "test1")

    plan.assert(value=str(network_topology["nodes"]["test1"]["ports"][vars.RPC_PORT_ID+"_test1"][0]),
                assertion="==", target_value=str(1))
    plan.assert(value=str(network_topology["nodes"]["test1"]["ports"][vars.WAKU_LIBP2P_PORT_ID+"_test1"][0]),
                assertion="==", target_value=str(2))
    plan.assert(value=str(network_topology["nodes"]["test1"]["ports"][vars.PROMETHEUS_PORT_ID+"_test1"][0]),
                assertion="==", target_value=str(3))
