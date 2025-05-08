#!/bin/bash
# Install script for the Instana M8PrcSvr plugin

set -e

# Default installation directories
DEFAULT_INSTANA_DIR="/opt/instana/agent"
DEFAULT_PLUGIN_DIR="${DEFAULT_INSTANA_DIR}/plugins/custom_sensors/microstrategy_m8prcsvr"

# Define usage function
function show_usage {
    echo "Usage: $0 [OPTIONS]"
    echo "Install the MicroStrategy M8PrcSvr monitoring plugin for Instana"
    echo ""
    echo "Options:"
    echo "  -d, --directory DIR    Installation directory (default: ${DEFAULT_PLUGIN_DIR})"
    echo "  -r, --restart          Restart Instana agent after installation"
    echo "  -h, --help             Show this help message and exit"
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
            echo "Error: Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$( dirname "$SCRIPT_DIR" )"
COMMON_DIR="${INSTALL_DIR}/common"

echo "Installing M8PrcSvr plugin to ${INSTALL_DIR}..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Create plugin directories
echo "Creating plugin directories..."
mkdir -p "${INSTALL_DIR}"
mkdir -p "${COMMON_DIR}"

# Copy plugin files
echo "Copying plugin files..."
cp "${SCRIPT_DIR}/sensor.py" "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/plugin.json" "${INSTALL_DIR}/"

# Copy common files
echo "Copying common files..."
cp "${PARENT_DIR}/common/process_monitor.py" "${COMMON_DIR}/"
cp "${PARENT_DIR}/common/otel_connector.py" "${COMMON_DIR}/"
cp "${PARENT_DIR}/common/base_sensor.py" "${COMMON_DIR}/"
cp "${PARENT_DIR}/common/logging_config.py" "${COMMON_DIR}/"
cp "${PARENT_DIR}/common/__init__.py" "${COMMON_DIR}/"

# Create __init__.py if it doesn't exist
touch "${INSTALL_DIR}/__init__.py"

# Set permissions
echo "Setting permissions..."
chmod 755 "${INSTALL_DIR}/sensor.py"
chmod 644 "${INSTALL_DIR}/plugin.json"
chmod 644 "${COMMON_DIR}"/*.py

# Install dependencies
echo "Installing dependencies..."
pip3 install -r "$PARENT_DIR/common/requirements.txt"

# Create a systemd service file
SERVICE_FILE="/etc/systemd/system/instana-m8prcsvr-sensor.service"
if [ -f "$SERVICE_FILE" ]; then
    echo "Service file already exists. Skipping..."
else
    echo "Creating systemd service file..."
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Instana M8PrcSvr Sensor
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

    echo "Enabling service..."
    systemctl daemon-reload
    systemctl enable instana-m8prcsvr-sensor.service
    
    # Start the service if requested
    if [ "$RESTART_AGENT" = true ]; then
        echo "Starting service..."
        systemctl start instana-m8prcsvr-sensor.service
    fi
fi

echo "Installation complete!"
echo "M8PrcSvr plugin has been installed to ${INSTALL_DIR}"
echo "To check the status of the service, run: systemctl status instana-m8prcsvr-sensor.service"
