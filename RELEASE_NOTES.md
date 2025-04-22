# Release Notes

## Version 0.0.7 (2025-04-22)

### feat: Added M8RefSvr plugin
- Created new plugin for monitoring MicroStrategy Reference Server processes
- Added comprehensive documentation for the new plugin
- Updated test suite to include M8RefSvr tests
- Fixed ResourceWarnings in test suite
- Improved error handling in sensor scripts

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
