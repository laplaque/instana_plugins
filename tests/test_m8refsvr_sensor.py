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
        from m8refsvr.sensor import PROCESS_NAME, PLUGIN_NAME, VERSION
        self.assertEqual(PROCESS_NAME, "M8RefSvr")
        self.assertEqual(PLUGIN_NAME, "com.instana.plugin.python.microstrategy_m8refsvr")
        self.assertEqual(VERSION, "0.0.6")
    
    @patch('common.base_sensor.run_sensor')
    def test_main_function(self, mock_run_sensor):
        """Test that the main function calls run_sensor with the correct arguments."""
        # Import the module first
        import m8refsvr.sensor
        
        # Save the original __name__
        original_name = m8refsvr.sensor.__name__
        
        try:
            # Mock __name__ == "__main__"
            m8refsvr.sensor.__name__ = "__main__"
            
            # Re-import to trigger the __name__ == "__main__" block
            import importlib
            importlib.reload(m8refsvr.sensor)
            
            # Verify run_sensor was called with the correct arguments
            mock_run_sensor.assert_called_once_with(
                m8refsvr.sensor.PROCESS_NAME,
                m8refsvr.sensor.PLUGIN_NAME,
                m8refsvr.sensor.VERSION
            )
        finally:
            # Restore the original __name__
            m8refsvr.sensor.__name__ = original_name

if __name__ == '__main__':
    unittest.main()
