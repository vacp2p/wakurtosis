# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Test Imports
tests_arguments = import_module(system_variables.TEST_ARGUMENTS_MODULE)
test_files = import_module(system_variables.TEST_FILES_MODULE)
test_waku = import_module(system_variables.TEST_WAKU_MODULE)


def run(args):

    tests_arguments.test_apply_default_to_input_args_default()
    tests_arguments.test_apply_default_to_input_args_with_input()

    test_files.test_get_toml_configuration_artifact_same_config_true()
    test_files.test_get_toml_configuration_artifact_same_config_false()
    test_files.test_generate_template_node_targets_single()
    test_files.test_generate_template_node_targets_multiple()
    test_files.test_generate_template_prometheus_url()
    test_files.test_prepare_artifact_files_grafana()

    test_waku.test_network_creation()
    test_waku.test_create_waku_id()
    test_waku.test__merge_peer_ids()
    test_waku.test__add_information()