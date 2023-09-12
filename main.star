# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
prometheus = import_module(vars.PROMETHEUS_MODULE)
grafana = import_module(vars.GRAFANA_MODULE)
args_parser = import_module(vars.ARGUMENT_PARSER_MODULE)
wls = import_module(vars.WLS_MODULE)
collectnet = import_module(vars.COLLECTNET_MODULE)
nodes = import_module(vars.NODE_BUILDERS_MODULE)
assertions = import_module(vars.ASSERTIONS_MODULE)


def run(plan, args):

    # Load global config file
    config_file = args_parser.get_configuration_file_name(plan, args)
    config_json = read_file(src=config_file)
    config = json.decode(config_json)

    kurtosis_config = config[vars.KURTOSIS_KEY]
    interconnection_batch = kurtosis_config[vars.INTERCONNECTION_BATCH_KEY]

    # Load network topology
    network_topology = read_file(src=vars.TOPOLOGIES_LOCATION + vars.DEFAULT_TOPOLOGY_FILE)
    network_topology = json.decode(network_topology)

    # Set up nodes
    nodes.instantiate_services(plan, network_topology, not kurtosis_config["interconnect_nodes"], False)

    # Set up prometheus + grafana
    if kurtosis_config["monitoring"]:
        prometheus_service = prometheus.set_up_prometheus(plan, network_topology)
        grafana_service = grafana.set_up_grafana(plan, prometheus_service)

    # Interconnect nodes if needed
    if kurtosis_config[vars.INTERCONNECT_NODES]:
        nodes.interconnect_nodes(plan, network_topology, interconnection_batch)

    # Start topology collection if requested
    if "collectnet" in kurtosis_config:
      collectnet_service = collectnet.init(plan, network_topology, config_file)

    # Setup WLS & Start the Simulation
    if kurtosis_config["injection"]:
        wls_service = wls.init(plan, network_topology, config_file, prometheus_service)

    # Tests
    if kurtosis_config["testing"]:
        assertions.start_test(plan, kurtosis_config, network_topology)

