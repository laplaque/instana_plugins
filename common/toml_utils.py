#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

TOML utilities for plugin configuration management.
Centralized TOML parsing with comprehensive error handling.
"""
import os
import sys
from typing import Tuple, Dict, Any, Optional

def load_toml_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Universal TOML file loader with proper error handling.
    
    Args:
        file_path: Path to TOML file
        
    Returns:
        Parsed TOML data or None if loading fails
    """
    if not os.path.exists(file_path):
        return None
        
    try:
        import tomllib
    except ImportError:
        # Python < 3.11 fallback
        try:
            import tomli as tomllib
        except ImportError:
            return None
    
    try:
        with open(file_path, 'rb') as f:
            return tomllib.load(f)
    except Exception as e:
        print(f"Warning: Failed to load TOML file {file_path}: {e}", file=sys.stderr)
        return None

def load_plugin_config(plugin_directory: str) -> Tuple[str, str, str, str]:
    """
    Load plugin configuration from plugin.toml or fallback to __init__.py
    
    Args:
        plugin_directory: Path to plugin directory
        
    Returns:
        tuple: (SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME, DESCRIPTION)
    """
    plugin_toml_path = os.path.join(plugin_directory, 'plugin.toml')
    
    # Try TOML configuration first
    config = load_toml_file(plugin_toml_path)
    if config:
        metadata = config.get('metadata', {})
        return (
            metadata.get('service_namespace', 'MicroStrategy'),
            metadata.get('process_name', 'Unknown'),
            metadata.get('plugin_name', 'unknown'),
            metadata.get('description', 'TOML-based plugin')
        )
    
    # Fallback to __init__.py using absolute import
    return _load_from_init_py(plugin_directory)

def _load_from_init_py(plugin_directory: str) -> Tuple[str, str, str, str]:
    """Fallback loader for __init__.py configuration."""
    try:
        init_path = os.path.join(plugin_directory, '__init__.py')
        
        if os.path.exists(init_path):
            import importlib.util
            
            # Create a unique module name to avoid conflicts
            module_name = f"plugin_init_{os.path.basename(plugin_directory)}"
            
            spec = importlib.util.spec_from_file_location(module_name, init_path)
            if spec and spec.loader:
                plugin_init = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin_init)
                
                # Extract configuration variables
                SERVICE_NAMESPACE = getattr(plugin_init, 'SERVICE_NAMESPACE', 'Unknown')
                PROCESS_NAME = getattr(plugin_init, 'PROCESS_NAME', 'Unknown')
                PLUGIN_NAME = getattr(plugin_init, 'PLUGIN_NAME', 'unknown')
                description = f"Legacy {PROCESS_NAME} monitoring"
                
                return (SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME, description)
            else:
                raise ImportError("Could not create module spec for __init__.py")
        else:
            raise FileNotFoundError("__init__.py not found in plugin directory")
            
    except Exception as e:
        print(f"Error: Could not load configuration from plugin.toml or __init__.py: {e}", file=sys.stderr)
        print(f"Plugin directory: {plugin_directory}", file=sys.stderr)
        _debug_plugin_directory(plugin_directory)
        sys.exit(1)

def _debug_plugin_directory(plugin_directory: str):
    """Debug helper to list available files."""
    plugin_toml_path = os.path.join(plugin_directory, 'plugin.toml')
    init_py_path = os.path.join(plugin_directory, '__init__.py')
    
    print(f"TOML file exists: {os.path.exists(plugin_toml_path)}", file=sys.stderr)
    print(f"__init__.py exists: {os.path.exists(init_py_path)}", file=sys.stderr)
    
    try:
        files = os.listdir(plugin_directory)
        print(f"Available files: {files}", file=sys.stderr)
    except Exception:
        pass

def get_manifest_value(key_path: str, default_value: Any = None) -> Any:
    """
    Get any value from common/manifest.toml using dot notation.
    
    Args:
        key_path: Dot-separated path to value (e.g., 'metadata.version')
        default_value: Value to return if not found
        
    Returns:
        Value from manifest or default_value
    """
    current_dir = os.path.dirname(__file__)
    manifest_path = os.path.join(current_dir, 'manifest.toml')
    
    manifest = load_toml_file(manifest_path)
    if not manifest:
        return default_value
    
    # Navigate nested dictionary using dot notation
    keys = key_path.split('.')
    value = manifest
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default_value

def get_manifest_metadata() -> Dict[str, Any]:
    """Get complete metadata section from manifest.toml."""
    return get_manifest_value('metadata', {
        'version': '0.0.20',
        'metadata_schema_version': '1.0',
        'framework_name': 'OpenTelemetry Process Monitor',
        'python_version_min': '3.6',
        'maintainer': 'laplaque/instana_plugins Contributors'
    })
