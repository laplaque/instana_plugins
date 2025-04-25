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

PROCESS_NAME = "M8PrcSvr"
PLUGIN_NAME = "com.instana.plugin.python.microstrategy_m8prcsvr"
VERSION = "0.0.10"

if __name__ == "__main__":
    run_sensor(PROCESS_NAME, PLUGIN_NAME, VERSION)
