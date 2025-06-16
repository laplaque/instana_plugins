"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.

Version and configuration management module.
Provides centralized access to version information from manifest.toml
"""

from .toml_utils import get_manifest_value, get_manifest_metadata

def get_version():
    """
    Load version information from common/manifest.toml
    
    Returns:
        str: Version string
        
    Raises:
        RuntimeError: If version cannot be read from manifest.toml
    """
    version = get_manifest_value('metadata.version', None)
    if version is None:
        raise RuntimeError("Version not found in manifest.toml - manifest file may be incomplete or corrupted")
    return version

def get_metadata_schema_version():
    """
    Load metadata schema version from common/manifest.toml
    
    Returns:
        str: Metadata schema version string
    """
    return get_manifest_value('metadata.metadata_schema_version', '1.0')

def get_framework_metadata():
    """
    Load complete framework metadata from common/manifest.toml
    
    Returns:
        dict: Dictionary containing all metadata fields
    """
    return get_manifest_metadata()
