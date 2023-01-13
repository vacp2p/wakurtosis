# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

def get_configuration_file_name(input_args):
    # Parse command line argument (config file)
    config_file = system_variables.DEFAULT_CONFIG_FILE
    if hasattr(input_args, "config_file"):
        config_file = input_args.config_file
        print("Got config file: %s" %config_file)
    else:
        print("Got default config file: %s" %config_file)

    return config_file

