# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(system_variables.FILE_HELPERS_MODULE)


def test_get_toml_configuration_artifact_same_config_true():
    artifact_id, file_name = files.get_toml_configuration_artifact("test", True, "id_1")

    assert(value=file_name, assertion="==", target_value=system_variables.GENERAL_TOML_CONFIGURATION_NAME)
    assert (value=artifact_id, assertion="==", target_value="id_1")


def test_get_toml_configuration_artifact_same_config_false():
    artifact_id, file_name = files.get_toml_configuration_artifact("test", False, "id_2")

    assert(value=file_name, assertion="==", target_value="test.toml")
    assert(value=artifact_id, assertion="==", target_value="id_2")


def test_generate_template_node_targets_single():
    service_struct = struct(ip_address="1.1.1.1", ports={"http": PortSpec(number=80)})
    services_example={"test1":{"service_info": service_struct}}

    template_data = files.generate_template_node_targets(services_example, "http")

    assert(value=template_data["targets"], assertion="==", target_value='["1.1.1.1:80"]')


def test_generate_template_node_targets_multiple():
    service_struct_1 = struct(ip_address="1.1.1.1", ports={"http": PortSpec(number=80)})
    service_struct_2 = struct(ip_address="2.2.2.2", ports={"http": PortSpec(number=88)})
    services_example={"test1":{"service_info": service_struct_1},
                      "test2":{"service_info": service_struct_2}}

    template_data = files.generate_template_node_targets(services_example, "http")

    assert(value=template_data["targets"], assertion="==",target_value='["1.1.1.1:80","2.2.2.2:88"]')

def test_generate_template_prometheus_url():
    prometheus_service_struct = struct(ip_address="1.2.3.4",
                               ports={system_variables.PROMETHEUS_PORT_ID:
                                          PortSpec(number=system_variables.PROMETHEUS_TCP_PORT)})

    result = files.generate_template_prometheus_url(prometheus_service_struct)
    assert(value=result["prometheus_url"], assertion="==", target_value="1.2.3.4:8008")

def test_prepare_artifact_files_grafana():
    config, custom, dashboard = files.prepare_artifact_files_grafana("a", "b", "c")

    assert(value=config, assertion="==", target_value="a")
    assert (value=custom, assertion="==", target_value="b")
    assert (value=dashboard, assertion="==", target_value="c")