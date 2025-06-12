#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the base_sensor module.
"""
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os
import argparse

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
from common.base_sensor import parse_args, monitor_process, run_sensor

class TestBaseSensor(unittest.TestCase):
    """Test cases for the base_sensor module."""

    def test_parse_args(self):
        """Test argument parsing."""
        # Test with default arguments
        with patch('sys.argv', ['sensor.py']):
            args = parse_args("Test description")
            self.assertEqual(args.agent_host, "localhost")
            self.assertEqual(args.agent_port, 4317)
            self.assertEqual(args.interval, 60)
            self.assertFalse(args.once)
            self.assertEqual(args.log_level, "INFO")
        
        # Test with custom arguments
        with patch('sys.argv', [
            'sensor.py',
            '--agent-host', 'test-host',
            '--agent-port', '1234',
            '--interval', '30',
            '--once',
            '--log-level', 'DEBUG'
        ]):
            args = parse_args("Test description")
            self.assertEqual(args.agent_host, "test-host")
            self.assertEqual(args.agent_port, 1234)
            self.assertEqual(args.interval, 30)
            self.assertTrue(args.once)
            self.assertEqual(args.log_level, "DEBUG")

    @patch('common.base_sensor.InstanaOTelConnector')
    @patch('common.base_sensor.get_process_metrics')
    @patch('time.sleep')
    def test_monitor_process_once(self, mock_sleep, mock_get_metrics, mock_connector):
        """Test monitor_process with run_once=True."""
        # Mock connector and metrics
        mock_connector_instance = MagicMock()
        mock_connector.return_value = mock_connector_instance
        mock_span = MagicMock()
        mock_connector_instance.create_span.return_value.__enter__.return_value = mock_span
        
        mock_metrics = {
            "cpu_usage": 10.5,
            "memory_usage": 20.3,
            "process_count": 3
        }
        mock_get_metrics.return_value = mock_metrics
        
        # Call function
        result = monitor_process(
            process_name="TestProcess",
            plugin_name="test.plugin",
            agent_host="test-host",
            agent_port=1234,
            interval=30,
            run_once=True
        )
        
        # Verify connector setup
        mock_connector.assert_called_once_with(
            service_name="test.plugin",
            agent_host="test-host",
            agent_port=1234,
            resource_attributes={
                "process.name": "TestProcess",
                "host.name": os.uname()[1]
            },
            metadata_db_path=None,
            service_namespace="Unknown"
        )
        
        # Verify metrics collection
        mock_connector_instance.create_span.assert_called_once()
        mock_get_metrics.assert_called_once_with("TestProcess")
        mock_connector_instance.record_metrics.assert_called_once_with(mock_metrics)
        
        # Verify result
        self.assertTrue(result)
        
        # Verify shutdown was called
        mock_connector_instance.shutdown.assert_called_once()
        
        # Verify sleep was not called
        mock_sleep.assert_not_called()

    @patch('common.base_sensor.InstanaOTelConnector')
    @patch('common.base_sensor.get_process_metrics')
    @patch('time.sleep')
    def test_monitor_process_continuous(self, mock_sleep, mock_get_metrics, mock_connector):
        """Test monitor_process with continuous monitoring."""
        # Mock connector and metrics
        mock_connector_instance = MagicMock()
        mock_connector.return_value = mock_connector_instance
        mock_span = MagicMock()
        mock_connector_instance.create_span.return_value.__enter__.return_value = mock_span
        
        mock_metrics = {
            "cpu_usage": 10.5,
            "memory_usage": 20.3,
            "process_count": 3
        }
        mock_get_metrics.return_value = mock_metrics
        
        # Make sleep raise KeyboardInterrupt after first call
        mock_sleep.side_effect = [None, KeyboardInterrupt]
        
        # Call function
        monitor_process(
            process_name="TestProcess",
            plugin_name="test.plugin",
            agent_host="test-host",
            agent_port=1234,
            interval=30
        )
        
        # Verify connector setup
        mock_connector.assert_called_once()
        
        # Verify metrics collection happened twice
        self.assertEqual(mock_connector_instance.create_span.call_count, 2)
        self.assertEqual(mock_get_metrics.call_count, 2)
        self.assertEqual(mock_connector_instance.record_metrics.call_count, 2)
        
        # Verify sleep was called with the interval
        self.assertEqual(mock_sleep.call_count, 2)
        mock_sleep.assert_has_calls([call(30), call(30)])
        
        # Verify shutdown was called
        mock_connector_instance.shutdown.assert_called_once()

    @patch('common.base_sensor.setup_logging')
    @patch('common.base_sensor.daemonize')
    @patch('common.base_sensor.parse_args')
    @patch('common.base_sensor.monitor_process')
    @patch('common.base_sensor.logging.getLogger')
    @patch('sys.exit')
    def test_run_sensor_once(self, mock_exit, mock_get_logger, mock_monitor, mock_parse_args, mock_daemonize, mock_setup_logging):
        """Test run_sensor with --once flag."""
        # Mock args
        mock_args = MagicMock()
        mock_args.agent_host = "test-host"
        mock_args.agent_port = 1234
        mock_args.interval = 30
        mock_args.once = True
        mock_args.log_level = "DEBUG"
        mock_args.stop = False
        mock_args.restart = False
        mock_args.install_location = "/usr/local/bin"
        mock_args.log_file = None
        mock_parse_args.return_value = mock_args
        
        # Mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Mock monitor_process to return True
        mock_monitor.return_value = True
        
        # Call function
        run_sensor("TestProcess", "test.plugin", "1.0.0")
        
        # Verify parse_args was called
        mock_parse_args.assert_called_once()
        
        # Verify monitor_process was called with correct args
        mock_monitor.assert_called_once_with(
            process_name="TestProcess",
            plugin_name="test.plugin",
            agent_host="test-host",
            agent_port=1234,
            interval=30,
            run_once=True,
            metadata_db_path=mock_args.metadata_db_path,
            service_namespace="Unknown"
        )
        
        # Verify sys.exit was called with 0 (success)
        mock_exit.assert_called_once_with(0)

    @patch('common.base_sensor.setup_logging')
    @patch('common.base_sensor.daemonize')
    @patch('common.base_sensor.parse_args')
    @patch('common.base_sensor.monitor_process')
    @patch('common.base_sensor.logging.getLogger')
    @patch('sys.exit')
    def test_run_sensor_continuous(self, mock_exit, mock_get_logger, mock_monitor, mock_parse_args, mock_daemonize, mock_setup_logging):
        """Test run_sensor with continuous monitoring."""
        # Mock args
        mock_args = MagicMock()
        mock_args.agent_host = "test-host"
        mock_args.agent_port = 1234
        mock_args.interval = 30
        mock_args.once = False
        mock_args.log_level = "DEBUG"
        mock_args.stop = False
        mock_args.restart = False
        mock_args.install_location = "/usr/local/bin"
        mock_args.log_file = None
        mock_parse_args.return_value = mock_args
        
        # Mock logger
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Call function
        run_sensor("TestProcess", "test.plugin", "1.0.0")
        
        # Verify parse_args was called
        mock_parse_args.assert_called_once()
        
        # Verify monitor_process was called with correct args
        mock_monitor.assert_called_once_with(
            process_name="TestProcess",
            plugin_name="test.plugin",
            agent_host="test-host",
            agent_port=1234,
            interval=30,
            metadata_db_path=mock_args.metadata_db_path,
            service_namespace="Unknown"
        )
        
        # Verify sys.exit was not called
        mock_exit.assert_not_called()

if __name__ == '__main__':
    unittest.main()
