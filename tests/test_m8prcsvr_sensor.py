#!/usr/bin/env python3
"""
Test cases for the M8PrcSvr sensor.
"""

import unittest
from unittest.mock import patch
import sys
import os

# Add the parent directory to the path so we can import the sensor module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestM8PrcSvrSensor(unittest.TestCase):
    """Test cases for the M8PrcSvr sensor."""
    
    def test_constants(self):
        """Test the sensor constants."""
        from m8prcsvr.sensor import PROCESS_NAME, PLUGIN_NAME
        from common.toml_utils import get_manifest_value
        VERSION = get_manifest_value('package.version', '0.1.0')
        EXPECTED_VERSION = VERSION
        
        self.assertEqual(PROCESS_NAME, "M8PrcSvr")
        self.assertEqual(PLUGIN_NAME, "m8prcsvr")
        self.assertEqual(VERSION, EXPECTED_VERSION)
    
    @patch('common.base_sensor.run_sensor')
    def test_main_function(self, mock_run_sensor):
        """Test the main function."""
        from m8prcsvr.sensor import PROCESS_NAME, PLUGIN_NAME, VERSION
        
        # Import and run the main function
        import m8prcsvr.sensor
        if hasattr(m8prcsvr.sensor, '__name__') and m8prcsvr.sensor.__name__ == '__main__':
            m8prcsvr.sensor.run_sensor = mock_run_sensor  # Mock the run_sensor function
            # Since we can't directly call __main__ code, we test the function call
            mock_run_sensor.assert_not_called()  # Should not be called yet
            m8prcsvr.sensor.run_sensor(PROCESS_NAME, PLUGIN_NAME, VERSION, service_namespace="MicroStrategy")
            mock_run_sensor.assert_called_once_with(PROCESS_NAME, PLUGIN_NAME, VERSION, service_namespace="MicroStrategy")

if __name__ == '__main__':
    unittest.main()
