# MstrSvr Plugin for Instana

A custom Instana plugin for monitoring Strategy₿ Intelligence Server (MstrSvr) processes. This plugin collects process-specific metrics and sends them to Instana using OpenTelemetry.

## Overview

The MstrSvr plugin monitors the Strategy₿ Intelligence Server component, providing real-time visibility into its resource usage and performance characteristics.

## Features

- Real-time monitoring of Strategy₿ Intelligence Server processes
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

- Strategy₿ environment with Intelligence Server processes

## Installation

Use the installation script to easily deploy the plugin:

```bash
# Clone the repository
git clone https://github.com/laplaque/instana_plugins.git
cd instana_plugins/mstrsvr

# Run the installer script
sudo ./install-instana-mstrsvr-plugin.sh
```

### Permissions Requirements

The installation script requires elevated privileges (sudo) to:

1. Copy files to the Instana agent directory (typically `/opt/instana/agent/plugins/custom_sensors/`)
2. Set appropriate file permissions
3. Create and enable a systemd service for automatic startup

### Installing Without Root Privileges

If you need to install without sudo access:

1. Create a custom sensors directory in your user space:

   ```bash
   mkdir -p ~/instana-plugins/custom_sensors/microstrategy_mstrsvr
   mkdir -p ~/instana-plugins/custom_sensors/common
   ```

2. Copy the necessary files:

   ```bash
   cp -r mstrsvr/* ~/instana-plugins/custom_sensors/microstrategy_mstrsvr/
   cp -r common/* ~/instana-plugins/custom_sensors/common/
   ```

3. Ensure the Instana agent is configured to receive OpenTelemetry data by adding to `configuration.yaml` (enabled by default in Instana agent version 1.1.726 or higher):

   ```yaml
   com.instana.plugin.opentelemetry:
     grpc:
       enabled: true
     http:
       enabled: true
   ```

4. Set up a user-level service or cron job to run the sensor:

   ```bash
   # Example crontab entry to run every minute
   * * * * * env PYTHONPATH=/home/yourusername/instana-plugins/custom_sensors /home/yourusername/instana-plugins/custom_sensors/microstrategy_mstrsvr/sensor.py
   ```

### Process Monitoring Permissions

The plugin needs access to process information. If running without root:

1. Ensure your user has permission to read `/proc` entries for the MstrSvr processes
2. If the MstrSvr processes run as a different user, you may need to:
   - Run the Instana agent as the same user
   - Use Linux capabilities to grant specific permissions:

     ```bash
     sudo setcap cap_dac_read_search,cap_sys_ptrace+ep ~/instana-plugins/custom_sensors/microstrategy_mstrsvr/sensor.py
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
   /opt/instana/agent/plugins/custom_sensors/microstrategy_mstrsvr/sensor.py
   ```

3. For systemd service, add these environment variables to the service configuration:

   ```bash
   sudo systemctl edit instana-mstrsvr-sensor
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

To verify the plugin is correctly detecting MstrSvr processes:

```bash
/opt/instana/agent/plugins/custom_sensors/microstrategy_mstrsvr/sensor.py
```

This will output JSON with the collected metrics if processes are found.

## How It Works

The plugin uses:

- `common/process_monitor.py` to collect metrics about MstrSvr processes
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
   sudo systemctl edit instana-mstrsvr-sensor
   ```

   Add the following to override the default interval (in seconds):

   ```ini
   [Service]
   Environment="COLLECTION_INTERVAL=30"
   ```

2. **When running manually**:

   ```bash
   COLLECTION_INTERVAL=15 /opt/instana/agent/plugins/custom_sensors/microstrategy_mstrsvr/sensor.py
   ```

3. **Using a custom scheduler**:
   You can create a custom scheduling mechanism using systemd timers or more sophisticated cron configurations.

### One-time Execution

For testing or ad-hoc monitoring, you can run the sensor once:

```bash
/opt/instana/agent/plugins/custom_sensors/microstrategy_mstrsvr/sensor.py --run-once
```

### Recommended Frequencies

- **Standard monitoring**: 60 seconds (default)
- **Detailed monitoring**: 15-30 seconds
- **Minimal overhead**: 300 seconds (5 minutes)

The optimal frequency depends on your monitoring needs and the performance impact on your system. More frequent collection provides better visibility but increases overhead.

### Considerations for Intelligence Server

For Strategy₿ Intelligence Server, consider these factors when setting the collection frequency:

- **High-load production servers**: Use 60-120 seconds to minimize overhead
- **During peak usage periods**: Consider reducing frequency to 120-300 seconds
- **During troubleshooting**: Temporarily increase to 15-30 seconds for more detailed data
- **Development/Test environments**: 30-60 seconds provides a good balance

## Troubleshooting

If metrics aren't appearing in Instana:

1. Verify the MstrSvr process is running: `ps aux | grep -i mstrsvr`
2. Check if the sensor is running: `ps aux | grep microstrategy_mstrsvr`
3. Examine the Instana agent logs for errors
4. Run the sensor manually with debug logging:

   ```bash
   PYTHONPATH=/opt/instana/agent/plugins/custom_sensors LOG_LEVEL=DEBUG /opt/instana/agent/plugins/custom_sensors/microstrategy_mstrsvr/sensor.py
   ```

5. Verify the Instana agent is accepting OTLP connections on port 4317

### Common Issues

1. **Process Not Found**:
   - If you see "No processes found matching 'MstrSvr'" in the logs, verify that:
     - The Strategy₿ Intelligence Server process is running
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
     ./sensor.py --log-file=/var/log/instana/mstrsvr.log
     ```

### Edge Cases and Limitations

1. **High-Load Strategy₿ Environments**:
   - In high-load environments, the Intelligence Server may spawn many processes
   - Consider increasing the collection interval to reduce monitoring overhead
   - For servers with >50% CPU utilization, use 120-300 second intervals

2. **Clustered Environments**:
   - In clustered Strategy₿ environments, install the plugin on each node
   - Each node will report metrics independently to Instana
   - Metrics are not automatically aggregated across cluster nodes

3. **Memory-Intensive Workloads**:
   - For Intelligence Servers handling memory-intensive workloads:
     - Monitor the plugin's own resource usage
     - Consider using the `--once` flag with a custom scheduler for better control
     - Adjust collection frequency based on server load patterns

4. **Process Name Variations**:
   - Some Strategy₿ installations may use different process names
   - The plugin uses case-insensitive matching for "MstrSvr"
   - If your process name differs significantly, modify the sensor.py file

## Release Notes

For a detailed history of changes and improvements, see the [Release Notes](../docs/releases/RELEASE_NOTES.md).

## License

This plugin is licensed under the MIT License.

Copyright © 2025 laplaque/instana_plugins Contributors
