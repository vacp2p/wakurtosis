# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(vars.WAKU_MODULE)
prometheus = import_module(vars.PROMETHEUS_MODULE)
grafana = import_module(vars.GRAFANA_MODULE)
args_parser = import_module(vars.ARGUMENT_PARSER_MODULE)
wsl = import_module(vars.WSL_MODULE)
nodes = import_module(vars.NODE_BUILDERS_MODULE)


def run(plan, args):

    # Load global config file
    config_file = args_parser.get_configuration_file_name(plan, args)
    config_json = read_file(src=config_file)
    config = json.decode(config_json)

    kurtosis_config = config['kurtosis']
    wsl_config = config['wsl']
    interconnection_batch = kurtosis_config['interconnection_batch']

    # Load network topology
    waku_topology_json = read_file(src=vars.TOPOLOGIES_LOCATION + vars.DEFAULT_TOPOLOGY_FILE)
    waku_topology = json.decode(waku_topology_json)

    # Set up nodes
    services = nodes.instantiate_services(plan, waku_topology, False)

    # Set up prometheus + graphana
    prometheus_service = prometheus.set_up_prometheus(plan, services)
    grafana_service = grafana.set_up_grafana(plan, prometheus_service)

    waku.interconnect_waku_nodes(plan, waku_topology, services, interconnection_batch)

    # # Setup WSL & Start the Simulation
    wsl_service = wsl.init(plan, services, wsl_config)
