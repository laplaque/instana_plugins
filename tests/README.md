# Instana Plugins Testing

This directory contains utilities to test the Instana MicroStrategy plugins installation and functionality.

## Testing Installation

After installing one or more of the MicroStrategy plugins, you can use the `test_installation.py` script to verify that everything is working properly.

### Prerequisites

Make sure you have installed the required Python dependencies:

```bash
pip install -r ../common/requirements.txt
```

### Running the Test

To test if your installation was successful, simply run:

```bash
./test_installation.py
```

This will:
1. Check for required Python dependencies
2. Determine if requirements need to be installed for each plugin or just once
3. Look for plugin installations in standard locations
4. Run each installed sensor in test mode
5. Provide a summary of test results

### Options

The test script provides several options:

```
usage: test_installation.py [-h] [--dependencies-only] [--plugin {m8mulprc,m8prcsvr,m8refsvr,mstrsvr}]

Test Instana plugins installation

optional arguments:
  -h, --help            show this help message and exit
  --dependencies-only   Only check dependencies, skip plugin tests
  --plugin {m8mulprc,m8prcsvr,m8refsvr,mstrsvr}
                        Test specific plugin(s) only
```

Examples:

```bash
# Test only dependencies installation
./test_installation.py --dependencies-only

# Test only the M8MulPrc plugin
./test_installation.py --plugin m8mulprc

# Test multiple specific plugins
./test_installation.py --plugin m8mulprc --plugin mstrsvr
```

## Other Test Utilities

### OpenTelemetry Check

To verify that OpenTelemetry is properly installed:

```bash
./check_otel_installation.py
```

This script will check for essential OpenTelemetry components and provide guidance if any are missing.

## Troubleshooting

If tests fail, check the following:

1. Make sure Python 3 is installed and in your PATH
2. Verify that all dependencies are installed (use `--dependencies-only`)
3. Check that the plugin directories exist and have the correct permissions
4. Look for error messages in the test output
5. Try running the sensor script directly:
   ```bash
   # Replace PATH_TO_PLUGIN with actual path
   PYTHONPATH=PATH_TO_PLUGIN python3 PATH_TO_PLUGIN/sensor.py --run-once --log-level=DEBUG
   ```

For further assistance, refer to the plugin documentation or create an issue in the GitHub repository.
