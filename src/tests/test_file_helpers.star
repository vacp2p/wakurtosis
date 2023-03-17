# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(vars.FILE_HELPERS_MODULE)


def test_get_toml_configuration_artifact_same_config_true(plan):
    artifact_id = files.get_toml_configuration_artifact(plan, "test.toml", "id_1", True)

    plan.assert(value=artifact_id, assertion="==", target_value="id_1")


def test_get_toml_configuration_artifact_same_config_false(plan):
    # This test should be mocked, but there are not enough tools for this, as topology generated
    # should be empty. test.toml file is there specifically for this test.
    artifact_id = files.get_toml_configuration_artifact(plan, "test.toml", "id_2", True)

    plan.assert(value=artifact_id, assertion="==", target_value="id_2")


def test_generate_template_node_targets_single(plan):
    network_topology={"nodes": {"test1":{"ip_address": "1.1.1.1",
                                         "ports": { "rpc_test1": (80, 'tcp')}}}}

    template_data = files.generate_template_node_targets(network_topology, "rpc", "targets")

    plan.assert(value=template_data["targets"], assertion="==", target_value='["1.1.1.1:80"]')


def test_generate_template_node_targets_multiple(plan):
    network_topology={"nodes": {"test1":{"ip_address": "1.1.1.1", "ports": { "rpc_test1": (80, 'tcp')}},
                                "test2":{"ip_address": "2.2.2.2", "ports": { "rpc_test2": (10, 'tcp')}}}}

    template_data = files.generate_template_node_targets(network_topology, "rpc", "targets")

    plan.assert(value=template_data["targets"], assertion="==",
                target_value='["1.1.1.1:80","2.2.2.2:10"]')

def test_generate_template_prometheus_url(plan):
    prometheus_service_struct = struct(ip_address="1.2.3.4",
                                       ports={vars.PROMETHEUS_PORT_ID:
                                          PortSpec(number=vars.PROMETHEUS_PORT_NUMBER)})

    result = files.generate_template_prometheus_url(prometheus_service_struct)
    plan.assert(value=result["prometheus_url"], assertion="==", target_value="1.2.3.4:8008")

def test_prepare_artifact_files_grafana(plan):
    config, custom, dashboard = files.prepare_artifact_files_grafana(plan, "a", "b", "c")

    plan.assert(value=config, assertion="==", target_value="a")
    plan.assert(value=custom, assertion="==", target_value="b")
    plan.assert(value=dashboard, assertion="==", target_value="c")
