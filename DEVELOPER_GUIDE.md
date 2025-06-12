# Developer's Guide: Creating Custom Instana Process Monitoring Plugins

This guide provides comprehensive instructions for creating custom process monitoring plugins using the OpenTelemetry-based framework provided in this repository.

## Table of Contents

- [Quick Start](#quick-start)
- [Framework Overview](#framework-overview)
- [Creating a New Plugin](#creating-a-new-plugin)
- [Plugin Configuration](#plugin-configuration)
- [Testing Your Plugin](#testing-your-plugin)
- [Installation Script Development](#installation-script-development)
- [Advanced Customization](#advanced-customization)
- [Best Practices](#best-practices)
- [Complete Example](#complete-example)
- [Troubleshooting](#troubleshooting)

## Quick Start

To create a new plugin for monitoring a process called "MyApp":

1. **Create plugin directory**: `mkdir myapp`
2. **Create configuration**: `myapp/__init__.py`
3. **Create sensor**: `myapp/sensor.py`
4. **Create tests**: `tests/test_myapp_sensor.py`
5. **Create installer**: `myapp/install-instana-myapp-plugin.sh`
6. **Test your plugin**: `python myapp/sensor.py --run-once`

## Framework Overview

### Architecture

The framework consists of two main layers:

```
┌─────────────────────────────────────┐
│           Your Plugin               │
│  ┌─────────────┐ ┌─────────────────┐│
│  │ __init__.py │ │    sensor.py    ││
│  │ (config)    │ │ (entry point)   ││
│  └─────────────┘ └─────────────────┘│
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│         Common Framework            │
│  ┌──────────────┐ ┌──────────────┐  │
│  │ base_sensor  │ │process_monitor│ │
│  │ otel_connector│ │logging_config │ │
│  │ metadata_store│ │check_deps    │  │
│  └──────────────┘ └──────────────┘  │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│       OpenTelemetry / Instana       │
└─────────────────────────────────────┘
```

### Key Components

- **base_sensor.py**: Main framework logic, argument parsing, OpenTelemetry setup
- **process_monitor.py**: Process detection and metrics collection
- **otel_connector.py**: OpenTelemetry protocol implementation
- **logging_config.py**: Centralized logging configuration
- **metadata_store.py**: Thread-safe metadata persistence

### Data Flow

1. Your sensor calls `run_sensor()` with process name and configuration
2. Framework detects processes matching your criteria
3. Metrics are collected from `/proc` filesystem
4. Data is sent to Instana via OpenTelemetry OTLP protocol
5. Process repeats at configured intervals

## Creating a New Plugin

### Step 1: Plugin Directory Structure

Create a new directory for your plugin. Use lowercase names following the existing convention:

```bash
mkdir myapp
cd myapp
```

### Step 2: Configuration File (`__init__.py`)

This file defines the core configuration for your plugin:

```python
"""
Configuration for the myapp sensor plugin.
"""

# OpenTelemetry service namespace for grouping services
SERVICE_NAMESPACE = "MyCompany"

# Process name to monitor (case-insensitive matching will be used)
PROCESS_NAME = "MyApp"

# Plugin identifier for Instana (should match directory name)
PLUGIN_NAME = "myapp"
```

#### Configuration Options Explained

- **SERVICE_NAMESPACE**: Groups your services in Instana. Use your company/product name.
- **PROCESS_NAME**: The process name to search for. The framework uses case-insensitive regex matching.
- **PLUGIN_NAME**: Unique identifier for your plugin. Should match your directory name.

### Step 3: Sensor Entry Point (`sensor.py`)

This is the main executable file for your plugin:

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 Your Name/Organization

Process monitoring plugin for MyApp processes.
"""
import sys
import os

# Add the parent directory to the path to import the common modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.base_sensor import run_sensor
from common import VERSION

# Import configuration from package __init__.py
from . import SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME

if __name__ == "__main__":
    run_sensor(PROCESS_NAME, PLUGIN_NAME, VERSION, service_namespace=SERVICE_NAMESPACE)
```

#### Key Points:

- **Shebang**: Makes the file executable directly
- **Path manipulation**: Allows importing common modules
- **Configuration import**: Uses your `__init__.py` constants
- **run_sensor call**: The framework handles everything else

### Step 4: Make Sensor Executable

```bash
chmod +x sensor.py
```

## Plugin Configuration

### Advanced Process Matching

The framework supports flexible process matching. You can customize the process detection in several ways:

#### Simple Name Matching (Default)
```python
PROCESS_NAME = "MyApp"  # Matches: myapp, MyApp, MYAPP, etc.
```

#### Regex Pattern Matching
```python
PROCESS_NAME = "MyApp.*"  # Matches: MyApp, MyAppServer, MyAppWorker, etc.
```

#### Exact Matching
```python
PROCESS_NAME = "^MyApp$"  # Matches only: MyApp (exact case-insensitive)
```

### Service Namespace Best Practices

Choose meaningful service namespaces that group related services:

```python
# Good examples:
SERVICE_NAMESPACE = "MyCompany"      # Company-wide services
SERVICE_NAMESPACE = "ECommerce"      # Product-specific services
SERVICE_NAMESPACE = "Infrastructure" # Infrastructure services

# Avoid:
SERVICE_NAMESPACE = "App"           # Too generic
SERVICE_NAMESPACE = "Monitoring"    # Redundant
```

### Multiple Process Variants

If you need to monitor multiple related processes, create separate plugins:

```
myapp-web/          # Web server processes
myapp-worker/       # Background worker processes
myapp-db/          # Database processes
```

Each with their own configuration and process names.

## Testing Your Plugin

### Basic Testing

Test your plugin immediately after creation:

```bash
# Test process detection (safe, read-only)
python sensor.py --run-once --log-level=DEBUG

# Test with specific agent connection
python sensor.py --run-once --agent-host=localhost --agent-port=4317
```

### Creating Unit Tests

Create a test file `tests/test_myapp_sensor.py`:

```python
#!/usr/bin/env python3
"""
Test cases for the MyApp sensor.
"""

import unittest
from unittest.mock import patch
import sys
import os

# Add the parent directory to the path so we can import the sensor module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMyAppSensor(unittest.TestCase):
    """Test cases for the MyApp sensor."""
    
    def test_constants(self):
        """Test the sensor constants."""
        from myapp import SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME
        
        self.assertEqual(SERVICE_NAMESPACE, "MyCompany")
        self.assertEqual(PROCESS_NAME, "MyApp")
        self.assertEqual(PLUGIN_NAME, "myapp")
    
    def test_sensor_import(self):
        """Test that the sensor module can be imported."""
        try:
            import myapp.sensor
            self.assertTrue(hasattr(myapp.sensor, 'run_sensor'))
        except ImportError as e:
            self.fail(f"Failed to import sensor module: {e}")
    
    @patch('common.base_sensor.run_sensor')
    def test_main_function_call(self, mock_run_sensor):
        """Test the main function parameters."""
        from myapp import SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME
        from common import VERSION
        
        # Import the sensor module
        import myapp.sensor
        
        # Manually call the main logic (since we can't easily test __main__)
        myapp.sensor.run_sensor(PROCESS_NAME, PLUGIN_NAME, VERSION, service_namespace=SERVICE_NAMESPACE)
        
        # Verify the function was called with correct parameters
        mock_run_sensor.assert_called_once_with(
            PROCESS_NAME, 
            PLUGIN_NAME, 
            VERSION, 
            service_namespace=SERVICE_NAMESPACE
        )

if __name__ == '__main__':
    unittest.main()
```

### Running Tests

```bash
# Run your specific test
python -m unittest tests/test_myapp_sensor.py

# Run all tests
cd tests
python run_tests.py

# Run with verbose output
python -m unittest -v tests/test_myapp_sensor.py
```

### Test Coverage Best Practices

Your tests should cover:

1. **Configuration validation**: Ensure constants are correct
2. **Import testing**: Verify modules can be imported
3. **Function calls**: Mock and verify framework calls
4. **Error handling**: Test failure scenarios

## Installation Script Development

### Creating the Installation Script

Create `install-instana-myapp-plugin.sh`:

```bash
#!/bin/bash
#
# MIT License
#
# Copyright (c) 2025 Your Name/Organization
#
# MyApp Instana Plugin Installer
#

# Use the Strategy₿ installer as a template
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$( dirname "$SCRIPT_DIR" )"

# Source the shared version extraction script
source "${PARENT_DIR}/common/extract_version.sh"

# Default installation directories
DEFAULT_BASE_DIR="/opt/instana_plugins"

# Define plugin-specific variables
PROCESS_NAME="MyApp"
PLUGIN_DIR_NAME="myapp"  # Must match your directory name

# ... rest of the installation script follows the template pattern
```

### Customization Points

When adapting an existing installation script, change these variables:

```bash
# Change these for your plugin:
PROCESS_NAME="MyApp"           # Display name in messages
PLUGIN_DIR_NAME="myapp"        # Directory name (lowercase)
SERVICE_NAME="instana-myapp-monitor"  # Systemd service name

# Update help text:
function show_usage {
    echo -e "Usage: $0 [OPTIONS]"
    echo -e "Install the MyApp monitoring plugin for Instana"
    # ... rest of help text
}
```

### Testing Installation Script

```bash
# Test script syntax
bash -n install-instana-myapp-plugin.sh

# Test help output
./install-instana-myapp-plugin.sh --help

# Test installation (as root or with sudo)
sudo ./install-instana-myapp-plugin.sh

# Test non-root installation
./install-instana-myapp-plugin.sh -d ~/instana-plugins
```

## Advanced Customization

### Custom Metrics Collection

If you need custom metrics beyond the standard process metrics, you can extend the framework:

#### Option 1: Custom Process Monitor (Advanced)

Create a custom process monitor by extending the base class:

```python
# myapp/custom_monitor.py
from common.process_monitor import ProcessMonitor

class MyAppProcessMonitor(ProcessMonitor):
    def collect_custom_metrics(self, pid):
        """Collect additional metrics specific to MyApp."""
        custom_metrics = {}
        
        # Example: Read custom metrics from a file
        try:
            with open(f'/proc/{pid}/status') as f:
                # Parse custom data
                pass
        except Exception as e:
            self.logger.warning(f"Failed to collect custom metrics: {e}")
        
        return custom_metrics
```

#### Option 2: Environment Variables

Use environment variables for runtime customization:

```python
# In your sensor.py
import os

# Custom collection interval
COLLECTION_INTERVAL = int(os.environ.get('MYAPP_INTERVAL', '60'))

# Custom process filter
PROCESS_FILTER = os.environ.get('MYAPP_PROCESS_FILTER', PROCESS_NAME)
```

### Custom OpenTelemetry Attributes

Add custom resource attributes:

```python
# In your __init__.py
CUSTOM_ATTRIBUTES = {
    "service.version": "1.0.0",
    "deployment.environment": "production",
    "myapp.cluster": "east-coast"
}
```

Then modify your sensor to pass these attributes to the framework.

### Multiple Process Types in One Plugin

If you need to monitor multiple related processes:

```python
# myapp/__init__.py
PROCESS_NAMES = ["MyAppWeb", "MyAppWorker", "MyAppDB"]
SERVICE_NAMESPACE = "MyApp"
PLUGIN_NAME = "myapp"

# myapp/sensor.py
from . import PROCESS_NAMES, SERVICE_NAMESPACE, PLUGIN_NAME

if __name__ == "__main__":
    for process_name in PROCESS_NAMES:
        run_sensor(process_name, f"{PLUGIN_NAME}-{process_name.lower()}", VERSION, 
                  service_namespace=SERVICE_NAMESPACE)
```

## Best Practices

### Naming Conventions

- **Plugin directories**: lowercase, hyphens for multi-word (`my-app`)
- **Process names**: PascalCase matching actual process names (`MyApp`)
- **Plugin names**: lowercase, matching directory (`myapp`)
- **Service namespace**: PascalCase, meaningful grouping (`MyCompany`)

### Security Considerations

1. **Minimal permissions**: Use Linux capabilities when possible
2. **No hardcoded secrets**: Use environment variables
3. **Input validation**: Validate all user inputs
4. **TLS encryption**: Enable for production deployments

### Performance Optimization

1. **Reasonable intervals**: Default to 60 seconds for production
2. **Resource monitoring**: Monitor your plugin's own resource usage
3. **Efficient process detection**: Use specific process name patterns
4. **Error handling**: Fail gracefully without crashing

### Documentation Standards

Include in your plugin directory:

1. **README.md**: Plugin-specific documentation
2. **CHANGELOG.md**: Version history and changes
3. **examples/**: Configuration examples
4. **docs/**: Additional documentation if needed

### Version Management

Follow semantic versioning and update these files:

1. **common/__init__.py**: Framework version
2. **Plugin README**: Version compatibility
3. **Installation script**: Version checks
4. **Tests**: Version validation

## Complete Example

Here's a complete working example for monitoring a fictional "WebServer" process:

### Directory Structure
```
webserver/
├── __init__.py
├── sensor.py
├── install-instana-webserver-plugin.sh
└── README.md
```

### webserver/__init__.py
```python
"""
Configuration for the webserver sensor plugin.
"""

SERVICE_NAMESPACE = "WebInfrastructure"
PROCESS_NAME = "WebServer"
PLUGIN_NAME = "webserver"
```

### webserver/sensor.py
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 Your Organization

WebServer process monitoring plugin for Instana.
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.base_sensor import run_sensor
from common import VERSION
from . import SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME

if __name__ == "__main__":
    run_sensor(PROCESS_NAME, PLUGIN_NAME, VERSION, service_namespace=SERVICE_NAMESPACE)
```

### tests/test_webserver_sensor.py
```python
#!/usr/bin/env python3
"""
Test cases for the WebServer sensor.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestWebServerSensor(unittest.TestCase):
    def test_constants(self):
        from webserver import SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME
        
        self.assertEqual(SERVICE_NAMESPACE, "WebInfrastructure")
        self.assertEqual(PROCESS_NAME, "WebServer")
        self.assertEqual(PLUGIN_NAME, "webserver")

if __name__ == '__main__':
    unittest.main()
```

### Usage
```bash
# Test the plugin
python webserver/sensor.py --run-once --log-level=DEBUG

# Install the plugin
sudo ./webserver/install-instana-webserver-plugin.sh

# Run tests
python -m unittest tests/test_webserver_sensor.py
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'common'
   ```
   **Solution**: Ensure `sys.path.insert()` is correct and common directory exists

2. **Process Not Found**
   ```
   No processes found matching 'MyApp'
   ```
   **Solution**: Check process name spelling and case, verify process is running

3. **Permission Denied**
   ```
   PermissionError: [Errno 13] Permission denied: '/proc/12345/stat'
   ```
   **Solution**: Run with appropriate permissions or use Linux capabilities

4. **OpenTelemetry Connection Failed**
   ```
   Failed to export metrics: connection refused
   ```
   **Solution**: Verify Instana agent is running and accepting OTLP connections

### Debugging Tips

1. **Use debug logging**: `--log-level=DEBUG`
2. **Test incrementally**: Start with `--run-once`
3. **Check process list**: `ps aux | grep -i myapp`
4. **Verify agent**: `systemctl status instana-agent`
5. **Check ports**: `netstat -ln | grep 4317`

### Getting Help

1. **Framework issues**: Check existing plugins for patterns
2. **OpenTelemetry issues**: Review OTLP documentation
3. **Instana integration**: Consult Instana agent documentation
4. **Testing issues**: Review test patterns in existing test files

---

## Contributing

When contributing new plugins or framework improvements:

1. **Follow existing patterns**: Study current implementations
2. **Add comprehensive tests**: Include unit and integration tests
3. **Document thoroughly**: Update this guide and add plugin-specific docs
4. **Test on multiple environments**: Verify compatibility
5. **Update version tracking**: Increment versions appropriately

This framework is designed to be extensible and maintainable. By following these patterns and best practices, you can create robust monitoring plugins that integrate seamlessly with Instana.
