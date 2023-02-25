# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(vars.WAKU_MODULE)
prometheus = import_module(vars.PROMETHEUS_MODULE)
grafana = import_module(vars.GRAFANA_MODULE)
args_parser = import_module(vars.ARGUMENT_PARSER_MODULE)
wls = import_module(vars.WLS_MODULE)
nodes = import_module(vars.NODE_BUILDERS_MODULE)
nomos = import_module(vars.NOMOS_MODULE)


def run(plan, args):

    # Load global config file
    config_file = args_parser.get_configuration_file_name(plan, args)
    config_json = read_file(src=config_file)
    config = json.decode(config_json)

    kurtosis_config = config[vars.KURTOSIS_KEY]
    wls_config = config[vars.WLS_KEY]
    interconnection_batch = kurtosis_config[vars.INTERCONNECTION_BATCH_KEY]

    # Load network topology
    network_topology = read_file(src=vars.TOPOLOGIES_LOCATION + vars.DEFAULT_TOPOLOGY_FILE)
    network_topology = json.decode(network_topology)

    # Set up nodes
    nodes.instantiate_services(plan, network_topology, False)

    # Set up prometheus + grafana
    prometheus_service = prometheus.set_up_prometheus(plan, network_topology)

    grafana_service = grafana.set_up_grafana(plan, prometheus_service)

    waku.interconnect_waku_nodes(plan, network_topology, interconnection_batch)

    # Setup WLS & Start the Simulation
    wls_service = wls.init(plan, network_topology, wls_config)
