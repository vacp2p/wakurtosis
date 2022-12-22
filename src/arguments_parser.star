system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

def apply_default_to_input_args(input_args):
    same_config = system_variables.SAME_TOML_CONFIGURATION
    topology_file = system_variables.DEFAULT_TOPOLOGY_FILE

    if hasattr(input_args, system_variables.SAME_TOML_CONFIGURATION_NAME):
        same_config = input_args.same_toml_configuration

    if hasattr(input_args, system_variables.TOPOLOGY_FILE_NAME):
        topology_file = input_args.topology

    return struct(same_toml_configuration=same_config, topology_file=topology_file)
