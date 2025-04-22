#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the process_monitor module.
"""
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import subprocess

# Add the parent directory and mocks to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'mocks')))

# Mock the OpenTelemetry imports before importing the module
sys.modules['opentelemetry'] = MagicMock()
sys.modules['opentelemetry.trace'] = MagicMock()
sys.modules['opentelemetry.sdk'] = MagicMock()
sys.modules['opentelemetry.sdk.trace'] = MagicMock()
sys.modules['opentelemetry.sdk.trace.export'] = MagicMock()
sys.modules['opentelemetry.sdk.resources'] = MagicMock()
sys.modules['opentelemetry.exporter.otlp.proto.grpc.trace_exporter'] = MagicMock()
sys.modules['opentelemetry.sdk.metrics'] = MagicMock()
sys.modules['opentelemetry.sdk.metrics.export'] = MagicMock()
sys.modules['opentelemetry.exporter.otlp.proto.grpc.metric_exporter'] = MagicMock()
sys.modules['opentelemetry.metrics'] = MagicMock()
sys.modules['opentelemetry.semantic_conventions'] = MagicMock()

# Now import the module under test
from common.process_monitor import (
    get_process_metrics, 
    get_disk_io_for_pid, 
    get_file_descriptor_count,
    get_thread_count,
    get_context_switches,
    report_metrics
)

class TestProcessMonitor(unittest.TestCase):
    """Test cases for the process_monitor module."""

    @patch('common.process_monitor.subprocess.check_output')
    @patch('common.process_monitor.get_disk_io_for_pid')
    @patch('common.process_monitor.get_file_descriptor_count')
    @patch('common.process_monitor.get_thread_count')
    @patch('common.process_monitor.get_context_switches')
    def test_get_process_metrics(self, mock_get_ctx, mock_get_threads, 
                                mock_get_fds, mock_get_disk_io, mock_check_output):
        """Test getting process metrics."""
        # Mock subprocess output
        mock_check_output.return_value = b"""  PID %CPU %MEM COMMAND
  1234  5.0  2.0 TestProcess
  5678  3.0  1.5 TestProcess
"""
        # Mock other function returns
        mock_get_disk_io.return_value = (1000, 2000)
        mock_get_fds.return_value = 50
        mock_get_threads.return_value = 10
        mock_get_ctx.return_value = (100, 200)
        
        # Call function
        metrics = get_process_metrics("TestProcess")
        
        # Verify subprocess call
        mock_check_output.assert_called_once()
        
        # Verify metrics
        self.assertEqual(metrics["process_count"], 2)
        self.assertEqual(metrics["cpu_usage"], 8.0)  # 5.0 + 3.0
        self.assertEqual(metrics["memory_usage"], 3.5)  # 2.0 + 1.5
        self.assertEqual(metrics["disk_read_bytes"], 2000)  # 1000 * 2
        self.assertEqual(metrics["disk_write_bytes"], 4000)  # 2000 * 2
        self.assertEqual(metrics["open_file_descriptors"], 100)  # 50 * 2
        self.assertEqual(metrics["thread_count"], 20)  # 10 * 2
        self.assertEqual(metrics["voluntary_ctx_switches"], 200)  # 100 * 2
        self.assertEqual(metrics["nonvoluntary_ctx_switches"], 400)  # 200 * 2
        self.assertEqual(metrics["monitored_pids"], "1234,5678")

    @patch('common.process_monitor.subprocess.check_output')
    def test_get_process_metrics_no_match(self, mock_check_output):
        """Test getting process metrics with no matching processes."""
        # Mock subprocess output with no matching processes
        mock_check_output.return_value = b"""  PID %CPU %MEM COMMAND
  1234  5.0  2.0 OtherProcess
  5678  3.0  1.5 AnotherProcess
"""
        
        # Call function
        metrics = get_process_metrics("TestProcess")
        
        # Verify result is None
        self.assertIsNone(metrics)

    @patch('common.process_monitor.subprocess.check_output')
    def test_get_process_metrics_subprocess_error(self, mock_check_output):
        """Test handling of subprocess errors."""
        # Mock subprocess error
        mock_check_output.side_effect = subprocess.CalledProcessError(1, "ps")
        
        # Call function
        metrics = get_process_metrics("TestProcess")
        
        # Verify result is None
        self.assertIsNone(metrics)

    @patch('builtins.open')
    def test_get_disk_io_for_pid(self, mock_open):
        """Test getting disk I/O for a PID."""
        # Mock file content
        mock_file = MagicMock()
        mock_file.__enter__.return_value.readlines.return_value = [
            "rchar: 1000\n",
            "wchar: 2000\n",
            "read_bytes: 3000\n",
            "write_bytes: 4000\n"
        ]
        mock_open.return_value = mock_file
        
        # Call function
        read_bytes, write_bytes = get_disk_io_for_pid("1234")
        
        # Verify results
        self.assertEqual(read_bytes, 3000)
        self.assertEqual(write_bytes, 4000)
        mock_open.assert_called_once_with("/proc/1234/io", "r")

    @patch('builtins.open')
    def test_get_disk_io_for_pid_error(self, mock_open):
        """Test error handling in get_disk_io_for_pid."""
        # Mock file error
        mock_open.side_effect = Exception("Test error")
        
        # Call function
        read_bytes, write_bytes = get_disk_io_for_pid("1234")
        
        # Verify default results on error
        self.assertEqual(read_bytes, 0)
        self.assertEqual(write_bytes, 0)

    @patch('os.path.exists')
    @patch('os.listdir')
    def test_get_file_descriptor_count(self, mock_listdir, mock_exists):
        """Test getting file descriptor count."""
        # Mock directory exists and content
        mock_exists.return_value = True
        mock_listdir.return_value = ["0", "1", "2"]
        
        # Call function
        count = get_file_descriptor_count("1234")
        
        # Verify results
        self.assertEqual(count, 3)
        mock_exists.assert_called_once_with("/proc/1234/fd")
        mock_listdir.assert_called_once_with("/proc/1234/fd")

    @patch('os.path.exists')
    def test_get_file_descriptor_count_no_dir(self, mock_exists):
        """Test getting file descriptor count when directory doesn't exist."""
        # Mock directory doesn't exist
        mock_exists.return_value = False
        
        # Call function
        count = get_file_descriptor_count("1234")
        
        # Verify results
        self.assertEqual(count, 0)

    @patch('os.path.exists')
    @patch('os.listdir')
    def test_get_thread_count_from_task_dir(self, mock_listdir, mock_exists):
        """Test getting thread count from task directory."""
        # Mock directory exists and content
        mock_exists.return_value = True
        mock_listdir.return_value = ["1234", "1235", "1236"]
        
        # Call function
        count = get_thread_count("1234")
        
        # Verify results
        self.assertEqual(count, 3)
        mock_exists.assert_called_once_with("/proc/1234/task")
        mock_listdir.assert_called_once_with("/proc/1234/task")

    @patch('os.path.exists')
    @patch('builtins.open')
    def test_get_thread_count_from_status(self, mock_open, mock_exists):
        """Test getting thread count from status file."""
        # Mock directory doesn't exist but status file does
        mock_exists.return_value = False
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "Threads: 5\n"
        mock_open.return_value = mock_file
        
        # Call function
        count = get_thread_count("1234")
        
        # Verify results
        self.assertEqual(count, 5)
        mock_open.assert_called_once_with("/proc/1234/status", "r")

    @patch('builtins.open')
    def test_get_context_switches(self, mock_open):
        """Test getting context switches."""
        # Mock file content
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = """
voluntary_ctxt_switches: 1000
nonvoluntary_ctxt_switches: 2000
"""
        mock_open.return_value = mock_file
        
        # Call function
        vol_ctx, nonvol_ctx = get_context_switches("1234")
        
        # Verify results
        self.assertEqual(vol_ctx, 1000)
        self.assertEqual(nonvol_ctx, 2000)
        mock_open.assert_called_once_with("/proc/1234/status", "r")

    @patch('builtins.open')
    def test_get_context_switches_error(self, mock_open):
        """Test error handling in get_context_switches."""
        # Mock file error
        mock_open.side_effect = Exception("Test error")
        
        # Call function
        vol_ctx, nonvol_ctx = get_context_switches("1234")
        
        # Verify default results on error
        self.assertEqual(vol_ctx, 0)
        self.assertEqual(nonvol_ctx, 0)

    @patch('common.process_monitor.get_process_metrics')
    @patch('builtins.print')
    def test_report_metrics(self, mock_print, mock_get_metrics):
        """Test report_metrics function."""
        # Mock metrics
        mock_metrics = {
            "cpu_usage": 10.5,
            "memory_usage": 20.3,
            "process_count": 3
        }
        mock_get_metrics.return_value = mock_metrics
        
        # Create a mock for InstanaOTelConnector
        mock_connector = MagicMock()
        mock_connector_instance = MagicMock()
        mock_connector.return_value = mock_connector_instance
        mock_span = MagicMock()
        mock_connector_instance.create_span.return_value.__enter__.return_value = mock_span
        
        # Call function with patched InstanaOTelConnector
        with patch('common.process_monitor.InstanaOTelConnector', mock_connector):
            report_metrics("TestProcess", "test.plugin")
        
        # Verify connector setup
        mock_connector.assert_called_once()
        mock_connector_instance.create_span.assert_called_once()
        mock_connector_instance.record_metrics.assert_called_once_with(mock_metrics)
        
        # Verify print was called with JSON
        mock_print.assert_called_once()

if __name__ == '__main__':
    unittest.main()
