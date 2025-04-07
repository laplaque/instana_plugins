#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.
"""
import sys
import os

# Add the parent directory to the path to import the common module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.process_monitor import report_metrics

# Define the process name with proper capitalization
PROCESS_NAME = "MSTRSvr"
PLUGIN_NAME = "com.instana.plugin.python.microstrategy_mstrsvr"

if __name__ == "__main__":
    report_metrics(PROCESS_NAME, PLUGIN_NAME)

