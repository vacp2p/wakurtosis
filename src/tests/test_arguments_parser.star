# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

# Module Imports
arg_parser = import_module(vars.ARGUMENT_PARSER_MODULE)


def test_load_config_args_default(plan):
    input_args = struct()

    parsed = arg_parser.get_configuration_file_name(plan, input_args)

    plan.verify(value=parsed, assertion="==", target_value = vars.DEFAULT_CONFIG_FILE)


def test_load_config_args_given(plan):
    input_args = struct(config_file="test.json")

    parsed = arg_parser.get_configuration_file_name(plan, input_args)

    plan.verify(value=parsed, assertion="==", target_value = "test.json")
