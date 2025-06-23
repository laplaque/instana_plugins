#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.
"""
from common.logging_config import setup_logging

setup_logging()  # Configure logging at the start of the module
import os
import sqlite3
import uuid
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

# Import schema version for migrations from manifest.toml
try:
    from common.toml_utils import get_manifest_value
    METADATA_SCHEMA_VERSION = get_manifest_value('metadata.metadata_schema_version', '1.0')
except ImportError:
    METADATA_SCHEMA_VERSION = "1.0"  # Fallback if import fails
    logger.error("TOML utilities not available. Metric definitions cannot be loaded. Please ensure common/toml_utils.py exists and get_expanded_metrics is available.")

logger = logging.getLogger(__name__)

class MetadataStore:
    """
    SQLite-based metadata storage for OpenTelemetry metrics and services.
    
    This class provides persistent storage of service and metric identifiers,
    ensuring consistent telemetry data across restarts and maintaining proper
    formatting of metric names and values.
    """
    
    def _build_metrics_query(self, operation_type, include_otel_type=True):
        """
        Build a parametrized SQL query for metrics table operations.
        
        Args:
            operation_type: Either 'insert' or 'update'
            include_otel_type: Whether to include otel_type column
            
        Returns:
            Tuple of (sql_query, param_order) where param_order is the list
            of parameter names in the order they should be provided
        """
        if operation_type == 'insert':
            columns = ["id", "service_id", "name", "display_name", "unit", 
                      "format_type", "decimal_places", "is_percentage", "is_counter"]
            placeholders = ["?"] * len(columns)
            param_order = ["id", "service_id", "name", "display_name", "unit", 
                          "format_type", "decimal_places", "is_percentage", "is_counter"]
            
            if include_otel_type:
                columns.append("otel_type")
                placeholders.append("?")
                param_order.append("otel_type")
                
            columns.extend(["first_seen", "last_seen"])
            placeholders.extend(["?", "?"])
            param_order.extend(["first_seen", "last_seen"])
            
            sql = f"""
            INSERT INTO metrics 
            ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            """
            
            return sql, param_order
        
        elif operation_type == 'update':
            set_clauses = ["display_name = ?", "unit = ?", "format_type = ?", 
                          "decimal_places = ?", "is_percentage = ?"]
            param_order = ["display_name", "unit", "format_type", 
                          "decimal_places", "is_percentage"]
            
            if include_otel_type:
                set_clauses.append("otel_type = ?")
                param_order.append("otel_type")
                
            set_clauses.append("last_seen = ?")
            param_order.append("last_seen")
            param_order.append("id")  # For WHERE clause
            
            sql = f"""
            UPDATE metrics 
            SET {', '.join(set_clauses)}
            WHERE id = ?
            """
            
            return sql, param_order
    
    def sanitize_for_metrics(self, input_string: str) -> str:
        """
        Convert any string to safe technical identifier using only [a-z0-9_].
        
        This function sanitizes service names and metric names to ensure they
        are compatible with OpenTelemetry, databases, and monitoring systems.
        
        Args:
            input_string: Raw string that may contain special characters
            
        Returns:
            Sanitized string safe for technical use
        """
        if not input_string:
            return 'unknown'
            
        # 1. Convert to lowercase
        result = input_string.lower()
        
        # 2. Replace ANY non-alphanumeric character with underscore
        result = re.sub(r'[^a-z0-9]', '_', result)
        
        # 3. Collapse multiple underscores into single underscore
        result = re.sub(r'_+', '_', result)
        
        # 4. Remove leading/trailing underscores
        result = result.strip('_')
        
        # 5. Ensure it starts with a letter (prefix if needed)
        if result and result[0].isdigit():
            result = 'metric_' + result
        
        # 6. Handle empty result
        return result or 'unknown'
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the metadata store.
        
        Args:
            db_path: Path to the SQLite database file. If None, uses default location.
        """
        if db_path is None:
            # Create db in a .instana_plugins directory in the user's home
            home_dir = os.path.expanduser("~")
            db_dir = os.path.join(home_dir, ".instana_plugins")
            
            # Ensure the directory exists
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.debug(f"Ensuring metadata directory exists: {db_dir}")
            except OSError as e:
                logger.warning(f"Could not create metadata directory {db_dir}: {e}")
                # Fall back to a temporary directory if we can't create the intended one
                import tempfile
                db_dir = tempfile.gettempdir()
                logger.warning(f"Using temporary directory instead: {db_dir}")
                
            db_path = os.path.join(db_dir, "metadata.db")
            
        self.db_path = db_path
        logger.info(f"Using metadata database at: {self.db_path}")
        
        # Initialize schema cache
        self.metrics_columns = None
        
        # Initialize the database schema
        self._init_db()
        
        # Cache the metrics table schema after initialization
        self._cache_metrics_schema()
        
    def _init_db(self):
        """Initialize the database schema and run migrations if needed."""
        try:
            # Run schema migration first
            self._run_migrations()
            logger.debug("Database schema initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _get_db_connection(self):
        """
        Context manager for database connections.
        
        Provides consistent connection handling with automatic cleanup
        and proper exception handling.
        
        Returns:
            sqlite3.Connection: Database connection context manager
        """
        return sqlite3.connect(self.db_path)
    
    def _cache_metrics_schema(self):
        """
        Cache the metrics table schema to avoid repeated PRAGMA calls.
        This improves performance by eliminating database queries on every metric operation.
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get metrics table schema once and cache it
                cursor.execute("PRAGMA table_info(metrics)")
                columns = [column[1] for column in cursor.fetchall()]
                self.metrics_columns = set(columns)
                
            logger.debug(f"Cached metrics table schema: {len(self.metrics_columns)} columns")
            
        except sqlite3.Error as e:
            logger.error(f"Error caching metrics schema: {e}")
            # Fall back to None, which will trigger the old behavior
            self.metrics_columns = None
    
    def _get_current_schema_version(self) -> Optional[str]:
        """
        Get the current schema version from the database.
        
        Returns:
            Current schema version or None if no version table exists
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if schema_version table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='schema_version'
                """)
                
                if not cursor.fetchone():
                    return None
                    
                # Get current version
                cursor.execute("SELECT version FROM schema_version ORDER BY updated_date DESC LIMIT 1")
                result = cursor.fetchone()
                
                return result[0] if result else None
                
        except sqlite3.Error as e:
            logger.error(f"Error getting schema version: {e}")
            return None
    
    def _set_schema_version(self, version: str):
        """
        Set the current schema version in the database.
        
        Args:
            version: Schema version to set
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Create schema_version table if it doesn't exist
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version TEXT NOT NULL,
                        created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert new version record
                now = datetime.now().isoformat()
                cursor.execute("""
                    INSERT INTO schema_version (version, created_date, updated_date)
                    VALUES (?, ?, ?)
                """, (version, now, now))
                
                conn.commit()
                logger.info(f"Set schema version to: {version}")
                
        except sqlite3.Error as e:
            logger.error(f"Error setting schema version: {e}")
            raise
    
    def _migrate_to_version_1_0(self):
        """
        Migrate database to schema version 1.0.
        
        For version 1.0, we delete any existing legacy database and create fresh schema.
        """
        try:
            # Check if database file exists and has any tables
            database_exists = os.path.exists(self.db_path)
            has_legacy_data = False
            
            if database_exists:
                with self._get_db_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Check if any tables exist (indicating legacy data)
                    cursor.execute("""
                        SELECT name FROM sqlite_master 
                        WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    """)
                    tables = cursor.fetchall()
                    has_legacy_data = len(tables) > 0
            
            if has_legacy_data:
                logger.warning("Legacy metadata database detected. Previous metadata will be deleted and recreated for schema v1.0")
                
                # Delete the old database file
                os.remove(self.db_path)
                logger.info("Legacy metadata database deleted")
            
            # Create fresh database with v1.0 schema
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Create hosts table
                cursor.execute("""
                CREATE TABLE hosts (
                    id TEXT PRIMARY KEY,
                    hostname TEXT UNIQUE,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP
                )
                """)
                
                # Create service_namespaces table
                cursor.execute("""
                CREATE TABLE service_namespaces (
                    id TEXT PRIMARY KEY,
                    namespace TEXT UNIQUE,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP
                )
                """)
                
                # Create services table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id TEXT PRIMARY KEY,
                    full_name TEXT UNIQUE,
                    display_name TEXT,
                    version TEXT,
                    description TEXT,
                    host_id TEXT,
                    namespace_id TEXT,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP,
                    FOREIGN KEY (host_id) REFERENCES hosts(id),
                    FOREIGN KEY (namespace_id) REFERENCES service_namespaces(id)
                )
                """)
                
                # Create metrics table
                cursor.execute("""
                CREATE TABLE metrics (
                    id TEXT PRIMARY KEY,
                    service_id TEXT,
                    name TEXT,
                    display_name TEXT,
                    unit TEXT,
                    format_type TEXT,
                    decimal_places INTEGER DEFAULT 2,
                    is_percentage BOOLEAN DEFAULT 0,
                    is_counter BOOLEAN DEFAULT 0,
                    first_seen TIMESTAMP,
                    last_seen TIMESTAMP,
                    FOREIGN KEY (service_id) REFERENCES services(id),
                    UNIQUE(service_id, name)
                )
                """)
                
                # Create format rules table
                cursor.execute("""
                CREATE TABLE format_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT UNIQUE,
                    replacement TEXT,
                    rule_type TEXT,
                    priority INTEGER
                )
                """)
                
                # Add default format rules
                default_rules = [
                    ("cpu", "CPU", "word_replacement", 100),
                    ("_", " ", "character_replacement", 50),
                    ("word_start", "capitalize", "word_formatting", 10)
                ]
                
                for pattern, replacement, rule_type, priority in default_rules:
                    cursor.execute("""
                    INSERT INTO format_rules
                    (pattern, replacement, rule_type, priority)
                    VALUES (?, ?, ?, ?)
                    """, (pattern, replacement, rule_type, priority))
                
                conn.commit()
            
            # Set schema version
            self._set_schema_version("1.0")
            logger.info("Database migrated to schema version 1.0")
            
        except (sqlite3.Error, OSError) as e:
            logger.error(f"Error migrating to version 1.0: {e}")
            raise

    def _migrate_to_version_2_0(self):
        """
        Migrate database from version 1.0 to version 2.0.
        
        Adds otel_type column to metrics table with intelligent type inference.
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                logger.info("Migrating database from version 1.0 to 2.0...")
                
                # Check if otel_type column already exists
                cursor.execute("PRAGMA table_info(metrics)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'otel_type' not in columns:
                    # Add otel_type column with default value
                    cursor.execute("ALTER TABLE metrics ADD COLUMN otel_type TEXT DEFAULT 'Gauge'")
                    logger.info("Added otel_type column to metrics table")
                    
                    # Intelligent type inference for existing metrics
                    cursor.execute("SELECT id, name, is_counter FROM metrics")
                    metrics = cursor.fetchall()
                    
                    migration_stats = {'Gauge': 0, 'Counter': 0, 'UpDownCounter': 0}
                    
                    for metric_id, name, is_counter in metrics:
                        # Infer OpenTelemetry type based on metric characteristics
                        if is_counter:
                            if any(keyword in name.lower() for keyword in ['bytes', 'switches', 'read', 'write']):
                                otel_type = 'Counter'  # Monotonic counters
                            else:
                                otel_type = 'UpDownCounter'  # Can go up/down
                        else:
                            otel_type = 'Gauge'  # Instantaneous values
                        
                        # Update the metric with inferred type
                        cursor.execute("UPDATE metrics SET otel_type = ? WHERE id = ?", (otel_type, metric_id))
                        migration_stats[otel_type] += 1
                    
                    logger.info(f"Migration statistics: {migration_stats}")
                else:
                    logger.info("otel_type column already exists, skipping schema modification")
                
                conn.commit()
            
            # Set schema version
            self._set_schema_version("2.0")
            logger.info("Database migrated to schema version 2.0")
            
        except sqlite3.Error as e:
            logger.error(f"Error migrating to version 2.0: {e}")
            raise
    
    def _run_migrations(self):
        """
        Run database migrations to bring schema up to current version.
        """
        current_version = self._get_current_schema_version()
        target_version = METADATA_SCHEMA_VERSION
        
        logger.debug(f"Current schema version: {current_version}, Target: {target_version}")
        
        if current_version is None:
            # No version info - treat as legacy or new database
            if target_version == "2.0":
                # Create database with v1.0 first, then migrate to v2.0
                logger.info("No schema version found, creating v1.0 then migrating to v2.0")
                self._migrate_to_version_1_0()
                self._migrate_to_version_2_0()
            else:
                logger.info("No schema version found, migrating to version 1.0")
                self._migrate_to_version_1_0()
            
        elif current_version != target_version:
            # Handle specific migration paths
            if current_version == "1.0" and target_version == "2.0":
                logger.info(f"Migrating from version {current_version} to {target_version}")
                self._migrate_to_version_2_0()
            elif target_version == "1.0":
                logger.info(f"Migrating from version {current_version} to {target_version}")
                self._migrate_to_version_1_0()
            else:
                logger.warning(f"Unknown migration path from {current_version} to {target_version}")
                
        else:
            logger.debug(f"Schema is already at target version {target_version}")
            
    def get_or_create_host(self, hostname: str) -> str:
        """
        Get existing host ID or create a new one if it doesn't exist.
        
        Args:
            hostname: Hostname of the system
            
        Returns:
            Host UUID
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if host exists
                cursor.execute(
                    "SELECT id FROM hosts WHERE hostname = ?",
                    (hostname,)
                )
                result = cursor.fetchone()
                
                now = datetime.now().isoformat()
                
                if result:
                    # Host exists, update last_seen
                    host_id = result[0]
                    cursor.execute(
                        "UPDATE hosts SET last_seen = ? WHERE id = ?",
                        (now, host_id)
                    )
                    conn.commit()
                    logger.debug(f"Using existing host: {hostname} (ID: {host_id})")
                    
                else:
                    # Host doesn't exist, create new
                    host_id = str(uuid.uuid4())
                    cursor.execute(
                        """
                        INSERT INTO hosts 
                        (id, hostname, first_seen, last_seen)
                        VALUES (?, ?, ?, ?)
                        """,
                        (host_id, hostname, now, now)
                    )
                    conn.commit()
                    logger.info(f"Created new host: {hostname} (ID: {host_id})")
                    
                return host_id
            
        except sqlite3.Error as e:
            logger.error(f"Error in get_or_create_host: {e}")
            # Fall back to generating an ID without persistence
            return str(uuid.uuid4())
    
    def get_or_create_service_namespace(self, namespace: str) -> str:
        """
        Get existing service namespace ID or create a new one if it doesn't exist.
        
        Args:
            namespace: Service namespace (e.g., MicroStrategy)
            
        Returns:
            Service namespace UUID
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if namespace exists
                cursor.execute(
                    "SELECT id FROM service_namespaces WHERE namespace = ?",
                    (namespace,)
                )
                result = cursor.fetchone()
                
                now = datetime.now().isoformat()
                
                if result:
                    # Namespace exists, update last_seen
                    namespace_id = result[0]
                    cursor.execute(
                        "UPDATE service_namespaces SET last_seen = ? WHERE id = ?",
                        (now, namespace_id)
                    )
                    conn.commit()
                    logger.debug(f"Using existing namespace: {namespace} (ID: {namespace_id})")
                    
                else:
                    # Namespace doesn't exist, create new
                    namespace_id = str(uuid.uuid4())
                    cursor.execute(
                        """
                        INSERT INTO service_namespaces 
                        (id, namespace, first_seen, last_seen)
                        VALUES (?, ?, ?, ?)
                        """,
                        (namespace_id, namespace, now, now)
                    )
                    conn.commit()
                    logger.info(f"Created new namespace: {namespace} (ID: {namespace_id})")
                    
                return namespace_id
            
        except sqlite3.Error as e:
            logger.error(f"Error in get_or_create_service_namespace: {e}")
            # Fall back to generating an ID without persistence
            return str(uuid.uuid4())

    def get_or_create_service(self, full_name: str, version: str = "", description: str = "", hostname: str = "", service_namespace: str = "") -> Tuple[str, str]:
        """
        Get existing service ID or create a new one if it doesn't exist.
        
        Args:
            full_name: Raw service name that will be sanitized for storage
            version: Service version (optional)
            description: Service description (optional)
            hostname: Hostname where the service is running (optional)
            service_namespace: Service namespace for grouping (optional)
            
        Returns:
            Tuple of (service_id, display_name)
        """
        try:
            # Sanitize full name for technical storage
            sanitized_name = self.sanitize_for_metrics(full_name)
            
            # Extract display name from original full name for human readability
            display_name = self._extract_service_display_name(full_name)
            
            # Get or create host and namespace IDs if provided
            host_id = None
            if hostname:
                host_id = self.get_or_create_host(hostname)
                
            namespace_id = None
            if service_namespace:
                namespace_id = self.get_or_create_service_namespace(service_namespace)
            
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if service exists using sanitized name
                cursor.execute(
                    "SELECT id, display_name FROM services WHERE full_name = ?",
                    (sanitized_name,)
                )
                result = cursor.fetchone()
                
                now = datetime.now().isoformat()
                
                if result:
                    # Service exists, update last_seen
                    service_id, existing_display_name = result
                    
                    # Get existing version and description if new ones aren't provided
                    if not version or not description:
                        cursor.execute(
                            "SELECT version, description FROM services WHERE id = ?",
                            (service_id,)
                        )
                        existing_values = cursor.fetchone()
                        if existing_values:
                            existing_version, existing_description = existing_values
                            # Use existing values if new ones aren't provided
                            if not version:
                                version = existing_version
                            if not description:
                                description = existing_description
                    
                    # Update service information
                    cursor.execute(
                        """
                        UPDATE services 
                        SET display_name = ?, version = ?, description = ?, host_id = ?, namespace_id = ?, last_seen = ? 
                        WHERE id = ?
                        """,
                        (display_name, version, description, host_id, namespace_id, now, service_id)
                    )
                    
                    conn.commit()
                    logger.debug(f"Using existing service: {full_name} (ID: {service_id})")
                    
                else:
                    # Service doesn't exist, create new
                    service_id = str(uuid.uuid4())
                    cursor.execute(
                        """
                        INSERT INTO services 
                        (id, full_name, display_name, version, description, host_id, namespace_id, first_seen, last_seen)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (service_id, sanitized_name, display_name, version, description, host_id, namespace_id, now, now)
                    )
                    conn.commit()
                    logger.info(f"Created new service: {full_name} → {sanitized_name} (ID: {service_id})")
                    
                return service_id, display_name
            
        except sqlite3.Error as e:
            logger.error(f"Error in get_or_create_service: {e}")
            # Fall back to generating an ID without persistence
            service_id = str(uuid.uuid4())
            display_name = self._extract_service_display_name(full_name)
            return service_id, display_name
            
    def get_or_create_metric(
        self,
        service_id: str,
        name: str,
        unit: str = "",
        format_type: str = "number",
        decimal_places: int = 2,
        is_percentage: bool = False,
        is_counter: bool = False,
        otel_type: str = "Gauge"
    ) -> Tuple[str, str]:
        """
        Get existing metric ID or create a new one if it doesn't exist.
        
        Args:
            service_id: ID of the service this metric belongs to
            name: Metric name (e.g., cpu_usage)
            unit: Unit of measurement
            format_type: How to format the value (number, percentage, bytes, etc.)
            decimal_places: Number of decimal places for rounding
            is_percentage: Whether this metric should be displayed as a percentage
            is_counter: Whether this metric is a counter (integer)
            otel_type: OpenTelemetry metric type (Gauge, Counter, UpDownCounter)
            
        Returns:
            Tuple of (metric_id, display_name)
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Format display name
                display_name = self._format_metric_name(name)
                
                # Check if metric exists
                cursor.execute(
                    "SELECT id, display_name FROM metrics WHERE service_id = ? AND name = ?",
                    (service_id, name)
                )
                result = cursor.fetchone()
                
                now = datetime.now().isoformat()
                
                # Determine if otel_type should be included based on schema
                include_otel_type = self.metrics_columns and 'otel_type' in self.metrics_columns
                
                if result:
                    # Metric exists, update last_seen and other fields
                    metric_id, existing_display_name = result
                    
                    # Build the appropriate SQL update query
                    sql, param_order = self._build_metrics_query('update', include_otel_type)
                    
                    # Prepare parameters dictionary
                    params = {
                        'display_name': display_name,
                        'unit': unit,
                        'format_type': format_type,
                        'decimal_places': decimal_places,
                        'is_percentage': is_percentage,
                        'otel_type': otel_type,
                        'last_seen': now,
                        'id': metric_id
                    }
                    
                    # Extract parameters in the correct order
                    param_values = [params[param] for param in param_order]
                    
                    # Execute the query
                    cursor.execute(sql, param_values)
                    
                    # Log appropriate message based on schema
                    if not include_otel_type:
                        if self.metrics_columns is None:
                            logger.warning("Metrics schema cache is not available, falling back to legacy update pattern")
                        elif 'otel_type' not in self.metrics_columns:
                            logger.debug(f"Schema inconsistency detected: 'otel_type' column not found in cached schema. Available columns: {sorted(self.metrics_columns)}")
                    
                    conn.commit()
                    logger.debug(f"Using existing metric: {name} (ID: {metric_id})")
                    
                else:
                    # Metric doesn't exist, create new
                    metric_id = str(uuid.uuid4())
                    
                    # Build the appropriate SQL insert query
                    sql, param_order = self._build_metrics_query('insert', include_otel_type)
                    
                    # Prepare parameters dictionary
                    params = {
                        'id': metric_id,
                        'service_id': service_id,
                        'name': name,
                        'display_name': display_name,
                        'unit': unit,
                        'format_type': format_type,
                        'decimal_places': decimal_places,
                        'is_percentage': is_percentage,
                        'is_counter': is_counter,
                        'otel_type': otel_type,
                        'first_seen': now,
                        'last_seen': now
                    }
                    
                    # Extract parameters in the correct order
                    param_values = [params[param] for param in param_order]
                    
                    # Execute the query
                    cursor.execute(sql, param_values)
                    
                    # Log appropriate message based on schema
                    if not include_otel_type:
                        if self.metrics_columns is None:
                            logger.warning("Metrics schema cache is not available, falling back to legacy insert pattern")
                        elif 'otel_type' not in self.metrics_columns:
                            logger.debug(f"Schema inconsistency detected: 'otel_type' column not found in cached schema. Available columns: {sorted(self.metrics_columns)}")
                    
                    conn.commit()
                    logger.info(f"Created new metric: {name} (ID: {metric_id}, Type: {otel_type})")
                    
                return metric_id, display_name
            
        except sqlite3.Error as e:
            logger.error(f"Error in get_or_create_metric: {e}")
            # Fall back to generating an ID without persistence
            metric_id = str(uuid.uuid4())
            display_name = self._format_metric_name(name)
            return metric_id, display_name
            
    def get_service_info(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific service.
        
        Args:
            service_id: ID of the service
            
        Returns:
            Dictionary of service information or None if not found
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT id, full_name, display_name, version, description
                    FROM services
                    WHERE id = ?
                    """,
                    (service_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'full_name': result[1],
                        'display_name': result[2],
                        'version': result[3],
                        'description': result[4]
                    }
                return None
            
        except sqlite3.Error as e:
            logger.error(f"Error in get_service_info: {e}")
            return None
    
    def get_metrics_for_service(self, service_id: str) -> List[Dict[str, Any]]:
        """
        Get all metrics for a specific service.
        
        Args:
            service_id: ID of the service
            
        Returns:
            List of metric information dictionaries
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT id, name, display_name, unit, format_type, decimal_places, is_percentage
                    FROM metrics
                    WHERE service_id = ?
                    """,
                    (service_id,)
                )
                results = cursor.fetchall()
                
                return [
                    {
                        'id': row[0],
                        'name': row[1],
                        'display_name': row[2],
                        'unit': row[3],
                        'format_type': row[4],
                        'decimal_places': row[5],
                        'is_percentage': bool(row[6])
                    }
                    for row in results
                ]
            
        except sqlite3.Error as e:
            logger.error(f"Error in get_metrics_for_service: {e}")
            return []
    
    def get_metric_info(self, service_id: str, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific metric.
        
        Args:
            service_id: ID of the service this metric belongs to
            name: Metric name
            
        Returns:
            Dictionary of metric information or None if not found
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT id, display_name, unit, format_type, decimal_places, is_percentage
                    FROM metrics
                    WHERE service_id = ? AND name = ?
                    """,
                    (service_id, name)
                )
                result = cursor.fetchone()
                
                if result:
                    return {
                        'id': result[0],
                        'display_name': result[1],
                        'unit': result[2],
                        'format_type': result[3],
                        'decimal_places': result[4],
                        'is_percentage': bool(result[5])
                    }
                return None
            
        except sqlite3.Error as e:
            logger.error(f"Error in get_metric_info: {e}")
            return None
            
    def get_format_rules(self) -> List[Dict[str, Any]]:
        """
        Get all format rules ordered by priority.
        
        Returns:
            List of format rules as dictionaries
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute(
                    """
                    SELECT pattern, replacement, rule_type, priority
                    FROM format_rules
                    ORDER BY priority DESC
                    """
                )
                results = cursor.fetchall()
                
                return [
                    {
                        'pattern': row[0],
                        'replacement': row[1],
                        'rule_type': row[2],
                        'priority': row[3]
                    }
                    for row in results
                ]
            
        except sqlite3.Error as e:
            logger.error(f"Error in get_format_rules: {e}")
            # Return default rules if database access fails
            return [
                {
                    'pattern': 'cpu',
                    'replacement': 'CPU',
                    'rule_type': 'word_replacement',
                    'priority': 100
                },
                {
                    'pattern': '_',
                    'replacement': ' ',
                    'rule_type': 'character_replacement',
                    'priority': 50
                },
                {
                    'pattern': 'word_start',
                    'replacement': 'capitalize',
                    'rule_type': 'word_formatting',
                    'priority': 10
                }
            ]
            
    def _extract_service_display_name(self, full_name: str) -> str:
        """
        Extract the display name from the full service name.
        
        Args:
            full_name: Full service name (e.g., com.instana.plugin.python.microstrategy_m8mulprc)
            
        Returns:
            Display name (e.g., Microstrategy M8mulprc)
        """
        # Extract the part after "python."
        match = re.search(r'\.python\.(.+)$', full_name)
        if match:
            base_name = match.group(1)
        else:
            # Fallback if pattern doesn't match
            parts = full_name.split('.')
            base_name = parts[-1] if parts else full_name
            
        # Format the display name
        return self._format_metric_name(base_name)
        
    def _format_metric_name(self, name: str) -> str:
        """
        Format a metric name according to the formatting rules.
        
        Args:
            name: Raw metric name (e.g., cpu_usage)
            
        Returns:
            Formatted display name (e.g., CPU Usage)
        """
        # Special handling for CPU core metrics
        cpu_core_match = re.match(r'cpu_core_(\d+)', name)
        if cpu_core_match:
            return f"CPU {cpu_core_match.group(1)}"
            
        # Replace underscores with spaces
        display_name = name.replace('_', ' ')
        
        # Replace "cpu" with "CPU" (case insensitive)
        display_name = re.sub(r'\bcpu\b', 'CPU', display_name, flags=re.IGNORECASE)
        
        # Capitalize each word except for those already handled
        words = display_name.split()
        formatted_words = []
        for word in words:
            if word.upper() != 'CPU':  # Skip words that are already in special format
                word = word.capitalize()
            formatted_words.append(word)
            
        return ' '.join(formatted_words)
        
    def get_simple_metric_name(self, full_metric_name: str) -> str:
        """
        Extract a simple, OpenTelemetry-compliant name from a fully qualified metric name.
        
        This function handles various metric naming conventions and returns names that
        comply with OpenTelemetry requirements (ASCII, <=63 chars, no spaces).
        
        Args:
            full_metric_name: The fully qualified metric name
            
        Returns:
            The simple metric name for OpenTelemetry registration (not display)
        """
        if not full_metric_name:
            return "unknown"
            
        # First try splitting on '/'
        parts = full_metric_name.split('/')
        simple_name = parts[-1] if len(parts) > 1 else full_metric_name
        
        # If no '/' was found, try splitting on '.'
        if simple_name == full_metric_name and '.' in full_metric_name:
            parts = full_metric_name.split('.')
            simple_name = parts[-1]
        
        # Remove any {} suffixes (for parameterized metrics)
        simple_name = re.sub(r'\{.*\}$', '', simple_name)
        
        # Return the simple name without formatting for OpenTelemetry compliance
        # (formatting is handled separately for display purposes)
        return simple_name.strip()
    
    def sync_metric_from_toml(
        self,
        service_id: str,
        name: str,
        unit: str = "",
        otel_type: str = "Gauge",
        decimals: int = 2,
        is_percentage: bool = False,
        is_counter: bool = False,
        description: str = "",
        pattern_type: Optional[str] = None,
        pattern_source: Optional[str] = None,
        pattern_range: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Sync a metric definition from TOML to database.
        
        This method creates or updates a metric definition in the database
        based on TOML configuration parameters.
        
        Args:
            service_id: ID of the service this metric belongs to
            name: Metric name from TOML
            unit: Unit from TOML
            otel_type: OpenTelemetry metric type from TOML
            decimals: Number of decimal places from TOML
            is_percentage: Whether metric is a percentage from TOML
            is_counter: Whether metric is a counter from TOML
            description: Description from TOML
            pattern_type: Pattern type from TOML (e.g., "indexed")
            pattern_source: Pattern source from TOML (e.g., "cpu_count")
            pattern_range: Pattern range from TOML (e.g., "0-auto")
            
        Returns:
            Tuple of (metric_id, display_name)
        """
        # Use the existing get_or_create_metric method with TOML parameters
        return self.get_or_create_metric(
            service_id=service_id,
            name=name,
            unit=unit,
            format_type="counter" if is_counter else ("percentage" if is_percentage else "number"),
            decimal_places=decimals,
            is_percentage=is_percentage,
            is_counter=is_counter,
            otel_type=otel_type
        )
    
    def get_service_metrics(self, service_id: str) -> List[Dict[str, Any]]:
        """
        Get all metrics for a service from the database registry.
        
        Args:
            service_id: ID of the service
            
        Returns:
            List of metric dictionaries with all required fields
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Check if otel_type column exists
                include_otel_type = self.metrics_columns and 'otel_type' in self.metrics_columns
                
                if include_otel_type:
                    cursor.execute(
                        """
                        SELECT id, name, display_name, unit, format_type, 
                               decimal_places, is_percentage, is_counter, otel_type
                        FROM metrics
                        WHERE service_id = ?
                        """,
                        (service_id,)
                    )
                else:
                    cursor.execute(
                        """
                        SELECT id, name, display_name, unit, format_type, 
                               decimal_places, is_percentage, is_counter
                        FROM metrics
                        WHERE service_id = ?
                        """,
                        (service_id,)
                    )
                
                results = cursor.fetchall()
                
                metrics = []
                for row in results:
                    metric = {
                        'id': row[0],
                        'name': row[1], 
                        'display_name': row[2],
                        'unit': row[3],
                        'format_type': row[4],
                        'decimal_places': row[5],
                        'is_percentage': bool(row[6]),
                        'is_counter': bool(row[7]),
                        'otel_type': row[8] if include_otel_type and len(row) > 8 else 'Gauge',
                        'description': f"Metric for {row[1]}"  # Generate description if not stored
                    }
                    metrics.append(metric)
                
                logger.debug(f"Retrieved {len(metrics)} metrics for service {service_id}")
                return metrics
            
        except sqlite3.Error as e:
            logger.error(f"Error in get_service_metrics: {e}")
            return []
    
    def remove_obsolete_metrics(self, service_id: str, current_metric_names: set) -> int:
        """
        Remove metrics from database that are no longer in TOML configuration.
        
        Args:
            service_id: ID of the service
            current_metric_names: Set of metric names currently in TOML
            
        Returns:
            Number of metrics removed
        """
        try:
            with self._get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Get all metrics currently in database for this service
                cursor.execute(
                    "SELECT id, name FROM metrics WHERE service_id = ?",
                    (service_id,)
                )
                database_metrics = cursor.fetchall()
                
                # Find metrics to remove (in database but not in current TOML)
                metrics_to_remove = []
                for metric_id, metric_name in database_metrics:
                    if metric_name not in current_metric_names:
                        metrics_to_remove.append((metric_id, metric_name))
                
                # Remove obsolete metrics
                removed_count = 0
                for metric_id, metric_name in metrics_to_remove:
                    cursor.execute("DELETE FROM metrics WHERE id = ?", (metric_id,))
                    removed_count += 1
                    logger.info(f"Removed obsolete metric: {metric_name} (ID: {metric_id})")
                
                conn.commit()
                
                if removed_count > 0:
                    logger.info(f"Removed {removed_count} obsolete metrics for service {service_id}")
                
                return removed_count
            
        except sqlite3.Error as e:
            logger.error(f"Error in remove_obsolete_metrics: {e}")
            return 0

    def format_metric_value(
        self, 
        value: float, 
        is_percentage: bool = False,
        is_counter: bool = False,
        decimal_places: int = 2
    ) -> float:
        """
        Format a metric value according to the formatting rules.
        
        Args:
            value: Raw metric value
            is_percentage: Whether this metric should be displayed as a percentage
            is_counter: Whether this metric is a counter (integer)
            decimal_places: Number of decimal places for rounding
            
        Returns:
            Formatted value (as integer for counters, rounded float otherwise)
        """
        # Convert to percentage if required
        if is_percentage and value <= 1.0:
            value = value * 100.0
            
        # For counters, return as integer (rounded)
        if is_counter:
            return int(round(value))
            
        # Otherwise round to specified decimal places
        return round(value, decimal_places)
