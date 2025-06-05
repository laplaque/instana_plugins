#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the InstanaOTelConnector class.
"""
import unittest
from unittest.mock import patch, MagicMock, call
import sys
import os

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
from common.otel_connector import InstanaOTelConnector

class TestInstanaOTelConnector(unittest.TestCase):
    """Test cases for the InstanaOTelConnector class."""

    @patch('common.otel_connector.OTLPSpanExporter')
    @patch('common.otel_connector.TracerProvider')
    @patch('common.otel_connector.BatchSpanProcessor')
    @patch('common.otel_connector.trace.set_tracer_provider')
    @patch('common.otel_connector.trace.get_tracer')
    def test_init_and_setup_tracing(self, mock_get_tracer, mock_set_tracer_provider, 
                                    mock_batch_processor, mock_tracer_provider, 
                                    mock_span_exporter):
        """Test initialization and tracing setup."""
        # Setup mocks
        mock_tracer = MagicMock()
        mock_get_tracer.return_value = mock_tracer
        
        # Create connector
        connector = InstanaOTelConnector(
            service_name="test_service",
            agent_host="test_host",
            agent_port=1234
        )
        
        # Verify tracer setup
        mock_span_exporter.assert_called_once_with(endpoint="test_host:1234", insecure=True)
        mock_tracer_provider.assert_called_once()
        mock_batch_processor.assert_called_once()
        mock_set_tracer_provider.assert_called_once()
        mock_get_tracer.assert_called_once()
        
        # Verify connector attributes
        self.assertEqual(connector.service_name, "test_service")
        self.assertEqual(connector.agent_host, "test_host")
        self.assertEqual(connector.agent_port, 1234)
        self.assertEqual(connector.tracer, mock_tracer)

    @patch('common.otel_connector.OTLPMetricExporter')
    @patch('common.otel_connector.PeriodicExportingMetricReader')
    @patch('common.otel_connector.MeterProvider')
    @patch('common.otel_connector.set_meter_provider')
    @patch('common.otel_connector.get_meter_provider')
    def test_setup_metrics(self, mock_get_meter_provider, mock_set_meter_provider,
                          mock_meter_provider, mock_reader, mock_exporter):
        """Test metrics setup."""
        # Setup mocks
        mock_meter = MagicMock()
        mock_meter_provider_instance = MagicMock()
        mock_get_meter_provider.return_value = mock_meter_provider_instance
        mock_meter_provider_instance.get_meter.return_value = mock_meter
        
        # Create connector with mocked tracing
        with patch.object(InstanaOTelConnector, '_setup_tracing'):
            connector = InstanaOTelConnector(
                service_name="test_service",
                agent_host="test_host",
                agent_port=1234
            )
        
        # Verify metrics setup
        mock_exporter.assert_called_once_with(endpoint="test_host:1234", insecure=True)
        mock_reader.assert_called_once()
        mock_meter_provider.assert_called_once()
        mock_set_meter_provider.assert_called_once()
        mock_meter_provider_instance.get_meter.assert_called_once()
        
        # Verify connector attributes
        self.assertEqual(connector.meter, mock_meter)

    @patch.object(InstanaOTelConnector, '_setup_tracing')
    @patch.object(InstanaOTelConnector, '_setup_metrics')
    def test_record_metrics(self, mock_setup_metrics, mock_setup_tracing):
        """Test recording metrics."""
        # Create connector with mocked setup methods
        connector = InstanaOTelConnector(
            service_name="test_service",
            agent_host="test_host",
            agent_port=1234
        )
        
        # Test with numeric metrics
        metrics = {
            "cpu_usage": 10.5,
            "memory_usage": 20.3,
            "process_count": 3
        }
        connector.record_metrics(metrics)
        
        # Verify metrics state was updated
        self.assertEqual(connector._metrics_state["cpu_usage"], 10.5)
        self.assertEqual(connector._metrics_state["memory_usage"], 20.3)
        self.assertEqual(connector._metrics_state["process_count"], 3)
        
        # Test with string metrics
        metrics = {
            "cpu_usage": "10.5",
            "non_numeric": "text"
        }
        connector.record_metrics(metrics)
        
        # Verify metrics state was updated for numeric string
        self.assertEqual(connector._metrics_state["cpu_usage"], 10.5)
        self.assertNotIn("non_numeric", connector._metrics_state)

    @patch.object(InstanaOTelConnector, '_setup_tracing')
    @patch.object(InstanaOTelConnector, '_setup_metrics')
    def test_create_span(self, mock_setup_metrics, mock_setup_tracing):
        """Test creating a span."""
        # Create connector with mocked setup methods
        connector = InstanaOTelConnector(
            service_name="test_service",
            agent_host="test_host",
            agent_port=1234
        )
        
        # Mock tracer
        connector.tracer = MagicMock()
        mock_span = MagicMock()
        connector.tracer.start_as_current_span.return_value = mock_span
        
        # Create span
        span = connector.create_span("test_span", {"attr": "value"})
        
        # Verify span creation
        connector.tracer.start_as_current_span.assert_called_once_with(
            "test_span", attributes={"attr": "value"}
        )
        self.assertEqual(span, mock_span)

    @patch.object(InstanaOTelConnector, '_setup_tracing')
    def test_create_metric_callback_generator(self, mock_setup_tracing):
        """Test that _create_metric_callback correctly produces a generator that yields values."""
        # Create connector
        connector = InstanaOTelConnector(
            service_name="test_service",
            agent_host="test_host",
            agent_port=1234
        )
        
        # Add metrics to the state
        connector._metrics_state = {
            "test_metric": 42.0,
            "another_metric": 99.5
        }
        
        # Create callback for a metric that exists in the state
        callback = connector._create_metric_callback("test_metric")
        
        # Call the callback with a mock options object
        mock_options = MagicMock()
        result = list(callback(mock_options))
        
        # Verify the callback yielded a value (we can't check the exact type due to mocking)
        self.assertEqual(len(result), 1)
        
        # Test callback for metric not in state (should yield nothing)
        callback = connector._create_metric_callback("non_existent_metric")
        result = list(callback(mock_options))
        self.assertEqual(len(result), 0)

    @patch.object(InstanaOTelConnector, '_setup_tracing')
    def test_register_observable_metrics(self, mock_setup_tracing):
        """Test registering observable metrics."""
        # Create connector with mocked meter
        connector = InstanaOTelConnector(
            service_name="test_service",
            agent_host="test_host",
            agent_port=1234
        )
        
        # Mock the meter and gauge
        connector.meter = MagicMock()
        mock_gauge = MagicMock()
        connector.meter.create_observable_gauge.return_value = mock_gauge
        
        # Call register_observable_metrics
        connector._register_observable_metrics()
        
        # Base expected metrics (core metrics without CPU cores)
        base_metrics = [
            "cpu_usage", "memory_usage", "process_count", "disk_read_bytes", 
            "disk_write_bytes", "open_file_descriptors", "thread_count",
            "voluntary_ctx_switches", "nonvoluntary_ctx_switches"
        ]
        
        # Our implementation now uses the actual CPU count from the system
        cpu_core_count = os.cpu_count() or 1  # Same approach as in the implementation
        expected_cpu_core_metrics = [f"cpu_core_{i}" for i in range(cpu_core_count)]
        
        # All expected metrics
        expected_metrics = base_metrics + expected_cpu_core_metrics
        
        # Verify the number of calls to create_observable_gauge
        # +1 for the general metrics gauge
        self.assertEqual(connector.meter.create_observable_gauge.call_count, 
                         len(expected_metrics) + 1)
        
        # Verify metrics were added to registry
        for metric in expected_metrics:
            self.assertIn(metric, connector._metrics_registry)
            
        # Verify each call to create_observable_gauge includes callbacks parameter
        for call_args in connector.meter.create_observable_gauge.call_args_list:
            args, kwargs = call_args
            self.assertIn('callbacks', kwargs)
            self.assertIsInstance(kwargs['callbacks'], list)
            self.assertTrue(len(kwargs['callbacks']) > 0)
    
    @patch.object(InstanaOTelConnector, '_setup_tracing')
    @patch.object(InstanaOTelConnector, '_setup_metrics')
    def test_shutdown(self, mock_setup_metrics, mock_setup_tracing):
        """Test shutdown method."""
        # Create connector with mocked setup methods
        connector = InstanaOTelConnector(
            service_name="test_service",
            agent_host="test_host",
            agent_port=1234
        )
        
        # Mock providers
        connector._tracer_provider = MagicMock()
        connector._meter_provider = MagicMock()
        
        # Call shutdown
        connector.shutdown()
        
        # Verify flush calls
        connector._tracer_provider.force_flush.assert_called_once()
        connector._meter_provider.force_flush.assert_called_once()

if __name__ == '__main__':
    unittest.main()
