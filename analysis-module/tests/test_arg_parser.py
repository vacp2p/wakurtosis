# Python Imports
import unittest
from unittest.mock import patch

# Project Imports
from src import arg_parser


class TestAnalysis(unittest.TestCase):

    @patch('sys.argv', ['my_script.py', '-sp', 'test1', '-p', '41234'])
    def test_parse_args(self):
        sim, port = arg_parser.parse_args()
        print(sim, port)
        self.assertEqual(sim, "test1")
        self.assertEqual(port, "41234")

    @patch('sys.argv', ['my_script.py'])
    def test_parse_args_default(self):
        sim, port = arg_parser.parse_args()
        self.assertEqual(sim, "/simulation_data/")
        self.assertEqual(port, None)
