# Version 0.0.12 Release Notes

## Fixed Issues

- Fixed `ModuleNotFoundError: No module named 'common.base_sensor'` error in all plugins
- Added missing `__init__.py` files to all module directories (m8mulprc, m8prcsvr, m8refsvr, mstrsvr)
- Updated installation scripts to create proper Python package structure
- Replaced deprecated `distutils.util.strtobool` with a custom implementation
- Enhanced error handling for missing OpenTelemetry packages

## Compatibility

- Tested with Python 3.8+
- Compatible with Instana agent versions 1.2.0+

## Installation

For installation instructions, please refer to the README.md file in each plugin directory.
