# Python Imports
import unittest
from unittest.mock import patch, mock_open

# Project Imports
from src import analysis_cproc


class TestAnalysisCProc(unittest.TestCase):

    def test_compute_simulation_time_window(self):
            min_tss = 1000000
            max_tss = 2000000
            expected_simulation_start_ts = min_tss
            expected_simulation_end_ts = max_tss
            expected_simulation_time_ms = round((max_tss - min_tss) / 1000000)

            actual_simulation_start_ts, actual_simulation_end_ts, actual_simulation_time_ms = analysis_cproc.compute_simulation_time_window(min_tss, max_tss)

            self.assertEqual(actual_simulation_start_ts, expected_simulation_start_ts)
            self.assertEqual(actual_simulation_end_ts, expected_simulation_end_ts)
            self.assertEqual(actual_simulation_time_ms, expected_simulation_time_ms)

    def test_extract_node_id(self):
        # Case 1: Standard string with node ID
        s = "node-123.toml"
        expected_node_id = "node_123"
        self.assertEqual(analysis_cproc.extract_node_id(s), expected_node_id)

        # Case 2: String with node ID but additional characters
        s = "prefix-node-456.toml-suffix"
        expected_node_id = "node_456"
        self.assertEqual(analysis_cproc.extract_node_id(s), expected_node_id)

        # Case 3: String without node ID
        s = "node.toml"
        expected_node_id = None
        self.assertEqual(analysis_cproc.extract_node_id(s), expected_node_id)

        # Case 4: Empty string
        s = ""
        expected_node_id = None
        self.assertEqual(analysis_cproc.extract_node_id(s), expected_node_id)

    def test_add_sample_to_metrics(self):
        # Case 1: Adding a sample to an empty metrics_dict
        metrics_dict = {}
        node_id = "node_123"
        sample = {'PID': 123}

        nodes_cnt = analysis_cproc.add_sample_to_metrics(sample, node_id, metrics_dict)

        self.assertEqual(nodes_cnt, 1)
        self.assertEqual(metrics_dict, {node_id: {'samples' : [sample]}})

        # Case 2: Adding a sample to a metrics_dict that already contains the node_id
        sample2 = {'PID': 456}
        nodes_cnt = analysis_cproc.add_sample_to_metrics(sample2, node_id, metrics_dict)

        self.assertEqual(nodes_cnt, 0)  # It should return 0 because the node_id already exists in the metrics_dict
        self.assertEqual(metrics_dict, {node_id: {'samples' : [sample, sample2]}})

    def test_parse_container_nodes(self):
        # Case 1: Sample PID exists in container nodes
        container_id = 'container_123'
        container_data = {'samples': [{'PID': 1}, {'PID': 2}]}
        container_nodes = {1: 'node_1', 2: 'node_2'}
        metrics_dict = {}

        nodes_cnt = analysis_cproc.parse_container_nodes(container_id, container_data, container_nodes, metrics_dict)

        self.assertEqual(nodes_cnt, 2)
        self.assertDictEqual(metrics_dict, {'node_1': {'samples': [{'PID': 1}]}, 'node_2': {'samples': [{'PID': 2}]}})

        # Case 2: Sample PID does not exist in container nodes
        container_id = 'container_456'
        container_data = {'samples': [{'PID': 3}]}
        container_nodes = {1: 'node_1', 2: 'node_2'}
        metrics_dict = {}

        nodes_cnt = analysis_cproc.parse_container_nodes(container_id, container_data, container_nodes, metrics_dict)

        self.assertEqual(nodes_cnt, 0)
        self.assertDictEqual(metrics_dict, {})

    def test_extract_container_nodes(self):
        # Case 1: All processes have node IDs
        container_id = 'container_123'
        container_data = {'info': {'processes': [{'binary': 'node-1.toml', 'pid': 1}, {'binary': 'node-2.toml', 'pid': 2}]}}

        container_nodes = analysis_cproc.extract_container_nodes(container_id, container_data)

        self.assertDictEqual(container_nodes, {1: 'node_1', 2: 'node_2'})

        # Case 2: Some processes don't have node IDs
        container_id = 'container_456'
        container_data = {'info': {'processes': [{'binary': 'node.toml', 'pid': 1}, {'binary': 'node-2.toml', 'pid': 2}]}}

        container_nodes = analysis_cproc.extract_container_nodes(container_id, container_data)

        self.assertDictEqual(container_nodes, {2: 'node_2'})

        # Case 3: No processes have node IDs
        container_id = 'container_789'
        container_data = {'info': {'processes': [{'binary': 'node.toml', 'pid': 1}, {'binary': 'node.toml', 'pid': 2}]}}

        container_nodes = analysis_cproc.extract_container_nodes(container_id, container_data)

        self.assertDictEqual(container_nodes, {})

    @patch("json.load")
    @patch("builtins.open", new_callable=mock_open, read_data="data")
    def test_load_metrics_file(self, mock_file, mock_json):
        # Case 1: Successful load
        mock_json.return_value = {'header': 'header', 'containers': {'container1': 'data1', 'container2': 'data2'}}
        metrics_file_path = 'path/to/metrics_file.json'

        metrics_obj = analysis_cproc.load_metrics_file(metrics_file_path)

        self.assertDictEqual(metrics_obj, {'header': 'header', 'containers': {'container1': 'data1', 'container2': 'data2'}})

        # Reset the mock
        mock_file.reset_mock()

        # Case 2: Unsuccessful load (file does not exist)
        mock_file.side_effect = FileNotFoundError()
        metrics_file_path = 'path/to/non_existent_file.json'

        with self.assertRaises(FileNotFoundError):  # The function should raise FileNotFoundError, not SystemExit
            analysis_cproc.load_metrics_file(metrics_file_path)




@patch("builtins.open", new_callable=mock_open, read_data='{"key":"value"}')
@patch("analysis_cproc.load_metrics_file")
@patch("analysis_cproc.process_metrics_file")
@patch("analysis_cproc.analysis_logger.G_LOGGER")
def test_load_process_level_metrics(self, mock_logger, mock_process_metrics_file, mock_load_metrics_file, mock_open):
    # Case 1: Normal execution
    metrics_file_path = 'path/to/metrics_file.json'
    mock_load_metrics_file.return_value = {
        'header': 'header',
        'containers': {
            'container_1': {
                'info': {'processes': [{'binary': 'node-1.toml', 'pid': 1}]},
                'samples': [{'PID': 1}]
            }
        }
    }
    mock_process_metrics_file.return_value = (mock_load_metrics_file.return_value, None)

    try:
        analysis_cproc.load_process_level_metrics(metrics_file_path)
    except SystemExit:
        pass

    mock_load_metrics_file.assert_called_once_with(metrics_file_path)
    mock_process_metrics_file.assert_called_once_with(mock_load_metrics_file.return_value)

    # Case 2: Exception handling
    mock_load_metrics_file.reset_mock()
    mock_load_metrics_file.side_effect = Exception("Test exception")
    try:
        analysis_cproc.load_process_level_metrics(metrics_file_path)
    except SystemExit:
        pass
    mock_logger.error.assert_called_once()



def test_compute_node_metrics(self):
    # Case 1: Valid node data
    node_obj = {
        'samples': [
            {'CPUPercentage': 10, 'MemoryUsageMB': 500, 
            'NetStats': {'all': {'total_received': 2048, 'total_sent': 2048}}, 
            'DiskIORChar': 2048, 'DiskIOWChar': 2048}
        ]
    }

    num_samples, max_cpu_usage, max_memory_usage, total_rx_mbytes, total_tx_mbytes, max_disk_read_mbytes, max_disk_write_mbytes = analysis_cproc.compute_node_metrics(node_obj)

    self.assertEqual(num_samples, 1)
    self.assertEqual(max_cpu_usage, 10)
    self.assertEqual(max_memory_usage, 500)
    self.assertEqual(total_rx_mbytes, 0.001953125)
    self.assertEqual(total_tx_mbytes, 0.001953125)
    self.assertEqual(max_disk_read_mbytes, 0.001953125)
    self.assertEqual(max_disk_write_mbytes, 0.001953125)


@patch("analysis_cproc.load_metrics_file")
@patch("analysis_cproc.compute_node_metrics")
def test_compute_process_level_metrics(self, mock_compute_node_metrics, mock_load_metrics_file):
    # Case 1: Normal execution
    simulation_path = 'path/to/simulation'
    config_obj = {'key': 'value'}
    mock_load_metrics_file.return_value = (
        {
            'header': 'header',
            'containers': {
                'container_1': {
                    'info': {'processes': [{'binary': 'node-1.toml', 'pid': 1}]},
                    'samples': [{'PID': 1}]
                }
            }
        },
        'info'
    )
    mock_compute_node_metrics.return_value = (0, 0, 0, 0, 0, 0, 0)  # mock_compute_node_metrics should return a tuple
    result = analysis_cproc.compute_process_level_metrics(simulation_path, config_obj)

    self.assertIsInstance(result, tuple)
    self.assertEqual(len(result), 6)
    mock_compute_node_metrics.assert_called()

@patch("builtins.open", new_callable=mock_open)
@patch("json.dump")
def test_export_summary(self, mock_json_dump, mock_open):
    # Case 1: Normal execution
    simulation_path = 'path/to/simulation'
    summary = {'key': 'value'}

    analysis_cproc.export_summary(simulation_path, summary)

    mock_open.assert_called_with(f'{simulation_path}/summary.json', 'w')
    mock_json_dump.assert_called_with(summary, mock_open(), indent=4)

    