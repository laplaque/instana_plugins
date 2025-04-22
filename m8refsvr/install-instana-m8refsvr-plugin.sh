#!/bin/bash
# Install script for the Instana M8RefSvr plugin

set -e

# Default installation directory
INSTALL_DIR="/opt/instana/agent/plugins/custom_sensors"
PLUGIN_NAME="microstrategy_m8refsvr"
PLUGIN_DIR="${INSTALL_DIR}/${PLUGIN_NAME}"
COMMON_DIR="${INSTALL_DIR}/common"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

# Create plugin directories
echo "Creating plugin directories..."
mkdir -p "${PLUGIN_DIR}"
mkdir -p "${COMMON_DIR}"

# Copy plugin files
echo "Copying plugin files..."
cp "$(dirname "$0")/sensor.py" "${PLUGIN_DIR}/"
cp "$(dirname "$0")/plugin.json" "${PLUGIN_DIR}/"

# Copy common files
echo "Copying common files..."
cp "$(dirname "$0")/../common/process_monitor.py" "${COMMON_DIR}/"
cp "$(dirname "$0")/../common/otel_connector.py" "${COMMON_DIR}/"
cp "$(dirname "$0")/../common/base_sensor.py" "${COMMON_DIR}/"
cp "$(dirname "$0")/../common/logging_config.py" "${COMMON_DIR}/"
cp "$(dirname "$0")/../common/__init__.py" "${COMMON_DIR}/"

# Create __init__.py if it doesn't exist
touch "${PLUGIN_DIR}/__init__.py"

# Set permissions
echo "Setting permissions..."
chmod 755 "${PLUGIN_DIR}/sensor.py"
chmod 644 "${PLUGIN_DIR}/plugin.json"
chmod 644 "${COMMON_DIR}"/*.py

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/instana-m8refsvr-sensor.service"
echo "Creating systemd service file: ${SERVICE_FILE}"

cat > "${SERVICE_FILE}" << EOF
[Unit]
Description=Instana M8RefSvr Sensor
After=network.target instana-agent.service

[Service]
Type=simple
User=root
Environment="PYTHONPATH=${INSTALL_DIR}"
ExecStart=${PLUGIN_DIR}/sensor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
echo "Configuring systemd service..."
systemctl daemon-reload
systemctl enable instana-m8refsvr-sensor.service
systemctl start instana-m8refsvr-sensor.service

echo "Installation complete!"
echo "M8RefSvr plugin has been installed and started."
echo "Check status with: systemctl status instana-m8refsvr-sensor.service"
