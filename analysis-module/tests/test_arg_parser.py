# Python Imports
import unittest
from unittest.mock import patch

# Project Imports
from src import arg_parser


class TestAnalysis(unittest.TestCase):

    @patch('sys.argv', ['my_script.py', '-sp', 'test1', '-t', 'test2', '-p', 'test3', '-i', 'test4'])
    def test_parse_args(self):
        sim, tomls, port, infra = arg_parser.parse_args()
        self.assertEqual(sim, "test1")
        self.assertEqual(tomls, "test2")
        self.assertEqual(port, "test3")
        self.assertEqual(infra, "test4")