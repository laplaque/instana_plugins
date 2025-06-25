#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

Test schema migration functionality for MetadataStore.
"""

import unittest
import tempfile
import os
import sqlite3
from common.metadata_store import MetadataStore
from common.toml_utils import get_manifest_value

# Get schema version from manifest.toml
try:
    METADATA_SCHEMA_VERSION = get_manifest_value('metadata.metadata_schema_version', '1.0')
except ImportError:
    METADATA_SCHEMA_VERSION = "1.0"  # Fallback if import fails


class TestSchemaMigration(unittest.TestCase):
    """Test schema migration functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_migration.db")

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        os.rmdir(self.temp_dir)

    def test_new_database_creation(self):
        """Test creating a new database with current schema version."""
        # Create new database
        store = MetadataStore(self.db_path)
        
        # Verify schema version is set correctly
        current_version = store._get_current_schema_version()
        self.assertEqual(current_version, METADATA_SCHEMA_VERSION)
        
        # Verify all required tables exist using centralized connection manager
        with store._get_db_connection() as conn:
            cursor = conn.cursor()
            
            required_tables = {
                'schema_version', 'hosts', 'service_namespaces', 
                'services', 'metrics', 'format_rules'
            }
            
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            existing_tables = {row[0] for row in cursor.fetchall()}
            
            self.assertEqual(existing_tables, required_tables)

    def test_legacy_database_migration(self):
        """Test migration from legacy database without schema version."""
        # Create a legacy database manually
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create some legacy tables and data
            cursor.execute("CREATE TABLE old_services (id INTEGER, name TEXT)")
            cursor.execute("CREATE TABLE old_metrics (id INTEGER, metric_name TEXT)")
            cursor.execute("INSERT INTO old_services VALUES (1, 'legacy_service')")
            cursor.execute("INSERT INTO old_metrics VALUES (1, 'legacy_metric')")
            
            conn.commit()
        
        # Initialize MetadataStore (should trigger migration)
        store = MetadataStore(self.db_path)
        
        # Verify migration completed
        current_version = store._get_current_schema_version()
        self.assertEqual(current_version, "2.0")
        
        # Verify legacy data is removed and new schema is in place using centralized connection
        with store._get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check legacy tables are gone
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name IN ('old_services', 'old_metrics')
            """)
            legacy_tables = cursor.fetchall()
            self.assertEqual(len(legacy_tables), 0)
            
            # Check new tables exist
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='schema_version'
            """)
            self.assertIsNotNone(cursor.fetchone())

    def test_existing_current_schema(self):
        """Test that existing database with current schema is not migrated."""
        # Create database with current schema
        store1 = MetadataStore(self.db_path)
        
        # Add some test data
        service_id, _ = store1.get_or_create_service(
            "com.instana.plugin.python.test",
            version="1.0"
        )
        metric_id, _ = store1.get_or_create_metric(
            service_id,
            "test_metric"
        )
        
        # Initialize another instance (should not trigger migration)
        store2 = MetadataStore(self.db_path)
        
        # Verify data is preserved
        service_info = store2.get_service_info(service_id)
        self.assertIsNotNone(service_info)
        self.assertEqual(service_info['full_name'], "com_instana_plugin_python_test")
        
        metric_info = store2.get_metric_info(service_id, "test_metric")
        self.assertIsNotNone(metric_info)
        self.assertEqual(metric_info['id'], metric_id)

    def test_schema_version_operations(self):
        """Test schema version getting and setting operations."""
        store = MetadataStore(self.db_path)
        
        # Test getting current version
        version = store._get_current_schema_version()
        self.assertEqual(version, "2.0")
        
        # Test setting a new version
        store._set_schema_version("1.1")
        new_version = store._get_current_schema_version()
        self.assertEqual(new_version, "1.1")
        
        # Verify version history is tracked using centralized connection
        with store._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM schema_version")
            count = cursor.fetchone()[0]
            self.assertEqual(count, 2)  # Direct creation of 2.0 + new 1.1 set in this test

    def test_format_rules_initialization(self):
        """Test that default format rules are created during migration."""
        store = MetadataStore(self.db_path)
        
        format_rules = store.get_format_rules()
        self.assertGreater(len(format_rules), 0)
        
        # Check for specific default rules
        patterns = {rule['pattern'] for rule in format_rules}
        expected_patterns = {'cpu', '_', 'word_start'}
        self.assertTrue(expected_patterns.issubset(patterns))

    def test_migration_error_handling(self):
        """Test error handling during migration."""
        # Create an invalid database file
        with open(self.db_path, 'w') as f:
            f.write("invalid database content")
        
        # MetadataStore should handle this gracefully
        with self.assertRaises(Exception):
            MetadataStore(self.db_path)

    def test_centralized_connection_manager(self):
        """Test that the centralized connection manager works correctly."""
        store = MetadataStore(self.db_path)
        
        # Test that _get_db_connection returns a valid connection
        with store._get_db_connection() as conn:
            self.assertIsNotNone(conn)
            cursor = conn.cursor()
            
            # Test that we can execute queries
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            self.assertGreater(len(tables), 0)
            
        # Verify we can get multiple connections sequentially
        with store._get_db_connection() as conn1:
            with store._get_db_connection() as conn2:
                # Both connections should work independently
                cursor1 = conn1.cursor()
                cursor2 = conn2.cursor()
                cursor1.execute("SELECT 1")
                cursor2.execute("SELECT 2")
                self.assertEqual(cursor1.fetchone()[0], 1)
                self.assertEqual(cursor2.fetchone()[0], 2)
        
    def test_connection_manager_exception_safety(self):
        """Test that connections are properly cleaned up even when exceptions occur."""
        store = MetadataStore(self.db_path)
        
        # Test exception handling in connection manager
        try:
            with store._get_db_connection() as conn:
                cursor = conn.cursor()
                # Execute a valid query first
                cursor.execute("SELECT 1")
                # Now execute an invalid query to trigger an exception
                cursor.execute("INVALID SQL SYNTAX")
        except sqlite3.Error:
            # Expected exception - connection should still be cleaned up properly
            pass
        
        # Verify we can still get new connections after an exception
        with store._get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)


if __name__ == '__main__':
    unittest.main()
