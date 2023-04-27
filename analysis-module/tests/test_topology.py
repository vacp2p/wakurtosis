# Python Imports
import unittest
from unittest.mock import patch

# Project Imports
from src import topology


class TestTopology(unittest.TestCase):
    @patch('builtins.open')
    @patch('tomllib.load')
    def test_load_topics_nwaku(self, mock_toml_load, mock_open):
        mock_node_info = {
            "node_config": "config.toml",
            "image": "nim-waku",
        }
        mock_nodes = {"node1": {}, "node2": {}}
        mock_toml_config = {"topics": "topic1 topic2 topic3"}
        mock_toml_load.return_value = mock_toml_config

        topology._load_topics(mock_node_info, mock_nodes, "node1", "/path/to/tomls/")
        mock_open.assert_called_once_with('/path/to/tomls/config.toml', mode='rb')
        mock_toml_load.assert_called_once_with(mock_open.return_value.__enter__.return_value)
        self.assertListEqual(mock_nodes["node1"]["topics"], ["topic1", "topic2", "topic3"])

    @patch('builtins.open')
    @patch('tomllib.load')
    def test_load_topics_gowaku(self, mock_toml_load, mock_open):
        mock_node_info = {
            "node_config": "config.toml",
            "image": "go-waku",
        }
        mock_nodes = {"node1": {}, "node2": {}}
        mock_toml_config = {"topics": ["topic1", "topic2", "topic3"]}
        mock_toml_load.return_value = mock_toml_config

        topology._load_topics(mock_node_info, mock_nodes, "node1", "/path/to/tomls/")
        mock_open.assert_called_once_with('/path/to/tomls/config.toml', mode='rb')
        mock_toml_load.assert_called_once_with(mock_open.return_value.__enter__.return_value)
        self.assertListEqual(mock_nodes["node1"]["topics"], ["topic1", "topic2", "topic3"])

    @patch('builtins.open')
    @patch('tomllib.load')
    def test_load_topics_into_topology(self, mock_toml_load, mock_open):
        nodes = {
            "nodes": {
                "node1": {
                    "node_config": "config.toml",
                    "image": "nim-waku",
                },
                "node2": {
                    "node_config": "config.toml",
                    "image": "nim-waku",
                }}
        }
        mock_toml_config = {"topics": "topic1 topic2 topic3"}
        mock_toml_load.return_value = mock_toml_config

        topology.load_topics_into_topology(nodes, "")

        self.assertEqual(nodes["nodes"]["node1"]["topics"], ["topic1", "topic2", "topic3"])
        self.assertEqual(nodes["nodes"]["node2"]["topics"], ["topic1", "topic2", "topic3"])
