# Instana Plugins Collection

A collection of custom plugins for Instana monitoring of MicroStrategy processes.

## Available Plugins

- [M8MulPrc Plugin](m8mulprc/README.md) - Monitor MicroStrategy M8MulPrc processes
- [MSTRSvr Plugin](mstrsvr/README.md) - Monitor MicroStrategy Intelligence Server processes

## Features

- Process-specific monitoring for MicroStrategy components
- Case-insensitive process detection
- Process resource usage tracking
- OpenTelemetry integration for metrics and traces
- Easy installation with automatic configuration

## Common Metrics Collected

- CPU Usage
- Memory Usage
- Process Count
- Disk Read/Write Bytes
- Open File Descriptors
- Thread Count
- Voluntary/Non-voluntary Context Switches

## Architecture Diagram

```mermaid
graph TD
    subgraph "MicroStrategy Server"
        M8["M8MulPrc Process"] 
        MS["MSTRSvr Process"]
    end
    
    subgraph "Instana Plugins"
        M8S["M8MulPrc Sensor"]
        MSS["MSTRSvr Sensor"]
        
        subgraph "Common Components"
            PM["Process Monitor"]
            OTEL["OTel Connector"]
        end
        
        M8S --> PM
        MSS --> PM
        M8S --> OTEL
        MSS --> OTEL
    end
    
    subgraph "Instana Agent"
        OTLP["OTLP Receiver"]
        PLUGIN["Plugin Framework"]
    end
    
    M8 -.-> M8S
    MS -.-> MSS
    PM --> OTEL
    OTEL --> OTLP
    PLUGIN --> OTLP
    
    subgraph "Instana Backend"
        METRICS["Metrics Storage"]
        TRACES["Traces Storage"]
        UI["Instana UI"]
    end
    
    OTLP --> METRICS
    OTLP --> TRACES
    METRICS --> UI
    TRACES --> UI
    
    classDef process fill:#f9f,stroke:#333,stroke-width:2px;
    classDef component fill:#bbf,stroke:#33f,stroke-width:1px;
    classDef common fill:#bfb,stroke:#3f3,stroke-width:1px;
    classDef agent fill:#fbb,stroke:#f33,stroke-width:1px;
    classDef backend fill:#bbb,stroke:#333,stroke-width:1px;
    
    class M8,MS process;
    class M8S,MSS component;
    class PM,OTEL common;
    class OTLP,PLUGIN agent;
    class METRICS,TRACES,UI backend;
```

## Requirements

- Instana Agent 1.2.0 or higher
- Python 3.6 or higher
- OpenTelemetry Python packages
- MicroStrategy environment

## Installation

Each plugin has its own installation script and documentation. Navigate to the specific plugin directory for detailed instructions.

```bash
# Clone the repository
git clone https://github.com/laplaque/instana_plugins.git
cd instana_plugins

# Install specific plugins
cd m8mulprc
sudo ./install-instana-m8mulprc-plugin.sh

# Or for MSTRSvr
cd ../mstrsvr
sudo ./install-instana-mstrsvr-plugin.sh
```

## Architecture

The plugins use a common framework for process monitoring and OpenTelemetry integration:

- `common/process_monitor.py` - Core process metrics collection
- `common/otel_connector.py` - OpenTelemetry integration for Instana

Each plugin implements a sensor that uses these common components to monitor specific MicroStrategy processes.

## License

[MIT License](LICENSE)

Copyright © 2025 laplaque/instana_plugins Contributors
