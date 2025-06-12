"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.

Version and configuration management module.
Provides centralized access to version information from manifest.toml
"""

import os

def get_version():
    """
    Load version information from common/manifest.toml
    
    Returns:
        str: Version string
    """
    try:
        # Try to import TOML library
        try:
            import tomllib
        except ImportError:
            # Python < 3.11 fallback
            try:
                import tomli as tomllib
            except ImportError:
                return "0.0.20"  # Fallback version
        
        # Find manifest.toml in current directory
        current_dir = os.path.dirname(__file__)
        manifest_path = os.path.join(current_dir, 'manifest.toml')
        
        if os.path.exists(manifest_path):
            with open(manifest_path, 'rb') as f:
                manifest = tomllib.load(f)
            
            version = manifest.get('metadata', {}).get('version', '0.0.20')
            return version
        else:
            return "0.0.20"  # Fallback if manifest not found
            
    except Exception:
        return "0.0.20"  # Fallback on any error

def get_metadata_schema_version():
    """
    Load metadata schema version from common/manifest.toml
    
    Returns:
        str: Metadata schema version string
    """
    try:
        # Try to import TOML library
        try:
            import tomllib
        except ImportError:
            # Python < 3.11 fallback
            try:
                import tomli as tomllib
            except ImportError:
                return "1.0"  # Fallback version
        
        # Find manifest.toml in current directory
        current_dir = os.path.dirname(__file__)
        manifest_path = os.path.join(current_dir, 'manifest.toml')
        
        if os.path.exists(manifest_path):
            with open(manifest_path, 'rb') as f:
                manifest = tomllib.load(f)
            
            schema_version = manifest.get('metadata', {}).get('metadata_schema_version', '1.0')
            return schema_version
        else:
            return "1.0"  # Fallback if manifest not found
            
    except Exception:
        return "1.0"  # Fallback on any error

def get_framework_metadata():
    """
    Load complete framework metadata from common/manifest.toml
    
    Returns:
        dict: Dictionary containing all metadata fields
    """
    try:
        # Try to import TOML library
        try:
            import tomllib
        except ImportError:
            # Python < 3.11 fallback
            try:
                import tomli as tomllib
            except ImportError:
                return {
                    'version': '0.0.20',
                    'metadata_schema_version': '1.0',
                    'framework_name': 'OpenTelemetry Process Monitor',
                    'python_version_min': '3.6',
                    'maintainer': 'laplaque/instana_plugins Contributors'
                }
        
        # Find manifest.toml in current directory
        current_dir = os.path.dirname(__file__)
        manifest_path = os.path.join(current_dir, 'manifest.toml')
        
        if os.path.exists(manifest_path):
            with open(manifest_path, 'rb') as f:
                manifest = tomllib.load(f)
            
            return manifest.get('metadata', {})
        else:
            return {
                'version': '0.0.20',
                'metadata_schema_version': '1.0',
                'framework_name': 'OpenTelemetry Process Monitor',
                'python_version_min': '3.6',
                'maintainer': 'laplaque/instana_plugins Contributors'
            }
            
    except Exception:
        return {
            'version': '0.0.20',
            'metadata_schema_version': '1.0',
            'framework_name': 'OpenTelemetry Process Monitor',
            'python_version_min': '3.6',
            'maintainer': 'laplaque/instana_plugins Contributors'
        }
