# System Imports
system_variables = import_module("github.com/logos-co/wakurtosis/src/system_variables.star")


def apply_default_to_input_args(input_args):
    
    same_config = system_variables.SAME_TOML_CONFIGURATION
    if hasattr(input_args, system_variables.SAME_TOML_CONFIGURATION_NAME):
        same_config = input_args.same_toml_configuration

    topology_file = system_variables.DEFAULT_TOPOLOGY_FILE    
    if hasattr(input_args, system_variables.TOPOLOGY_FILE_NAME):
        topology_file = input_args.topology

    simulation_time = system_variables.SIMULATION_TIME 
    if hasattr(input_args, "simulation_time"):
        simulation_time = int(input_args.simulation_time)
        print("Got simulation time: %ds." %simulation_time)
    else:
        print("Got default simulation time: %ds." %simulation_time)

    message_rate = system_variables.MESSAGE_RATE
    if hasattr(input_args, "message_rate"):
        message_rate = int(input_args.message_rate)
        print("Got message rate: %d pps" %message_rate)
    else:
        print("Got default message rate: %d packets per second" %message_rate)

    min_packet_size = system_variables.MIN_PACKET_SIZE
    if hasattr(input_args, "min_packet_size"):
        min_packet_size = int(input_args.min_packet_size)
        print("Got min. packet size of: %d bytes" %min_packet_size)
    else:
        print("Got default min. packet size of: %d bytes" %min_packet_size)
    
    max_packet_size = system_variables.MAX_PACKET_SIZE
    if hasattr(input_args, "max_packet_size"):
        max_packet_size = int(input_args.max_packet_size)
        print("Got max. packet size of: %d bytes" %max_packet_size)
    else:
        print("Got default max. packet size of: %d bytes" %max_packet_size)

    return struct(same_toml_configuration=same_config, topology_file=topology_file,  simulation_time=simulation_time, message_rate=message_rate, min_packet_size=min_packet_size, max_packet_size=max_packet_size)
