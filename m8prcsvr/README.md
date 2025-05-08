# M8PrcSvr Sensor

This sensor monitors the MicroStrategy M8PrcSvr process and reports metrics to Instana.

## Installation

Run the installation script with default settings:

```bash
sudo ./install-instana-m8prcsvr-plugin.sh
```

Or specify a custom installation directory:

```bash
sudo ./install-instana-m8prcsvr-plugin.sh -d /path/to/custom/directory
```

For all available options:

```bash
sudo ./install-instana-m8prcsvr-plugin.sh --help
```

### Installation Options

The installation script supports these command-line options:

- `-d, --directory DIR` : Specify a custom installation directory (default: `/opt/instana/agent/plugins/custom_sensors/microstrategy_m8prcsvr`)
- `-r, --restart` : Start the service immediately after installation
- `-h, --help` : Show help message and exit

## Configuration

The sensor can be configured using command-line arguments:

- `--agent-host`: Instana agent host (default: localhost)
- `--agent-port`: Instana agent port (default: 4317)
- `--interval`: Metrics collection interval in seconds (default: 60)
- `--once`: Run the sensor once and exit
- `--log-level`: Log level (default: INFO)
- `--log-file`: Log file path (default: m8prcsvr-sensor.log)

## Usage

```bash
python sensor.py [options]
```
