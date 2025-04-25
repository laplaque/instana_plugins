# M8PrcSvr Sensor

This sensor monitors the MicroStrategy M8PrcSvr process and reports metrics to Instana.

## Installation

Run the installation script:

```bash
./install-instana-m8prcsvr-plugin.sh
```

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
