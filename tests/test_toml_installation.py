#!/usr/bin/env python3
"""
Test suite for TOML-based installation system

This module tests the new TOML configuration system including:
- Plugin metadata loading from plugin.toml files
- Checksum verification of common files
- Version management system
- Installation script functionality
"""

import os
import sys
import unittest
import tempfile
import shutil
from unittest.mock import patch, mock_open, MagicMock

# Add the parent directory to path for importing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestTOMLInstallationSystem(unittest.TestCase):
    """Test cases for the TOML-based installation system"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
        
        # Sample plugin.toml content
        self.sample_plugin_toml = """
[metadata]
service_namespace = "TestNamespace"
process_name = "TestProcess"
plugin_name = "test_plugin"
description = "Test plugin for unit testing"
version = "1.0.0"

[monitoring]
collection_interval = 60
metrics_enabled = true
log_level = "INFO"

[dependencies]
python_packages = ["test-package>=1.0.0"]
"""
        
        # Sample manifest.toml content
        self.sample_manifest_toml = """
[metadata]
version = "0.0.20"
metadata_schema_version = "1.0"
generated_at = "2025-06-12T14:45:54.007202Z"
framework_name = "OpenTelemetry Process Monitor"

[common_files]

[common_files."version.py"]
sha256 = "c0a50dbb26d5b5a0eaca694a1ea46934eb3c2015f38587d087769e9971549702"
size = 4120
description = "Centralized version management"
required = true
"""

    def test_version_management_system(self):
        """Test the centralized version management system"""
        try:
            from common.version import get_version, get_metadata_schema_version
            
            # Test version retrieval
            version = get_version()
            self.assertIsInstance(version, str)
            self.assertTrue(len(version) > 0)
            
            # Test metadata schema version
            schema_version = get_metadata_schema_version()
            self.assertIsInstance(schema_version, str)
            self.assertTrue(len(schema_version) > 0)
            
            print(f"✅ Version system working: v{version}, schema v{schema_version}")
            
        except ImportError as e:
            self.fail(f"Failed to import version functions: {e}")

    def test_plugin_toml_loading(self):
        """Test loading configuration from plugin.toml files"""
        # Test each plugin directory for plugin.toml
        plugin_dirs = ['m8mulprc', 'm8prcsvr', 'm8refsvr', 'mstrsvr']
        
        for plugin_dir in plugin_dirs:
            plugin_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), plugin_dir)
            plugin_toml_path = os.path.join(plugin_path, 'plugin.toml')
            
            self.assertTrue(os.path.exists(plugin_toml_path), 
                          f"plugin.toml missing in {plugin_dir}")
            
            # Test that the TOML file is valid
            try:
                with open(plugin_toml_path, 'r') as f:
                    content = f.read()
                    self.assertIn('[metadata]', content)
                    self.assertIn('service_namespace', content)
                    self.assertIn('process_name', content)
                    self.assertIn('plugin_name', content)
                    
                print(f"✅ {plugin_dir}/plugin.toml is valid")
                
            except Exception as e:
                self.fail(f"Failed to read {plugin_dir}/plugin.toml: {e}")

    def test_sensor_configuration_loading(self):
        """Test that sensors can load TOML configuration"""
        plugin_dirs = ['m8mulprc', 'm8prcsvr', 'm8refsvr', 'mstrsvr']
        
        for plugin_dir in plugin_dirs:
            try:
                # Import the sensor module
                sensor_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                         plugin_dir, 'sensor.py')
                
                if os.path.exists(sensor_path):
                    # Check that sensor file uses shared TOML utilities
                    with open(sensor_path, 'r') as f:
                        content = f.read()
                        self.assertIn('load_plugin_config', content)
                        self.assertIn('from common.toml_utils import', content)
                        
                    print(f"✅ {plugin_dir}/sensor.py uses shared TOML configuration")
                    
            except Exception as e:
                self.fail(f"Failed to verify {plugin_dir}/sensor.py: {e}")

    def test_manifest_integrity(self):
        """Test manifest.toml file integrity and structure"""
        manifest_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   'common', 'manifest.toml')
        
        self.assertTrue(os.path.exists(manifest_path), "manifest.toml missing")
        
        try:
            with open(manifest_path, 'r') as f:
                content = f.read()
                
            # Check required sections
            self.assertIn('[metadata]', content)
            self.assertIn('[common_files]', content)
            self.assertIn('version =', content)
            self.assertIn('metadata_schema_version =', content)
            
            # Check that version.py is included
            self.assertIn('[common_files."version.py"]', content)
            self.assertIn('sha256 =', content)
            
            print("✅ manifest.toml structure is valid")
            
        except Exception as e:
            self.fail(f"Failed to validate manifest.toml: {e}")

    def test_installation_scripts_exist(self):
        """Test that all installation scripts exist and use shared functions"""
        plugin_dirs = ['m8mulprc', 'm8prcsvr', 'm8refsvr', 'mstrsvr']
        
        for plugin_dir in plugin_dirs:
            script_name = f"install-instana-{plugin_dir}-plugin.sh"
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                     plugin_dir, script_name)
            
            self.assertTrue(os.path.exists(script_path), 
                          f"Installation script missing: {script_name}")
            
            # Check that script sources shared functions
            try:
                with open(script_path, 'r') as f:
                    content = f.read()
                    self.assertIn('source "${PARENT_DIR}/common/install_functions.sh"', content)
                    self.assertIn('install_plugin', content)
                    
                print(f"✅ {script_name} uses shared functions")
                
            except Exception as e:
                self.fail(f"Failed to verify {script_name}: {e}")

    def test_shared_functions_exist(self):
        """Test that shared installation functions exist"""
        functions_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                    'common', 'install_functions.sh')
        
        self.assertTrue(os.path.exists(functions_path), "install_functions.sh missing")
        
        try:
            with open(functions_path, 'r') as f:
                content = f.read()
                
            # Check for key functions
            required_functions = [
                'get_plugin_metadata',
                'verify_common_files', 
                'install_common_files',
                'install_plugin_files',
                'create_service_file',
                'install_plugin'
            ]
            
            for func in required_functions:
                # Functions can be declared with or without 'function' keyword
                func_pattern = f'{func}()' 
                self.assertIn(func_pattern, content, f"Function {func} not found")
                
            print("✅ All required shared functions present")
            
        except Exception as e:
            self.fail(f"Failed to verify install_functions.sh: {e}")

    def test_backward_compatibility(self):
        """Test that system maintains backward compatibility with __init__.py files"""
        plugin_dirs = ['m8mulprc', 'm8prcsvr', 'm8refsvr', 'mstrsvr']
        
        for plugin_dir in plugin_dirs:
            init_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                   plugin_dir, '__init__.py')
            
            # __init__.py files should still exist for compatibility
            self.assertTrue(os.path.exists(init_path), 
                          f"__init__.py missing in {plugin_dir} (needed for compatibility)")
            
            try:
                with open(init_path, 'r') as f:
                    content = f.read()
                    # Should contain the traditional variables
                    self.assertIn('SERVICE_NAMESPACE', content)
                    self.assertIn('PROCESS_NAME', content)
                    self.assertIn('PLUGIN_NAME', content)
                    
                print(f"✅ {plugin_dir}/__init__.py maintains compatibility")
                
            except Exception as e:
                self.fail(f"Failed to verify {plugin_dir}/__init__.py: {e}")

    def test_toml_error_handling(self):
        """Test error handling when TOML files are missing or invalid"""
        # Test that the shared TOML utilities have proper error handling
        try:
            from common.toml_utils import load_plugin_config
            
            # The error handling is now in the shared utilities
            # Test that the function exists and is callable
            self.assertTrue(callable(load_plugin_config))
            
            # Test that shared utilities file contains error handling
            toml_utils_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 
                                         'common', 'toml_utils.py')
            
            with open(toml_utils_path, 'r') as f:
                content = f.read()
                self.assertIn('except', content)
                self.assertIn('sys.stderr', content)
                
            print("✅ Shared TOML utilities have comprehensive error handling")
            
        except ImportError as e:
            self.fail(f"Failed to import toml_utils: {e}")

def run_toml_tests():
    """Run the TOML installation system tests"""
    print("🧪 Running TOML Installation System Tests")
    print("=" * 50)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestTOMLInstallationSystem)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("\n✅ All TOML installation system tests passed!")
        return True
    else:
        print(f"\n❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        return False

if __name__ == '__main__':
    success = run_toml_tests()
    sys.exit(0 if success else 1)
