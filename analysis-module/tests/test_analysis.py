# Python Imports
import unittest
import sys

# Proyect Imports
from src import analysis


class TestAnalysis(unittest.TestCase):

    def test_compare_tss_min(self):
        tss = 0
        min_tss = 5
        max_tss = 10
        min_tss, max_tss = analysis.compare_tss(tss, min_tss, max_tss)
        self.assertEqual(min_tss, 0)

    def test_compare_tss_max(self):
        tss = 15
        min_tss = 5
        max_tss = 10
        min_tss, max_tss = analysis.compare_tss(tss, min_tss, max_tss)
        self.assertEqual(max_tss, 15)

    def test_compare_tss_same(self):
        tss = 6
        min_tss = 5
        max_tss = 10
        min_tss, max_tss = analysis.compare_tss(tss, min_tss, max_tss)
        self.assertEqual(min_tss, 5)
        self.assertEqual(max_tss, 10)

    def test_get_relay_line_info(self):
        log_line = "TRC 2023-04-18 08:31:28.591+00:00 waku.relay received                        topics=\"waku node\" tid=1 file=waku_node.nim:395 peerId=16U*96opVg pubsubTopic=topic_C hash=0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc receivedTime=1681806688591971328"
        msg_topics, msg_topic, msg_hash, msg_peer_id = analysis.get_relay_line_info(log_line)
        self.assertEqual(msg_topics, "waku node")
        self.assertEqual(msg_topic, "topic_C")
        self.assertEqual(msg_hash, "0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc")
        self.assertEqual(msg_peer_id, "16U*96opVg")

    def test_analyze_published_first_time(self):
        log_line = "TRC 2023-04-18 08:31:30.147+00:00 waku.relay published                       topics=\"waku node\" tid=1 file=waku_node.nim:484 peerId=16U*96opVg pubsubTopic=topic_C hash=0x122071785e0803dafa9cdd288ed7db0d32277f7cab110b798f631d0fcd2d58dd7463 publishTime=1681806690147236096"
        published_time = 1681806690147236096
        msgs_dict = {}
        node_logs = {}
        node_logs["16U*96opVg"] = {'published': [], 'received': [],
                              'container_name': "test", 'peer_id': "test"}
        analysis.analyze_published(log_line, node_logs, msgs_dict, published_time)
        self.assertEqual(node_logs["16U*96opVg"]["published"][0][2], "topic_C")
        self.assertEqual(node_logs["16U*96opVg"]["published"][0][3], "0x122071785e0803dafa9cdd288ed7db0d32277f7cab110b798f631d0fcd2d58dd7463")
        self.assertEqual(msgs_dict, {'0x122071785e0803dafa9cdd288ed7db0d32277f7cab110b798f631d0fcd2d58dd7463':
                                         {'published': [{'ts': published_time, 'peer_id': "16U*96opVg"}], 'received': []}})

    def test_analyze_published_second_time(self):
        log_line = "TRC 2023-04-18 08:31:30.147+00:00 waku.relay published                       topics=\"waku node\" tid=1 file=waku_node.nim:484 peerId=16U*96opVg pubsubTopic=topic_C hash=0x122071785e0803dafa9cdd288ed7db0d32277f7cab110b798f631d0fcd2d58dd7463 publishTime=1681806690147236096"
        log_line2 = "TRC 2023-04-18 08:31:30.147+00:00 waku.relay published                       topics=\"waku node\" tid=1 file=waku_node.nim:484 peerId=16U*96opVg pubsubTopic=topic_C hash=0x122071785e0803dafa9cdd288ed7db0d32277f7cab110b798f631d0fcd2d58dd7463 publishTime=1681806690147236097"
        published_time = 1681806690147236096
        published_time2 = 1681806690147236097
        msgs_dict = {}
        node_logs = {}
        node_logs["16U*96opVg"] = {'published': [], 'received': [],
                                   'container_name': "test", 'peer_id': "test"}
        analysis.analyze_published(log_line, node_logs, msgs_dict, published_time)
        analysis.analyze_published(log_line2, node_logs, msgs_dict, published_time2)
        self.assertEqual(node_logs["16U*96opVg"]["published"][1][2], "topic_C")
        self.assertEqual(node_logs["16U*96opVg"]["published"][1][3],
                         "0x122071785e0803dafa9cdd288ed7db0d32277f7cab110b798f631d0fcd2d58dd7463")
        self.assertEqual(msgs_dict, {'0x122071785e0803dafa9cdd288ed7db0d32277f7cab110b798f631d0fcd2d58dd7463':
                                         {'published': [{'ts': published_time, 'peer_id': "16U*96opVg"},
                                                        {'ts': published_time2, 'peer_id': "16U*96opVg"}], 'received': []}})

    def test_analyze_received_first_time(self):
        log_line = "TRC 2023-04-18 08:31:28.591+00:00 waku.relay received                        topics=\"waku node\" tid=1 file=waku_node.nim:395 peerId=16U*96opVg pubsubTopic=topic_C hash=0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc receivedTime=1681806688591971328"
        received_time = 1681806688591971328
        msgs_dict = {}
        node_logs = {}
        node_logs["16U*96opVg"] = {'published': [], 'received': [],
                                   'container_name': "test", 'peer_id': "test"}
        analysis.analyze_received(log_line, node_logs, msgs_dict, received_time)
        self.assertEqual(node_logs["16U*96opVg"]["received"][0][2], "topic_C")
        self.assertEqual(node_logs["16U*96opVg"]["received"][0][3],
                         "0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc")
        self.assertEqual(msgs_dict, {'0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc':
                                         {'published': [], 'received': [{'ts': received_time, 'peer_id': "16U*96opVg"}]}})


    def test_analyze_received_second_time(self):
        log_line = "TRC 2023-04-18 08:31:28.591+00:00 waku.relay received                        topics=\"waku node\" tid=1 file=waku_node.nim:395 peerId=16U*96opVg pubsubTopic=topic_C hash=0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc receivedTime=1681806688591971328"
        log_line2 = "TRC 2023-04-18 08:31:28.591+00:00 waku.relay received                        topics=\"waku node\" tid=1 file=waku_node.nim:395 peerId=16U*96opVg pubsubTopic=topic_C hash=0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc receivedTime=1681806688591971329"
        received_time = 1681806688591971328
        received_time2 = 1681806688591971329
        msgs_dict = {}
        node_logs = {}
        node_logs["16U*96opVg"] = {'published': [], 'received': [],
                                   'container_name': "test", 'peer_id': "test"}
        analysis.analyze_received(log_line, node_logs, msgs_dict, received_time)
        analysis.analyze_received(log_line2, node_logs, msgs_dict, received_time2)
        self.assertEqual(node_logs["16U*96opVg"]["received"][1][2], "topic_C")
        self.assertEqual(node_logs["16U*96opVg"]["received"][1][3],
                         "0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc")
        self.assertEqual(msgs_dict, {'0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc':
                                         {'published': [], 'received': [{'ts': received_time, 'peer_id': "16U*96opVg"},
                                                                        {'ts': received_time2, 'peer_id': "16U*96opVg"}]}})

    def test_parse_lines_in_file(self):
        lines = [
        "TRC 2023-04-18 08:31:28.591+00:00 publish                                    topics=\"waku node\" tid=1 file=protocol.nim:160 pubsubTopic=topic_C",
        "TRC 2023-04-18 08:31:28.591+00:00 waku.relay received                        topics=\"waku node\" tid=1 file=waku_node.nim:395 peerId=16U*92yDon pubsubTopic=topic_C hash=0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc receivedTime=1681806688591453952",
        "TRC 2023-04-18 08:31:28.591+00:00 waku.relay published                       topics=\"waku node\" tid=1 file=waku_node.nim:484 peerId=16U*92yDon pubsubTopic=topic_C hash=0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc publishTime=1681806688591803648"
        ]
        msgs_dict = {}
        node_logs = {}
        max_tss = -sys.maxsize - 1
        min_tss = sys.maxsize

        node_logs["16U*92yDon"] = {'published': [], 'received': [],
                                   'container_name': "test", 'peer_id': "test"}

        min_tss, max_tss = analysis.parse_lines_in_file(lines, node_logs, msgs_dict, 10, 2681806688591803648)
        self.assertEqual(node_logs["16U*92yDon"]["received"][0][2], "topic_C")
        self.assertEqual(node_logs["16U*92yDon"]["received"][0][3],
                            "0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc")
        self.assertEqual(node_logs["16U*92yDon"]["published"][0][2], "topic_C")
        self.assertEqual(node_logs["16U*92yDon"]["published"][0][3],
                            "0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc")
        self.assertEqual(min_tss, 10)
        self.assertEqual(max_tss, 2681806688591803648)

    def test_compute_message_latencies(self): # todo further testing
        msgs_dict = {'0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc':
                         {'published': [{'ts': 10, 'peer_id': "16U*96opVi"}], 'received': [{'ts': 20, 'peer_id': "16U*96opVg"}]}}
        analysis.compute_message_latencies(msgs_dict)
        self.assertEqual(msgs_dict["0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc"]["latencies"][0], 10)

    def test_compute_propagation_times(self):
        msgs_dict = {'0x12208ff2358cd9e488cd5f2806c9859dbd28768c52b6f52614c3148e45c5c12edadc':
                         {'published': [{'ts': 10, 'peer_id': "16U*96opVi"}], 'received': [{'ts': 20, 'peer_id': "16U*96opVg"}],
                          "latencies": [1000000]}}
        result = analysis.compute_propagation_times(msgs_dict)
        self.assertEqual(result[0], 1)

    def test_compute_message_delivery(self):
        mesages = {"a": 1, "b": 2, "c": 3}
        delivered = {"a": 1, "b": 2, "c": 3}
        result = analysis.compute_message_delivery(mesages, delivered)
        self.assertEqual(result, 100)
