# Python Imports
import argparse

# Project Imports
from src import vars


def parse_args():
    """ Parse command line args """
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--simulation_path", help="Simulation results path",
                        default=vars.G_DEFAULT_SIMULATION_PATH)
    parser.add_argument("-t", "--toml_folder", help="Tomls folder name",
                        default=vars.G_DEFAULT_TOML_PATH)
    parser.add_argument("-p", "--prometheus_port", help="Pometheus port")

    args = parser.parse_args()

    simulation_path = args.simulation_path
    tomls_folder = args.toml_folder
    port = args.prometheus_port

    return simulation_path, tomls_folder, port
