# Instana MicroStrategy MSTRSvr Monitor Plugin

A custom Instana plugin for monitoring MicroStrategy MSTRSvr processes (Intelligence Server). This plugin collects process-specific metrics including CPU usage, memory usage, disk I/O, file descriptors, thread count, and context switches.

## Features

- Process-specific monitoring for MicroStrategy MSTRSvr (Intelligence Server)
- Case-insensitive process detection
- Process resource usage tracking
- OpenTelemetry integration for metrics and traces
- Easy installation with automatic configuration

## Metrics Collected

- CPU Usage
- Memory Usage
- Process Count
- Disk Read/Write Bytes
- Open File Descriptors
- Thread Count
- Voluntary/Non-voluntary Context Switches

## Requirements

- Instana Agent 1.2.0 or higher
- Python 3.6 or higher
- OpenTelemetry Python packages
- MicroStrategy environment with MSTRSvr processes

## Installation

Use the installation script to easily deploy the plugin:

```bash
# Clone the repository
git clone https://github.com/laplaque/instana_plugins.git
cd instana_plugins/mstrsvr

# Run the installer script
sudo ./install-instana-mstrsvr-plugin.sh
```

## Configuration

The installer will attempt to add the required configuration to your Instana agent. If that fails, you can manually add the following to your Instana agent configuration:

```yaml
com.instana.plugin.python:
  enabled: true
  custom_sensors:
    - id: microstrategy_mstrsvr
      path: /opt/instana/agent/plugins/custom_sensors/microstrategy_mstrsvr/sensor.py
      interval: 30000  # Run every 30 seconds
```

## Testing

To test if the plugin is correctly detecting MSTRSvr processes:

```bash
/opt/instana/agent/plugins/custom_sensors/microstrategy_mstrsvr/sensor.py
```

This should output JSON with the collected metrics if processes are found.

## How It Works

The plugin uses the `common/process_monitor.py` module to collect metrics about MSTRSvr processes and the `common/otel_connector.py` module to send these metrics to Instana using OpenTelemetry.

The sensor runs continuously, collecting metrics every minute and sending them to the Instana agent.

## Troubleshooting

If you're not seeing metrics in Instana:

1. Check if the MSTRSvr process is running: `ps aux | grep -i mstrsvr`
2. Verify the sensor is running: `ps aux | grep microstrategy_mstrsvr`
3. Check the Instana agent logs for errors
4. Run the sensor manually with debug logging: `PYTHONPATH=/opt/instana/agent/plugins/custom_sensors /opt/instana/agent/plugins/custom_sensors/microstrategy_mstrsvr/sensor.py`

## Release Notes

For a detailed history of changes and improvements, see the [Release Notes](../RELEASE_NOTES.md).

#This should output JSON with the collected metrics if processes are found.

## How It Works

The plugin uses the `common/process_monitor.py` module to collect metrics about MSTRSvr processes and the `common/otel_connector.py` module to send these metrics to Instana using OpenTelemetry.

The sensor runs continuously, collecting metrics every minute and sending them to the Instana agent.

## Troubleshooting

If you're not seeing metrics in Instana:

1. Check if the MSTRSvr process is running: `ps aux | grep -i mstrsvr`
2. Verify the sensor is running: `ps aux | grep microstrategy_mstrsvr`
3. Check the Instana agent logs for errors
4. Run the sensor manually with debug logging: `PYTHONPATH=/opt/instana/agent/plugins/custom_sensors /opt/instana/agent/plugins/custom_sensors/microstrategy_mstrsvr/sensor.py`

## License

This plugin is licensed under the MIT License.

Copyright © 2025 laplaque/instana_plugins Contributors

