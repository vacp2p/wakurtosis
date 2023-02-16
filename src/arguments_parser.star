# System Imports
vars = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")

def get_configuration_file_name(plan, input_args):
    # Parse command line argument (config file)
    config_file = vars.DEFAULT_CONFIG_FILE
    if hasattr(input_args, "config_file"):
        config_file = input_args.config_file
        plan.print("Got config file: %s" %config_file)
    else:
        plan.print("Got default config file: %s" %config_file)

    return config_file

