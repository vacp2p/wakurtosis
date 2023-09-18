# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
nwaku_builder = import_module(vars.NWAKU_BUILDER_MODULE)

def test_prepare_nwaku_service(plan):
    test_dict = {}
    topology = {"nodes": {"test1": {vars.GENNET_PORT_SHIFT_KEY: 0},
                          "test2": {vars.GENNET_PORT_SHIFT_KEY: 1}}}

    nwaku_builder.prepare_nwaku_service(["test1", "test2"], test_dict,
                                        ["test1.toml", "test2.toml"],
                                        ["a1", "a2"], "run",
                                        "id_1", topology, False)

    # hasattr doesn't work in dicts?
    plan.verify(value=str(test_dict.get("id_1")),
        assertion="!=", target_value="None")

    plan.verify(value=test_dict["id_1"].image,
        assertion="==", target_value=vars.NWAKU_IMAGE)

    for node in ["test1", "test2"]:
        plan.verify(value=str(test_dict["id_1"].ports[vars.WAKU_RPC_PORT_ID+vars.ID_STR_SEPARATOR+node].number),
            assertion="==", target_value = str(vars.WAKU_RPC_PORT_NUMBER +
                                               topology["nodes"][node][vars.GENNET_PORT_SHIFT_KEY]))
        plan.verify(value=str(test_dict["id_1"].ports[vars.PROMETHEUS_PORT_ID+vars.ID_STR_SEPARATOR+node].number),
            assertion="==", target_value=str(vars.PROMETHEUS_PORT_NUMBER +
                                             topology["nodes"][node][vars.GENNET_PORT_SHIFT_KEY]))
        plan.verify(value=str(test_dict["id_1"].ports[vars.WAKU_LIBP2P_PORT_ID+vars.ID_STR_SEPARATOR+node].number),
                assertion="==", target_value=str(vars.WAKU_LIBP2P_PORT +
                                                 topology["nodes"][node][vars.GENNET_PORT_SHIFT_KEY]))

    for node, file in zip(["test1", "test2"], ["a1", "a2"]):
        plan.verify(value=test_dict["id_1"].files[vars.CONTAINER_NODE_CONFIG_FILE_LOCATION+node],
                assertion="==", target_value=file)

    for node, file in zip(["test1", "test2"], ["run", "run"]):
        plan.verify (value=test_dict["id_1"].files[vars.CONTAINER_NODE_SCRIPT_RUN_LOCATION],
        assertion="==", target_value=file)

    for i in range(len(test_dict["id_1"].entrypoint)):
        plan.verify(value=test_dict["id_1"].entrypoint[i], assertion="==",
                target_value=vars.GENERAL_ENTRYPOINT[i])


def test__prepare_nwaku_cmd_in_service(plan):

    topology = {"nodes": {"a": {"port_shift": 0}, "b": {"port_shift": 1}}}
    result = nwaku_builder._prepare_nwaku_cmd_in_service(["a", "b"], ["c", "d"], topology)

    plan.verify(value=result[0],
            assertion="==",
            target_value=vars.CONTAINER_NODE_SCRIPT_RUN_LOCATION+
                vars.NWAKU_SCRIPT_ENTRYPOINT+" "+vars.CONTAINER_NODE_CONFIG_FILE_LOCATION
                +"a"+"/"+"c"+" "+"0"+" & "+vars.CONTAINER_NODE_SCRIPT_RUN_LOCATION+
                vars.NWAKU_SCRIPT_ENTRYPOINT+" "+vars.CONTAINER_NODE_CONFIG_FILE_LOCATION+
                "b"+"/"+"d"+" "+"1"
                )
