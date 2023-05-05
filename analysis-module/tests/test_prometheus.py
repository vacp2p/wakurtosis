# Python Imports
import unittest
from unittest.mock import patch

# Project Imports
from src import prometheus


class TestPrometheus(unittest.TestCase):

    @patch('prometheus.fetch_metric')
    def test_fetch_cadvisor_stats_from_prometheus(self, query):
        query.side_effect = [10, 20, 30]

        metrics = {
            "to_query": {
                "metric_1": {
                    "metric_name": "metric_1_name",
                    "statistic": "sum",
                    "toMB": False
                },
                "metric_2": {
                    "metric_name": ["metric_2_name_1", "metric_2_name_2"],
                    "statistic": "max",
                    "toMB": False
                }
            }
        }
        prom = None
        container_ip = "192.168.1.1"
        start_ts = 1630000000000000000
        end_ts = 1630000100000000000

        prometheus.fetch_cadvisor_stats_from_prometheus(metrics, prom, container_ip, start_ts, end_ts)

        self.assertEqual(metrics["to_query"]["metric_1"]["values"], [sum([10, 20, 30])])
        self.assertEqual(metrics["to_query"]["metric_2"]["values"], [[max([10, 20, 30])], [max([5, 15, 25])]])

    @patch('prom.custom_query_range')
    def test_fetch_metric(self, query):
        metric_result = query.return_value.__enter__.return_value
        metric_result.read.return_value = [{'metric': {'__name__': 'container_memory_usage_bytes'},
                                            'values': [[1683281260, '5382144'], [1683281261, '5382144'],
                                                       [1683281262, '5382144'], [1683281263, '6291456'],
                                                       [1683281320, '10289152']]}]
        metric_values = prometheus.fetch_metric(None, None, None, None, None, False)
        self.assertEqual(metric_values, [5382144, 5382144, 5382144, 6291456, 10289152])

    @patch('prom.custom_query_range')
    def test_fetch_metric_mbytes(self, query):
        metric_result = query.return_value.__enter__.return_value
        metric_result.read.return_value = [{'metric': {'__name__': 'container_memory_usage_bytes'},
                                            'values': [[1683281260, '1048576'], [1683281261, '5382144'],
                                                       [1683281262, '5382144'], [1683281263, '6291456'],
                                                       [1683281320, '10289152']]}]
        metric_values = prometheus.fetch_metric(None, None, None, None, None, True)
        self.assertEqual(metric_values, [1, 5382144, 5382144, 6291456, 10289152])
