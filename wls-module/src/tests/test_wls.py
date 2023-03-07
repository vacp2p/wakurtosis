import unittest
import random
from unittest.mock import mock_open, patch

from src import wls

random.seed(0)


class TestWLS(unittest.TestCase):

    def create_patch(self, name):
        patcher = patch(name)
        thing = patcher.start()
        self.addCleanup(patcher.stop)
        return thing

    def test_parse_cli(self):
        args_parsed = wls.parse_cli(["-cfg", "test1", "-t", "test2"])
        self.assertEqual(args_parsed.config_file, "test1")
        self.assertEqual(args_parsed.topology_file, "test2")

    def test_parse_cli_only_cfg(self):
        args_parsed = wls.parse_cli(["-cfg", "test1"])
        self.assertEqual(args_parsed.config_file, "test1")
        self.assertEqual(args_parsed.topology_file, wls.G_DEFAULT_TOPOLOGY_FILE)

    def test_parse_cli_only_t(self):
        args_parsed = wls.parse_cli(["-t", "test2"])
        self.assertEqual(args_parsed.config_file, wls.G_DEFAULT_CONFIG_FILE)
        self.assertEqual(args_parsed.topology_file, "test2")

    def test_parse_cli_no_args(self):
        args_parsed = wls.parse_cli([])
        self.assertEqual(args_parsed.config_file, wls.G_DEFAULT_CONFIG_FILE)
        self.assertEqual(args_parsed.topology_file, wls.G_DEFAULT_TOPOLOGY_FILE)

    def test_parse_cli_error(self):
        with self.assertRaises(SystemExit):
            wls.parse_cli(["-cfg", "test1", "-t", "test2", "-error"])

    def test__load_topics_nwaku(self):
        m = mock_open(read_data='asd')
        with patch('builtins.open', m) as mocked_open:
            mock_tomllib_load = self.create_patch('tomllib.load')
            mock_tomllib_load.return_value = {"topics": 'test1 test2'}

            node_info = {"image": "nim-waku", "node_config": "asd"}
            node = {}
            node["test"] = {}

            wls._load_topics(node_info, node, "test")
            self.assertEqual(node["test"]["topics"], ["test1", "test2"])

    def test__load_topics_gowaku(self):
        m = mock_open(read_data='asd')
        with patch('builtins.open', m) as mocked_open:
            mock_tomllib_load = self.create_patch('tomllib.load')
            mock_tomllib_load.return_value = {"topics": ['test1', 'test2']}

            node_info = {"image": "go-waku", "node_config": "asd"}
            node = {}
            node["test"] = {}

            wls._load_topics(node_info, node, "test")
            self.assertEqual(node["test"]["topics"], ["test1", "test2"])

    def test__load_topics_error(self):
        m = mock_open(read_data='asd')
        with patch('builtins.open', m) as mocked_open:
            mock_tomllib_load = self.create_patch('tomllib.load')
            mock_tomllib_load.return_value = {"topics": 'test1 test2'}

            node_info = {"image": "error", "node_config": "asd"}
            node = {}
            node["test"] = {}

            with self.assertRaises(Exception):
                wls._load_topics(node_info, node, "test")

    def test_load_topics_into_topology(self):
        m = mock_open(read_data='asd')
        with patch('builtins.open', m) as mocked_open:
            mock_tomllib_load = self.create_patch('tomllib.load')
            mock_tomllib_load.return_value = {"topics": 'test1 test2'}

            topology = {"nodes": {"test": {"image": "nim-waku", "node_config": "asd"}}}
            wls.load_topics_into_topology(topology)
            self.assertEqual(topology["nodes"]["test"]["topics"], ["test1", "test2"])

    def test_load_topics_into_topology_error(self):
        m = mock_open(read_data='asd')
        with patch('builtins.open', m) as mocked_open:
            mock_tomllib_load = self.create_patch('tomllib.load')
            mock_tomllib_load.return_value = {"topics": 'test1 test2'}

            topology = {"nodes": {"test": {"image": "error", "node_config": "asd"}}}
            with self.assertRaises(SystemExit):
                wls.load_topics_into_topology(topology)

    def test_get_random_emitters_all(self):
        topology = {"nodes": {"test1": 1, "test2": 2}}
        config = {"emitters_fraction": 1}
        emitters = wls.get_random_emitters(topology, config)

        self.assertEqual(emitters, {"test1": 1, "test2": 2})

    def test_get_random_emitters_half(self):
        topology = {"nodes": {"test1": 1, "test2": 2}}
        config = {"emitters_fraction": 0.5}
        emitters = wls.get_random_emitters(topology, config)

        self.assertEqual(emitters, {"test2": 2})

    def test_get_random_emitters_error(self):
        topology = {"nodes": {"test1": 1, "test2": 2}}
        config = {"emitters_fraction": 0}
        with self.assertRaises(SystemExit):
            wls.get_random_emitters(topology, config)

    def test_get_random_emitters_error2(self):
        topology = {"nodes": {"test1": 1, "test2": 2}}
        config = {"emitters_fraction": 2}
        with self.assertRaises(SystemExit):
            wls.get_random_emitters(topology, config)

    def test__is_simulation_finished(self):
        # time.time returns the number of seconds passed since epoch
        mock_time = self.create_patch('time.time')
        # we assume we are at time 10
        mock_time.return_value = 10

        # we want the simulation last for 5 seconds
        wls_config = {'simulation_time': 5}

        # if simulation started at time 3, 10-5 >= 3 -> true
        finished = wls._is_simulation_finished(3, wls_config, {})
        self.assertTrue(finished)

    def test__is_simulation_finished_false(self):
        # time.time returns the number of seconds passed since epoch
        mock_time = self.create_patch('time.time')
        # we assume we are at time 10
        mock_time.return_value = 10

        # we want the simulation last for 5 seconds
        wls_config = {'simulation_time': 5}

        # if simulation started at time 7, 10-7 >= 7 -> false
        finished = wls._is_simulation_finished(7, wls_config, {})
        self.assertFalse(finished)

    def test__time_to_send_text_message_true(self):
        mock_time = self.create_patch('time.time')
        mock_time.return_value = 5

        # We want to send messages every second, last message time was 1,
        # and we are at time 5-> true
        next_message = wls._time_to_send_next_message(1, 1)
        self.assertTrue(next_message)

    def test__time_to_send_text_message_false(self):
        mock_time = self.create_patch('time.time')
        mock_time.return_value = 5

        # We want to send messages every 10 seconds, last message time was 1,
        # and we are at time 5-> false
        next_message = wls._time_to_send_next_message(1, 10)
        self.assertFalse(next_message)

    def test__select_emitter_and_topic(self):
        emitters = {"test1": {"ip_address": 1, "ports": {"rpc_test1": (2, "asd")},
                              "topics": ["test1a", "test1b"]},
                    "test2": {"ip_address": 5, "ports": {"rpc_test2": (6, "tcp")},
                              "topics": ["test2a", "test2b"]},
                    "test3": {"ip_address": 10, "ports": {"rpc_test3": (11, "tcp")},
                              "topics": ["test3a", "test3b"]}}

        emitter_address, topic = wls._select_emitter_with_topic(emitters)

        self.assertEqual(emitter_address, "http://5:6/")
        self.assertEqual(topic, "test2b")

    def test__inject_message(self):
        mock_dist = self.create_patch('src.utils.payloads.make_payload_dist')
        mock_dist.return_value = "payload", 2
        mock_send_message = self.create_patch('src.utils.waku_messaging.send_msg_to_node')
        mock_send_message.return_value = {'result': True}, None, "asd", 1

        messages_dict = {}
        wls_config = {"dist_type": "dist", "min_packet_size": 1, "max_packet_size": 10}
        wls._inject_message("1.1.1.1", "test", messages_dict, wls_config)
        self.assertIn("688787d8ff144c502c7f5cffaafe2cc588d86079f9de88304c26b0cb99ce91c6",
                      messages_dict.keys())
        hash_dict = messages_dict["688787d8ff144c502c7f5cffaafe2cc588d86079f9de88304c26b0cb99ce91c6"]
        self.assertEqual(hash_dict['ts'], 1)
        self.assertEqual(hash_dict['injection_point'], "1.1.1.1")
        self.assertEqual(hash_dict['nonce'], 0)
        self.assertEqual(hash_dict['topic'], "test")
        self.assertEqual(hash_dict['payload'], "payload")
        self.assertEqual(hash_dict['payload_size'], 2)

    def test__inject_message_error(self):
        mock_dist = self.create_patch('src.utils.payloads.make_payload_dist')
        mock_dist.return_value = "payload", 2
        mock_send_message = self.create_patch('src.utils.waku_messaging.send_msg_to_node')
        mock_send_message.return_value = {'result': True}, None, "asd", 1

        messages_dict = {"688787d8ff144c502c7f5cffaafe2cc588d86079f9de88304c26b0cb99ce91c6": "asd"}
        wls_config = {"dist_type": "dist", "min_packet_size": 1, "max_packet_size": 10}
        wls._inject_message("1.1.1.1", "test", messages_dict, wls_config)
        self.assertEqual(len(messages_dict), 1)

