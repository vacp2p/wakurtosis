waku = import_module("github.com/logos-co/wakurtosis/waku_methods.star")
prometheus = import_module("github.com/logos-co/wakurtosis/prometheus.star")
grafana = import_module("github.com/logos-co/wakurtosis/grafana.star")


def run(args):
    waku_topology = read_file(src="github.com/logos-co/wakurtosis/kurtosis-module/starlark/waku_test_topology.json")

    same_toml_configuration = args.same_toml_configuration
    waku_topology = json.decode(waku_topology)

    waku_topology = {
        "waku_0": {
            "ports_shift": 0,
            "topics": ["test"],
            "static_nodes": [
                "waku_1",
            ]
        },
        "waku_1": {
            "ports_shift": 1,
            "topics": ["test"],
            "static_nodes": [
                "waku_0"
            ]
        },
        "waku_2": {
            "ports_shift": 1,
            "topics": ["test"],
            "static_nodes": [
                "waku_0",
                "waku_1"
            ]
        }
    }

    services = waku.instantiate_waku_nodes(waku_topology, same_toml_configuration)

    # Set up prometheus + graphana
    prometheus_service = prometheus.set_up_prometheus(services)
    grafana.set_up_graphana(prometheus_service)

    waku.interconnect_waku_nodes(waku_topology, services)

    waku.send_test_messages(waku_topology, 5, "0.5")

    waku.get_waku_peers(waku_topology.keys()[1])
