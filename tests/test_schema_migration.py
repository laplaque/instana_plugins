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
from common import METADATA_SCHEMA_VERSION


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
        
        # Verify all required tables exist
        conn = sqlite3.connect(self.db_path)
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
        conn.close()

    def test_legacy_database_migration(self):
        """Test migration from legacy database without schema version."""
        # Create a legacy database manually
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create some legacy tables and data
        cursor.execute("CREATE TABLE old_services (id INTEGER, name TEXT)")
        cursor.execute("CREATE TABLE old_metrics (id INTEGER, metric_name TEXT)")
        cursor.execute("INSERT INTO old_services VALUES (1, 'legacy_service')")
        cursor.execute("INSERT INTO old_metrics VALUES (1, 'legacy_metric')")
        
        conn.commit()
        conn.close()
        
        # Initialize MetadataStore (should trigger migration)
        store = MetadataStore(self.db_path)
        
        # Verify migration completed
        current_version = store._get_current_schema_version()
        self.assertEqual(current_version, "1.0")
        
        # Verify legacy data is removed and new schema is in place
        conn = sqlite3.connect(self.db_path)
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
        
        conn.close()

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
        self.assertEqual(service_info['full_name'], "com.instana.plugin.python.test")
        
        metric_info = store2.get_metric_info(service_id, "test_metric")
        self.assertIsNotNone(metric_info)
        self.assertEqual(metric_info['id'], metric_id)

    def test_schema_version_operations(self):
        """Test schema version getting and setting operations."""
        store = MetadataStore(self.db_path)
        
        # Test getting current version
        version = store._get_current_schema_version()
        self.assertEqual(version, "1.0")
        
        # Test setting a new version
        store._set_schema_version("1.1")
        new_version = store._get_current_schema_version()
        self.assertEqual(new_version, "1.1")
        
        # Verify version history is tracked
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM schema_version")
        count = cursor.fetchone()[0]
        self.assertEqual(count, 2)  # Initial 1.0 + new 1.1
        conn.close()

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


if __name__ == '__main__':
    unittest.main()
