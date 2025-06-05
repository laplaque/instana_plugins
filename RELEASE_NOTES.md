# Release Notes

## Version 0.0.16 (2025-06-05)

### feat: Centralized version parameter and fixed OpenTelemetry Observation yield pattern

- Centralized version parameter in `common/__init__.py` as a single source of truth
- Modified all sensor files to import the VERSION from common
- Updated installation scripts to extract the version dynamically from Python
- Fixed OpenTelemetry Observable callbacks to use the yield Observation pattern
- Added proper import of Observation class at the top of the file
- Simplified version management: version only needs to be updated in one place
- Eliminated potential version inconsistencies between different components
- Improved maintainability for future releases
- Further enhanced compatibility with latest OpenTelemetry API for metrics observation

## Version 0.0.15 (2025-06-04)

### fix: Updated ObservableGauge API usage for OpenTelemetry >= 1.20.0

- Fixed `'_ObservableGauge' object has no attribute 'observe'` error
- Updated implementation to use the newer OpenTelemetry API pattern
- Changed to pass callbacks directly to create_observable_gauge method
- Improved metric observation with proper callback parameter handling
- Updated tests to match the new implementation pattern
- Ensures compatibility with OpenTelemetry version 1.20.0 and newer

## Version 0.0.14 (2025-06-04)

### fix: Fixed OpenTelemetry metric recording with ObservableGauge

- Fixed `'_Gauge' object has no attribute 'record'` error in OpenTelemetry metrics
- Replaced `Gauge.record()` with individual `ObservableGauge` metrics and callbacks
- Each metric now has its own ObservableGauge for better visualization in Instana
- Added proper descriptions for each metric type
- Improved error handling for non-numeric metrics
- Enhanced debugging for metric observation and recording

## Version 0.0.13 (2025-06-02)

### feat: Installation testing and process simplification

- Added installation testing system to verify plugin installations
- Created dependency checking to avoid reinstalling packages
- Updated all installation scripts with dependency verification
- Installation scripts now skip package installation when dependencies are satisfied
- Added comprehensive testing documentation
- Added demonstration script for installation testing
- Changed default installation directory to `/opt/instana_plugins/`
- Removed dependency on Instana agent directories
- Improved service naming convention to `instana-microstrategy-{process}-monitor`
- Removed unnecessary plugin.json files
- Simplified plugin detection in installation test
- Modified test framework to support both old and new directory structures

## Version 0.0.12 (2025-05-22)

### fix: Fixed Python package import issues and enhanced error handling

- Fixed `ModuleNotFoundError: No module named 'common.base_sensor'` error in all plugins
- Added missing `__init__.py` files to all module directories (m8mulprc, m8prcsvr, m8refsvr, mstrsvr)
- Updated installation scripts to create proper Python package structure
- Replaced deprecated `distutils.util.strtobool` with a custom implementation
- Enhanced error handling for missing OpenTelemetry packages
- Improved robustness when running in environments without OpenTelemetry installed

## Version 0.0.11 (2025-05-08)

### feat: Added custom installation directory support for all plugins

- Added `-d/--directory` parameter to all plugin installation scripts for specifying custom installation directories
- Updated m8refsvr/install-instana-m8refsvr-plugin.sh to support the `-d` parameter
- Updated m8prcsvr/install-instana-m8prcsvr-plugin.sh to support the `-d` parameter
- Added `-r/--restart` parameter for consistent service control across all plugins
- Updated documentation in affected README files:
  - m8refsvr/README.md
  - m8prcsvr/README.md
  - main README.md
- Ensured all plugins now have consistent command-line parameters and behavior
- Improved flexibility for deployments in non-standard environments

## Version 0.0.10 (2025-04-25)

### feat: Added M8PrcSvr plugin

- Created new plugin for monitoring MicroStrategy M8PrcSvr processes
- Added comprehensive test suite for the M8PrcSvr plugin
- Updated README.md with M8PrcSvr plugin information
- Integrated with existing monitoring framework
- Added installation script for easy deployment

## Version 0.0.9 (2025-04-23)

### Changes v0.0.9

- Consolidated GitHub Actions workflows for tag validation
- Combined "Validate Tag Version" and "Validate Tag Format" into a single workflow
- Improved documentation for OpenTelemetry integration
- Added TLS configuration options for secure connections

### Bug Fixes v0.0.9

- Fixed issue with process detection for case-sensitive process names
- Improved error handling for network connectivity issues

## Version 0.0.8 (2025-04-22)

### feat: Added M8RefSvr plugin

- Created new plugin for monitoring MicroStrategy Reference Server processes
- Added comprehensive documentation for the new plugin
- Updated test suite to include M8RefSvr tests
- Fixed ResourceWarnings in test suite
- Improved error handling in sensor scripts

## Version 0.0.7 (2025-03-15)

### Changes v0.0.7

- Added support for MicroStrategy 2025 platform
- Enhanced logging with rotation capabilities
- Improved error handling for process monitoring

### Bug Fixes v0.0.7

- Fixed memory leak in long-running monitoring sessions
- Resolved issue with metric collection during process restarts

## Version 0.0.6 (2025-04-22)

### feat: Enhanced logging and test framework

- Added centralized logging configuration with log rotation
- Improved test coverage with edge case handling
- Added comprehensive troubleshooting documentation
- Fixed resource warnings in tests related to unclosed file handlers
- Corrected handling of special characters in process names
- Improved error handling in OpenTelemetry connector

### docs: Expanded documentation with known limitations

- Updated documentation with known limitations and edge cases
- Enhanced test framework with better mocking of OpenTelemetry
- Added coverage reporting to test suite
- Added detailed troubleshooting sections to plugin READMEs
- Improved installation and configuration instructions

## Version 0.0.3 (2025-04-09)

### docs: Enhanced OpenTelemetry documentation and configuration

- Added detailed OpenTelemetry data ingestion configuration instructions to README
- Updated documentation for Kubernetes environments with specific service endpoints
- Added version information to sensor scripts for better tracking
- Included agent configuration examples from IBM documentation
- Improved explanation of data flow between plugins and Instana based on diagram

### chore: Version management improvements

- Added explicit version numbers to sensor scripts
- Updated version display in log messages
- Standardized version format across components

## Version 0.0.2 (2025-04-01)

### Added

- Support for OpenTelemetry metrics and traces
- Improved error handling in process monitoring
- Added thread count and context switch metrics

### Fixed

- Case-insensitive process name matching
- Better handling of missing process information

## Version 0.0.1 (2025-03-15)

### docs: Add network diagram to README using Mermaid

- Added a comprehensive architecture diagram to the README.md
- Visualized the plugin ecosystem including MicroStrategy processes, Instana Plugins, Common Components, Instana Agent, and Instana Backend
- Used Mermaid syntax for better visualization and maintainability

### refactor: Improve process metrics reporting with enhanced error handling and OTel integration

- Enhanced error handling in process metrics reporting
- Improved OpenTelemetry integration in common/process_monitor.py
- Added better type hints for code documentation
- Restructured the report_metrics function for more reliable operation

### feat: Enhanced OpenTelemetry connector and documentation

- Improved error handling and fallbacks in common/otel_connector.py
- Added comprehensive documentation with examples
- Implemented gauge caching to avoid recreating gauges
- Added connection testing functionality
- Added support for metric prefixes
- Enhanced logging with more detailed messages

### feat: Update plugin.json with OpenTelemetry support and dynamic configuration

- Added explicit OpenTelemetry section to plugin.json
- Made plugin.json generation dynamic using variables in installer scripts
- Added descriptions for each metric
- Enhanced sample configuration with OpenTelemetry settings

### refactor: Replace inline sensor.py with project files in installers

- Modified installer scripts to use existing sensor.py files
- Created functions to copy common module files
- Improved installation process for better maintainability
- Ensured consistent installation across plugins

### refactor: Enhance sensor scripts with flexible metric collection and error handling

- Added configurable interval parameter to m8mulprc/sensor.py and mstrsvr/sensor.py
- Added "run once" mode for testing or one-time reporting
- Refactored metric collection into reusable functions
- Improved error handling and exit codes
- Made time imports consistent
