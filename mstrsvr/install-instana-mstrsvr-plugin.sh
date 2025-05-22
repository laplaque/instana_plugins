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

# Define plugin-specific variables
PROCESS_NAME="MSTRSvr"
PLUGIN_NAME="com.instana.plugin.python.microstrategy_mstrsvr"

echo -e "${GREEN}MicroStrategy ${PROCESS_NAME} Instana Plugin Installer${NC}"
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
    # Get the metrics from the process_monitor.py file
    # This ensures plugin.json stays in sync with the actual metrics being collected
    
    cat > "${INSTALL_DIR}/plugin.json" << EOF
{
  "__license": "MIT License, Copyright (c) 2025 laplaque/instana_plugins Contributors",
  "name": "${PLUGIN_NAME}",
  "version": "1.0.0",
  "type": "custom",
  "entity": {
    "type": "microstrategy_mstrsvr"
  },
  "metrics": {
    "cpu_usage": {
      "displayName": "CPU Usage",
      "unit": "%",
      "description": "Total CPU usage percentage across all ${PROCESS_NAME} processes"
    },
    "memory_usage": {
      "displayName": "Memory Usage",
      "unit": "MB",
      "description": "Total memory usage across all ${PROCESS_NAME} processes"
    },
    "process_count": {
      "displayName": "Process Count",
      "unit": "count",
      "description": "Number of running ${PROCESS_NAME} processes"
    },
    "disk_read_bytes": {
      "displayName": "Disk Read",
      "unit": "bytes",
      "description": "Total bytes read from disk by ${PROCESS_NAME} processes"
    },
    "disk_write_bytes": {
      "displayName": "Disk Write",
      "unit": "bytes",
      "description": "Total bytes written to disk by ${PROCESS_NAME} processes"
    },
    "open_file_descriptors": {
      "displayName": "Open File Descriptors",
      "unit": "count",
      "description": "Total number of open file descriptors across all ${PROCESS_NAME} processes"
    },
    "thread_count": {
      "displayName": "Thread Count",
      "unit": "count",
      "description": "Total number of threads across all ${PROCESS_NAME} processes"
    },
    "voluntary_ctx_switches": {
      "displayName": "Voluntary Context Switches",
      "unit": "count",
      "description": "Total voluntary context switches across all ${PROCESS_NAME} processes"
    },
    "nonvoluntary_ctx_switches": {
      "displayName": "Non-voluntary Context Switches",
      "unit": "count",
      "description": "Total non-voluntary context switches across all ${PROCESS_NAME} processes"
    },
    "monitored_pids": {
      "displayName": "Monitored PIDs",
      "unit": "text",
      "description": "List of monitored ${PROCESS_NAME} process IDs"
    }
  },
  "otel": {
    "enabled": true,
    "description": "This plugin uses OpenTelemetry for metrics collection"
  }
}
EOF

    echo -e "Created plugin.json with OpenTelemetry support"
}

function copy_sensor_files {
    # Get the directory of this script
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    
    # Copy sensor.py from the project
    cp "${SCRIPT_DIR}/sensor.py" "${INSTALL_DIR}/sensor.py"
    
    # Create __init__.py in the installation directory
    touch "${INSTALL_DIR}/__init__.py"
    
    # Create common directory
    mkdir -p "${INSTALL_DIR}/common"
    
    # Copy common files
    COMMON_DIR="${SCRIPT_DIR}/../common"
    cp "${COMMON_DIR}/__init__.py" "${INSTALL_DIR}/common/__init__.py"
    cp "${COMMON_DIR}/process_monitor.py" "${INSTALL_DIR}/common/process_monitor.py"
    cp "${COMMON_DIR}/otel_connector.py" "${INSTALL_DIR}/common/otel_connector.py"
    cp "${COMMON_DIR}/base_sensor.py" "${INSTALL_DIR}/common/base_sensor.py"
    cp "${COMMON_DIR}/logging_config.py" "${INSTALL_DIR}/common/logging_config.py"
    
    echo -e "Copied sensor files from project to ${INSTALL_DIR}"
}

function create_sample_config {
    cat > "${INSTALL_DIR}/sample-config.yaml" << EOF
# Sample configuration for Instana agent
# MIT License - Copyright (c) 2025 laplaque/instana_plugins Contributors
#
# Add this to your Instana agent configuration.yaml file

com.instana.plugin.python:
  enabled: true
  custom_sensors:
    - id: microstrategy_mstrsvr
      path: ${INSTALL_DIR}/sensor.py
      interval: 30000  # Run every 30 seconds (adjust as needed)
      args: "--agent-host localhost --agent-port 4317 --interval 30"

# OpenTelemetry configuration (if using Instana with OpenTelemetry)
com.instana.tracing:
  opentelemetry:
    enabled: true
    otlp:
      enabled: true
      receiver:
        port: 4317  # Default OTLP gRPC port
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
copy_sensor_files
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
