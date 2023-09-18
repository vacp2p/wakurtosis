# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
call_protocols = import_module(vars.CALL_PROTOCOLS)


def start_test(plan, kurtosis_config, network_topology):
    for name, values in kurtosis_config["assertions"].items():
        exec_recipe = ExecRecipe(
            command=["sleep", str(values["waiting"])]
        )

        plan.exec(
            service_name=network_topology["nodes"].values()[0]["container_id"],
            recipe=exec_recipe)

        for service_name, service_info in network_topology["nodes"].items():
            extract = {"jq_extract": values["jq_extract"]}

            response = call_protocols.send_http_get_req(plan, service_info["container_id"],
                                                        vars.WAKU_RPC_PORT_ID + vars.ID_STR_SEPARATOR + service_name,
                                                        values["endpoint"], extract)

            plan.verify(value=response["code"], assertion="==", target_value = 200)
            plan.verify(value=response["extract.jq_extract"], assertion=">",
                target_value=values["expected_value"])
            plan.remove_service(service_info["container_id"])
