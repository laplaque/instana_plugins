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
from common.process_monitor import report_metrics, parse_args

# Define the process name with proper capitalization
PROCESS_NAME = "M8MulPrc"
PLUGIN_NAME = "com.instana.plugin.python.microstrategy_m8mulprc"

if __name__ == "__main__":
    args = parse_args()
    process_name = args.process if args.process else PROCESS_NAME
    
    report_metrics(
        process_name=process_name,
        plugin_name=PLUGIN_NAME,
        format_output=args.format,
        continuous=args.continuous,
        interval=args.interval
    )

