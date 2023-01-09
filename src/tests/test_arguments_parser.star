# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
arg_parser = import_module(system_variables.ARGUMENT_PARSER_MODULE)


def test_apply_default_to_input_args_default():
    input_args = struct()

    parsed = arg_parser.apply_default_to_input_args(input_args)
    number_attributes = len(json.decode(json.encode(parsed)))

    assert (value=str(parsed.same_toml_configuration),
            assertion="==",
            target_value = str(system_variables.SAME_TOML_CONFIGURATION_DEFAULT_ARGUMENT_VALUE))
    assert (value=parsed.topology_file,
            assertion="==",
            target_value=system_variables.DEFAULT_TOPOLOGY_FILE_DEFAULT_ARGUMENT_VALUE)
    assert (value=str(number_attributes), assertion="==", target_value = "2")


def test_apply_default_to_input_args_with_input():
    input_args = struct(same_toml_configuration="test_config",
                        topology_file="test_topology")

    parsed = arg_parser.apply_default_to_input_args(input_args)

    number_attributes = len(json.decode(json.encode(parsed)))

    assert (value=str(parsed.same_toml_configuration),
            assertion="==",
            target_value = "test_config")
    assert (value=parsed.topology_file,
            assertion="==",
            target_value="test_topology")
    assert (value=str(number_attributes), assertion="==", target_value = "2")
