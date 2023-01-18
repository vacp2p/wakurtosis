# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(system_variables.WAKU_MODULE)
prometheus = import_module(system_variables.PROMETHEUS_MODULE)
grafana = import_module(system_variables.GRAFANA_MODULE)
args_parser = import_module(system_variables.ARGUMENT_PARSER_MODULE)
wsl = import_module(system_variables.WSL_MODULE)
gennet = import_module(system_variables.GENNET_MODULE)

def run(args):
    
    # Load global config file
    config_file = args_parser.get_configuration_file_name(args)
    config_json = read_file(src=config_file)
    config = json.decode(config_json)
    
    # Load network topology
    waku_topology_json = read_file(src=system_variables.TOPOLOGIES_LOCATION + 'network_data.json')
    waku_topology_json = read_file(src="github.com/logos-co/wakurtosis/" + config['topology_path'] + 'network_data.json')
    waku_topology = json.decode(waku_topology_json)

    # # Set up nodes
    same_toml_configuration = config['same_toml_configuration']
    waku_services = waku.instantiate_waku_nodes(waku_topology, same_toml_configuration)

    # # Set up prometheus + grafana
    prometheus_service = prometheus.set_up_prometheus(waku_services)
    grafana_service = grafana.set_up_grafana(prometheus_service)

    waku.interconnect_waku_nodes(waku_topology, waku_services)

    # # Setup WSL & Start the Simulation
    wsl_service = wsl.init(waku_services,  config['simulation_time'], config['message_rate'], config['min_packet_size'], config['max_packet_size'], config['inter_msg_type'], config['dist_type'], config['emitters_fraction'])