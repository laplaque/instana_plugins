# Release Notes

## Version 1.0.0

### Commit f9a009c - 2025-04-08
**docs: Add network diagram to README using Mermaid**
- Added a comprehensive architecture diagram to the README.md
- Visualized the plugin ecosystem including MicroStrategy processes, Instana Plugins, Common Components, Instana Agent, and Instana Backend
- Used Mermaid syntax for better visualization and maintainability

### Commit ff3c0fc - 2025-04-08
**refactor: Revert process_monitor.py and README.md to previous state**
- Reverted changes to process_monitor.py to maintain backward compatibility
- Restored README.md to its previous state

### Commit 75dff30 - 2025-04-08
**refactor: Improve process metrics reporting with enhanced error handling and OTel integration**
- Enhanced error handling in process metrics reporting
- Improved OpenTelemetry integration
- Added better type hints for code documentation
- Restructured the report_metrics function for more reliable operation

### Commit 2cdeb0e - 2025-04-08
**feat: Enhanced OpenTelemetry connector and documentation**
- Improved error handling and fallbacks in OTel connector
- Added comprehensive documentation with examples
- Implemented gauge caching to avoid recreating gauges
- Added connection testing functionality
- Added support for metric prefixes
- Enhanced logging with more detailed messages

### Commit cd843f7 - 2025-04-08
**feat: Update plugin.json with OpenTelemetry support and dynamic configuration**
- Added explicit OpenTelemetry section to plugin.json
- Made plugin.json generation dynamic using variables
- Added descriptions for each metric
- Enhanced sample configuration with OpenTelemetry settings
- Fixed a bug in the process_monitor.py file

### Commit 3e6cbe3 - 2025-04-08
**refactor: Replace inline sensor.py with project files in installers**
- Modified installer scripts to use existing sensor.py files
- Created functions to copy common module files
- Improved installation process for better maintainability
- Ensured consistent installation across plugins

### Commit f1a493a - 2025-04-08
**refactor: Enhance sensor scripts with flexible metric collection and error handling**
- Added configurable interval parameter
- Added "run once" mode for testing or one-time reporting
- Refactored metric collection into reusable functions
- Improved error handling and exit codes
- Made time imports consistent

## Initial Release
- Process-specific monitoring for MicroStrategy components
- Case-insensitive process detection
- Process resource usage tracking
- OpenTelemetry integration for metrics and traces
- Easy installation with automatic configuration
