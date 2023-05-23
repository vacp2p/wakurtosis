# Python Imports
import argparse

# Project Imports
from src import vars


def parse_args():
    """ Parse command line args """
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--simulation_path", help="Simulation results path",
                        default=vars.G_DEFAULT_SIMULATION_PATH)
    parser.add_argument("-p", "--prometheus_port", help="Pometheus port")
    parser.add_argument("-i", "--infra", help="Metrics infrastructure type")
                                            
    args = parser.parse_args()

    simulation_path = args.simulation_path
    port = args.prometheus_port
    infra_type = args.infra

    return simulation_path, port, infra_type
