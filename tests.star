# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
args_parser_test = import_module(vars.TEST_ARGUMENTS_MODULE)
file_helpers_test = import_module(vars.TEST_FILES_MODULE)
waku_test = import_module(vars.TEST_WAKU_MODULE)
wls_test = import_module(vars.TEST_WLS_MODULE)
node_builders_test = import_module(vars.TEST_NODE_BUILDERS_MODULE)
waku_builder_test = import_module(vars.TEST_WAKU_BUILDER_MODULE)
gowaku_builder_test = import_module(vars.TEST_GOWAKU_BUILDER_MODULE)
nwaku_builder_test = import_module(vars.TEST_NWAKU_BUILDER_MODULE)




def run(plan, args):

    args_parser_test.test_load_config_args_default(plan)
    args_parser_test.test_load_config_args_given(plan)

    file_helpers_test.test_get_toml_configuration_artifact_same_config_true(plan)
    file_helpers_test.test_get_toml_configuration_artifact_same_config_false(plan)
    file_helpers_test.test_generate_template_node_targets_single(plan)
    file_helpers_test.test_generate_template_node_targets_multiple(plan)
    file_helpers_test.test_generate_template_prometheus_url(plan)
    file_helpers_test.test_prepare_artifact_files_grafana(plan)

    waku_test.test_waku_methods(plan)

    node_builders_test.test_instantiate_services(plan)

    waku_builder_test.test_prepare_waku_ports_in_service(plan)

    waku_builder_test.test_prepare_waku_config_files_in_service(plan)
    waku_builder_test.test_add_waku_ports_info_to_topology(plan)


    gowaku_builder_test.test_prepare_gowaku_service(plan)
    gowaku_builder_test.test__prepare_gowaku_cmd_in_service(plan)

    nwaku_builder_test.test_prepare_nwaku_service(plan)
    nwaku_builder_test.test__prepare_nwaku_cmd_in_service(plan)

    wls_test.test_upload_config(plan)
    wls_test.test_create_new_topology_information(plan)
    wls_test.test_create_cmd(plan)
    wls_test.test_init(plan)
