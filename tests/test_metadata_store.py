#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.
"""
import os
import sys
import unittest
import tempfile
import shutil
import re
from unittest.mock import patch

# Add the parent directory to the path to import the common modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.version import get_version
from common.metadata_store import MetadataStore

# Get the version from the new version system
VERSION = get_version()

class TestMetadataStore(unittest.TestCase):
    """Test cases for the MetadataStore class"""
    
    def setUp(self):
        """Set up a temporary database for testing"""
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_metadata.db")
        self.store = MetadataStore(db_path=self.db_path)
        
    def tearDown(self):
        """Clean up temporary files"""
        shutil.rmtree(self.test_dir)
        
    def test_service_creation(self):
        """Test creating a service and retrieving its details"""
        # Create a service with version from common/__init__.py
        service_name = "com.instana.plugin.python.m8mulprc"
        description = "MicroStrategy M8 Multi-purpose Process Monitor"
        
        service_id, display_name = self.store.get_or_create_service(
            service_name, 
            version=VERSION,
            description=description
        )
        
        # Verify the service was created correctly
        self.assertIsNotNone(service_id)
        self.assertIsNotNone(display_name)
        
        # Verify display name extraction (should remove com.instana.plugin.python. prefix)
        self.assertNotIn("com.instana.plugin.python.", display_name)
        self.assertIn("m8mulprc", display_name.lower())
        
        # Get the service again - should return the same ID
        service_id2, _ = self.store.get_or_create_service(service_name)
        self.assertEqual(service_id, service_id2)
        
        # Get the service info and verify details
        service_info = self.store.get_service_info(service_id)
        self.assertIsNotNone(service_info)
        # The service name gets sanitized (dots replaced with underscores) for database storage
        expected_sanitized_name = service_name.replace('.', '_')
        self.assertEqual(expected_sanitized_name, service_info['full_name'])
        self.assertEqual(display_name, service_info['display_name'])
        self.assertEqual(VERSION, service_info['version'])
        self.assertEqual(description, service_info['description'])
    
    def test_metrics_for_service(self):
        """Test retrieving all metrics for a service"""
        # Create a service
        service_name = "com.instana.plugin.python.test_service_metrics"
        service_id, _ = self.store.get_or_create_service(
            service_name,
            version=VERSION,
            description="Test Service for Metrics"
        )
        
        # Create multiple metrics
        metrics_to_create = [
            ("cpu_usage", "%", "percentage", 2, True),
            ("memory_usage", "%", "percentage", 2, True),
            ("disk_read_bytes", "bytes", "bytes", 0, False),
            ("thread_count", "threads", "number", 0, False)
        ]
        
        for name, unit, format_type, decimal_places, is_percentage in metrics_to_create:
            self.store.get_or_create_metric(
                service_id=service_id,
                name=name,
                unit=unit,
                format_type=format_type,
                decimal_places=decimal_places,
                is_percentage=is_percentage
            )
        
        # Get all metrics for the service
        metrics = self.store.get_metrics_for_service(service_id)
        
        # Verify we got all the metrics we created
        self.assertEqual(len(metrics_to_create), len(metrics))
        
        # Verify each metric has the expected fields
        metric_names = [m['name'] for m in metrics]
        for name, _, _, _, _ in metrics_to_create:
            self.assertIn(name, metric_names)
    
    def test_metric_creation(self):
        """Test creating metrics and retrieving their details"""
        # Create a service first
        service_name = "com.instana.plugin.python.test_service"
        service_id, _ = self.store.get_or_create_service(service_name, version=VERSION)
        
        # Create a regular metric
        metric_name = "cpu_usage"
        metric_id, display_name = self.store.get_or_create_metric(
            service_id=service_id,
            name=metric_name,
            unit="%",
            format_type="percentage",
            decimal_places=2,
            is_percentage=True
        )
        
        # Verify the metric was created correctly
        self.assertIsNotNone(metric_id)
        self.assertEqual("CPU Usage", display_name)
        
        # Get the metric info
        metric_info = self.store.get_metric_info(service_id, metric_name)
        self.assertIsNotNone(metric_info)
        self.assertEqual(metric_id, metric_info['id'])
        self.assertEqual(display_name, metric_info['display_name'])
        self.assertEqual("%", metric_info['unit'])
        self.assertEqual("percentage", metric_info['format_type'])
        self.assertEqual(2, metric_info['decimal_places'])
        self.assertTrue(metric_info['is_percentage'])
        
        # Create a CPU core metric to test special formatting
        core_metric_name = "cpu_core_1"
        _, core_display_name = self.store.get_or_create_metric(
            service_id=service_id,
            name=core_metric_name,
            unit="%",
            is_percentage=True
        )
        
        # Verify special CPU core formatting
        self.assertEqual("CPU Core 1", core_display_name)
    
    def test_format_metric_name(self):
        """Test formatting metric names according to rules"""
        test_cases = [
            ("cpu_usage", "CPU Usage"),
            ("memory_usage", "Memory Usage"),
            ("disk_read_bytes", "Disk Read Bytes"),
            ("thread_count", "Thread Count"),
            ("cpu_core_0", "CPU Core 0"),
            ("cpu_core_15", "CPU Core 15"),
            ("voluntary_ctx_switches", "Voluntary Ctx Switches")
        ]
        
        for input_name, expected_output in test_cases:
            result = self.store._format_metric_name(input_name)
            self.assertEqual(expected_output, result)
    
    def test_extract_service_display_name(self):
        """Test extracting display names from service full names"""
        test_cases = [
            ("com.instana.plugin.python.m8mulprc", "M8mulprc"),
            ("com.instana.plugin.python.m8refsvr", "M8refsvr"),
            ("com.instana.plugin.java.tomcat", "Tomcat"),
            ("standalone_service", "Standalone Service")  # Fallback case
        ]
        
        for input_name, expected_output in test_cases:
            result = self.store._extract_service_display_name(input_name)
            self.assertEqual(expected_output, result)
    
    def test_format_metric_value(self):
        """Test formatting metric values"""
        # Test percentage conversion
        self.assertEqual(75.0, self.store.format_metric_value(0.75, is_percentage=True))
        self.assertEqual(100.0, self.store.format_metric_value(1.0, is_percentage=True))
        
        # Test decimal place rounding
        self.assertEqual(75.12, self.store.format_metric_value(75.123, is_percentage=False, decimal_places=2))
        self.assertEqual(75.1, self.store.format_metric_value(75.123, is_percentage=False, decimal_places=1))
        
        # Test combined percentage and rounding
        self.assertEqual(75.5, self.store.format_metric_value(0.755, is_percentage=True, decimal_places=1))
        
        # Test no conversion for already-percentage values over 1.0
        self.assertEqual(75.0, self.store.format_metric_value(75.0, is_percentage=True))
        
        # Test counter formatting (should return integers)
        self.assertEqual(75, self.store.format_metric_value(75.123, is_counter=True))
        self.assertEqual(76, self.store.format_metric_value(75.789, is_counter=True))
        
        # Test counter with percentage (percentage conversion happens first, then integer conversion)
        self.assertEqual(75, self.store.format_metric_value(0.753, is_percentage=True, is_counter=True))

if __name__ == '__main__':
    unittest.main()
