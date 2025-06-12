#!/usr/bin/env python3
"""
M8PrcSvr Sensor

This module monitors the MicroStrategy M8PrcSvr process and reports metrics to Instana.
"""

import sys
import os

# Add the parent directory to the path so we can import common modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from common.base_sensor import run_sensor
from common.version import get_version

def load_plugin_config():
    """
    Load plugin configuration from plugin.toml or fallback to __init__.py
    
    Returns:
        tuple: (SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME, DESCRIPTION)
    """
    current_dir = os.path.dirname(__file__)
    plugin_toml_path = os.path.join(current_dir, 'plugin.toml')
    
    # Try TOML configuration first
    if os.path.exists(plugin_toml_path):
        try:
            import tomllib
        except ImportError:
            # Python < 3.11 fallback
            try:
                import tomli as tomllib
            except ImportError:
                # If no TOML library available, fall back to __init__.py
                pass
            else:
                try:
                    with open(plugin_toml_path, 'rb') as f:
                        config = tomllib.load(f)
                    
                    metadata = config.get('metadata', {})
                    return (
                        metadata.get('service_namespace', 'MicroStrategy'),
                        metadata.get('process_name', 'Unknown'),
                        metadata.get('plugin_name', 'unknown'),
                        metadata.get('description', 'TOML-based plugin')
                    )
                except Exception as e:
                    print(f"Warning: Failed to load plugin.toml: {e}", file=sys.stderr)
        else:
            try:
                with open(plugin_toml_path, 'rb') as f:
                    config = tomllib.load(f)
                
                metadata = config.get('metadata', {})
                return (
                    metadata.get('service_namespace', 'MicroStrategy'),
                    metadata.get('process_name', 'Unknown'),
                    metadata.get('plugin_name', 'unknown'),
                    metadata.get('description', 'TOML-based plugin')
                )
            except Exception as e:
                print(f"Warning: Failed to load plugin.toml: {e}", file=sys.stderr)
    
    # Fallback to __init__.py using absolute import
    try:
        init_path = os.path.join(current_dir, '__init__.py')
        
        if os.path.exists(init_path):
            import importlib.util
            
            # Create a unique module name to avoid conflicts
            module_name = f"plugin_init_{os.path.basename(current_dir)}"
            
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
        print(f"Plugin directory: {current_dir}", file=sys.stderr)
        print(f"TOML file exists: {os.path.exists(plugin_toml_path)}", file=sys.stderr)
        print(f"__init__.py exists: {os.path.exists(os.path.join(current_dir, '__init__.py'))}", file=sys.stderr)
        
        # List available files for debugging
        try:
            files = os.listdir(current_dir)
            print(f"Available files: {files}", file=sys.stderr)
        except Exception:
            pass
        
        sys.exit(1)

# Load configuration
SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME, DESCRIPTION = load_plugin_config()

if __name__ == "__main__":
    run_sensor(PROCESS_NAME, PLUGIN_NAME, get_version(), service_namespace=SERVICE_NAMESPACE)
