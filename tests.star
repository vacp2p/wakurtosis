# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
args_parser_test = import_module(system_variables.TEST_ARGUMENTS_MODULE)
file_helpers_test = import_module(system_variables.TEST_FILES_MODULE)
waku_test = import_module(system_variables.TEST_WAKU_MODULE)


def run(args):
    args_parser_test.test_load_config_args_default()
    args_parser_test.test_load_config_args_given()

    file_helpers_test.test_get_toml_configuration_artifact_same_config_true()
    file_helpers_test.test_get_toml_configuration_artifact_same_config_false()
    file_helpers_test.test_generate_template_node_targets_single()
    file_helpers_test.test_generate_template_node_targets_multiple()
    file_helpers_test.test_generate_template_prometheus_url()
    file_helpers_test.test_prepare_artifact_files_grafana()

    waku_test.test_network_creation()
    waku_test.test_create_waku_id()
    waku_test.test__merge_peer_ids()
    waku_test.test__add_information()
