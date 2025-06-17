#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for the refactored MetadataStore class.
"""
import unittest
import os
import sqlite3
import tempfile
import shutil
from datetime import datetime
from unittest.mock import patch, MagicMock

from common.metadata_store import MetadataStore

class TestMetadataRefactor(unittest.TestCase):
    """Test the refactored MetadataStore class."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_metadata.db")
        
    def tearDown(self):
        """Clean up after tests."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_build_metrics_query_insert_with_otel(self):
        """Test _build_metrics_query for insert with otel_type."""
        store = MetadataStore(self.db_path)
        sql, param_order = store._build_metrics_query('insert', True)
        
        # Check that SQL contains all expected columns
        self.assertIn("id", sql)
        self.assertIn("service_id", sql)
        self.assertIn("name", sql)
        self.assertIn("otel_type", sql)
        self.assertIn("first_seen", sql)
        self.assertIn("last_seen", sql)
        
        # Check param order includes all expected parameters
        self.assertIn("id", param_order)
        self.assertIn("service_id", param_order)
        self.assertIn("name", param_order)
        self.assertIn("otel_type", param_order)
        self.assertIn("first_seen", param_order)
        self.assertIn("last_seen", param_order)
    
    def test_build_metrics_query_insert_without_otel(self):
        """Test _build_metrics_query for insert without otel_type."""
        store = MetadataStore(self.db_path)
        sql, param_order = store._build_metrics_query('insert', False)
        
        # Check that SQL contains expected columns but not otel_type
        self.assertIn("id", sql)
        self.assertIn("service_id", sql)
        self.assertIn("name", sql)
        self.assertNotIn("otel_type", sql)
        self.assertIn("first_seen", sql)
        self.assertIn("last_seen", sql)
        
        # Check param order includes expected parameters but not otel_type
        self.assertIn("id", param_order)
        self.assertIn("service_id", param_order)
        self.assertIn("name", param_order)
        self.assertNotIn("otel_type", param_order)
        self.assertIn("first_seen", param_order)
        self.assertIn("last_seen", param_order)
    
    def test_build_metrics_query_update_with_otel(self):
        """Test _build_metrics_query for update with otel_type."""
        store = MetadataStore(self.db_path)
        sql, param_order = store._build_metrics_query('update', True)
        
        # Check that SQL contains all expected SET clauses
        self.assertIn("display_name = ?", sql)
        self.assertIn("unit = ?", sql)
        self.assertIn("otel_type = ?", sql)
        self.assertIn("last_seen = ?", sql)
        
        # Check param order includes all expected parameters
        self.assertIn("display_name", param_order)
        self.assertIn("unit", param_order)
        self.assertIn("otel_type", param_order)
        self.assertIn("last_seen", param_order)
        self.assertIn("id", param_order)  # For WHERE clause
    
    def test_build_metrics_query_update_without_otel(self):
        """Test _build_metrics_query for update without otel_type."""
        store = MetadataStore(self.db_path)
        sql, param_order = store._build_metrics_query('update', False)
        
        # Check that SQL contains expected SET clauses but not otel_type
        self.assertIn("display_name = ?", sql)
        self.assertIn("unit = ?", sql)
        self.assertNotIn("otel_type = ?", sql)
        self.assertIn("last_seen = ?", sql)
        
        # Check param order includes expected parameters but not otel_type
        self.assertIn("display_name", param_order)
        self.assertIn("unit", param_order)
        self.assertNotIn("otel_type", param_order)
        self.assertIn("last_seen", param_order)
        self.assertIn("id", param_order)  # For WHERE clause
    
    def test_get_or_create_metric_with_otel_type(self):
        """Test _build_metrics_query includes otel_type for insert and update."""
        # Create a store with a mocked metrics_columns that includes otel_type
        with patch.object(MetadataStore, '_init_db'), \
             patch.object(MetadataStore, '_cache_metrics_schema'):
            store = MetadataStore(self.db_path)
            
        # Set up the metrics_columns to include otel_type (v2.0 schema)
        store.metrics_columns = {
            'id', 'service_id', 'name', 'display_name', 'unit', 
            'format_type', 'decimal_places', 'is_percentage', 
            'is_counter', 'first_seen', 'last_seen', 'otel_type'
        }
        
        # Test build_metrics_query directly for insert with otel_type
        insert_sql, insert_params = store._build_metrics_query('insert', True)
        self.assertIn('otel_type', insert_sql)
        self.assertIn('otel_type', insert_params)
        
        # Test build_metrics_query directly for update with otel_type
        update_sql, update_params = store._build_metrics_query('update', True)
        self.assertIn('otel_type = ?', update_sql)
        self.assertIn('otel_type', update_params)
    
    def test_get_or_create_metric_without_otel_type(self):
        """Test _build_metrics_query excludes otel_type for insert and update."""
        # Create a store with a mocked metrics_columns that does not include otel_type
        with patch.object(MetadataStore, '_init_db'), \
             patch.object(MetadataStore, '_cache_metrics_schema'):
            store = MetadataStore(self.db_path)
            
        # Set up the metrics_columns to exclude otel_type (v1.0 schema)
        store.metrics_columns = {
            'id', 'service_id', 'name', 'display_name', 'unit', 
            'format_type', 'decimal_places', 'is_percentage', 
            'is_counter', 'first_seen', 'last_seen'
        }
        
        # Test build_metrics_query directly for insert without otel_type
        insert_sql, insert_params = store._build_metrics_query('insert', False)
        self.assertNotIn('otel_type', insert_sql)
        self.assertNotIn('otel_type', insert_params)
        
        # Test build_metrics_query directly for update without otel_type
        update_sql, update_params = store._build_metrics_query('update', False)
        self.assertNotIn('otel_type = ?', update_sql)
        self.assertNotIn('otel_type', update_params)

if __name__ == '__main__':
    unittest.main()
