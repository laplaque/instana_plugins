#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the sensor modules.
"""
import unittest
from unittest.mock import MagicMock
import sys
import os

# Add the parent directory and mocks to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'mocks')))

# Mock the OpenTelemetry imports before importing the module
sys.modules['opentelemetry'] = MagicMock()
sys.modules['opentelemetry.trace'] = MagicMock()
sys.modules['opentelemetry.sdk'] = MagicMock()
sys.modules['opentelemetry.sdk.trace'] = MagicMock()
sys.modules['opentelemetry.sdk.trace.export'] = MagicMock()
sys.modules['opentelemetry.sdk.resources'] = MagicMock()
sys.modules['opentelemetry.exporter.otlp.proto.grpc.trace_exporter'] = MagicMock()
sys.modules['opentelemetry.sdk.metrics'] = MagicMock()
sys.modules['opentelemetry.sdk.metrics.export'] = MagicMock()
sys.modules['opentelemetry.exporter.otlp.proto.grpc.metric_exporter'] = MagicMock()
sys.modules['opentelemetry.metrics'] = MagicMock()
sys.modules['opentelemetry.semantic_conventions'] = MagicMock()

class TestSensors(unittest.TestCase):
    """Test cases for the sensor modules."""

    def test_m8prcsvr_sensor(self):
        """Test M8PrcSvr sensor."""
        # Import the sensor module
        import m8prcsvr.sensor
        from common.toml_utils import get_manifest_value
        from common.version import get_version
        EXPECTED_VERSION = get_manifest_value('metadata.version', '0.1.0')
        
        # Verify constants are set correctly
        self.assertEqual(m8prcsvr.sensor.PROCESS_NAME, "M8PrcSvr")
        self.assertEqual(m8prcsvr.sensor.PLUGIN_NAME, "m8prcsvr")
        # Verify version alignment with manifest.toml
        self.assertEqual(get_version(), EXPECTED_VERSION)

    def test_m8mulprc_sensor(self):
        """Test M8MulPrc sensor."""
        # Import the sensor module
        import m8mulprc.sensor
        from common.toml_utils import get_manifest_value
        from common.version import get_version
        EXPECTED_VERSION = get_manifest_value('metadata.version', '0.1.0')
        
        # Verify constants are set correctly
        self.assertEqual(m8mulprc.sensor.PROCESS_NAME, "M8MulPrc")
        self.assertEqual(m8mulprc.sensor.PLUGIN_NAME, "m8mulprc")
        # Verify version alignment with manifest.toml
        self.assertEqual(get_version(), EXPECTED_VERSION)

    def test_mstrsvr_sensor(self):
        """Test MstrSvr sensor."""
        # Import the sensor module
        import mstrsvr.sensor
        from common.toml_utils import get_manifest_value
        from common.version import get_version
        EXPECTED_VERSION = get_manifest_value('metadata.version', '0.1.0')
        
        # Verify constants are set correctly
        self.assertEqual(mstrsvr.sensor.PROCESS_NAME, "MstrSvr")
        self.assertEqual(mstrsvr.sensor.PLUGIN_NAME, "mstrsvr")
        # Verify version alignment with manifest.toml
        self.assertEqual(get_version(), EXPECTED_VERSION)
        
    def test_m8refsvr_sensor(self):
        """Test M8RefSvr sensor."""
        # Import the sensor module
        import m8refsvr.sensor
        from common.toml_utils import get_manifest_value
        from common.version import get_version
        EXPECTED_VERSION = get_manifest_value('metadata.version', '0.1.0')
        
        # Verify constants are set correctly
        self.assertEqual(m8refsvr.sensor.PROCESS_NAME, "M8RefSvr")
        self.assertEqual(m8refsvr.sensor.PLUGIN_NAME, "m8refsvr")
        # Verify version alignment with manifest.toml
        self.assertEqual(get_version(), EXPECTED_VERSION)

if __name__ == '__main__':
    unittest.main()
