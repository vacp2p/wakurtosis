# Python Imports
import unittest
from unittest.mock import patch

# Project Imports
from src import arg_parser


class TestAnalysis(unittest.TestCase):

    @patch('sys.argv', ['my_script.py', '-sp', 'test1', '-t', 'test2'])
    def test_parse_args(self):
        sim, tomls = arg_parser.parse_args()
        self.assertEqual(sim, "test1")
        self.assertEqual(tomls, "test2")