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

from common.metadata_store import MetadataStore

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
        # Create a service
        service_name = "com.instana.plugin.python.microstrategy_m8mulprc"
        service_id, display_name = self.store.get_or_create_service(service_name)
        
        # Verify the service was created correctly
        self.assertIsNotNone(service_id)
        self.assertIsNotNone(display_name)
        
        # Verify display name extraction (should remove com.instana.plugin.python. prefix)
        self.assertNotIn("com.instana.plugin.python.", display_name)
        self.assertIn("microstrategy", display_name.lower())
        
        # Get the service again - should return the same ID
        service_id2, _ = self.store.get_or_create_service(service_name)
        self.assertEqual(service_id, service_id2)
    
    def test_metric_creation(self):
        """Test creating metrics and retrieving their details"""
        # Create a service first
        service_name = "com.instana.plugin.python.test_service"
        service_id, _ = self.store.get_or_create_service(service_name)
        
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
        self.assertEqual("CPU 1", core_display_name)
    
    def test_format_metric_name(self):
        """Test formatting metric names according to rules"""
        test_cases = [
            ("cpu_usage", "CPU Usage"),
            ("memory_usage", "Memory Usage"),
            ("disk_read_bytes", "Disk Read Bytes"),
            ("thread_count", "Thread Count"),
            ("cpu_core_0", "CPU 0"),
            ("cpu_core_15", "CPU 15"),
            ("voluntary_ctx_switches", "Voluntary Ctx Switches")
        ]
        
        for input_name, expected_output in test_cases:
            result = self.store._format_metric_name(input_name)
            self.assertEqual(expected_output, result)
    
    def test_extract_service_display_name(self):
        """Test extracting display names from service full names"""
        test_cases = [
            ("com.instana.plugin.python.microstrategy_m8mulprc", "Microstrategy M8mulprc"),
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

if __name__ == '__main__':
    unittest.main()
