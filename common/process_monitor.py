#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.
"""
from common.logging_config import setup_logging

setup_logging()  # Configure logging at the start of the module
import os
import subprocess
import json
import re
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Import the OpenTelemetry connector
from common.otel_connector import InstanaOTelConnector

# Configure logging
logger = logging.getLogger(__name__)

def get_process_metrics(process_name):
    """
    Get metrics for processes matching the given process name.
    
    Args:
        process_name (str): The name of the process to monitor
        
    Returns:
        dict: A dictionary containing process metrics or None if no processes found
    """
    try:
        # Get process information
        process_info = subprocess.check_output(
            ["ps", "-eo", "pid,pcpu,pmem,comm", "--sort=-pcpu"],
            stderr=subprocess.PIPE
        ).decode('utf-8')
        
        # Filter for processes (case insensitive)
        process_regex = re.compile(process_name, re.IGNORECASE)
        matching_processes = [line for line in process_info.split('\n') if process_regex.search(line)]
        
        process_count = len(matching_processes)
        if process_count == 0:
            logger.warning(f"No processes found matching '{process_name}'")
            return None
            
        # Initialize metrics
        total_cpu = 0
        total_memory = 0
        total_disk_read = 0
        total_disk_write = 0
        total_open_fds = 0
        total_threads = 0
        total_voluntary_ctx_switches = 0
        total_nonvoluntary_ctx_switches = 0
        
        # Track PIDs for logging
        process_pids = []
        
        for process in matching_processes:
            parts = process.split()
            if len(parts) < 4:
                continue
            
            try:
                pid = parts[0]
                process_pids.append(pid)
                total_cpu += float(parts[1])
                total_memory += float(parts[2])
                
                # Get disk I/O for this PID
                read_bytes, write_bytes = get_disk_io_for_pid(pid)
                total_disk_read += read_bytes
                total_disk_write += write_bytes
                
                # Get file descriptor count
                open_fds = get_file_descriptor_count(pid)
                total_open_fds += open_fds
                
                # Get thread count
                thread_count = get_thread_count(pid)
                total_threads += thread_count
                
                # Get context switches
                vol_ctx, nonvol_ctx = get_context_switches(pid)
                total_voluntary_ctx_switches += vol_ctx
                total_nonvoluntary_ctx_switches += nonvol_ctx
            except Exception as e:
                logger.warning(f"Error processing PID {pid}: {str(e)}")
                continue
    except subprocess.CalledProcessError as e:
        logger.error(f"Error executing process command: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_process_metrics: {str(e)}")
        return None
    
    return {
        "cpu_usage": total_cpu,
        "memory_usage": total_memory,
        "process_count": process_count,
        "disk_read_bytes": total_disk_read,
        "disk_write_bytes": total_disk_write,
        "open_file_descriptors": total_open_fds,
        "thread_count": total_threads,
        "voluntary_ctx_switches": total_voluntary_ctx_switches,
        "nonvoluntary_ctx_switches": total_nonvoluntary_ctx_switches,
        "monitored_pids": ",".join(process_pids)  # For debugging
    }

def get_disk_io_for_pid(pid):
    """Get disk I/O statistics for a specific process ID"""
    try:
        # Read current I/O stats
        with open(f"/proc/{pid}/io", "r") as f:
            io_content = f.readlines()
        
        read_bytes = 0
        write_bytes = 0
        
        for line in io_content:
            if "read_bytes" in line:
                read_bytes = int(line.split(":")[1].strip())
            elif "write_bytes" in line:
                write_bytes = int(line.split(":")[1].strip())
        
        return read_bytes, write_bytes
    except Exception:
        return 0, 0

def get_file_descriptor_count(pid):
    """Get the number of open file descriptors for a process"""
    try:
        # Count entries in /proc/{pid}/fd directory
        fd_dir = f"/proc/{pid}/fd"
        if os.path.exists(fd_dir):
            return len(os.listdir(fd_dir))
        return 0
    except Exception:
        return 0

def get_thread_count(pid):
    """Get the number of threads for a process"""
    try:
        # Count entries in /proc/{pid}/task directory
        task_dir = f"/proc/{pid}/task"
        if os.path.exists(task_dir):
            return len(os.listdir(task_dir))
        
        # Alternative method using status file
        with open(f"/proc/{pid}/status", "r") as f:
            status_content = f.read()
            thread_match = re.search(r"Threads:\s+(\d+)", status_content)
            if thread_match:
                return int(thread_match.group(1))
        return 0
    except Exception:
        return 0

def get_context_switches(pid):
    """Get voluntary and non-voluntary context switches for a process"""
    try:
        with open(f"/proc/{pid}/status", "r") as f:
            status_content = f.read()
            
            vol_match = re.search(r"voluntary_ctxt_switches:\s+(\d+)", status_content)
            nonvol_match = re.search(r"nonvoluntary_ctxt_switches:\s+(\d+)", status_content)
            
            vol_ctx = int(vol_match.group(1)) if vol_match else 0
            nonvol_ctx = int(nonvol_match.group(1)) if nonvol_match else 0
            
            return vol_ctx, nonvol_ctx
    except Exception:
        return 0, 0

def report_metrics(process_name, plugin_name, agent_host="localhost", agent_port=4317, 
                  use_tls=False, ca_cert_path=None, client_cert_path=None, client_key_path=None):
    """
    Report metrics for the given process to Instana using OpenTelemetry.
    This function is kept for backward compatibility.
    
    Args:
        process_name (str): The name of the process to monitor
        plugin_name (str): The name of the Instana plugin
        agent_host (str): Hostname of the Instana agent (default: localhost)
        agent_port (int): Port of the Instana agent's OTLP receiver (default: 4317)
        use_tls (bool): Whether to use TLS encryption for the connection (default: False)
        ca_cert_path (str): Path to CA certificate file for TLS verification (optional)
        client_cert_path (str): Path to client certificate file for TLS authentication (optional)
        client_key_path (str): Path to client key file for TLS authentication (optional)
    """
    logger.warning("report_metrics is deprecated. Use get_process_metrics with InstanaOTelConnector instead.")
    
    try:
        # Import here to avoid circular imports
        from common.otel_connector import InstanaOTelConnector
        
        # Create a span to track the metric collection process
        otel = InstanaOTelConnector(
            service_name=plugin_name,
            agent_host=agent_host,
            agent_port=agent_port,
            resource_attributes={
                "process.name": process_name,
                "host.name": os.uname()[1]
            },
            use_tls=use_tls,
            ca_cert_path=ca_cert_path,
            client_cert_path=client_cert_path,
            client_key_path=client_key_path
        )
        
        # Create a span for the metric collection
        with otel.create_span(
            name=f"collect_{process_name}_metrics",
            attributes={"process.name": process_name}
        ):
            # Collect metrics
            metrics = get_process_metrics(process_name)
            
            # Record metrics using OpenTelemetry
            otel.record_metrics(metrics)
            
            # For backward compatibility, also print the JSON output
            output = {
                "name": plugin_name,
                "entityId": f"{process_name.lower()}-" + os.uname()[1],
                "timestamp": int(datetime.now().timestamp() * 1000),
                "metrics": metrics
            }
            
            print(json.dumps(output), flush=True)
            logger.info(f"Reported metrics for {process_name} using OpenTelemetry")
            
    except Exception as e:
        logger.error(f"Error reporting metrics: {e}")
        
        # Fallback to traditional output in case of error
        metrics = get_process_metrics(process_name)
        output = {
            "name": plugin_name,
            "entityId": f"{process_name.lower()}-" + os.uname()[1],
            "timestamp": int(datetime.now().timestamp() * 1000),
            "metrics": metrics
        }
        print(json.dumps(output), flush=True)
