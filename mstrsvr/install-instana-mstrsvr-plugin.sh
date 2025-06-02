#!/bin/bash
#
# MIT License
#
# Copyright (c) 2025 laplaque/instana_plugins Contributors
#
# This file is part of the Instana Plugins collection.
# Version: 0.0.12
#

# MSTRSvr Instana Plugin Installer
# --------------------------------

# Set error handling
set -e

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function for cleanup on error
function cleanup {
    echo -e "${RED}Installation failed. Cleaning up...${NC}"
    # Add cleanup code here if needed
}
trap cleanup ERR

# Define script directories early
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$( dirname "$SCRIPT_DIR" )"

# Default installation directories
DEFAULT_INSTANA_DIR="/opt/instana/agent"
DEFAULT_PLUGIN_DIR="${DEFAULT_INSTANA_DIR}/plugins/custom_sensors/microstrategy_mstrsvr"

# Define plugin-specific variables
PROCESS_NAME="MSTRSvr"
PLUGIN_NAME="com.instana.plugin.python.microstrategy_mstrsvr"

# Define usage function
function show_usage {
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "Install the MicroStrategy ${PROCESS_NAME} monitoring plugin for Instana"
    echo -e "\nOptions:"
    echo -e "  -d, --directory DIR    Installation directory (default: ${DEFAULT_PLUGIN_DIR})"
    echo -e "  -r, --restart          Restart service after installation"
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

echo -e "${GREEN}MicroStrategy ${PROCESS_NAME} Instana Plugin Installer${NC}"
echo -e "Installation directory: ${INSTALL_DIR}"

COMMON_DIR="${INSTALL_DIR}/common"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is required but not installed. Please install Python 3 and try again.${NC}"
    exit 1
fi

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

# Function to copy plugin.json
function copy_plugin_json {
    cp "${SCRIPT_DIR}/plugin.json" "${INSTALL_DIR}/plugin.json"
    echo -e "Copied plugin.json from project to ${INSTALL_DIR}"
}

# Function to copy sensor files
function copy_sensor_files {
    # Copy sensor.py from the project
    cp "${SCRIPT_DIR}/sensor.py" "${INSTALL_DIR}/sensor.py"
    
    # Create __init__.py in the installation directory
    touch "${INSTALL_DIR}/__init__.py"
    
    # Create common directory
    mkdir -p "${INSTALL_DIR}/common"
    
    # Copy common files
    COMMON_DIR="${INSTALL_DIR}/common"
    cp "${PARENT_DIR}/common/__init__.py" "${COMMON_DIR}/__init__.py"
    cp "${PARENT_DIR}/common/process_monitor.py" "${COMMON_DIR}/process_monitor.py"
    cp "${PARENT_DIR}/common/otel_connector.py" "${COMMON_DIR}/otel_connector.py"
    cp "${PARENT_DIR}/common/base_sensor.py" "${COMMON_DIR}/base_sensor.py"
    cp "${PARENT_DIR}/common/logging_config.py" "${COMMON_DIR}/logging_config.py"
    
    echo -e "Copied sensor files from project to ${INSTALL_DIR}"
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
copy_plugin_json
copy_sensor_files

# Set permissions
echo -e "Setting permissions..."
chmod 755 "${INSTALL_DIR}/sensor.py"
chmod 644 "${INSTALL_DIR}/plugin.json"
chmod 644 "${COMMON_DIR}"/*.py

# Check dependencies
echo -e "Checking if dependencies are already installed..."
if python3 "$PARENT_DIR/common/check_dependencies.py" --requirements "$PARENT_DIR/common/requirements.txt" --quiet; then
    echo -e "${GREEN}All dependencies are already satisfied. Skipping installation.${NC}"
else
    echo -e "Installing dependencies..."
    if [ "$EUID" -ne 0 ]; then
        echo -e "${YELLOW}Installing dependencies for non-root user...${NC}"
        pip3 install --user -r "$PARENT_DIR/common/requirements.txt"
    else
        pip3 install -r "$PARENT_DIR/common/requirements.txt"
    fi
fi

# Create a systemd service file
SERVICE_NAME="instana-${PROCESS_NAME,,}-sensor"  # lowercase process name
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

if [ "$EUID" -eq 0 ]; then
    if [ -f "$SERVICE_FILE" ]; then
        echo -e "${YELLOW}Service file already exists. Skipping...${NC}"
    else
        echo -e "Creating systemd service file..."
        cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Instana ${PROCESS_NAME} Sensor
After=network.target

[Service]
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/sensor.py
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1
Environment="PYTHONPATH=${INSTALL_DIR}"

[Install]
WantedBy=multi-user.target
EOF

        echo -e "Enabling service..."
        systemctl daemon-reload
        systemctl enable ${SERVICE_NAME}.service
        
        # Start the service if requested
        if [ "$RESTART_AGENT" = true ]; then
            echo -e "Starting service..."
            systemctl start ${SERVICE_NAME}.service
        fi
    fi
else
    # For non-root users, create user-level systemd service
    echo -e "${YELLOW}Non-root installation detected. To run the sensor without root:${NC}"
    echo -e "1. Create a user-level systemd service in ~/.config/systemd/user/"
    echo -e "2. Or use cron to schedule the sensor:"
    echo -e "   * * * * * env PYTHONPATH=${INSTALL_DIR} python3 ${INSTALL_DIR}/sensor.py --run-once"
    echo -e "3. Or run manually with:"
    echo -e "   env PYTHONPATH=${INSTALL_DIR} python3 ${INSTALL_DIR}/sensor.py"
    
    # Create a sample user-level systemd service file
    USER_SERVICE_DIR="$HOME/.config/systemd/user"
    if [ ! -d "$USER_SERVICE_DIR" ]; then
        mkdir -p "$USER_SERVICE_DIR"
    fi
    
    USER_SERVICE_FILE="$USER_SERVICE_DIR/${SERVICE_NAME}.service"
    echo -e "Creating sample user-level systemd service at ${USER_SERVICE_FILE}"
    cat > "$USER_SERVICE_FILE" << EOF
[Unit]
Description=Instana ${PROCESS_NAME} Sensor (User Service)
After=network.target

[Service]
ExecStart=/usr/bin/python3 ${INSTALL_DIR}/sensor.py
Restart=always
Environment=PYTHONUNBUFFERED=1
Environment="PYTHONPATH=${INSTALL_DIR}"

[Install]
WantedBy=default.target
EOF
    echo -e "To enable and start the user service:"
    echo -e "systemctl --user daemon-reload"
    echo -e "systemctl --user enable ${SERVICE_NAME}.service"
    echo -e "systemctl --user start ${SERVICE_NAME}.service"
fi

echo -e "${GREEN}MicroStrategy ${PROCESS_NAME} Instana Plugin installed successfully!${NC}"
echo -e "Installation directory: ${INSTALL_DIR}"
echo -e "\nTo test the plugin, run: ${INSTALL_DIR}/sensor.py --run-once --log-level=DEBUG"

if [ "$EUID" -eq 0 ]; then
    echo -e "To check the service status, run: systemctl status ${SERVICE_NAME}.service"
fi

exit 0
