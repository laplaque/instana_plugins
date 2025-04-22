#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for all unit tests.
"""
import unittest
import sys
import os
import importlib.util
import argparse
import coverage

# Add the parent directory to the path to import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'mocks')))

def setup_mocks():
    """Set up mock modules for OpenTelemetry if not installed"""
    try:
        import opentelemetry
        print("Using installed OpenTelemetry modules")
        return True
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
        return False

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Run tests for Instana Plugins')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage report')
    parser.add_argument('--xml', action='store_true', help='Generate XML test report')
    parser.add_argument('--pattern', default='test_*.py', help='Test file pattern (default: test_*.py)')
    parser.add_argument('--verbose', '-v', action='count', default=1, help='Verbosity level')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    
    # Set up mocks if needed
    has_otel = setup_mocks()
    
    # Initialize coverage if requested
    if args.coverage:
        cov = coverage.Coverage(
            source=['common'],
            omit=['*/__pycache__/*', '*/tests/*', '*/mocks/*']
        )
        cov.start()
    
    # Discover and run all tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover(start_dir='tests', pattern=args.pattern)
    
    # Run the tests
    if args.xml:
        import xmlrunner
        test_runner = xmlrunner.XMLTestRunner(output='test-reports', verbosity=args.verbose)
    else:
        test_runner = unittest.TextTestRunner(verbosity=args.verbose)
    
    result = test_runner.run(test_suite)
    
    # Generate coverage report if requested
    if args.coverage:
        cov.stop()
        cov.save()
        print("\nCoverage Report:")
        cov.report()
        cov.html_report(directory='coverage_html')
        print(f"HTML coverage report generated in coverage_html/")
    
    # Exit with non-zero code if tests failed
    sys.exit(0 if result.wasSuccessful() else 1)
