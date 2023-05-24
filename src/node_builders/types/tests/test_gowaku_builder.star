# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
gowaku_builder = import_module(vars.GOWAKU_BUILDER_MODULE)


def test_prepare_gowaku_service(plan):
    test_dict = {}
    topology = {"nodes": {"test1": {vars.GENNET_PORT_SHIFT_KEY: 0},
                          "test2": {vars.GENNET_PORT_SHIFT_KEY: 1}}}

    gowaku_builder.prepare_gowaku_service(["test1", "test2"], test_dict,
                                          ["test1.toml", "test2.toml"],
                                          ["a1", "a2"],
                                          "id_1", topology)

    # hasattr doesn't work in dicts?
    plan.assert(value=str(test_dict.get("id_1")),
        assertion="!=", target_value="None")

    plan.assert(value=test_dict["id_1"].image,
        assertion="==", target_value=vars.GOWAKU_IMAGE)

    for node in ["test1", "test2"]:
        plan.assert(value=str(test_dict["id_1"].ports[vars.WAKU_RPC_PORT_ID+vars.ID_STR_SEPARATOR+node].number),
            assertion="==", target_value = str(vars.WAKU_RPC_PORT_NUMBER +
                                               topology["nodes"][node][vars.GENNET_PORT_SHIFT_KEY]))
        plan.assert(value=str(test_dict["id_1"].ports[vars.PROMETHEUS_PORT_ID+vars.ID_STR_SEPARATOR+node].number),
            assertion="==", target_value=str(vars.PROMETHEUS_PORT_NUMBER +
                                             topology["nodes"][node][vars.GENNET_PORT_SHIFT_KEY]))
        plan.assert(value=str(test_dict["id_1"].ports[vars.WAKU_LIBP2P_PORT_ID+vars.ID_STR_SEPARATOR+node].number),
                assertion="==", target_value=str(vars.WAKU_LIBP2P_PORT +
                                                 topology["nodes"][node][vars.GENNET_PORT_SHIFT_KEY]))

    for node, file in zip(["test1", "test2"], ["a1", "a2"]):
        plan.assert(value=test_dict["id_1"].files[vars.CONTAINER_NODE_CONFIG_FILE_LOCATION+node],
                assertion="==", target_value=file)

    for i in range(len(test_dict["id_1"].entrypoint)):
        plan.assert(value=test_dict["id_1"].entrypoint[i], assertion="==",
                target_value=vars.GENERAL_ENTRYPOINT[i])


def test__prepare_gowaku_cmd_in_service(plan):

    topology = {"nodes": {"a": {"port_shift": 0}, "b": {"port_shift": 1}}}
    result = gowaku_builder._prepare_gowaku_cmd_in_service(["a", "b"], ["c", "d"], topology)

    plan.assert(value=result[0],
            assertion="==",
            target_value=vars.GOWAKU_ENTRYPOINT+" "+vars.WAKUNODE_CONFIGURATION_FILE_FLAG+
                vars.CONTAINER_NODE_CONFIG_FILE_LOCATION+"a"+"/"+"c"+" "+
                vars.WAKUNODE_PORT_SHIFT_FLAG+"0"+" & "+
                vars.GOWAKU_ENTRYPOINT+" "+vars.WAKUNODE_CONFIGURATION_FILE_FLAG+
                vars.CONTAINER_NODE_CONFIG_FILE_LOCATION+"b"+"/"+"d"+" "+
                vars.WAKUNODE_PORT_SHIFT_FLAG+"1"
                )
