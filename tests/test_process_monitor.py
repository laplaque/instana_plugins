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
    @patch('common.process_monitor.get_process_cpu_per_core')
    def test_get_process_metrics(self, mock_get_cpu_per_core, mock_get_ctx, mock_get_threads, 
                                mock_get_fds, mock_get_disk_io, mock_check_output):
        """Test getting process metrics with parent processes."""
        # Mock subprocess output with PID, PPID, CPU, MEM, COMMAND format using semicolon delimiter
        # 1234 is a parent process (PPID=1)
        # 5678 is a parent process (PPID=1)
        # 9012 is a child thread (PPID=1234)
        mock_check_output.return_value = b"""1234;1;5.0;2.0;TestProcess
5678;1;3.0;1.5;TestProcess
9012;1234;2.0;1.0;TestProcess
"""
        # Mock other function returns
        mock_get_disk_io.return_value = (1000, 2000)
        mock_get_fds.return_value = 50
        mock_get_threads.return_value = 10
        mock_get_ctx.return_value = (100, 200)
        mock_get_cpu_per_core.return_value = {}  # No per-core CPU usage
        
        # Call function
        metrics = get_process_metrics("TestProcess")
        
        # The check_output is now called multiple times - verify it was called with the expected arguments for ps
        mock_check_output.assert_any_call(
            ["ps", "-eo", "pid,ppid,pcpu,pmem,comm", "--sort=-pcpu", "-o", "delimiter=;"],
            stderr=subprocess.PIPE
        )
        
        # Verify metrics - only parent processes should be counted
        self.assertEqual(metrics["process_count"], 2)  # Only 1234 and 5678 are parent processes
        self.assertEqual(metrics["cpu_usage"], 8.0)  # 5.0 + 3.0 (only parent processes)
        self.assertEqual(metrics["memory_usage"], 3.5)  # 2.0 + 1.5 (only parent processes)
        self.assertEqual(metrics["thread_count"], 20)  # 10 * 2 (thread count from each parent)
        self.assertEqual(metrics["monitored_pids"], "1234,5678")  # Only parent PIDs
        
        # Verify the new thread statistics metrics
        self.assertEqual(metrics["max_threads_per_process"], 10.0)
        self.assertEqual(metrics["min_threads_per_process"], 10.0)
        self.assertEqual(metrics["avg_threads_per_process"], 10.0)

    @patch('common.process_monitor.subprocess.check_output')
    def test_get_process_metrics_no_match(self, mock_check_output):
        """Test getting process metrics with no matching processes."""
        # Mock subprocess output with no matching processes using semicolon delimiter
        mock_check_output.return_value = b"""1234;1;5.0;2.0;OtherProcess
5678;1;3.0;1.5;AnotherProcess
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

    @patch('builtins.open')
    def test_get_thread_count_from_status_file(self, mock_open):
        """Test getting thread count from status file (preferred method)."""
        # Mock status file content with thread info
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "Threads: 5\n"
        mock_open.return_value = mock_file
        
        # Call function
        count = get_thread_count("1234")
        
        # Verify results - should use status file first
        self.assertEqual(count, 5)
        mock_open.assert_called_once_with("/proc/1234/status", "r")

    @patch('builtins.open')
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_get_thread_count_fallback_to_task_dir(self, mock_listdir, mock_exists, mock_open):
        """Test fallback to task directory when status file fails."""
        # Mock status file error
        mock_open.side_effect = FileNotFoundError("No such file")
        
        # Mock task directory exists with content
        mock_exists.return_value = True
        mock_listdir.return_value = ["1234", "1235", "1236"]
        
        # Call function
        count = get_thread_count("1234")
        
        # Verify results - should fall back to task directory
        self.assertEqual(count, 3)
        mock_exists.assert_called_once_with("/proc/1234/task")
        mock_listdir.assert_called_once_with("/proc/1234/task")

    @patch('builtins.open')
    @patch('os.path.exists')
    @patch('subprocess.check_output')
    def test_get_thread_count_fallback_to_ps(self, mock_check_output, mock_exists, mock_open):
        """Test fallback to ps command when both other methods fail."""
        # Mock status file error
        mock_open.side_effect = FileNotFoundError("No such file")
        
        # Mock task directory doesn't exist
        mock_exists.return_value = False
        
        # Mock ps command output
        mock_check_output.return_value = b"NLWP\n4"
        
        # Call function
        count = get_thread_count("1234")
        
        # Verify results - should fall back to ps command
        self.assertEqual(count, 4)
        mock_check_output.assert_called_once_with(
            ["ps", "-o", "nlwp", "-p", "1234"],
            stderr=subprocess.PIPE
        )

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
        
        # Create a mock for InstanaOTelConnector that will be used inside the function
        mock_connector = MagicMock()
        mock_connector_instance = MagicMock()
        mock_connector.return_value = mock_connector_instance
        mock_span = MagicMock()
        mock_connector_instance.create_span.return_value.__enter__.return_value = mock_span
        
        # Patch the internal import inside report_metrics
        with patch.dict('sys.modules', {'common.otel_connector': MagicMock()}):
            # Set the InstanaOTelConnector class in the mocked module
            sys.modules['common.otel_connector'].InstanaOTelConnector = mock_connector
            
            # Call function with patched import
            report_metrics("TestProcess", "test.plugin")
        
        # Verify connector setup
        mock_connector.assert_called_once()
        mock_connector_instance.create_span.assert_called_once()
        mock_connector_instance.record_metrics.assert_called_once_with(mock_metrics)
        
        # Verify print was called with JSON
        mock_print.assert_called_once()

    @patch('common.process_monitor.subprocess.check_output')
    @patch('common.process_monitor.get_thread_count')
    @patch('common.process_monitor.get_disk_io_for_pid')
    @patch('common.process_monitor.get_file_descriptor_count')
    @patch('common.process_monitor.get_context_switches')
    @patch('common.process_monitor.get_process_cpu_per_core')
    def test_parent_child_process_separation(self, mock_get_cpu_per_core, mock_get_ctx, 
                                           mock_get_fds, mock_get_disk_io, 
                                           mock_get_threads, mock_check_output):
        """Test separation of parent and child processes."""
        # Mock subprocess output with complex parent-child relationships using semicolon delimiter
        mock_check_output.return_value = b"""1000;1;1.0;1.0;TestProcess
1001;1000;0.5;0.5;TestProcess
1002;1000;0.5;0.5;TestProcess
2000;1;2.0;2.0;TestProcess
2001;2000;1.0;1.0;TestProcess
"""
        # Mock function returns
        mock_get_threads.side_effect = [5, 3]  # 5 for PID 1000, 3 for PID 2000
        mock_get_disk_io.return_value = (1000, 2000)
        mock_get_fds.return_value = 50
        mock_get_ctx.return_value = (100, 200)
        mock_get_cpu_per_core.return_value = {}
        
        # Call function
        metrics = get_process_metrics("TestProcess")
        
        # Verify only parent processes are counted
        self.assertEqual(metrics["process_count"], 2)  # Only PIDs 1000 and 2000
        self.assertEqual(metrics["cpu_usage"], 3.0)  # 1.0 + 2.0
        self.assertEqual(metrics["memory_usage"], 3.0)  # 1.0 + 2.0
        self.assertEqual(metrics["thread_count"], 8)  # 5 + 3
        self.assertEqual(metrics["monitored_pids"], "1000,2000")
        
        # Verify thread statistics
        self.assertEqual(metrics["max_threads_per_process"], 5.0)
        self.assertEqual(metrics["min_threads_per_process"], 3.0)
        self.assertEqual(metrics["avg_threads_per_process"], 4.0)

if __name__ == '__main__':
    unittest.main()
