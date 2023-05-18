# Python Imports
import unittest
from unittest.mock import patch

from prometheus_api_client import PrometheusConnect

# Project Imports
from src import prometheus
from src import plotting_configurations


class TestPrometheus(unittest.TestCase):

    @patch('src.prometheus.fetch_metric')
    def test_fetch_cadvisor_stats_from_prometheus_by_node(self, mock_fetch_metric):
        mock_fetch_metric.side_effect = [
            [10, 20, 30]
        ]

        metrics = {
            "by_node": ["container_cpu_load_average_10s"]
        }
        prom = None
        container_ip = "192.168.1.1"
        start_ts = 1630000000000000000
        end_ts = 1630000100000000000

        prometheus.fetch_cadvisor_stats_from_prometheus_by_node(metrics, prom, container_ip, start_ts, end_ts)

        self.assertEqual(plotting_configurations.plotting_config["container_cpu_load_average_10s"]["values"], [30])

    @patch.object(PrometheusConnect, 'custom_query_range')
    def test_fetch_metric(self, mock_custom_query_range):
        mock_custom_query_range.return_value = [
            {
                'metric': {'__name__': 'container_memory_usage_bytes'},
                'values': [
                    [1683281260, '5382144'],
                    [1683281261, '5382144'],
                    [1683281262, '5382144'],
                    [1683281263, '6291456'],
                    [1683281320, '10289152']
                ]
            }
        ]

        prom = PrometheusConnect()

        metric_values = prometheus.fetch_metric(prom, None, None, None, None, False)
        self.assertEqual(metric_values, [5382144, 5382144, 5382144, 6291456, 10289152])

    @patch.object(PrometheusConnect, 'custom_query_range')
    def test_fetch_metric_mbytes(self, mock_custom_query_range):
        mock_custom_query_range.return_value = [
            {
                'metric': {'__name__': 'container_memory_usage_bytes'},
                'values': [
                    [1683281260, '5382144'],
                    [1683281261, '5382144'],
                    [1683281262, '5382144'],
                    [1683281263, '6291456'],
                    [1683281320, '10289152']
                ]
            }
        ]
        prom = PrometheusConnect()

        metric_values = prometheus.fetch_metric(prom, None, None, None, None, True)
        self.assertEqual(metric_values, [5.1328125, 5.1328125, 5.1328125, 6.0, 9.8125])

    @patch.object(PrometheusConnect, 'custom_query_range')
    def test_fetch_metric_empty(self, mock_custom_query_range):
        mock_custom_query_range.return_value = []
        prom = PrometheusConnect()

        metric_values = prometheus.fetch_metric(prom, None, None, None, None, True)
        self.assertEqual(metric_values, [0])

    @patch('src.prometheus.fetch_accumulated_metric_for_all_nodes')
    def test_fetch_cadvisor_stats_from_prometheus_by_simulation(self, mock_fetch_accumulated_metric_for_all_nodes):
        metrics = {
            "by_simulation": [
                "container_network_receive_bytes_total",
                "container_network_transmit_bytes_total"
            ]
        }

        mock_fetch_accumulated_metric_for_all_nodes.side_effect = [[12, 17, 13, 5, 8, 4], [1, 4, 3]]
        prom = PrometheusConnect()

        prometheus.fetch_cadvisor_stats_from_prometheus_by_simulation(metrics, prom, None, 0, 0)

        self.assertEqual(plotting_configurations.plotting_config["container_network_receive_bytes_total"]["values"],
                         [[12, 17, 13, 5, 8, 4]])
        self.assertEqual(plotting_configurations.plotting_config["container_network_transmit_bytes_total"]["values"],
                         [[1, 4, 3]])

    @patch('src.prometheus.fetch_metric_with_timestamp')
    def test_fetch_accumulated_metric_for_all_nodes_1(self, mock_fetch_metric_with_timestamp):
        mock_fetch_metric_with_timestamp.side_effect = [[[1683281260, 1],
                                                         [1683281260, 4],
                                                         [1683281261, 3],
                                                         [1683281261, 3],
                                                         [1683281262, 5],
                                                         [1683281263, 4],
                                                         [1683281320, 8]]]

        prom = PrometheusConnect()
        ips = ["test"]
        metric_values = prometheus.fetch_accumulated_metric_for_all_nodes(prom, None, ips, None, None, None)

        self.assertEqual(metric_values, [5, 6, 5, 4, 8])

    @patch('src.prometheus.fetch_metric_with_timestamp')
    def test_fetch_accumulated_metric_for_all_nodes_2(self, mock_fetch_metric_with_timestamp):
        mock_fetch_metric_with_timestamp.side_effect = [[[1683281260, 1], [1683281260, 4], [1683281261, 3],
                                                         [1683281261, 3], [1683281262, 5], [1683281263, 4],
                                                         [1683281320, 8]],
                                                        [[1683281260, 7], [1683281260, 1], [1683281261, 6],
                                                         [1683281261, 5], [1683281262, 8], [1683281263, 1],
                                                         [1683281330, 4]]]

        prom = PrometheusConnect()
        ips = ["test1", "test2"]
        metric_values = prometheus.fetch_accumulated_metric_for_all_nodes(prom, None, ips, None, None, None)

        self.assertEqual(metric_values, [13, 17, 13, 5, 8, 4])

    @patch('src.prometheus.fetch_metric_with_timestamp')
    def test_fetch_accumulated_metric_for_all_nodes_empty(self, mock_fetch_metric_with_timestamp):
        mock_fetch_metric_with_timestamp.side_effect = [[[0, 0]], [[0, 0]]]

        prom = PrometheusConnect()
        ips = ["test1", "test2"]
        metric_values = prometheus.fetch_accumulated_metric_for_all_nodes(prom, None, ips, None, None, None)

        self.assertEqual(metric_values, [0])

    @patch.object(PrometheusConnect, 'custom_query_range')
    def test_fetch_metric_with_timestamp(self, mock_custom_query_range):
        mock_custom_query_range.return_value = [
            {
                'metric': {'__name__': 'container_memory_usage_bytes'},
                'values': [
                    [1683281260, '5382144'],
                    [1683281261, '5382144'],
                    [1683281262, '5382144'],
                    [1683281263, '6291456'],
                    [1683281320, '10289152']
                ]
            }
        ]
        prom = PrometheusConnect()

        metric_values = prometheus.fetch_metric_with_timestamp(prom, None, None, None, None)
        self.assertEqual(metric_values,
                         [[1683281260, '5382144'], [1683281261, '5382144'], [1683281262, '5382144'],
                          [1683281263, '6291456'],
                          [1683281320, '10289152']])

    @patch.object(PrometheusConnect, 'custom_query_range')
    def test_fetch_metric_with_timestamp_empty_data(self, mock_custom_query_range):
        mock_custom_query_range.return_value = []
        prom = PrometheusConnect()

        metric_values = prometheus.fetch_metric_with_timestamp(prom, None, None, None, None)
        self.assertEqual(metric_values, [[0, 0]])
