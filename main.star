# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
prometheus = import_module(vars.PROMETHEUS_MODULE)
grafana = import_module(vars.GRAFANA_MODULE)
args_parser = import_module(vars.ARGUMENT_PARSER_MODULE)
wls = import_module(vars.WLS_MODULE)
nodes = import_module(vars.NODE_BUILDERS_MODULE)
nwaku_builder = import_module(vars.NWAKU_BUILDER_MODULE)
waku = import_module(vars.WAKU_MODULE)
gennet = import_module(vars.GENNET_MODULE)


def run(plan, args):
    plan.print(args)
    # Load global config_file_content file
    config_file_path = args_parser.get_configuration_file_name(plan, args)
    config_json = read_file(src=config_file_path)

    config_file_content = json.decode(config_json)

    kurtosis_config = config_file_content[vars.KURTOSIS_KEY]
    # gennet_config = config_file_content[vars.GENNET_KEY]
    interconnection_batch = kurtosis_config[vars.INTERCONNECTION_BATCH_KEY]

    bootstrap_node_service = nwaku_builder.instantiate_bootstrap_nwaku_service(plan, "node-bootstrap")
    node_rpc_port_id = vars.WAKU_RPC_PORT_ID + vars.ID_STR_SEPARATOR + "node-bootstrap"

    enr = waku.get_wakunode_enr(plan, "node-bootstrap", node_rpc_port_id)

    # Init gennet
    gennet_service = gennet.init(plan, config_file_path, enr)

    test_recipe = ExecRecipe(
        command = ["cat", "/gennet/network_data/network_data.json"],
        extract={
            "topology": ". | tojson",
        },
    )

    result = plan.wait(
        service_name = vars.GENNET_SERVICE_NAME,
        recipe=test_recipe,
        field="code",
        assertion="==",
        target_value=0
    )

    plan.print(result)
    plan.print(type(result))
    test = result["extract.topology"]
    plan.print(test)
    plan.print(type(test))

    test_2 = json.decode(test)
    plan.print(test_2)
    #plan.print(result["topology"])

    #plan.print(type(json.decode(result["extract.topology"])))
    #nodes.instantiate_services(plan, result, False, False)
    """







    
    # Load network topology
    network_topology = read_file(src=vars.TOPOLOGIES_LOCATION + vars.DEFAULT_TOPOLOGY_FILE)
    network_topology = json.decode(network_topology)

    # Use address in other node toml files
    nodes.instantiate_services(plan, network_topology, False, False)

    # Set up prometheus + grafana
    prometheus_service = prometheus.set_up_prometheus(plan, network_topology)

    grafana_service = grafana.set_up_grafana(plan, prometheus_service)

    nodes.interconnect_nodes(plan, network_topology, interconnection_batch)

    # Setup WLS & Start the Simulation
    wls_service = wls.init(plan, network_topology, config_file_path)
    """

