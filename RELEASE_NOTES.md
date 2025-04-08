# Release Notes

## Version 0.0.1

### docs: Add network diagram to README using Mermaid
- Added a comprehensive architecture diagram to the README.md (v0.0.1)
- Visualized the plugin ecosystem including MicroStrategy processes, Instana Plugins, Common Components, Instana Agent, and Instana Backend
- Used Mermaid syntax for better visualization and maintainability

### refactor: Revert process_monitor.py and README.md to previous state
- Reverted changes to process_monitor.py to maintain backward compatibility (v0.0.1)
- Restored README.md to its previous state

### refactor: Improve process metrics reporting with enhanced error handling and OTel integration
- Enhanced error handling in process metrics reporting (v0.0.1)
- Improved OpenTelemetry integration in common/process_monitor.py
- Added better type hints for code documentation
- Restructured the report_metrics function for more reliable operation

### feat: Enhanced OpenTelemetry connector and documentation
- Improved error handling and fallbacks in common/otel_connector.py (v0.0.1)
- Added comprehensive documentation with examples
- Implemented gauge caching to avoid recreating gauges
- Added connection testing functionality
- Added support for metric prefixes
- Enhanced logging with more detailed messages

### feat: Update plugin.json with OpenTelemetry support and dynamic configuration
- Added explicit OpenTelemetry section to plugin.json (v0.0.1)
- Made plugin.json generation dynamic using variables in installer scripts
- Added descriptions for each metric
- Enhanced sample configuration with OpenTelemetry settings
- Fixed a bug in the process_monitor.py file

### refactor: Replace inline sensor.py with project files in installers
- Modified installer scripts to use existing sensor.py files (v0.0.1)
- Created functions to copy common module files
- Improved installation process for better maintainability
- Ensured consistent installation across plugins

### refactor: Enhance sensor scripts with flexible metric collection and error handling
- Added configurable interval parameter to m8mulprc/sensor.py and mstrsvr/sensor.py (v0.0.1)
- Added "run once" mode for testing or one-time reporting
- Refactored metric collection into reusable functions
- Improved error handling and exit codes
- Made time imports consistent

## Initial Release (v0.0.1)
- Process-specific monitoring for MicroStrategy components
- Case-insensitive process detection
- Process resource usage tracking
- OpenTelemetry integration for metrics and traces
- Easy installation with automatic configuration
