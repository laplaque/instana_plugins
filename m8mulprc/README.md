# M8MulPrc Plugin for Instana

A custom Instana plugin for monitoring MicroStrategy M8MulPrc processes. This plugin collects process-specific metrics and sends them to Instana using OpenTelemetry.

## Overview

The M8MulPrc plugin monitors the MicroStrategy Multi-Process Server component, providing real-time visibility into its resource usage and performance characteristics.

## Features

- Real-time monitoring of MicroStrategy M8MulPrc processes
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
- OpenTelemetry Python packages
- MicroStrategy environment with M8MulPrc processes

## Installation

Use the installation script to easily deploy the plugin:

```bash
# Clone the repository
git clone https://github.com/laplaque/instana_plugins.git
cd instana_plugins/m8mulprc

# Run the installer script
sudo ./install-instana-m8mulprc-plugin.sh
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
   mkdir -p ~/instana-plugins/custom_sensors/microstrategy_m8mulprc
   mkdir -p ~/instana-plugins/custom_sensors/common
   ```

2. Copy the necessary files:
   ```bash
   cp -r m8mulprc/* ~/instana-plugins/custom_sensors/microstrategy_m8mulprc/
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
   * * * * * PYTHONPATH=/home/yourusername/instana-plugins/custom_sensors /home/yourusername/instana-plugins/custom_sensors/microstrategy_m8mulprc/sensor.py
   ```

### Process Monitoring Permissions

The plugin needs access to process information. If running without root:

1. Ensure your user has permission to read `/proc` entries for the M8MulPrc processes
2. If the M8MulPrc processes run as a different user, you may need to:
   - Run the Instana agent as the same user
   - Use Linux capabilities to grant specific permissions:
     ```bash
     sudo setcap cap_dac_read_search,cap_sys_ptrace+ep ~/instana-plugins/custom_sensors/microstrategy_m8mulprc/sensor.py
     ```
   - Adjust process group permissions to allow monitoring

## Configuration

The installer will automatically configure your Instana agent. If manual configuration is needed, add the following to your Instana agent configuration:

```yaml
com.instana.plugin.python:
  enabled: true
  custom_sensors:
    - id: microstrategy_m8mulprc
      path: /opt/instana/agent/plugins/custom_sensors/microstrategy_m8mulprc/sensor.py
      interval: 30000  # Run every 30 seconds
```

## Testing

To verify the plugin is correctly detecting M8MulPrc processes:

```bash
/opt/instana/agent/plugins/custom_sensors/microstrategy_m8mulprc/sensor.py
```

This will output JSON with the collected metrics if processes are found.

## How It Works

The plugin uses:
- `common/process_monitor.py` to collect metrics about M8MulPrc processes
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
   sudo systemctl edit instana-m8mulprc-sensor
   ```
   Add the following to override the default interval (in seconds):
   ```
   [Service]
   Environment="COLLECTION_INTERVAL=30"
   ```

2. **When running manually**:
   ```bash
   COLLECTION_INTERVAL=15 /opt/instana/agent/plugins/custom_sensors/microstrategy_m8mulprc/sensor.py
   ```

3. **In Instana agent configuration** (if using agent plugin scheduling):
   ```yaml
   com.instana.plugin.python:
     enabled: true
     custom_sensors:
       - id: microstrategy_m8mulprc
         path: /opt/instana/agent/plugins/custom_sensors/microstrategy_m8mulprc/sensor.py
         interval: 30000  # 30 seconds in milliseconds
   ```

### One-time Execution

For testing or ad-hoc monitoring, you can run the sensor once:

```bash
/opt/instana/agent/plugins/custom_sensors/microstrategy_m8mulprc/sensor.py --run-once
```

### Recommended Frequencies

- **Standard monitoring**: 60 seconds (default)
- **Detailed monitoring**: 15-30 seconds
- **Minimal overhead**: 300 seconds (5 minutes)

The optimal frequency depends on your monitoring needs and the performance impact on your system. More frequent collection provides better visibility but increases overhead.

## Troubleshooting

If metrics aren't appearing in Instana:

1. Verify the M8MulPrc process is running: `ps aux | grep -i m8mulprc`
2. Check if the sensor is running: `ps aux | grep microstrategy_m8mulprc`
3. Examine the Instana agent logs for errors
4. Run the sensor manually with debug logging:
   ```bash
   PYTHONPATH=/opt/instana/agent/plugins/custom_sensors LOG_LEVEL=DEBUG /opt/instana/agent/plugins/custom_sensors/microstrategy_m8mulprc/sensor.py
   ```
5. Verify the Instana agent is accepting OTLP connections on port 4317

## Release Notes

For a detailed history of changes and improvements, see the [Release Notes](../RELEASE_NOTES.md).

## License

This plugin is licensed under the MIT License.

Copyright © 2025 laplaque/instana_plugins Contributors
