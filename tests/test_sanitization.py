#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

Unit tests for metadata sanitization functionality.
Tests the sanitize_for_metrics method comprehensively.
"""
import unittest
import sys
import os

# Add the parent directory to the path to import the common modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.metadata_store import MetadataStore

class TestMetadataSanitization(unittest.TestCase):
    """Test cases for metadata sanitization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.metadata_store = MetadataStore(db_path=":memory:")  # In-memory DB for testing
    
    def test_sanitize_basic_string(self):
        """Test sanitization of basic alphanumeric strings."""
        result = self.metadata_store.sanitize_for_metrics("simple_test")
        self.assertEqual(result, "simple_test")
        
        result = self.metadata_store.sanitize_for_metrics("SimpleTest123")
        self.assertEqual(result, "simpletest123")
    
    def test_sanitize_empty_string(self):
        """Test sanitization of empty strings."""
        result = self.metadata_store.sanitize_for_metrics("")
        self.assertEqual(result, "unknown")
        
        result = self.metadata_store.sanitize_for_metrics("   ")
        self.assertEqual(result, "unknown")
    
    def test_sanitize_none_input(self):
        """Test sanitization of None input."""
        # The method expects a string, but we should handle None gracefully
        try:
            result = self.metadata_store.sanitize_for_metrics(None)
            self.assertEqual(result, "unknown")
        except (TypeError, AttributeError):
            # If the method doesn't handle None, that's acceptable behavior
            pass
    
    def test_sanitize_unicode_characters(self):
        """Test sanitization of Unicode characters including emojis."""
        # Unicode symbols
        result = self.metadata_store.sanitize_for_metrics("Strategy₿.M8MulPrc")
        self.assertEqual(result, "strategy_m8mulprc")
        
        # Emojis
        result = self.metadata_store.sanitize_for_metrics("Service🚀Test")
        self.assertEqual(result, "service_test")
        
        # Mixed Unicode
        result = self.metadata_store.sanitize_for_metrics("Café@Résumé")
        self.assertEqual(result, "caf_r_sum")
    
    def test_sanitize_special_characters(self):
        """Test sanitization of special characters."""
        # Email-like
        result = self.metadata_store.sanitize_for_metrics("service@domain.com")
        self.assertEqual(result, "service_domain_com")
        
        # File path-like
        result = self.metadata_store.sanitize_for_metrics("path/to/service")
        self.assertEqual(result, "path_to_service")
        
        # Mixed special characters
        result = self.metadata_store.sanitize_for_metrics("Service!@#$%^&*()Name")
        self.assertEqual(result, "service_name")
    
    def test_sanitize_leading_digits(self):
        """Test sanitization of strings starting with digits."""
        result = self.metadata_store.sanitize_for_metrics("123service")
        self.assertEqual(result, "metric_123service")
        
        result = self.metadata_store.sanitize_for_metrics("9test_name")
        self.assertEqual(result, "metric_9test_name")
        
        result = self.metadata_store.sanitize_for_metrics("0")
        self.assertEqual(result, "metric_0")
    
    def test_sanitize_underscore_handling(self):
        """Test proper underscore collapsing and trimming."""
        # Multiple underscores
        result = self.metadata_store.sanitize_for_metrics("test___multiple___underscores")
        self.assertEqual(result, "test_multiple_underscores")
        
        # Leading/trailing underscores
        result = self.metadata_store.sanitize_for_metrics("___leading_trailing___")
        self.assertEqual(result, "leading_trailing")
        
        # Only underscores
        result = self.metadata_store.sanitize_for_metrics("_____")
        self.assertEqual(result, "unknown")
    
    def test_sanitize_case_sensitivity(self):
        """Test case insensitive sanitization."""
        result = self.metadata_store.sanitize_for_metrics("MixedCaseService")
        self.assertEqual(result, "mixedcaseservice")
        
        result = self.metadata_store.sanitize_for_metrics("UPPERCASE_SERVICE")
        self.assertEqual(result, "uppercase_service")
    
    def test_sanitize_complex_real_world_examples(self):
        """Test sanitization of complex real-world service names."""
        # MicroStrategy examples
        result = self.metadata_store.sanitize_for_metrics("Strategy₿.Intelligence.M8MulPrc")
        self.assertEqual(result, "strategy_intelligence_m8mulprc")
        
        # Database service
        result = self.metadata_store.sanitize_for_metrics("PostgreSQL-12.5")
        self.assertEqual(result, "postgresql_12_5")
        
        # Kubernetes service
        result = self.metadata_store.sanitize_for_metrics("api-gateway-v2.0")
        self.assertEqual(result, "api_gateway_v2_0")
        
        # Complex service name
        result = self.metadata_store.sanitize_for_metrics("com.example.service.WebAPI[v1.2.3]")
        self.assertEqual(result, "com_example_service_webapi_v1_2_3")
    
    def test_sanitize_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Very long string
        long_string = "a" * 200
        result = self.metadata_store.sanitize_for_metrics(long_string)
        self.assertEqual(result, long_string)  # Should preserve length
        
        # Single character
        result = self.metadata_store.sanitize_for_metrics("a")
        self.assertEqual(result, "a")
        
        # Only digits
        result = self.metadata_store.sanitize_for_metrics("12345")
        self.assertEqual(result, "metric_12345")
        
        # Mixed whitespace
        result = self.metadata_store.sanitize_for_metrics("test\t\nwith\rwhitespace")
        self.assertEqual(result, "test_with_whitespace")
    
    def test_sanitize_whitespace_variations(self):
        """Test various whitespace character handling."""
        # Regular spaces
        result = self.metadata_store.sanitize_for_metrics("test with spaces")
        self.assertEqual(result, "test_with_spaces")
        
        # Multiple spaces
        result = self.metadata_store.sanitize_for_metrics("test    multiple    spaces")
        self.assertEqual(result, "test_multiple_spaces")
        
        # Tab and newline characters
        result = self.metadata_store.sanitize_for_metrics("test\ttab\nnewline")
        self.assertEqual(result, "test_tab_newline")
    
    def test_sanitize_hyphen_and_dot_handling(self):
        """Test specific handling of hyphens and dots."""
        # Hyphens
        result = self.metadata_store.sanitize_for_metrics("service-name-test")
        self.assertEqual(result, "service_name_test")
        
        # Dots
        result = self.metadata_store.sanitize_for_metrics("service.name.test")
        self.assertEqual(result, "service_name_test")
        
        # Mixed hyphens and dots
        result = self.metadata_store.sanitize_for_metrics("service-name.test")
        self.assertEqual(result, "service_name_test")
    
    def test_sanitize_numeric_strings(self):
        """Test handling of various numeric patterns."""
        # Version numbers
        result = self.metadata_store.sanitize_for_metrics("v1.2.3")
        self.assertEqual(result, "v1_2_3")
        
        # IP address-like
        result = self.metadata_store.sanitize_for_metrics("192.168.1.1")
        self.assertEqual(result, "metric_192_168_1_1")
        
        # Mixed alpha-numeric
        result = self.metadata_store.sanitize_for_metrics("service2.0")
        self.assertEqual(result, "service2_0")

if __name__ == '__main__':
    unittest.main()
