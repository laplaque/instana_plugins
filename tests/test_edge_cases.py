#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for edge cases and limitations.
"""
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import logging
import tempfile
import shutil

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules to test
from common.process_monitor import get_process_metrics
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
    
    @patch('common.process_monitor.subprocess.check_output')
    def test_empty_process_output(self, mock_check_output):
        """Test handling of empty process output."""
        # Mock empty output from ps command
        mock_check_output.return_value = b""
        
        # Call the function
        result = get_process_metrics("TestProcess")
        
        # Should return None for empty output
        self.assertIsNone(result)
    
    @patch('common.process_monitor.subprocess.check_output')
    def test_malformed_process_output(self, mock_check_output):
        """Test handling of malformed process output."""
        # Mock malformed output from ps command
        mock_check_output.return_value = b"PID CPU MEM COMMAND\ninvalid data"
        
        # Call the function
        result = get_process_metrics("TestProcess")
        
        # Should return None for malformed output
        self.assertIsNone(result)
    
    @patch('common.process_monitor.subprocess.check_output')
    def test_process_with_special_chars(self, mock_check_output):
        """Test handling of process names with special characters."""
        # Mock output with special characters in process name - proper PS output format with semicolon delimiter
        mock_check_output.return_value = b"PID;PPID;%CPU;%MEM;COMMAND\n123;1;10.5;20.3;Test-Process[special]"
        
        # Call the function with regex special characters
        result = get_process_metrics("Test-Process\\[special\\]")
        
        # Should handle special characters correctly
        self.assertIsNotNone(result)
        self.assertEqual(result["process_count"], 1)
        self.assertEqual(result["cpu_usage"], 10.5)
    
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
    
    @patch('builtins.open')
    def test_proc_file_permission_error(self, mock_open):
        """Test handling of permission errors when accessing /proc files."""
        # Mock permission error when opening /proc file
        mock_open.side_effect = PermissionError("Permission denied")
        
        # Call the function that would access /proc
        from common.process_monitor import get_disk_io_for_pid
        read_bytes, write_bytes = get_disk_io_for_pid(1234)
        
        # Should handle the error gracefully
        self.assertEqual(read_bytes, 0)
        self.assertEqual(write_bytes, 0)
    
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

if __name__ == '__main__':
    unittest.main()
