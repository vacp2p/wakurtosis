# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
arg_parser = import_module(system_variables.ARGUMENT_PARSER_MODULE)


def test_load_config_args_default():
    input_args = struct()

    parsed = arg_parser.get_configuration_file_name(input_args)

    assert (value=parsed, assertion="==", target_value = system_variables.DEFAULT_CONFIG_FILE)


def test_load_config_args_given():
    input_args = struct(config_file="test.json")

    parsed = arg_parser.get_configuration_file_name(input_args)

    assert (value=parsed, assertion="==", target_value = "test.json")