#!/bin/bash
#
# MIT License
#
# Copyright (c) 2025 laplaque/instana_plugins Contributors
#
# This file is part of the Instana Plugins collection.
#

# MSTRSvr Instana Plugin Installer
# --------------------------------

# Default Instana agent location for Red Hat Linux
DEFAULT_INSTANA_DIR="/opt/instana/agent"
DEFAULT_PLUGIN_DIR="${DEFAULT_INSTANA_DIR}/plugins/custom_sensors/microstrategy_mstrsvr"

# Set colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Define usage function
function show_usage {
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "Install the MicroStrategy MSTRSvr monitoring plugin for Instana"
    echo -e "\nOptions:"
    echo -e "  -d, --directory DIR    Installation directory (default: ${DEFAULT_PLUGIN_DIR})"
    echo -e "  -r, --restart          Restart Instana agent after installation"
    echo -e "  -h, --help             Show this help message and exit"
}

# Parse command line arguments
INSTALL_DIR=$DEFAULT_PLUGIN_DIR
RESTART_AGENT=false

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -d|--directory)
            INSTALL_DIR="$2"
            shift 2
            ;;
        -r|--restart)
            RESTART_AGENT=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Error: Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

echo -e "${GREEN}MicroStrategy MSTRSvr Instana Plugin Installer${NC}"
echo -e "Installation directory: ${INSTALL_DIR}"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Warning: Not running as root. You may encounter permission issues.${NC}"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${RED}Installation aborted.${NC}"
        exit 1
    fi
fi

# Create plugin files
function create_plugin_json {
    cat > "${INSTALL_DIR}/plugin.json" << 'EOF'
{
  "__license": "MIT License, Copyright (c) 2025 laplaque/instana_plugins Contributors",
  "name": "com.custom.microstrategy.mstrsvr",
  "version": "1.0.0",
  "type": "custom",
  "entity": {
    "type": "microstrategy_mstrsvr"
  },
  "metrics": {
    "cpu_usage": {
      "displayName": "CPU Usage",
      "unit": "%"
    },
    "memory_usage": {
      "displayName": "Memory Usage",
      "unit": "MB"
    },
    "process_count": {
      "displayName": "Process Count",
      "unit": "count"
    },
    "disk_read_bytes": {
      "displayName": "Disk Read",
      "unit": "bytes"
    },
    "disk_write_bytes": {
      "displayName": "Disk Write",
      "unit": "bytes"
    },
    "open_file_descriptors": {
      "displayName": "Open File Descriptors",
      "unit": "count"
    },
    "thread_count": {
      "displayName": "Thread Count",
      "unit": "count"
    },
    "voluntary_ctx_switches": {
      "displayName": "Voluntary Context Switches",
      "unit": "count"
    },
    "nonvoluntary_ctx_switches": {
      "displayName": "Non-voluntary Context Switches",
      "unit": "count"
    },
    "monitored_pids": {
      "displayName": "Monitored PIDs",
      "unit": "text"
    }
  }
}
EOF
}

function create_sensor_py {
    cat > "${INSTALL_DIR}/sensor.py" << 'EOF'
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
PROCESS_NAME = "MSTRSvr"

def get_process_metrics():
    # Get MSTRSvr process information
    process_info = subprocess.check_output(["ps", "-eo", "pid,pcpu,pmem,comm", "--sort=-pcpu"]).decode('utf-8')
    
    # Filter for MSTRSvr processes (case insensitive)
    process_regex = re.compile(PROCESS_NAME, re.IGNORECASE)
    mstrsvr_processes = [line for line in process_info.split('\n') if process_regex.search(line)]
    
    process_count = len(mstrsvr_processes)
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
    
    for process in mstrsvr_processes:
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
        "name": "com.custom.microstrategy.mstrsvr",
        "entityId": f"{PROCESS_NAME.lower()}-" + os.uname()[1],  # Hostname as part of entity ID
        "timestamp": int(datetime.now().timestamp() * 1000),
        "metrics": metrics
    }
    
    print(json.dumps(output))

if __name__ == "__main__":
    report_metrics()
EOF
}

function create_sample_config {
    cat > "${INSTALL_DIR}/sample-config.yaml" << 'EOF'
# Sample configuration for Instana agent
# MIT License - Copyright (c) 2025 laplaque/instana_plugins Contributors
#
# Add this to your Instana agent configuration.yaml file

com.instana.plugin.python:
  enabled: true
  custom_sensors:
    - id: microstrategy_mstrsvr
      path: /opt/instana/agent/plugins/custom_sensors/microstrategy_mstrsvr/sensor.py
      interval: 30000  # Run every 30 seconds (adjust as needed)
EOF
}

# Create installation directory
echo -e "Creating installation directory..."
mkdir -p "${INSTALL_DIR}"
if [ $? -ne 0 ]; then
    echo -e "${RED}Error: Failed to create directory ${INSTALL_DIR}${NC}"
    exit 1
fi

# Create plugin files
echo -e "Creating plugin files..."
create_plugin_json
create_sensor_py
create_sample_config

# Set permissions
echo -e "Setting permissions..."
chmod 755 "${INSTALL_DIR}/sensor.py"
chmod 644 "${INSTALL_DIR}/plugin.json"
chmod 644 "${INSTALL_DIR}/sample-config.yaml"

# Check if Instana agent configuration exists
CONFIG_FILE="${DEFAULT_INSTANA_DIR}/etc/instana/configuration.yaml"
if [ -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}Instana agent configuration detected.${NC}"
    echo -e "To enable the MSTRSvr plugin, you need to add the following to your Instana agent configuration:"
    echo
    cat "${INSTALL_DIR}/sample-config.yaml"
    echo
    
    read -p "Would you like to append this configuration automatically? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Create backup of existing config
        cp "$CONFIG_FILE" "${CONFIG_FILE}.bak.$(date +%Y%m%d%H%M%S)"
        
        # Append configuration
        echo "" >> "$CONFIG_FILE"
        echo "# Added by MSTRSvr plugin installer $(date)" >> "$CONFIG_FILE"
        cat "${INSTALL_DIR}/sample-config.yaml" >> "$CONFIG_FILE"
        
        echo -e "${GREEN}Configuration added to $CONFIG_FILE${NC}"
        echo -e "${YELLOW}A backup of your original configuration was created.${NC}"
    fi
else
    echo -e "${YELLOW}Instana agent configuration not found at $CONFIG_FILE${NC}"
    echo -e "Please manually add the configuration from ${INSTALL_DIR}/sample-config.yaml"
fi

# Restart Instana agent if requested
if [ "$RESTART_AGENT" = true ]; then
    echo -e "Restarting Instana agent..."
    
    if command -v systemctl &> /dev/null && systemctl is-active --quiet instana-agent; then
        systemctl restart instana-agent
        echo -e "${GREEN}Instana agent restarted successfully.${NC}"
    else
        echo -e "${YELLOW}Could not restart Instana agent automatically.${NC}"
        echo -e "Please restart the agent manually with: systemctl restart instana-agent"
    fi
fi

echo -e "${GREEN}MicroStrategy MSTRSvr Instana Plugin installed successfully!${NC}"
echo -e "Installation directory: ${INSTALL_DIR}"
echo -e "\nTo test the plugin, run: ${INSTALL_DIR}/sensor.py"

exit 0

