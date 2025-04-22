#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

Test script for TLS connection with OpenTelemetry.
"""
import os
import sys
import logging
import argparse
from unittest.mock import patch, MagicMock

# Add parent directory to path to import common modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import mocks before real imports to prevent actual OpenTelemetry imports
from tests.mocks.opentelemetry import trace, metrics, Resource, TracerProvider, BatchSpanProcessor
from tests.mocks.opentelemetry import OTLPSpanExporter, MeterProvider, PeriodicExportingMetricReader, OTLPMetricExporter

# Now patch the modules
sys.modules['opentelemetry'] = MagicMock()
sys.modules['opentelemetry.trace'] = trace
sys.modules['opentelemetry.metrics'] = metrics
sys.modules['opentelemetry.sdk.resources'] = MagicMock()
sys.modules['opentelemetry.sdk.resources.Resource'] = Resource
sys.modules['opentelemetry.sdk.trace'] = MagicMock()
sys.modules['opentelemetry.sdk.trace.TracerProvider'] = TracerProvider
sys.modules['opentelemetry.sdk.trace.export'] = MagicMock()
sys.modules['opentelemetry.sdk.trace.export.BatchSpanProcessor'] = BatchSpanProcessor
sys.modules['opentelemetry.exporter.otlp.proto.grpc.trace_exporter'] = MagicMock()
sys.modules['opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter'] = OTLPSpanExporter
sys.modules['opentelemetry.sdk.metrics'] = MagicMock()
sys.modules['opentelemetry.sdk.metrics.MeterProvider'] = MeterProvider
sys.modules['opentelemetry.sdk.metrics.export'] = MagicMock()
sys.modules['opentelemetry.sdk.metrics.export.PeriodicExportingMetricReader'] = PeriodicExportingMetricReader
sys.modules['opentelemetry.exporter.otlp.proto.grpc.metric_exporter'] = MagicMock()
sys.modules['opentelemetry.exporter.otlp.proto.grpc.metric_exporter.OTLPMetricExporter'] = OTLPMetricExporter

# Now import the connector
from common.otel_connector import InstanaOTelConnector
from common.logging_config import setup_logging

def test_tls_configuration():
    """Test TLS configuration from environment variables"""
    # Set up environment variables
    os.environ['USE_TLS'] = 'true'
    os.environ['CA_CERT_PATH'] = '/path/to/ca.crt'
    os.environ['CLIENT_CERT_PATH'] = '/path/to/client.crt'
    os.environ['CLIENT_KEY_PATH'] = '/path/to/client.key'
    
    # Create connector
    connector = InstanaOTelConnector(service_name="test-service")
    
    # Verify TLS settings
    assert connector.use_tls is True, "TLS should be enabled"
    assert connector.ca_cert_path == '/path/to/ca.crt', "CA cert path not set correctly"
    assert connector.client_cert_path == '/path/to/client.crt', "Client cert path not set correctly"
    assert connector.client_key_path == '/path/to/client.key', "Client key path not set correctly"
    
    print("✅ TLS configuration test passed")
    return True

def test_tls_setup_tracing():
    """Test TLS configuration in _setup_tracing method"""
    # Set up environment variables
    os.environ['USE_TLS'] = 'true'
    os.environ['CA_CERT_PATH'] = '/path/to/ca.crt'
    
    # Create connector with patched OTLPSpanExporter
    with patch('tests.mocks.opentelemetry.OTLPSpanExporter') as mock_exporter:
        connector = InstanaOTelConnector(service_name="test-service")
        
        # Verify exporter was called with correct parameters
        mock_exporter.assert_called_once()
        args, kwargs = mock_exporter.call_args
        
        # Check that endpoint has https:// prefix
        assert 'endpoint' in kwargs, "endpoint parameter missing"
        assert kwargs['endpoint'].startswith('https://'), "TLS endpoint should start with https://"
        
        # Check that insecure is False
        assert 'insecure' in kwargs, "insecure parameter missing"
        assert kwargs['insecure'] is False, "insecure should be False for TLS"
        
        # Check that ca_file is set
        assert 'ca_file' in kwargs, "ca_file parameter missing"
        assert kwargs['ca_file'] == '/path/to/ca.crt', "ca_file not set correctly"
    
    print("✅ TLS tracing setup test passed")
    return True

def main():
    """Run the tests"""
    setup_logging(log_level=logging.DEBUG)
    
    parser = argparse.ArgumentParser(description='Test TLS configuration for OpenTelemetry connector')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("Running TLS configuration tests...")
    
    tests_passed = 0
    tests_total = 2
    
    try:
        if test_tls_configuration():
            tests_passed += 1
    except Exception as e:
        print(f"❌ TLS configuration test failed: {e}")
    
    try:
        if test_tls_setup_tracing():
            tests_passed += 1
    except Exception as e:
        print(f"❌ TLS tracing setup test failed: {e}")
    
    print(f"\nTests completed: {tests_passed}/{tests_total} passed")
    
    if tests_passed == tests_total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
