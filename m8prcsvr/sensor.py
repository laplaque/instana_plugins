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
from common import VERSION

# Import configuration from package __init__.py
from . import SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME

if __name__ == "__main__":
    run_sensor(PROCESS_NAME, PLUGIN_NAME, VERSION, service_namespace=SERVICE_NAMESPACE)
