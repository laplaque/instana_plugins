# M8RefSvr Plugin for Instana

A custom Instana plugin for monitoring MicroStrategy M8RefSvr processes. This plugin collects process-specific metrics and sends them to Instana using OpenTelemetry.

## Overview

The M8RefSvr plugin monitors the MicroStrategy Reference Server component, providing real-time visibility into its resource usage and performance characteristics.

## Features

- Real-time monitoring of MicroStrategy M8RefSvr processes
- Case-insensitive process detection for flexibility
- Detailed resource usage metrics collection
- OpenTelemetry integration for seamless Instana reporting
- Lightweight with minimal performance impact
- Configurable monitoring intervals

## Metrics Collected

- CPU Usage (%)
- Memory Usage (RSS, VMS)
- Process Count
- Disk I/O (read/write bytes)
- Open File Descriptors
- Thread Count
- Context Switches (voluntary/involuntary)

## Requirements

- Instana Agent 1.2.0 or higher
- Python 3.6 or higher
- OpenTelemetry Python packages:

  ```bash
  pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
  ```

- MicroStrategy environment with M8RefSvr processes

## Installation

Use the installation script to easily deploy the plugin:

```bash
# Clone the repository
git clone https://github.com/laplaque/instana_plugins.git
cd instana_plugins/m8refsvr

# Run the installer script with default settings
sudo ./install-instana-m8refsvr-plugin.sh

# Or specify a custom installation directory
sudo ./install-instana-m8refsvr-plugin.sh -d /path/to/custom/directory

# For all available options
sudo ./install-instana-m8refsvr-plugin.sh --help
```

### Installation Options

The installation script supports these command-line options:

- `-d, --directory DIR` : Specify a custom installation directory (default: `/opt/instana/agent/plugins/custom_sensors/microstrategy_m8refsvr`)
- `-r, --restart` : Start the service immediately after installation
- `-h, --help` : Show help message and exit

### Permissions Requirements

The installation script requires elevated privileges (sudo) to:

1. Copy files to the Instana agent directory (typically `/opt/instana/agent/plugins/custom_sensors/`)
2. Set appropriate file permissions
3. Create and enable a systemd service for automatic startup

### Installing Without Root Privileges

If you need to install without sudo access:

1. Create a custom sensors directory in your user space:

   ```bash
   mkdir -p ~/instana-plugins/custom_sensors/microstrategy_m8refsvr
   mkdir -p ~/instana-plugins/custom_sensors/common
   ```

2. Copy the necessary files:

   ```bash
   cp -r m8refsvr/* ~/instana-plugins/custom_sensors/microstrategy_m8refsvr/
   cp -r common/* ~/instana-plugins/custom_sensors/common/
   ```

3. Configure the Instana agent to look for plugins in this directory by adding to `configuration.yaml`:

   ```yaml
   com.instana.plugin.python:
     enabled: true
     custom_sensors_path: /home/yourusername/instana-plugins/custom_sensors
   ```

4. Set up a user-level service or cron job to run the sensor:

   ```bash
   # Example crontab entry to run every minute
   * * * * * PYTHONPATH=/home/yourusername/instana-plugins/custom_sensors /home/yourusername/instana-plugins/custom_sensors/microstrategy_m8refsvr/sensor.py
   ```

### Process Monitoring Permissions

The plugin needs access to process information. If running without root:

1. Ensure your user has permission to read `/proc` entries for the M8RefSvr processes
2. If the M8RefSvr processes run as a different user, you may need to:
   - Run the Instana agent as the same user
   - Use Linux capabilities to grant specific permissions:

     ```bash
     sudo setcap cap_dac_read_search,cap_sys_ptrace+ep ~/instana-plugins/custom_sensors/microstrategy_m8refsvr/sensor.py
     ```

   - Adjust process group permissions to allow monitoring

## Configuration

The installer will automatically set up the plugin to run as a systemd service. The plugin uses OpenTelemetry to send metrics to the Instana agent.

### Instana Agent Configuration

Ensure your Instana agent is configured to receive OpenTelemetry data (enabled by default in Instana agent version 1.1.726 or higher):

```yaml
com.instana.plugin.opentelemetry:
  grpc:
    enabled: true
  http:
    enabled: true
```

The Instana agent will listen for OpenTelemetry data on:

- Port 4317 for gRPC connections (used by default)
- Port 4318 for HTTP/HTTPS connections

### TLS Encryption

To enable TLS encryption for secure communication with the Instana agent:

1. Configure the Instana agent with TLS certificates:
   - Place certificate and key files in `<agent_installation>/etc/certs/`
   - By default, the agent looks for `tls.crt` and `tls.key` files
   - Restart the agent after adding certificates

2. Configure the sensor to use TLS by setting environment variables:

   ```bash
   USE_TLS=true \
   CA_CERT_PATH=/path/to/ca.crt \
   CLIENT_CERT_PATH=/path/to/client.crt \
   CLIENT_KEY_PATH=/path/to/client.key \
   /opt/instana/agent/plugins/custom_sensors/microstrategy_m8refsvr/sensor.py
   ```

3. For systemd service, add these environment variables to the service configuration:

   ```bash
   sudo systemctl edit instana-m8refsvr-sensor
   ```

   Add the following:

   ```ini
   [Service]
   Environment="USE_TLS=true"
   Environment="CA_CERT_PATH=/path/to/ca.crt"
   Environment="CLIENT_CERT_PATH=/path/to/client.crt"
   Environment="CLIENT_KEY_PATH=/path/to/client.key"
   ```

Note: When TLS is enabled, the plugin automatically uses `https://` protocol for connections.

## Testing

To verify the plugin is correctly detecting M8RefSvr processes:

```bash
/opt/instana/agent/plugins/custom_sensors/microstrategy_m8refsvr/sensor.py
```

This will output JSON with the collected metrics if processes are found.

## How It Works

The plugin uses:

- `common/process_monitor.py` to collect metrics about M8RefSvr processes
- `common/otel_connector.py` to send these metrics to Instana using OpenTelemetry

The sensor runs continuously, collecting metrics at configurable intervals and sending them to the Instana agent.

## Scheduling and Frequency

### Default Scheduling

When installed using the installation script, the plugin is configured as a systemd service that:

- Starts automatically at system boot
- Runs continuously in the background
- Collects metrics every 60 seconds by default

### Customizing the Collection Frequency

You can adjust how often metrics are collected in several ways:

1. **Modify the systemd service**:

   ```bash
   sudo systemctl edit instana-m8refsvr-sensor
   ```

   Add the following to override the default interval (in seconds):

   ```ini
   [Service]
   Environment="COLLECTION_INTERVAL=30"
   ```

2. **When running manually**:

   ```bash
   COLLECTION_INTERVAL=15 /opt/instana/agent/plugins/custom_sensors/microstrategy_m8refsvr/sensor.py
   ```

3. **Using a custom scheduler**:
   You can create a custom scheduling mechanism using systemd timers or more sophisticated cron configurations.

### One-time Execution

For testing or ad-hoc monitoring, you can run the sensor once:

```bash
/opt/instana/agent/plugins/custom_sensors/microstrategy_m8refsvr/sensor.py --run-once
```

### Recommended Frequencies

- **Standard monitoring**: 60 seconds (default)
- **Detailed monitoring**: 15-30 seconds
- **Minimal overhead**: 300 seconds (5 minutes)

The optimal frequency depends on your monitoring needs and the performance impact on your system. More frequent collection provides better visibility but increases overhead.

## Troubleshooting

If metrics aren't appearing in Instana:

1. Verify the M8RefSvr process is running: `ps aux | grep -i m8refsvr`
2. Check if the sensor is running: `ps aux | grep microstrategy_m8refsvr`
3. Examine the Instana agent logs for errors
4. Run the sensor manually with debug logging:

   ```bash
   PYTHONPATH=/opt/instana/agent/plugins/custom_sensors LOG_LEVEL=DEBUG /opt/instana/agent/plugins/custom_sensors/microstrategy_m8refsvr/sensor.py
   ```

5. Verify the Instana agent is accepting OTLP connections on port 4317

### Common Issues

1. **Process Not Found**:
   - If you see "No processes found matching 'M8RefSvr'" in the logs, verify that:
     - The MicroStrategy M8RefSvr process is running
     - The process name matches (case-insensitive matching is used)
     - You have permissions to view process information

2. **Permission Issues**:
   - If you see permission errors when accessing `/proc` files:
     - Run the sensor with elevated privileges
     - Ensure the user running the sensor has access to process information

3. **Connection to Instana Agent**:
   - If metrics aren't appearing in Instana:
     - Verify the agent host and port are correct
     - Check that the Instana agent is running
     - Ensure OpenTelemetry is enabled in the agent configuration

4. **Debugging**:
   - Run the sensor with `--log-level=DEBUG` for more detailed logs:

     ```bash
     ./sensor.py --log-level=DEBUG
     ```

   - Run once with `--once` flag to check for immediate issues:

     ```bash
     ./sensor.py --once --log-level=DEBUG
     ```

5. **Log File Location**:
   - By default, logs are written to `app.log` in the current directory
   - Specify a custom log file with `--log-file`:

     ```bash
     ./sensor.py --log-file=/var/log/instana/m8refsvr.log
     ```

### Edge Cases and Limitations

1. **Multiple M8RefSvr Instances**:
   - The plugin monitors all processes matching the "M8RefSvr" pattern
   - If you have multiple M8RefSvr instances, metrics will be aggregated
   - To monitor instances separately, modify the process name pattern

2. **Resource Constraints**:
   - On systems with limited resources, consider increasing the collection interval
   - For production environments with many processes, 60 seconds is recommended
   - Memory usage increases with the number of monitored processes

3. **Process Restarts**:
   - If M8RefSvr processes restart between collections, some metrics will reset
   - Disk I/O and context switch counters will start from zero after restart
   - Process count metrics will remain accurate even during restarts

4. **Virtualized Environments**:
   - In virtualized environments, CPU metrics may be relative to the VM allocation
   - Container environments may have limited access to host metrics
   - Some metrics may be unavailable in certain container runtimes

## Release Notes

For a detailed history of changes and improvements, see the [Release Notes](../RELEASE_NOTES.md).

## License

This plugin is licensed under the MIT License.

Copyright © 2025 laplaque/instana_plugins Contributors
