# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(vars.WAKU_MODULE)
prometheus = import_module(vars.PROMETHEUS_MODULE)
grafana = import_module(vars.GRAFANA_MODULE)
args_parser = import_module(vars.ARGUMENT_PARSER_MODULE)
wsl = import_module(vars.WSL_MODULE)
nodes = import_module(vars.NODE_BUILDERS_MODULE)

# todo: add subnetworks to run.sh
# todo: cambiar strings en node_builders y otros a variables del sistema


def run(plan, args):

    test = {"a":{"time": 10}, "b":{"time": 1}}
    hehe = test.keys()
    final = sorted(hehe, key=lambda x: (test[x]['time']))
    print(final)

    """
    # Load global config file
    config_file = args_parser.get_configuration_file_name(plan, args)
    config_json = read_file(src=config_file)
    config = json.decode(config_json)

    kurtosis_config = config['kurtosis']
    wsl_config = config['wsl']
    use_kubernetes = config['general']['kubernetes']
    interconnection_batch = kurtosis_config['interconnection_batch']
    subnetworks_configurations = kurtosis_config['subnetworks']

    # Load network topology
    network_topology_json = read_file(src=vars.TOPOLOGIES_LOCATION + vars.DEFAULT_TOPOLOGY_FILE)
    network_topology = json.decode(network_topology_json)

    # Set up nodes
    services = nodes.instantiate_services(plan, network_topology, False)

    # Set up Subnetworks if docker
    if not use_kubernetes:
        nodes.assign_subnetwork_to_nodes(network_topology)
        nodes.assign_subnetwork_configuration(subnetworks_configurations)

    # Set up prometheus + grafana
    prometheus_service = prometheus.set_up_prometheus(plan, services)
    grafana_service = grafana.set_up_grafana(plan, prometheus_service)

    # Interconnect nodes
    waku.interconnect_waku_nodes(plan, network_topology, services, interconnection_batch)

    # # Setup WSL & Start the Simulation
    wsl_service = wsl.init(plan, services, wsl_config)
    """