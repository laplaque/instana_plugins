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
from common.logging_config import setup_logging

setup_logging()  # Configure logging at the start of the module
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path to import the common modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.process_monitor import get_process_metrics
from common.otel_connector import InstanaOTelConnector

def parse_args(description):
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--agent-host', default='localhost',
                        help='Hostname of the Instana agent (default: localhost)')
    parser.add_argument('--agent-port', type=int, default=4317,
                        help='Port of the Instana agent OTLP receiver (default: 4317)')
    parser.add_argument('--interval', type=int, default=60,
                        help='Metrics collection interval in seconds (default: 60)')
    parser.add_argument('--once', action='store_true',
                        help='Run once and exit (default: continuous monitoring)')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level (default: INFO)')
    return parser.parse_args()

def monitor_process(process_name, plugin_name, agent_host, agent_port, interval=60, run_once=False):
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
    
    try:
        # Function to collect and report metrics once
        def collect_and_report():
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
                        return True
                    else:
                        logger.warning(f"No metrics found for process {process_name}")
                        return False
            except Exception as e:
                logger.error(f"Error collecting metrics for {process_name}: {e}")
                return False
        
        # Run once or continuously based on the parameter
        if run_once:
            result = collect_and_report()
            return result
        
        # Continuously collect and report metrics
        while True:
            try:
                collect_and_report()
                # Wait before collecting metrics again
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error monitoring {process_name}: {e}")
                time.sleep(interval)  # Wait before retrying
    finally:
        # Make sure we always try to shutdown the connector
        try:
            connector.shutdown()
        except Exception as e:
            logger.error(f"Error shutting down connector: {e}")

def run_sensor(process_name, plugin_name, version):
    """Main entry point for sensor scripts"""
    args = parse_args(f'Monitor {process_name} process metrics for Instana')
    
    # Set the log level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    logger.info(f"Starting {plugin_name} v{version} with Instana agent at {args.agent_host}:{args.agent_port}")
    
    if args.once:
        success = monitor_process(
            process_name=process_name,
            plugin_name=plugin_name,
            agent_host=args.agent_host,
            agent_port=args.agent_port,
            interval=args.interval,
            run_once=True
        )
        sys.exit(0 if success else 1)
    else:
        monitor_process(
            process_name=process_name,
            plugin_name=plugin_name,
            agent_host=args.agent_host,
            agent_port=args.agent_port,
            interval=args.interval
        )
