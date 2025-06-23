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
        """Test recording metrics with strict TOML validation."""
        # Create connector with mocked setup methods
        connector = InstanaOTelConnector(
            service_name="test_service",
            agent_host="test_host",
            agent_port=1234
        )
        
        # Add some metrics to the registry (simulating TOML-defined metrics)
        connector._metrics_registry.add("cpu_usage")
        connector._metrics_registry.add("memory_usage") 
        connector._metrics_registry.add("process_count")
        
        # Test with numeric metrics that are in registry
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
        
        # Test with string metrics (valid metric in registry)
        metrics = {
            "cpu_usage": "10.5",
            "undefined_metric": "text"  # This should be rejected
        }
        connector.record_metrics(metrics)
        
        # Verify metrics state was updated for numeric string but undefined metric rejected
        self.assertEqual(connector._metrics_state["cpu_usage"], 10.5)
        self.assertNotIn("undefined_metric", connector._metrics_state)
        
        # Test rejection of metrics not in registry
        metrics = {
            "unknown_metric": 42.0
        }
        old_state_length = len(connector._metrics_state)
        connector.record_metrics(metrics)
        
        # Verify unknown metric was rejected (state unchanged)
        self.assertEqual(len(connector._metrics_state), old_state_length)
        self.assertNotIn("unknown_metric", connector._metrics_state)

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
    @patch.object(InstanaOTelConnector, '_setup_metrics')
    @patch.object(InstanaOTelConnector, '_sync_toml_to_database')
    def test_register_observable_metrics(self, mock_sync_toml, mock_setup_metrics, mock_setup_tracing):
        """Test registering observable metrics with new database-driven approach."""
        # Setup mock database metrics
        mock_database_metrics = [
            {
                'name': 'cpu_usage',
                'otel_type': 'Gauge',
                'unit': '%',
                'decimal_places': 2,
                'is_percentage': True,
                'is_counter': False,
                'description': 'CPU usage percentage',
                'display_name': 'CPU Usage'
            },
            {
                'name': 'process_count',
                'otel_type': 'UpDownCounter',
                'unit': 'processes',
                'decimal_places': 0,
                'is_percentage': False,
                'is_counter': True,
                'description': 'Number of processes',
                'display_name': 'Process Count'
            }
        ]
        
        # Configure the sync mock to return True
        mock_sync_toml.return_value = True
        
        # Create connector (sync will be called during initialization)
        connector = InstanaOTelConnector(
            service_name="test_service",
            agent_host="test_host",
            agent_port=1234
        )
        
        # Mock the metadata store methods and create_observable method  
        with patch.object(connector._metadata_store, 'get_service_metrics', return_value=mock_database_metrics), \
             patch.object(connector, 'create_observable') as mock_create_observable:
            
            mock_create_observable.return_value = MagicMock()
            
            # Verify sync was called during initialization (before reset)
            self.assertTrue(mock_sync_toml.called)
            
            # Reset call count for the explicit test call
            mock_sync_toml.reset_mock()
            
            # Call register_observable_metrics explicitly 
            connector._register_observable_metrics()
            
            # Verify sync was called again in the explicit call
            self.assertTrue(mock_sync_toml.called)
            
            # Verify create_observable was called for each metric
            self.assertEqual(mock_create_observable.call_count, 2)
            
            # Verify metrics were added to registry
            self.assertIn('cpu_usage', connector._metrics_registry)
            self.assertIn('process_count', connector._metrics_registry)

    @patch.object(InstanaOTelConnector, '_setup_tracing')
    @patch.object(InstanaOTelConnector, '_setup_metrics')
    def test_create_observable_method(self, mock_setup_metrics, mock_setup_tracing):
        """Test the unified create_observable method with different metric types."""
        # Create connector
        connector = InstanaOTelConnector(
            service_name="test_service",
            agent_host="test_host",
            agent_port=1234
        )
        
        # Explicitly set meter to a MagicMock to avoid recursion issues
        connector.meter = MagicMock()
        
        # Mock metadata store method with patch and run tests inside context
        with patch.object(connector._metadata_store, 'get_simple_metric_name', return_value="test_metric"):
            # Test Gauge type
            result = connector.create_observable(
                name="test_gauge",
                otel_type="Gauge",
                unit="%",
                decimals=2,
                is_percentage=True,
                is_counter=False,
                description="Test gauge metric"
            )
            self.assertIsNotNone(result)
            
            # Test Counter type  
            result = connector.create_observable(
                name="test_counter",
                otel_type="Counter",
                unit="bytes",
                decimals=0,
                is_percentage=False,
                is_counter=True,
                description="Test counter metric"
            )
            self.assertIsNotNone(result)
            
            # Test UpDownCounter type
            result = connector.create_observable(
                name="test_updown",
                otel_type="UpDownCounter",
                unit="processes",
                decimals=0,
                is_percentage=False,
                is_counter=True,
                description="Test updown counter metric"
            )
            self.assertIsNotNone(result)
    
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
