# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Project Imports
wls = import_module(vars.WLS_MODULE)


def test_upload_config(plan):
    test_config = vars.TEST_FILES_LOCATION + "test_config_file.json"
    test = wls.upload_config(plan, test_config, "test_config")

    plan.verify(value=test, assertion="==", target_value="test_config")


def test_create_new_topology_information(plan):
    test_topology = {}
    test = wls.create_new_topology_information(plan, test_topology, "test_topology")

    plan.verify(value=test, assertion="==", target_value="test_topology")

def test_create_cmd(plan):
    config_file = "test.json"
    test = wls.create_cmd(config_file)
    result = [vars.WLS_CONFIG_FILE_FLAG, vars.WLS_CONFIG_PATH + config_file,
              vars.WLS_TOPOLOGY_FILE_FLAG, vars.WLS_TOPOLOGY_PATH + vars.CONTAINER_TOPOLOGY_FILE_NAME_WLS]

    for i in range(len(result)):
        plan.verify(value=test[i], assertion="==", target_value=result[i])

def test_init(plan):
    test_config = vars.TEST_FILES_LOCATION + "test_config_file.json"
    test = wls.upload_config(plan, test_config, "test_config_2")

    test_topology = {}

    test_wls_service = wls.init(plan, test_topology, test_config)

    plan.remove_service(vars.WLS_SERVICE_NAME)