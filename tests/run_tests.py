#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for all unit tests.
"""
import unittest
import sys
import os
import importlib.util

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'mocks')))

# Check if OpenTelemetry is installed, if not use mocks
try:
    import opentelemetry
    print("Using installed OpenTelemetry modules")
except ImportError:
    print("OpenTelemetry not installed, using mock modules")
    # Mock the OpenTelemetry imports
    from unittest.mock import MagicMock
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

if __name__ == '__main__':
    # Discover and run all tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir='tests', pattern='test_*.py')
    
    # Run the tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Exit with non-zero code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)
