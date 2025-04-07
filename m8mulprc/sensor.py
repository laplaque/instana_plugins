#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.
"""
import sys
import os
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to the path to import the common module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.process_monitor import report_metrics

# Define the process name with proper capitalization
PROCESS_NAME = "M8MulPrc"
PLUGIN_NAME = "com.instana.plugin.python.microstrategy_m8mulprc"

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Monitor M8MulPrc process metrics for Instana')
    parser.add_argument('--agent-host', default='localhost',
                        help='Hostname of the Instana agent (default: localhost)')
    parser.add_argument('--agent-port', type=int, default=4317,
                        help='Port of the Instana agent OTLP receiver (default: 4317)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    
    logger.info(f"Starting {PLUGIN_NAME} with Instana agent at {args.agent_host}:{args.agent_port}")
    
    report_metrics(
        process_name=PROCESS_NAME,
        plugin_name=PLUGIN_NAME,
        agent_host=args.agent_host,
        agent_port=args.agent_port
    )

