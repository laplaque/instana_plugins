#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for edge cases and limitations with psutil-based implementation.
"""
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import logging
import tempfile
import shutil
import psutil

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules to test
from common.process_monitor import get_process_metrics, get_disk_io_for_pid
from common.otel_connector import InstanaOTelConnector
from common.logging_config import setup_logging

class TestEdgeCases(unittest.TestCase):
    """Test cases for edge cases and limitations."""
    
    def setUp(self):
        # Create a temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Store original loggers to restore after tests
        self.root_handlers = logging.root.handlers.copy()
        self.root_level = logging.root.level
    
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)
        
        # Close all current handlers to avoid ResourceWarnings
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)
        
        # Restore original logging configuration
        for handler in self.root_handlers:
            logging.root.addHandler(handler)
        logging.root.setLevel(self.root_level)
    
    @patch('common.process_monitor.psutil.process_iter')
    def test_empty_process_output(self, mock_process_iter):
        """Test handling of empty process list."""
        # Mock empty process list
        mock_process_iter.return_value = []
        
        # Call the function
        result = get_process_metrics("TestProcess")
        
        # Should return None for empty process list
        self.assertIsNone(result)
    
    @patch('common.process_monitor.psutil.process_iter')
    def test_malformed_process_output(self, mock_process_iter):
        """Test handling of psutil exceptions during process iteration."""
        # Mock psutil to raise an exception
        mock_process_iter.side_effect = psutil.Error("psutil error")
        
        # Call the function
        result = get_process_metrics("TestProcess")
        
        # Should return None for psutil errors
        self.assertIsNone(result)
    
    @patch('common.process_monitor.psutil.process_iter')
    def test_process_with_special_chars(self, mock_process_iter):
        """Test handling of process names with special characters."""
        # Create a mock process with special characters in name
        mock_proc = MagicMock()
        mock_proc.pid = 5678
        mock_proc.ppid.return_value = 1
        mock_proc.name.return_value = "Test-Process[special]"
        mock_proc.cpu_percent.return_value = 10.5
        mock_proc.memory_percent.return_value = 20.3
        mock_proc.info = {
            'pid': 5678,
            'ppid': 1,
            'name': 'Test-Process[special]',
            'cpu_percent': 10.5,
            'memory_percent': 20.3
        }
        
        mock_process_iter.return_value = [mock_proc]
        
        # Mock helper functions to return basic values
        with patch('common.process_monitor.get_disk_io_for_pid') as mock_disk_io, \
             patch('common.process_monitor.get_file_descriptor_count') as mock_fd_count, \
             patch('common.process_monitor.get_thread_count') as mock_thread_count, \
             patch('common.process_monitor.get_context_switches') as mock_ctx_switches, \
             patch('common.process_monitor.get_process_cpu_per_core') as mock_cpu_per_core:
            
            mock_disk_io.return_value = (0, 0)
            mock_fd_count.return_value = 0
            mock_thread_count.return_value = 1
            mock_ctx_switches.return_value = (0, 0)
            mock_cpu_per_core.return_value = {}
            
            result = get_process_metrics("Test-Process")
            
            # Should handle special characters correctly
            self.assertIsNotNone(result)
            self.assertEqual(result["process_count"], 1)
            self.assertEqual(result["cpu_usage"], 10.5)
            self.assertEqual(result["memory_usage"], 20.3)
    
    @patch('common.process_monitor.psutil.process_iter')
    def test_process_access_denied(self, mock_process_iter):
        """Test handling of access denied errors for processes."""
        # Create a mock process that raises AccessDenied
        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_proc.ppid.side_effect = psutil.AccessDenied(1234)
        mock_proc.name.return_value = "TestProcess"
        mock_proc.info = {
            'name': 'TestProcess'
        }
        
        mock_process_iter.return_value = [mock_proc]
        
        result = get_process_metrics("TestProcess")
        
        # Should handle access denied gracefully and return None
        self.assertIsNone(result)
    
    @patch('common.process_monitor.psutil.process_iter')
    def test_process_no_such_process(self, mock_process_iter):
        """Test handling of NoSuchProcess errors."""
        # Create a mock process that raises NoSuchProcess during processing
        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_proc.ppid.side_effect = psutil.NoSuchProcess(1234)
        mock_proc.name.return_value = "TestProcess"
        mock_proc.info = {
            'name': 'TestProcess'
        }
        
        mock_process_iter.return_value = [mock_proc]
        
        result = get_process_metrics("TestProcess")
        
        # Should handle no such process gracefully and return None
        self.assertIsNone(result)
    
    @patch('common.process_monitor.psutil.process_iter')
    def test_zombie_process_handling(self, mock_process_iter):
        """Test handling of zombie processes."""
        # Create a mock process that raises ZombieProcess
        mock_proc = MagicMock()
        mock_proc.pid = 1234
        mock_proc.ppid.side_effect = psutil.ZombieProcess(1234)
        mock_proc.name.return_value = "TestProcess"
        mock_proc.info = {
            'name': 'TestProcess'
        }
        
        mock_process_iter.return_value = [mock_proc]
        
        result = get_process_metrics("TestProcess")
        
        # Should handle zombie processes gracefully and return None
        self.assertIsNone(result)
    
    def test_get_disk_io_for_pid_permission_error(self):
        """Test handling of permission errors when accessing disk I/O."""
        # Create a mock process that raises AccessDenied for io_counters
        mock_proc = MagicMock()
        mock_proc.io_counters.side_effect = psutil.AccessDenied(1234)
        
        read_bytes, write_bytes = get_disk_io_for_pid(mock_proc)
        
        # Should handle the error gracefully and return zeros
        self.assertEqual(read_bytes, 0)
        self.assertEqual(write_bytes, 0)
    
    def test_get_disk_io_for_pid_no_such_process(self):
        """Test handling of NoSuchProcess when getting disk I/O."""
        # Create a mock process that raises NoSuchProcess for io_counters
        mock_proc = MagicMock()
        mock_proc.io_counters.side_effect = psutil.NoSuchProcess(1234)
        
        read_bytes, write_bytes = get_disk_io_for_pid(mock_proc)
        
        # Should handle the error gracefully and return zeros
        self.assertEqual(read_bytes, 0)
        self.assertEqual(write_bytes, 0)
    
    @patch('common.otel_connector.OTLPSpanExporter')
    def test_large_metric_batch(self, mock_exporter):
        """Test handling of large metric batches."""
        # Create a connector with mocked exporter
        connector = InstanaOTelConnector(
            service_name="test_service",
            agent_host="test_host",
            agent_port=1234
        )
        
        # Mock meter
        connector.meter = MagicMock()
        
        # Create a large metrics dictionary (1000 metrics)
        large_metrics = {f"metric_{i}": i for i in range(1000)}
        
        # Record the large batch
        connector.record_metrics(large_metrics)
        
        # Verify metrics were stored in the state
        self.assertEqual(len(connector._metrics_state), 1000)
    
    def test_log_rotation_max_size(self):
        """Test log rotation when max size is reached."""
        log_file = os.path.join(self.test_dir, 'test_rotation.log')
        
        # Configure logging with small max size
        setup_logging(log_file=log_file)
        
        # Find the file handler
        file_handler = None
        for handler in logging.root.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                file_handler = handler
                # Set a very small max size for testing
                file_handler.maxBytes = 100
                break
        
        # Generate log messages to trigger rotation
        logger = logging.getLogger("test_rotation")
        for i in range(10):
            logger.info("X" * 20)  # Each message is ~20 bytes plus timestamp etc.
        
        # Check that backup files were created
        self.assertTrue(os.path.exists(log_file))
        self.assertTrue(os.path.exists(f"{log_file}.1"))
    
    @patch('common.otel_connector.OTLPSpanExporter')
    @patch('common.otel_connector.logger')
    def test_network_error_handling(self, mock_logger, mock_exporter):
        """Test handling of network errors when exporting metrics."""
        # Make the exporter raise a connection error
        mock_exporter.side_effect = ConnectionError("Failed to connect")
        
        # This should be caught and logged without crashing
        try:
            connector = InstanaOTelConnector(
                service_name="test_service",
                agent_host="test_host",
                agent_port=1234
            )
            # If we get here without an exception, the error was handled
            self.assertTrue(True)
            # Verify the error was logged
            mock_logger.error.assert_any_call("Error setting up tracing: Failed to connect")
        except ConnectionError:
            self.fail("ConnectionError was not handled")

    @patch('common.process_monitor.psutil.process_iter')
    def test_mixed_process_states(self, mock_process_iter):
        """Test handling of processes in mixed states (running, zombie, etc.)."""
        # Create multiple mock processes with different states
        running_proc = MagicMock()
        running_proc.pid = 1234
        running_proc.ppid.return_value = 1
        running_proc.name.return_value = "TestProcess"
        running_proc.cpu_percent.return_value = 10.0
        running_proc.memory_percent.return_value = 5.0
        running_proc.info = {
            'pid': 1234,
            'ppid': 1,
            'name': 'TestProcess',
            'cpu_percent': 10.0,
            'memory_percent': 5.0
        }
        
        zombie_proc = MagicMock()
        zombie_proc.pid = 5678
        zombie_proc.ppid.side_effect = psutil.ZombieProcess(5678)
        zombie_proc.name.return_value = "TestProcess"
        zombie_proc.info = {
            'name': 'TestProcess'
        }
        
        mock_process_iter.return_value = [running_proc, zombie_proc]
        
        # Mock helper functions for the running process
        with patch('common.process_monitor.get_disk_io_for_pid') as mock_disk_io, \
             patch('common.process_monitor.get_file_descriptor_count') as mock_fd_count, \
             patch('common.process_monitor.get_thread_count') as mock_thread_count, \
             patch('common.process_monitor.get_context_switches') as mock_ctx_switches, \
             patch('common.process_monitor.get_process_cpu_per_core') as mock_cpu_per_core:
            
            mock_disk_io.return_value = (100, 200)
            mock_fd_count.return_value = 5
            mock_thread_count.return_value = 2
            mock_ctx_switches.return_value = (10, 5)
            mock_cpu_per_core.return_value = {}
            
            result = get_process_metrics("TestProcess")
            
            # Should successfully handle the running process and ignore the zombie
            self.assertIsNotNone(result)
            self.assertEqual(result["process_count"], 1)  # Only the running process should be counted
            self.assertEqual(result["cpu_usage"], 10.0)
            self.assertEqual(result["memory_usage"], 5.0)

if __name__ == '__main__':
    unittest.main()
