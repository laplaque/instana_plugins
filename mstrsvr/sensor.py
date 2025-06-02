#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.
Version: 0.0.13
"""
import sys
import os

# Add the parent directory to the path to import the common modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.base_sensor import run_sensor

# Define the process name with proper capitalization
PROCESS_NAME = "MSTRSvr"
PLUGIN_NAME = "com.instana.plugin.python.microstrategy_mstrsvr"
VERSION = "0.0.13"

if __name__ == "__main__":
    run_sensor(PROCESS_NAME, PLUGIN_NAME, VERSION)
