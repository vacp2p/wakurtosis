import json
import unittest
import os

from src.utils import files


class TestFiles(unittest.TestCase):

    def test_load_config_file(self):
        config = files.load_config_file("test_files/test_config.json")
        self.assertEqual(config["general"]["prng_seed"], 1234)
        self.assertEqual(config["kurtosis"]["enclave_name"], "test")

    def test_config_file_error(self):
        with self.assertRaises(FileNotFoundError):
            files.load_config_file("test_files/test_config_error.json")

    def test_load_topology(self):
        test_topology = files.load_topology("test_files/test_topology.json")
        self.assertEqual(test_topology["containers"]["containers_0"][0], "node_0")
        self.assertEqual(test_topology["nodes"]["node_0"]["image"], "nim-waku")

    def test_load_topology_error(self):
        with self.assertRaises(FileNotFoundError):
            files.load_topology("test_files/test_topology_error.json")

    def test_save_messages_to_json(self):
        msgs_dict = {"test": "test"}
        files.save_messages_to_json(msgs_dict)
        with open("messages.json", "r") as f:
            self.assertEqual(json.load(f), msgs_dict)
        os.remove("messages.json")
