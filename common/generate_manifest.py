#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.

Manifest Generator for Common Files
Generates TOML manifest with checksums and metadata for all common framework files.
"""

import hashlib
import os
import sys
from datetime import datetime

def get_file_checksum(filepath):
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        print(f"Error reading file {filepath}: {e}")
        return None

def get_file_size(filepath):
    """Get file size in bytes"""
    try:
        return os.path.getsize(filepath)
    except OSError:
        return 0

def get_file_description(filename):
    """Get human-readable description for common files"""
    descriptions = {
        "__init__.py": "Common package initialization and version information",
        "version.py": "Centralized version and metadata management from manifest.toml",
        "base_sensor.py": "Base sensor framework with daemon management and CLI interface", 
        "process_monitor.py": "Process monitoring and system metrics collection utilities",
        "otel_connector.py": "OpenTelemetry connector for metrics export to Instana",
        "metadata_store.py": "Metadata storage and database schema management",
        "logging_config.py": "Centralized logging configuration and setup utilities",
        "check_dependencies.py": "Python dependency verification and validation utility",
        "extract_version.sh": "Shell script for version extraction from Python modules"
    }
    return descriptions.get(filename, f"Common framework component: {filename}")

def generate_manifest():
    """Generate manifest.toml with current file checksums and metadata"""
    
    # Get version and metadata schema version from version.py
    try:
        # Import from version.py
        sys.path.insert(0, os.path.dirname(__file__))
        from version import get_version, get_metadata_schema_version
        VERSION = get_version()
        METADATA_SCHEMA_VERSION = get_metadata_schema_version()
    except (ImportError, AttributeError) as e:
        print(f"Warning: Could not import version functions ({e}), using defaults")
        VERSION = "0.0.20"
        METADATA_SCHEMA_VERSION = "1.0"
    
    # List of common files that should be included in installations
    common_files = [
        "__init__.py",
        "version.py",
        "base_sensor.py", 
        "process_monitor.py",
        "otel_connector.py", 
        "metadata_store.py",
        "logging_config.py",
        "check_dependencies.py",
        "extract_version.sh"
    ]
    
    # Start building TOML content
    toml_content = []
    
    # Metadata section
    toml_content.append("[metadata]")
    toml_content.append(f'version = "{VERSION}"')
    toml_content.append(f'metadata_schema_version = "{METADATA_SCHEMA_VERSION}"')
    toml_content.append(f'generated_at = "{datetime.utcnow().isoformat()}Z"')
    toml_content.append('framework_name = "OpenTelemetry Process Monitor"')
    toml_content.append('python_version_min = "3.6"')
    toml_content.append('maintainer = "laplaque/instana_plugins Contributors"')
    toml_content.append('')
    
    # Dependencies section  
    toml_content.append("[dependencies]")
    toml_content.append('python_packages = [')
    toml_content.append('    "opentelemetry-api>=1.15.0",')
    toml_content.append('    "opentelemetry-sdk>=1.15.0",')
    toml_content.append('    "opentelemetry-exporter-otlp>=1.15.0"')
    toml_content.append(']')
    toml_content.append('')
    
    # Installation section
    toml_content.append("[installation]")
    toml_content.append('creates_systemd_service = true')
    toml_content.append('requires_python_path = true')
    toml_content.append('base_directory_default = "/opt/instana_plugins"')
    toml_content.append('supports_user_install = true')
    toml_content.append('backup_modified_files = true')
    toml_content.append('')
    
    # Common files section
    toml_content.append("[common_files]")
    toml_content.append('')
    
    # Process each common file
    missing_files = []
    for filename in common_files:
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        if os.path.exists(filepath):
            checksum = get_file_checksum(filepath)
            size = get_file_size(filepath)
            description = get_file_description(filename)
            
            if checksum:
                toml_content.append(f'[common_files."{filename}"]')
                toml_content.append(f'sha256 = "{checksum}"')
                toml_content.append(f'size = {size}')
                toml_content.append(f'description = "{description}"')
                toml_content.append('required = true')
                toml_content.append('')
            else:
                missing_files.append(filename)
        else:
            missing_files.append(filename)
    
    # Write manifest file
    manifest_path = os.path.join(os.path.dirname(__file__), 'manifest.toml')
    
    try:
        with open(manifest_path, 'w') as f:
            f.write('\n'.join(toml_content))
        
        print(f"✅ Generated manifest.toml for version {VERSION}")
        print(f"📁 Location: {manifest_path}")
        print(f"📊 Processed {len(common_files) - len(missing_files)} files")
        
        if missing_files:
            print(f"⚠️  Missing files: {', '.join(missing_files)}")
        
    except IOError as e:
        print(f"❌ Error writing manifest file: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if generate_manifest():
        sys.exit(0)
    else:
        sys.exit(1)
