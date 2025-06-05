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

logger = logging.getLogger(__name__)

class MetadataStore:
    """
    SQLite-based metadata storage for OpenTelemetry metrics and services.
    
    This class provides persistent storage of service and metric identifiers,
    ensuring consistent telemetry data across restarts and maintaining proper
    formatting of metric names and values.
    """
    
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
            os.makedirs(db_dir, exist_ok=True)
            db_path = os.path.join(db_dir, "metadata.db")
            
        self.db_path = db_path
        logger.info(f"Using metadata database at: {self.db_path}")
        
        # Initialize the database schema
        self._init_db()
        
    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create services table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS services (
                id TEXT PRIMARY KEY,
                full_name TEXT UNIQUE,
                display_name TEXT,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP
            )
            """)
            
            # Create metrics table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id TEXT PRIMARY KEY,
                service_id TEXT,
                name TEXT,
                display_name TEXT,
                unit TEXT,
                format_type TEXT,
                decimal_places INTEGER DEFAULT 2,
                is_percentage BOOLEAN DEFAULT 0,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                FOREIGN KEY (service_id) REFERENCES services(id),
                UNIQUE(service_id, name)
            )
            """)
            
            # Create format rules table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS format_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT UNIQUE,
                replacement TEXT,
                rule_type TEXT,
                priority INTEGER
            )
            """)
            
            # Add default format rules if they don't exist
            default_rules = [
                ("cpu", "CPU", "word_replacement", 100),
                ("_", " ", "character_replacement", 50),
                ("word_start", "capitalize", "word_formatting", 10)
            ]
            
            for pattern, replacement, rule_type, priority in default_rules:
                cursor.execute("""
                INSERT OR IGNORE INTO format_rules
                (pattern, replacement, rule_type, priority)
                VALUES (?, ?, ?, ?)
                """, (pattern, replacement, rule_type, priority))
            
            conn.commit()
            conn.close()
            logger.debug("Database schema initialized successfully")
            
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
            
    def get_or_create_service(self, full_name: str) -> Tuple[str, str]:
        """
        Get existing service ID or create a new one if it doesn't exist.
        
        Args:
            full_name: Full service name (e.g., com.instana.plugin.python.microstrategy_m8mulprc)
            
        Returns:
            Tuple of (service_id, display_name)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract display name from full name (part after python)
            display_name = self._extract_service_display_name(full_name)
            
            # Check if service exists
            cursor.execute(
                "SELECT id, display_name FROM services WHERE full_name = ?",
                (full_name,)
            )
            result = cursor.fetchone()
            
            now = datetime.now().isoformat()
            
            if result:
                # Service exists, update last_seen
                service_id, existing_display_name = result
                
                # Update display name if it has changed
                if existing_display_name != display_name:
                    cursor.execute(
                        "UPDATE services SET display_name = ?, last_seen = ? WHERE id = ?",
                        (display_name, now, service_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE services SET last_seen = ? WHERE id = ?",
                        (now, service_id)
                    )
                
                conn.commit()
                logger.debug(f"Using existing service: {full_name} (ID: {service_id})")
                
            else:
                # Service doesn't exist, create new
                service_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO services 
                    (id, full_name, display_name, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (service_id, full_name, display_name, now, now)
                )
                conn.commit()
                logger.info(f"Created new service: {full_name} (ID: {service_id})")
                
            conn.close()
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
        is_percentage: bool = False
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
            
        Returns:
            Tuple of (metric_id, display_name)
        """
        try:
            conn = sqlite3.connect(self.db_path)
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
            
            if result:
                # Metric exists, update last_seen
                metric_id, existing_display_name = result
                
                # Update display name if it has changed
                if existing_display_name != display_name:
                    cursor.execute(
                        """
                        UPDATE metrics 
                        SET display_name = ?, unit = ?, format_type = ?, 
                            decimal_places = ?, is_percentage = ?, last_seen = ? 
                        WHERE id = ?
                        """,
                        (display_name, unit, format_type, decimal_places, 
                         is_percentage, now, metric_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE metrics SET last_seen = ? WHERE id = ?",
                        (now, metric_id)
                    )
                
                conn.commit()
                logger.debug(f"Using existing metric: {name} (ID: {metric_id})")
                
            else:
                # Metric doesn't exist, create new
                metric_id = str(uuid.uuid4())
                cursor.execute(
                    """
                    INSERT INTO metrics 
                    (id, service_id, name, display_name, unit, format_type, 
                     decimal_places, is_percentage, first_seen, last_seen)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (metric_id, service_id, name, display_name, unit, format_type,
                     decimal_places, is_percentage, now, now)
                )
                conn.commit()
                logger.info(f"Created new metric: {name} (ID: {metric_id})")
                
            conn.close()
            return metric_id, display_name
            
        except sqlite3.Error as e:
            logger.error(f"Error in get_or_create_metric: {e}")
            # Fall back to generating an ID without persistence
            metric_id = str(uuid.uuid4())
            display_name = self._format_metric_name(name)
            return metric_id, display_name
            
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
            conn = sqlite3.connect(self.db_path)
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
            
            conn.close()
            
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT pattern, replacement, rule_type, priority
                FROM format_rules
                ORDER BY priority DESC
                """
            )
            results = cursor.fetchall()
            
            conn.close()
            
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
        
    def format_metric_value(
        self, 
        value: float, 
        is_percentage: bool = False,
        decimal_places: int = 2
    ) -> float:
        """
        Format a metric value according to the formatting rules.
        
        Args:
            value: Raw metric value
            is_percentage: Whether this metric should be displayed as a percentage
            decimal_places: Number of decimal places for rounding
            
        Returns:
            Formatted value
        """
        # Convert to percentage if required
        if is_percentage and value <= 1.0:
            value = value * 100.0
            
        # Round to specified decimal places
        return round(value, decimal_places)
