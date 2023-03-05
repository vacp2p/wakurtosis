import unittest
import random
import json
from unittest.mock import patch

from src.utils import waku_messaging

random.seed(1)


class TestPayloads(unittest.TestCase):

    def create_patch(self, name):
        patcher = patch(name)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def test__poisson_interval(self):
        test_1 = waku_messaging._poisson_interval(1)
        test_5 = waku_messaging._poisson_interval(5)
        test_10 = waku_messaging._poisson_interval(10)
        self.assertEqual(test_1, 0.1442910641095092)
        self.assertEqual(test_5, 0.3760312530841251)
        self.assertEqual(test_10, 0.1442968925346663)

    def test__get_waku_payload(self):
        mock_time = self.create_patch('time.time_ns')

        mock_time.return_value = 123456789
        test_payload = waku_messaging._get_waku_payload(1, 'test')
        self.assertEqual(test_payload, {'nonce': 1, 'ts': 123456789, 'payload': 'test'})

    def test__create_waku_msg(self):
        test_payload = waku_messaging._create_waku_msg('test')
        self.assertEqual(test_payload, {'payload': '227465737422'})

    def test__create_waku_rpc_data(self):
        test_data = waku_messaging._create_waku_rpc_data('test', 'test', 'test')
        self.assertEqual(test_data, {'jsonrpc': '2.0', 'method': 'post_waku_v2_relay_v1_message',
                                     'id': 1, 'params': ['test', 'test']})

    def test__send_waku_rpc(self):
        mock_response = self.create_patch('requests.post')
        mock_time = self.create_patch('time.time')

        mock_response.return_value.json.return_value = 'test'
        mock_time.return_value = 10
        test_response, test_time = waku_messaging._send_waku_rpc('test', 'test')
        self.assertEqual(test_response, 'test')
        self.assertEqual(test_time, 0)

    def test_send_msg_to_node(self):
        mock_waku_payload = self.create_patch('src.utils.waku_messaging._get_waku_payload')
        mock_create_waku_msg = self.create_patch('src.utils.waku_messaging._create_waku_msg')
        mock_send_waku_rpc = self.create_patch('src.utils.waku_messaging._send_waku_rpc')

        mock_waku_payload.return_value = {'ts': 1}
        mock_create_waku_msg.return_value = 'test3'
        mock_send_waku_rpc.return_value = ('test1', 0)

        test_response_1, test_response_2, test_response_3, test_response_4 = \
            waku_messaging.send_msg_to_node('test', 'test', 'test')

        self.assertEqual(test_response_1, 'test1')
        self.assertEqual(test_response_2, 0)
        self.assertEqual(test_response_3, json.dumps('test3'))
        self.assertEqual(test_response_4, 1)

    def test_get_next_time_to_msg_poisson(self):
        test = waku_messaging.get_next_time_to_msg('poisson', 1, 1)
        self.assertEqual(test, 0.29446371689426293)

    def test_get_next_time_to_msg_uniform(self):
        test = waku_messaging.get_next_time_to_msg('uniform', 1, 1)
        self.assertEqual(test, 1)

    def test_get_next_time_to_msg_invalid(self):
        with self.assertRaises(SystemExit) as cm:
            waku_messaging.get_next_time_to_msg('test', 1, 1)

        self.assertEqual(cm.exception.code, 1)
