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

# Add the parent directory to the path to import the common modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.process_monitor import get_process_metrics
from common.otel_connector import InstanaOTelConnector

# Define the process name with proper capitalization
PROCESS_NAME = "MSTRSvr"
PLUGIN_NAME = "com.instana.plugin.python.microstrategy_mstrsvr"

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Monitor MSTRSvr process metrics for Instana')
    parser.add_argument('--agent-host', default='localhost',
                        help='Hostname of the Instana agent (default: localhost)')
    parser.add_argument('--agent-port', type=int, default=4317,
                        help='Port of the Instana agent OTLP receiver (default: 4317)')
    return parser.parse_args()

def monitor_process(process_name, plugin_name, agent_host, agent_port):
    """Monitor the process and send metrics using OpenTelemetry"""
    # Initialize the OTel connector
    connector = InstanaOTelConnector(
        service_name=plugin_name,
        agent_host=agent_host,
        agent_port=agent_port,
        resource_attributes={
            "process.name": process_name,
            "host.name": os.uname()[1]
        }
    )
    
    # Continuously collect and report metrics
    while True:
        try:
            # Create a span for the metric collection
            with connector.create_span(
                name=f"collect_{process_name}_metrics",
                attributes={"process.name": process_name}
            ):
                # Get process metrics
                metrics = get_process_metrics(process_name)
                
                if metrics:
                    # Record metrics using OTel
                    connector.record_metrics(metrics)
                    logger.info(f"Sent metrics for {process_name}")
                    logger.debug(f"Metrics: {metrics}")
                else:
                    logger.warning(f"No metrics found for process {process_name}")
                
            # Wait before collecting metrics again
            import time
            time.sleep(60)  # Collect metrics every minute
            
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
            break
        except Exception as e:
            logger.error(f"Error monitoring {process_name}: {e}")
            import time
            time.sleep(60)  # Wait before retrying

if __name__ == "__main__":
    args = parse_args()
    
    logger.info(f"Starting {PLUGIN_NAME} with Instana agent at {args.agent_host}:{args.agent_port}")
    
    monitor_process(
        process_name=PROCESS_NAME,
        plugin_name=PLUGIN_NAME,
        agent_host=args.agent_host,
        agent_port=args.agent_port
    )

