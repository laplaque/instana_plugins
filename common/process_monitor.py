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
import re
import json
import logging
import multiprocessing
import platform
from datetime import datetime
from typing import Dict, Any, Optional, List

import psutil

# Import the OpenTelemetry connector
from common.otel_connector import InstanaOTelConnector

# Configure logging
logger = logging.getLogger(__name__)

def get_cpu_cores_count():
    """
    Get the number of CPU cores in the system.
    
    Returns:
        int: Number of CPU cores
    """
    return multiprocessing.cpu_count()

def get_process_cpu_per_core(pid):
    """
    Get per-core CPU usage for a specific process ID.
    
    Args:
        pid (str): Process ID
        
    Returns:
        dict: Dictionary with CPU core usage (core_id -> usage percentage)
    """
    try:
        # Get system-wide per-core CPU usage
        # Note: psutil doesn't provide per-process per-core CPU usage directly
        # We get system-wide per-core usage as a reasonable approximation
        per_core_usage = psutil.cpu_percent(percpu=True, interval=0.1)
        
        # Create core usage dictionary
        core_usage = {}
        for i, usage in enumerate(per_core_usage):
            core_usage[f"cpu_core_{i}"] = usage
            
        return core_usage
    except Exception as e:
        logger.debug(f"Error getting per-core CPU usage for PID {pid}: {e}")
        return {}

def get_process_metrics(process_name):
    """
    Get metrics for processes matching the given process name.
    
    Args:
        process_name (str): The name of the process to monitor
        
    Returns:
        dict: A dictionary containing process metrics or None if no processes found
    """
    try:
        # Filter for processes (case insensitive)
        process_regex = re.compile(process_name, re.IGNORECASE)
        matching_processes = []
        
        # Get all processes and filter by name
        for proc in psutil.process_iter(['pid', 'ppid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if proc.info and process_regex.search(proc.info['name']):
                    matching_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # Process may have disappeared or we don't have access
                continue
        
        if not matching_processes:
            logger.warning(f"No processes found matching '{process_name}'")
            return None
            
        # Parse the matching processes to identify parent processes and threads
        process_map = {}  # pid -> {ppid, info, etc.}
        parent_processes = []
        
        for proc in matching_processes:
            try:
                pid = str(proc.pid)
                ppid = str(proc.ppid())
                
                # Get CPU and memory percentages
                cpu_percent = proc.cpu_percent()
                memory_percent = proc.memory_percent()
                
                process_info = {
                    'pid': pid,
                    'ppid': ppid,
                    'cpu': cpu_percent,
                    'memory': memory_percent,
                    'command': proc.name(),
                    'process': proc,
                    'is_parent': False  # Will set to True for parent processes
                }
                process_map[pid] = process_info
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logger.debug(f"Error processing process {proc.pid}: {e}")
                continue
                
        # Identify parent processes - those whose PPID is not in our process_map
        # or is a system process (PPID=1 typically)
        for pid, info in process_map.items():
            ppid = info['ppid']
            if ppid not in process_map or ppid == '1':
                info['is_parent'] = True
                parent_processes.append(pid)
                
        # Log the detected parent processes and thread counts
        logger.debug(f"Detected {len(parent_processes)} parent processes for {process_name}: {parent_processes}")
        
        # Count parent processes
        process_count = len(parent_processes)
        if process_count == 0:
            logger.warning(f"No parent processes found matching '{process_name}'")
            return None
            
        # Initialize metrics
        total_cpu = 0.0
        total_memory = 0.0
        total_disk_read = 0
        total_disk_write = 0
        total_open_fds = 0
        total_threads = 0
        parent_thread_counts = []  # Track thread counts per parent process
        total_voluntary_ctx_switches = 0
        total_nonvoluntary_ctx_switches = 0
        
        # Track PIDs for logging
        process_pids = []
        
        # Initialize per-core CPU usage aggregation
        cpu_cores = get_cpu_cores_count()
        per_core_cpu = {f"cpu_core_{i}": 0.0 for i in range(cpu_cores)}
        
        # Process all parent processes first
        for pid in parent_processes:
            info = process_map[pid]
            proc = info['process']
            process_pids.append(pid)
            
            try:
                # Add CPU and memory from parent process
                total_cpu += info['cpu']
                total_memory += info['memory']
                
                # Get disk I/O for this PID
                read_bytes, write_bytes = get_disk_io_for_pid(proc)
                total_disk_read += read_bytes
                total_disk_write += write_bytes
                
                # Get file descriptor count
                open_fds = get_file_descriptor_count(proc)
                total_open_fds += open_fds
                
                # Get thread count for this parent process
                thread_count = get_thread_count(proc)
                total_threads += thread_count
                parent_thread_counts.append(thread_count)
                
                # Log thread count for debugging
                logger.debug(f"Process {pid} ({process_name}) has {thread_count} threads")
                
                # Get context switches
                vol_ctx, nonvol_ctx = get_context_switches(proc)
                total_voluntary_ctx_switches += vol_ctx
                total_nonvoluntary_ctx_switches += nonvol_ctx
                
                # Get per-core CPU usage (system-wide approximation)
                core_usage = get_process_cpu_per_core(pid)
                for core_id, usage in core_usage.items():
                    if core_id in per_core_cpu:
                        per_core_cpu[core_id] += usage
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                logger.warning(f"Error processing PID {pid}: {str(e)}")
                continue
            except Exception as e:
                logger.warning(f"Error processing PID {pid}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Unexpected error in get_process_metrics: {str(e)}")
        return None
    
    # CPU and memory are already percentages but need to be rounded
    # Counter metrics should be integers, not rounded floats
    metrics = {
        "cpu_usage": round(total_cpu, 2),                   # Already percentage
        "memory_usage": round(total_memory, 2),             # Already percentage
        "process_count": int(process_count),                # Counter - should be integer
        "disk_read_bytes": int(total_disk_read),            # Counter - should be integer
        "disk_write_bytes": int(total_disk_write),          # Counter - should be integer
        "open_file_descriptors": int(total_open_fds),       # Counter - should be integer
        "thread_count": int(total_threads),                 # Counter - should be integer
        "voluntary_ctx_switches": int(total_voluntary_ctx_switches),  # Counter - should be integer
        "nonvoluntary_ctx_switches": int(total_nonvoluntary_ctx_switches),  # Counter - should be integer
        "monitored_pids": ",".join(process_pids)            # For debugging
    }
    
    # Add thread statistics if available
    if parent_thread_counts:
        metrics["max_threads_per_process"] = int(max(parent_thread_counts))  # Counter - should be integer
        metrics["min_threads_per_process"] = int(min(parent_thread_counts))  # Counter - should be integer
        metrics["avg_threads_per_process"] = round(sum(parent_thread_counts) / len(parent_thread_counts), 2)  # Keep average as float
    
    # Add per-core CPU metrics if available
    for core_id, usage in per_core_cpu.items():
        if usage > 0:  # Only include cores that show activity
            metrics[core_id] = round(usage, 2)
    
    return metrics

def get_disk_io_for_pid(proc):
    """Get disk I/O statistics for a specific process"""
    try:
        io_counters = proc.io_counters()
        read_bytes = io_counters.read_bytes
        write_bytes = io_counters.write_bytes
        return read_bytes, write_bytes
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return 0, 0
    except Exception:
        return 0, 0

def get_file_descriptor_count(proc):
    """Get the number of open file descriptors for a process"""
    try:
        # Count open files and network connections
        open_files_count = len(proc.open_files())
        connections_count = len(proc.connections())
        return open_files_count + connections_count
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return 0
    except Exception:
        return 0

def get_thread_count(proc):
    """Get the number of threads for a process"""
    try:
        thread_count = proc.num_threads()
        logger.debug(f"Got thread count for PID {proc.pid}: {thread_count}")
        return thread_count
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        logger.debug(f"Could not access process {proc.pid} for thread count")
        return 0
    except Exception as e:
        logger.debug(f"Error in get_thread_count for PID {proc.pid}: {e}")
        return 0

def get_context_switches(proc):
    """Get voluntary and non-voluntary context switches for a process"""
    try:
        ctx_switches = proc.num_ctx_switches()
        vol_ctx = ctx_switches.voluntary
        nonvol_ctx = ctx_switches.involuntary
        return vol_ctx, nonvol_ctx
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return 0, 0
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
                "host.name": platform.node()
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
                "entityId": f"{process_name.lower()}-" + platform.node(),
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
            "entityId": f"{process_name.lower()}-" + platform.node(),
            "timestamp": int(datetime.now().timestamp() * 1000),
            "metrics": metrics
        }
        print(json.dumps(output), flush=True)
