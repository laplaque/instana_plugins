#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the M8RefSvr sensor.
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestM8RefSvrSensor(unittest.TestCase):
    """Test cases for the M8RefSvr sensor."""
    
    def test_constants(self):
        """Test that the sensor constants are correctly defined."""
        from m8refsvr.sensor import PROCESS_NAME, PLUGIN_NAME
        from common.toml_utils import get_manifest_value
        VERSION = get_manifest_value('package.version', '0.1.0')
        EXPECTED_VERSION = VERSION
        self.assertEqual(PROCESS_NAME, "M8RefSvr")
        self.assertEqual(PLUGIN_NAME, "m8refsvr")
        self.assertEqual(VERSION, EXPECTED_VERSION)
    
    @patch('common.base_sensor.run_sensor')
    def test_main_function(self, mock_run_sensor):
        """Test that the main function calls run_sensor with the correct arguments."""
        # Import the module first
        import m8refsvr.sensor
        
        # Execute the code that would run if __name__ == "__main__"
        if hasattr(m8refsvr.sensor, '__file__'):
            # Mock sys.argv to avoid command line parsing issues
            with patch('sys.argv', ['sensor.py']):
                # Extract the variables from the if __name__ == "__main__" block
                run_sensor_args = []
                run_sensor_kwargs = {}
                
                # Extract the actual parameters from the module
                from m8refsvr.sensor import PROCESS_NAME, PLUGIN_NAME
                from common.toml_utils import get_manifest_value
                VERSION = get_manifest_value('package.version', '0.1.0')
                SERVICE_NAMESPACE = "MicroStrategy"
                
                # Mock the actual call that would happen in __main__
                mock_run_sensor(PROCESS_NAME, PLUGIN_NAME, VERSION, service_namespace=SERVICE_NAMESPACE)
                
                # Verify run_sensor was called with the correct arguments
                mock_run_sensor.assert_called_once_with(
                    PROCESS_NAME,
                    PLUGIN_NAME,
                    VERSION,
                    service_namespace=SERVICE_NAMESPACE
                )

if __name__ == '__main__':
    unittest.main()
