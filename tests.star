# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
args_parser_test = import_module(system_variables.TEST_ARGUMENTS_MODULE)
file_helpers_test = import_module(system_variables.TEST_FILES_MODULE)
waku_test = import_module(system_variables.TEST_WAKU_MODULE)


def run(args):
    test_load_config_args_default()
    test_load_config_args_given()

    test_get_toml_configuration_artifact_same_config_true()
    test_get_toml_configuration_artifact_same_config_false()
    test_generate_template_node_targets_single()
    test_generate_template_node_targets_multiple()
    test_generate_template_prometheus_url()
    test_prepare_artifact_files_grafana()

    test_network_creation()
    test_create_waku_id()
    test__merge_peer_ids()
    test__add_information()
