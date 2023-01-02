# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
files = import_module(system_variables.FILE_HELPERS_MODULE)


# todo: Would be nice to mock upload files

def test_get_toml_configuration_artifact_same_config_true():
    artifact_id, file_name = files.get_toml_configuration_artifact("test", True, "id_1")

    assert(value=file_name, assertion="==", target_value=system_variables.GENERAL_TOML_CONFIGURATION_NAME)
    assert (value=artifact_id, assertion="==", target_value="id_1")


def test_get_toml_configuration_artifact_same_config_false():
    artifact_id, file_name = files.get_toml_configuration_artifact("test", False, "id_2")

    assert(value=file_name, assertion="==", target_value="test.toml")
    assert(value=artifact_id, assertion="==", target_value="id_2")


def test_generate_template_data_single():
    service_struct = struct(ip_address="1.1.1.1", ports={"http": PortSpec(number=80)})
    services_example={"test1":{"service_info": service_struct}}

    template_data = files.generate_template_targets_with_port(services_example, "http")

    assert(value=template_data["targets"], assertion="==", target_value='["1.1.1.1:80"]')


def test_generate_template_data_multiple():
    service_struct_1 = struct(ip_address="1.1.1.1", ports={"http": PortSpec(number=80)})
    service_struct_2 = struct(ip_address="2.2.2.2", ports={"http": PortSpec(number=88)})
    services_example={"test1":{"service_info": service_struct_1},
                      "test2":{"service_info": service_struct_2}}

    template_data = files.generate_template_targets_with_port(services_example, "http")

    assert(value=template_data["targets"], assertion="==",
            target_value='["1.1.1.1:80","2.2.2.2:88"]')
