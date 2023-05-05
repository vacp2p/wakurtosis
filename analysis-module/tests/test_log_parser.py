# Python Imports
import unittest
from unittest.mock import patch

# Project Imports
from src import log_parser


class TestLogParser(unittest.TestCase):

    @patch('builtins.open')
    @patch('json.load')
    def test_load_messages(self, mock_json_load, mock_open):
        mock_data = {'key': 'value'}
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.read.return_value = 'dummy'
        mock_json_load.return_value = mock_data

        data = log_parser.load_messages('/path/to/simulation')
        mock_open.assert_called_once_with('/path/to/simulation/messages.json', 'r')
        mock_json_load.assert_called_once_with(mock_file)
        self.assertEqual(data, mock_data)

    def test_prepare_node_in_logs(self):
        node_pbar = ['node1', 'node2']
        topology = {'nodes': {'node1': {'peer_id': 'peer1'}, 'node2': {'peer_id': 'peer2'}}}
        node_logs = {}
        container_name = 'container1'

        log_parser.prepare_node_in_logs(node_pbar, topology, node_logs, container_name)

        self.assertEqual(node_logs, {'pee*peer1': {'published': [], 'received': [],
                                                    'container_name': 'container1', 'peer_id': 'node1'},
                                     'pee*peer2': {'published': [], 'received': [],
                                                    'container_name': 'container1', 'peer_id': 'node2'}})
