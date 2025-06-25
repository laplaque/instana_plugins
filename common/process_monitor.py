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

def get_matching_processes(process_name):
    """
    Get all processes matching the given process name.
    
    Args:
        process_name (str): The name of the process to monitor
        
    Returns:
        list: List of psutil.Process objects matching the process name
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
        
        return matching_processes
    except Exception as e:
        logger.error(f"Error getting matching processes for '{process_name}': {e}")
        return []

def identify_parent_processes(matching_processes):
    """
    Identify parent processes from a list of matching processes.
    
    Args:
        matching_processes (list): List of psutil.Process objects
        
    Returns:
        tuple: (process_map, parent_processes) where process_map is a dict of process info
               and parent_processes is a list of parent process PIDs
    """
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
    
    return process_map, parent_processes

def aggregate_process_metrics(process_map, parent_processes, process_name):
    """
    Aggregate metrics from parent processes.
    
    Args:
        process_map (dict): Dictionary of process information
        parent_processes (list): List of parent process PIDs
        process_name (str): The name of the process being monitored
        
    Returns:
        dict: Dictionary containing aggregated metrics
    """
    process_count = len(parent_processes)
    if process_count == 0:
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
    total_cpu_user_time = 0.0
    total_cpu_system_time = 0.0
    total_memory_rss = 0
    total_memory_vms = 0
    
    # Track PIDs for logging
    process_pids = []
    
    # Process all parent processes
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
            
            # Get enhanced metrics
            cpu_times = proc.cpu_times()
            total_cpu_user_time += cpu_times.user
            total_cpu_system_time += cpu_times.system
            
            memory_info = proc.memory_info()
            total_memory_rss += memory_info.rss
            total_memory_vms += memory_info.vms
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            logger.warning(f"Error processing PID {pid}: {str(e)}")
            continue
        except Exception as e:
            logger.warning(f"Error processing PID {pid}: {str(e)}")
            continue
    
    # Calculate average CPU and memory usage across monitored processes (not sum)
    avg_cpu_usage = total_cpu / process_count if process_count > 0 else 0.0
    avg_memory_usage = total_memory / process_count if process_count > 0 else 0.0
    
    # Build metrics dictionary with proper formatting
    # Return the original percentage values - otel_connector.py will handle conversion
    metrics = {
        "cpu_usage": round(avg_cpu_usage, 4),         # Keep as percentage (0-100)
        "memory_usage": round(avg_memory_usage, 4),   # Keep as percentage (0-100)
        "process_count": int(process_count),                 # Counter - should be integer
        "disk_read_bytes": int(total_disk_read),             # Counter - should be integer
        "disk_write_bytes": int(total_disk_write),           # Counter - should be integer
        "open_file_descriptors": int(total_open_fds),        # Counter - should be integer
        "thread_count": int(total_threads),                  # Counter - should be integer
        "voluntary_ctx_switches": int(total_voluntary_ctx_switches),    # Counter - should be integer
        "nonvoluntary_ctx_switches": int(total_nonvoluntary_ctx_switches), # Counter - should be integer
        "cpu_user_time_total": round(total_cpu_user_time, 2),
        "cpu_system_time_total": round(total_cpu_system_time, 2),
        "memory_rss_total": int(total_memory_rss),
        "memory_vms_total": int(total_memory_vms),
        "monitored_pids": ",".join(process_pids)             # For debugging
    }
    
    # Add thread statistics if available
    if parent_thread_counts:
        metrics["max_threads_per_process"] = int(max(parent_thread_counts))  # Counter - should be integer
        metrics["min_threads_per_process"] = int(min(parent_thread_counts))  # Counter - should be integer
        metrics["avg_threads_per_process"] = round(sum(parent_thread_counts) / len(parent_thread_counts), 2)  # Keep average as float
    
    return metrics

def get_process_metrics(process_name):
    """
    Get metrics for processes matching the given process name.
    
    Args:
        process_name (str): The name of the process to monitor
        
    Returns:
        dict: A dictionary containing process metrics or None if no processes found
    """
    try:
        # Get all matching processes
        matching_processes = get_matching_processes(process_name)
        
        if not matching_processes:
            logger.warning(f"No processes found matching '{process_name}'")
            return None
            
        # Identify parent processes
        process_map, parent_processes = identify_parent_processes(matching_processes)
        
        # Log the detected parent processes and thread counts
        logger.debug(f"Detected {len(parent_processes)} parent processes for {process_name}: {parent_processes}")
        
        if not parent_processes:
            logger.warning(f"No parent processes found matching '{process_name}'")
            return None
            
        # Aggregate metrics from parent processes
        metrics = aggregate_process_metrics(process_map, parent_processes, process_name)
        
        return metrics
        
    except Exception as e:
        logger.error(f"Unexpected error in get_process_metrics: {str(e)}")
        return None

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
