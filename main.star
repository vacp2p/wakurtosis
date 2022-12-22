# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
waku = import_module(system_variables.WAKU_MODULE)
prometheus = import_module(system_variables.PROMETHEUS_MODULE)
grafana = import_module(system_variables.GRAFANA_MODULE)
parser = import_module(system_variables.ARGUMENT_PARSER_MODULE)


def run(args):
    args = parser.apply_default_to_input_args(args)

    same_toml_configuration = args.same_toml_configuration
    waku_topology = read_file(src=system_variables.TOPOLOGIES_LOCATION + args.topology_file)

    waku_topology = json.decode(waku_topology)

    # Set up nodes
    services = waku.instantiate_waku_nodes(waku_topology, same_toml_configuration)

    # Set up prometheus + graphana
    prometheus_service = prometheus.set_up_prometheus(services)
    grafana_service = grafana.set_up_graphana(prometheus_service)

    waku.interconnect_waku_nodes(waku_topology, services)

    waku.send_test_messages(waku_topology, system_variables.NUMBER_TEST_MESSAGES,
                            system_variables.DELAY_BETWEEN_TEST_MESSAGE)

    waku.get_waku_peers(waku_topology.keys()[1])
