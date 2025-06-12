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
import signal
import errno

logger = logging.getLogger(__name__)

PID_DIR = os.path.expanduser("~/.instana_plugins")

class PIDFileError(Exception):
    """Custom exception for PID file related errors."""
    pass

def get_pid_file_path(plugin_name):
    """Constructs the PID file path for a given plugin."""
    os.makedirs(PID_DIR, exist_ok=True)
    return os.path.join(PID_DIR, f"{plugin_name}.pid")

def write_pid_file(pid_file_path):
    """Writes the current process PID to the specified file."""
    try:
        with open(pid_file_path, 'w') as f:
            f.write(str(os.getpid()))
        logger.info(f"PID {os.getpid()} written to {pid_file_path}")
    except IOError as e:
        raise PIDFileError(f"Could not write PID file {pid_file_path}: {e}")

def read_pid_file(pid_file_path):
    """Reads the PID from the specified file."""
    try:
        with open(pid_file_path, 'r') as f:
            pid = int(f.read().strip())
        return pid
    except FileNotFoundError:
        return None
    except ValueError:
        raise PIDFileError(f"Invalid PID found in file {pid_file_path}")
    except IOError as e:
        raise PIDFileError(f"Could not read PID file {pid_file_path}: {e}")

def remove_pid_file(pid_file_path):
    """Removes the specified PID file."""
    try:
        os.remove(pid_file_path)
        logger.info(f"Removed PID file {pid_file_path}")
    except FileNotFoundError:
        pass # Already removed or never existed
    except IOError as e:
        logger.warning(f"Could not remove PID file {pid_file_path}: {e}")

def daemonize(plugin_name):
    """
    Daemonizes the current process using a POSIX-compliant double-fork procedure.
    Writes the PID to a file and redirects standard I/O.
    """
    pid_file_path = get_pid_file_path(plugin_name)

    # Check if PID file exists and process is running
    existing_pid = read_pid_file(pid_file_path)
    if existing_pid:
        try:
            os.kill(existing_pid, 0) # Check if process is still running
            raise PIDFileError(f"Another instance of {plugin_name} is already running with PID {existing_pid}. "
                               f"PID file: {pid_file_path}")
        except OSError as e:
            if e.errno == errno.ESRCH: # No such process
                logger.warning(f"Stale PID file found for {plugin_name}. Removing it.")
                remove_pid_file(pid_file_path)
            else:
                raise PIDFileError(f"Error checking existing PID {existing_pid}: {e}")

    # First fork
    try:
        pid = os.fork()
        if pid > 0:
            # Exit first parent
            sys.exit(0)
    except OSError as e:
        raise PIDFileError(f"First fork failed: {e}")

    # Decouple from parent environment
    os.chdir('/')
    os.setsid()
    os.umask(0)

    # Second fork
    try:
        pid = os.fork()
        if pid > 0:
            # Exit second parent
            sys.exit(0)
    except OSError as e:
        raise PIDFileError(f"Second fork failed: {e}")

    # Redirect standard file descriptors
    sys.stdout.flush()
    sys.stderr.flush()
    si = open(os.devnull, 'r')
    so = open(os.devnull, 'a+')
    se = open(os.devnull, 'a+')
    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())

    # Write PID file
    write_pid_file(pid_file_path)

    # Register cleanup for PID file on exit
    import atexit
    atexit.register(remove_pid_file, pid_file_path)

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
    parser.add_argument('--stop', action='store_true',
                        help='Stop the running daemon instance')
    parser.add_argument('--restart', action='store_true',
                        help='Restart the running daemon instance')
    # Removed duplicate --otel-port flag as it duplicated --agent-port functionality
    parser.add_argument('--install-location', default='/usr/local/bin',
                        help='Installation location (default: /usr/local/bin)')
    parser.add_argument('--log-level', default='INFO',
                        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                        help='Set the logging level (default: INFO)')
    parser.add_argument('--log-file', 
                        help='Path to the log file (default: project_root/logs/app.log)')
    parser.add_argument('--metadata-db-path',
                        help='Path to the metadata database (default: ~/.instana_plugins/metadata.db)')
    return parser.parse_args()

def monitor_process(process_name, plugin_name, agent_host, agent_port, interval=60, run_once=False, metadata_db_path=None, service_namespace="Unknown"):
    """Monitor the process and send metrics using OpenTelemetry"""
    # Initialize the OTel connector
    connector = InstanaOTelConnector(
        service_name=plugin_name,
        agent_host=agent_host,
        agent_port=agent_port,
        resource_attributes={
            "process.name": process_name,
            "host.name": os.uname()[1]
        },
        metadata_db_path=metadata_db_path,
        service_namespace=service_namespace
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

def run_sensor(process_name, plugin_name, version, service_namespace="Unknown"):
    """Main entry point for sensor scripts"""
    args = parse_args(f'Monitor {process_name} process metrics for Instana')

    # Set up logging with the specified log file and installation directory if provided
    setup_logging(
        log_level=getattr(logging, args.log_level),
        log_file=args.log_file,
        install_dir=args.install_location
    )

    pid_file_path = get_pid_file_path(plugin_name)

    if args.stop:
        logger.info(f"Attempting to stop {plugin_name}...")
        pid = read_pid_file(pid_file_path)
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent SIGTERM to PID {pid}. Waiting for process to terminate...")
                for _ in range(10): # Wait up to 10 seconds
                    if not os.path.exists(f"/proc/{pid}"): # Check if process is still running (Linux specific)
                        break
                    time.sleep(1)
                if os.path.exists(f"/proc/{pid}"):
                    logger.warning(f"Process {pid} did not terminate gracefully. Sending SIGKILL.")
                    os.kill(pid, signal.SIGKILL)
                remove_pid_file(pid_file_path)
                logger.info(f"{plugin_name} stopped successfully.")
                sys.exit(0)
            except OSError as e:
                if e.errno == errno.ESRCH:
                    logger.warning(f"Process with PID {pid} not found. Stale PID file removed.")
                    remove_pid_file(pid_file_path)
                else:
                    logger.error(f"Error stopping process {pid}: {e}")
                sys.exit(1)
        else:
            logger.info(f"{plugin_name} is not running (no PID file found).")
            sys.exit(0)

    if args.restart:
        logger.info(f"Attempting to restart {plugin_name}...")
        pid = read_pid_file(pid_file_path)
        if pid:
            try:
                os.kill(pid, signal.SIGTERM)
                logger.info(f"Sent SIGTERM to PID {pid}. Waiting for old process to terminate...")
                for _ in range(10):
                    if not os.path.exists(f"/proc/{pid}"):
                        break
                    time.sleep(1)
                if os.path.exists(f"/proc/{pid}"):
                    logger.warning(f"Old process {pid} did not terminate gracefully. Sending SIGKILL.")
                    os.kill(pid, signal.SIGKILL)
                remove_pid_file(pid_file_path)
            except OSError as e:
                if e.errno == errno.ESRCH:
                    logger.warning(f"Old process with PID {pid} not found. Stale PID file removed.")
                    remove_pid_file(pid_file_path)
                else:
                    logger.error(f"Error stopping old process {pid}: {e}")
                    sys.exit(1)
        else:
            logger.info(f"No running instance of {plugin_name} found. Starting new instance.")
        # Continue to start new instance below

    logger.info(f"Starting {plugin_name} v{version} with Instana agent at {args.agent_host}:{args.agent_port}")

    try:
        daemonize(plugin_name)
        logger.info(f"{plugin_name} daemonized successfully.")
    except PIDFileError as e:
        logger.error(f"Failed to daemonize {plugin_name}: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred during daemonization: {e}")
        sys.exit(1)

    # Main monitoring loop
    if args.once:
        success = monitor_process(
            process_name=process_name,
            plugin_name=plugin_name,
            agent_host=args.agent_host,
            agent_port=args.agent_port,
            interval=args.interval,
            run_once=True,
            metadata_db_path=args.metadata_db_path,
            service_namespace=service_namespace
        )
        sys.exit(0 if success else 1)
    else:
        monitor_process(
            process_name=process_name,
            plugin_name=plugin_name,
            agent_host=args.agent_host,
            agent_port=args.agent_port,
            interval=args.interval,
            metadata_db_path=args.metadata_db_path,
            service_namespace=service_namespace
        )
