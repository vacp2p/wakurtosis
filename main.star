waku = import_module("github.com/logos-co/wakurtosis/src/waku_methods.star")
prometheus = import_module("github.com/logos-co/wakurtosis/src/prometheus.star")
grafana = import_module("github.com/logos-co/wakurtosis/src/grafana.star")
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")
parser = import_module("github.com/logos-co/wakurtosis/src/arguments_parser.star")


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

    waku.send_test_messages(waku_topology, 5, "0.5")

    waku.get_waku_peers(waku_topology.keys()[1])
