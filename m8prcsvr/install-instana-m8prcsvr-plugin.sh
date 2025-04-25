#!/bin/bash
# Install script for the Instana M8PrcSvr plugin

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$( dirname "$SCRIPT_DIR" )"

echo "Installing M8PrcSvr plugin..."

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

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
ExecStart=/usr/bin/python3 $SCRIPT_DIR/sensor.py
Restart=always
User=root
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
EOF

    echo "Enabling and starting service..."
    systemctl daemon-reload
    systemctl enable instana-m8prcsvr-sensor.service
    systemctl start instana-m8prcsvr-sensor.service
fi

echo "Installation complete!"
echo "To check the status of the service, run: systemctl status instana-m8prcsvr-sensor.service"
