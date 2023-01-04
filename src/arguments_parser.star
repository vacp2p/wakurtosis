# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

def load_config_args(input_args):

    # Parse command line argument (CONFIG_FILE_LOCATION)
    config_file_location = system_variables.CONFIG_FILE_LOCATION
    if hasattr(input_args, "config_file_location"):
        config_file_location = input_args.config_file_location
        print("Got config file location: %s" %config_file_location)
    else:
        print("Got default config file location: %s" %config_file_location)

    # Parse command line argument (config file)
    config_file = system_variables.CONFIG_FILE_NAME
    if hasattr(input_args, "config_file"):
        config_file = input_args.config_file
        print("Got config file: %s" %config_file)
    else:
        print("Got default config file: %s" %config_file)

    return struct(config_file_location=config_file_location, config_file=config_file)
