#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.
"""
import os
import subprocess
import json
import time
import re
from datetime import datetime

# Define the process name with proper capitalization
PROCESS_NAME = "M8MulPrc"

def get_process_metrics():
    # Get M8MulPrc process information
    process_info = subprocess.check_output(["ps", "-eo", "pid,pcpu,pmem,comm", "--sort=-pcpu"]).decode('utf-8')
    
    # Filter for M8MulPrc processes (case insensitive)
    process_regex = re.compile(PROCESS_NAME, re.IGNORECASE)
    m8mulprc_processes = [line for line in process_info.split('\n') if process_regex.search(line)]
    
    process_count = len(m8mulprc_processes)
    total_cpu = 0
    total_memory = 0
    
    # Initialize metrics
    total_disk_read = 0
    total_disk_write = 0
    total_open_fds = 0
    total_threads = 0
    total_voluntary_ctx_switches = 0
    total_nonvoluntary_ctx_switches = 0
    
    # Track PIDs for logging
    process_pids = []
    
    for process in m8mulprc_processes:
        parts = process.split()
        if len(parts) >= 3:
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
            except ValueError as e:
                pass
    
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

def report_metrics():
    metrics = get_process_metrics()
    
    # Format output for Instana
    output = {
        "name": "com.custom.microstrategy.m8mulprc",
        "entityId": f"{PROCESS_NAME.lower()}-" + os.uname()[1],  # Hostname as part of entity ID
        "timestamp": int(datetime.now().timestamp() * 1000),
        "metrics": metrics
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    report_metrics()

