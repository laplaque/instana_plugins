# Release Notes

## Version 0.1.01 (2025-06-17)

### feat: Database Connection Management Improvements & Metric Formatting Fixes

**🔧 Database Connection Management Enhancements**
This release implements a centralized database connection manager addressing GitHub Copilot code review recommendations for improved resource management and exception safety.

**✅ Database Connection Improvements:**
- **Centralized Connection Manager**: Implemented `_get_db_connection()` method providing single point of control for SQLite connections
- **Context Manager Pattern**: All database operations now use proper context managers (`with` statements) for automatic resource cleanup  
- **Exception Safety**: Improved error handling and connection cleanup in case of exceptions
- **Code Consistency**: Standardized database connection pattern across all methods in `MetadataStore` class
- **Maintainability**: Centralized connection logic eliminates code duplication and simplifies future modifications
- **Resource Management**: Automatic cleanup prevents connection leaks and improves system stability

**🔧 Technical Changes:**
- **Enhanced `common/metadata_store.py`**: 
  - Added centralized `_get_db_connection()` context manager method
  - Updated critical database methods: `_cache_metrics_schema()`, `_get_current_schema_version()`, `_set_schema_version()`, migration methods, and CRUD operations
  - Replaced manual connection/close patterns with context managers
  - Maintained all existing functionality while improving reliability
- **Addressed GitHub Copilot Review**: Resolved suggestion for using context managers in SQLite connections
- **Code Quality**: Eliminated redundant connection handling code across 7+ database methods

### fix: Critical Metric Formatting Fixes

**🔧 Metric Display Fixes**
This patch release resolves critical metric formatting issues discovered during testing, ensuring proper display of metrics in Instana UI with correct decimal precision and clean metric names.

**✅ Issues Resolved:**
- **Metric Names**: Removed trailing braces from metric names in Instana UI display
- **Integer Decimals**: Fixed integer values displaying with unnecessary decimal places (15.000 → 15)
- **Percentage Display**: Corrected percentage metrics to show proper decimal precision (42.678912 → 42.68)

**🔧 Technical Changes:**
- **Enhanced `common/otel_connector.py`**: 
  - Added dynamic reading of `decimals` field from `manifest.toml` metric definitions
  - Implemented proper formatting based on metric configuration (percentage vs integer vs float)
  - Fixed metric name cleaning to remove trailing braces using metadata store functionality
- **Updated metric formatting logic**: Applied manifest-specified decimal places instead of hardcoded 3-decimal formatting
- **Maintained backward compatibility**: Existing installations continue to work unchanged

**📊 Before/After Examples:**
```
Before v0.1.01:
- cpu_usage{}: 42.678912 (excessive decimals)
- process_count{}: 15.000 (unnecessary decimals)
- memory_usage{}: 85.234567 (excessive decimals)

After v0.1.01:
- cpu_usage: 42.68 (proper 2-decimal percentage)
- process_count: 15 (clean integer)
- memory_usage: 85.23 (proper 2-decimal percentage)
```

**🎯 Impact:**
- **Database Reliability**: Improved connection management prevents resource leaks and enhances system stability
- **Code Maintainability**: Centralized connection handling simplifies future database enhancements
- **User Experience**: Clean, professional metric display in Instana UI
- **Data Accuracy**: Proper decimal precision based on metric type and configuration
- **Display Quality**: Eliminates visual clutter from excessive decimal places and naming artifacts

**✅ Testing:**
- All database tests pass with new connection manager implementation
- Verified formatting fixes with comprehensive test suite
- Confirmed proper decimal handling for all metric types (Gauge, Counter, UpDownCounter)
- Validated metric name cleaning functionality
- All existing tests continue to pass

**🔄 Deployment:**
- **Zero Downtime**: Can be deployed without service interruption
- **No Migration**: No database or configuration changes required
- **Immediate Effect**: Improvements visible immediately after deployment

---

## Version 0.1.00 (2025-06-16)

### feat: Enhanced --once Flag with Console Output & User Experience

**🚀 Major Enhancement: --once Flag Console Output & User Experience**
This release introduces significant improvements to the `--once` flag functionality, transforming it from a silent execution mode into a user-friendly debugging and testing tool with immediate console feedback.

**✨ New Features:**
- **Enhanced Console Output**: Displays collected metrics with visual indicators (✓) for success and helpful diagnostic messages (✗) for failures
- **Real-time Feedback**: Immediate console output without requiring log file inspection
- **Argument Validation**: Warning system alerts when `--once` and `--interval` flags conflict
- **Help Text Updates**: Clear documentation of flag interactions and behaviors
- **User Guidance**: Self-documenting command line interface

**🔧 Technical Improvements:**
- ✅ Skip daemonization when using `--once` flag to preserve console output
- ✅ Enhanced console output for both success and failure scenarios
- ✅ Argument validation with warning when `--once` and `--interval` are combined
- ✅ Updated help text to clarify flag interactions and behaviors

**📊 Benefits Summary:**
- **Before v0.1.00**: Silent execution requiring log file inspection, no argument validation, confusing debugging experience
- **After v0.1.00**: Immediate visual feedback with ✓/✗ indicators, clear diagnostic messages, argument validation, self-documenting interface

**🎯 Use Cases Enhanced:**
- **Debugging & Testing**: Immediate feedback for process monitoring validation
- **Development Workflow**: Fast iteration testing during plugin development  
- **Production Validation**: One-time health checks with clear success/failure indicators

**Example Usage:**
```bash
# Success case
$ python3 sensor.py --once
✓ Successfully collected 21 metrics for 'python':
  cpu_usage: 90.2
  memory_usage: 0.37
  [... all metrics displayed]

# Failure case  
$ python3 sensor.py --once
✗ No processes found matching 'ProcessName'
  This could mean:
  - The process is not currently running
  - The process name doesn't match the pattern
  - Permission issues accessing process information

# Argument conflict warning
$ python3 sensor.py --once --interval 30
Warning: --interval flag ignored when using --once mode
```

**🔄 Version Management:**
- Version updated to `0.1.00` in `common/manifest.toml`
- Dynamic version reading from TOML configuration maintained
- Fallback default preserved for error scenarios

**Impact:** Transforms `--once` from a silent execution mode into a powerful debugging and testing tool  
**Compatibility:** Fully backward compatible with existing installations  
**Migration:** No migration required - enhancements are automatically available  
**Dependencies:** No new external dependencies required

---

## Version 0.0.20 (2025-06-12)

### feat: Comprehensive TOML-Based Installation System

**🚀 Major Architectural Transformation**
- **TOML Configuration System**: Implemented industry-standard TOML configuration files replacing hardcoded Python __init__.py dependencies
- **Generic Framework**: Eliminated vendor-specific assumptions, creating truly vendor-agnostic installation system
- **95% Code Reduction**: Consolidated 4 installation scripts from ~200 lines each to ~20 lines using shared functions
- **Centralized Version Management**: Single source of truth in manifest.toml with automatic version propagation

**📁 New Infrastructure Components**
- **common/version.py**: Centralized version management system reading from manifest.toml
- **common/manifest.toml**: Auto-generated checksums and metadata for v0.0.20
- **common/install_functions.sh**: 6 core shared installation functions with 400+ lines of robust logic
- **[plugin]/plugin.toml**: TOML configuration files for all 4 plugins with rich metadata
- **tests/test_toml_installation.py**: Comprehensive test suite with 8 tests covering all aspects

**🔧 Installation System Enhancements**
- **SHA256 Checksum Verification**: Integrity checking for all common files with automatic validation
- **File-by-File Installation**: Detailed progress tracking and status reporting for each component
- **TOML Parser Integration**: Python-based reliable parsing within bash scripts
- **Fallback Mechanisms**: Backward compatibility with existing __init__.py files during transition
- **Force Update Capability**: Option to refresh modified files with --force-update flag

**🛡️ Quality Assurance & Testing**
- **Comprehensive Test Coverage**: 8 passing tests validating configuration loading, installation scripts, manifest integrity, version management, and error handling
- **Real Installation Verification**: End-to-end installation testing confirms functionality
- **Backward Compatibility**: Maintains existing __init__.py functionality while adding TOML capabilities
- **Error Handling**: Robust fallback mechanisms and detailed error reporting

**⚙️ Technical Implementation**
- **Shared Installation Logic**: common/install_functions.sh provides get_plugin_metadata(), verify_common_files(), install_common_files(), install_plugin_files(), create_service_file(), and install_plugin()
- **TOML Metadata System**: Rich plugin configuration with service_namespace, process_name, description, monitoring settings, and dependencies
- **Version System Integration**: All components now use centralized version from manifest.toml
- **Systemd Service Integration**: Dynamic service file creation with metadata-driven configuration

**🎯 Fixed Original Issue**
- **metadata_store.py Installation**: Resolved missing file issue that caused import errors
- **Complete File Coverage**: All common files now properly installed with verification
- **Checksum Validation**: Ensures file integrity and detects corruption or modification

**🔧 Metadata Sanitization Enhancement**
- **Vendor-Agnostic Service Names**: Added intelligent metadata sanitization converting any service names to safe technical identifiers using only `[a-z0-9_]`
- **Unicode Support**: Service names can now contain any characters including emojis, Unicode symbols, and special characters
- **Dual-Format Storage**: Maintains both sanitized technical identifiers for database performance and original names for human-readable display
- **Dynamic Metrics Prefixes**: Automatically derives metrics prefixes from service names using sanitization, eliminating hardcoded vendor assumptions
- **Database Performance**: All stored identifiers use consistent format for optimal query performance
- **Professional Standards**: Industry-standard sanitization practices ensure compatibility with any monitoring system

**Example transformations:**
- `"Strategy₿.M8MulPrc"` → `"strategy_m8mulprc"` (stored) + `"Strategy M8mulprc"` (display)
- `"Service@Domain.com"` → `"service_domain_com"` (stored) + `"Service Domain Com"` (display)
- `"123numeric-start"` → `"metric_123numeric_start"` (stored) + `"Metric 123numeric Start"` (display)

**Configuration Cleanup:**
- **Removed Hardcoded Metrics Prefixes**: Eliminated vendor-specific `metrics_prefix` entries from all 4 plugin.toml files
- **Automatic Prefix Generation**: System now derives metrics prefixes dynamically from service name templates
- **Vendor Independence**: No MicroStrategy or Strategy₿-specific hardcoded values remain in configuration

### Breaking Changes
None. This release maintains full backward compatibility while adding comprehensive new functionality.

### Migration Guide
Existing installations continue to work unchanged. The new TOML system runs alongside existing __init__.py files, providing a smooth migration path for future enhancements. The metadata sanitization system works automatically without requiring any configuration changes.

---

## Version 0.0.19 (2025-12-12)

### fix: Code Review Completion and Test Suite Fixes (2025-12-12)

**✅ Comprehensive Sensor Code Review Completed**
- **All 4 Sensors Reviewed**: m8mulprc, m8prcsvr, m8refsvr, mstrsvr - confirmed excellent architecture and code quality
- **Code Quality Assessment**: High-quality codebase with professional engineering practices validated
- **Architecture Analysis**: Clean modular design with proper separation of concerns confirmed
- **Security Review**: Safe SQL operations, proper error handling, and comprehensive logging validated
- **Test Coverage**: 73 tests covering all major components and edge cases

**🔧 Version Consistency Fixes**
- **Fixed Test Failures**: Resolved 6 test failures due to version mismatches between hardcoded expectations and actual version
- **Updated Test Files**: Modified `tests/test_m8prcsvr_sensor.py`, `tests/test_m8refsvr_sensor.py`, and `tests/test_sensor.py` to use dynamic version imports
- **Centralized Version Management**: Confirmed proper implementation already in place with `common/__init__.py` as single source of truth
- **Test Suite Validation**: All 73 tests now pass successfully, confirming code quality and functionality

**📋 Key Findings**
- **Strengths**: Excellent centralized version management, robust infrastructure, comprehensive test coverage, consistent error handling
- **Architecture**: Perfect framework design with shared base functionality and minimal plugin requirements
- **Quality**: Production-ready code with proper resource management, OpenTelemetry integration, and database schema versioning

### feat: Major Framework Transformation and Daemon Mode Implementation

**🚀 Daemon Mode Implementation (Primary Focus)**
- **Background Service Operation**: Sensors now run as persistent background processes with systemd integration
- **Configurable Monitoring Intervals**: Customizable collection frequency (default: 60 seconds) via environment variables and command-line options
- **Signal Handling**: Graceful shutdown on SIGTERM/SIGINT signals with proper cleanup
- **Process Lifecycle Management**: Automatic restart on failures via systemd service configuration
- **Enhanced Installation Scripts**: Automatic systemd service file creation with support for both root and user-level services

**🔄 Framework Transformation: Strategy₿ to Generic Platform**
- **Complete Architectural Restructuring**: Transformed from Strategy₿-specific monitoring tools into a Generic OpenTelemetry Process Monitoring Framework
- **Universal Process Detection**: Framework now supports monitoring ANY process type (Apache, PostgreSQL, custom applications, etc.)
- **Extensible Plugin Architecture**: Clean separation between framework core and plugin implementations
- **Reference Implementation Pattern**: Strategy₿ plugins repositioned as working examples demonstrating framework capabilities
- **Developer-Friendly Design**: Simple plugin creation requiring only minimal configuration (2 files: `__init__.py`, `sensor.py`)

**📖 Complete Developer Documentation**
- **New DEVELOPER_GUIDE.md**: Comprehensive 18KB guide with step-by-step plugin creation instructions
- **Quick Start Guide**: 6-step process to create custom monitoring plugins
- **Framework Architecture**: Detailed technical diagrams and component explanations
- **Working Examples**: Complete "WebServer" plugin implementation as template
- **Copy-Paste Ready Templates**: Code examples for all plugin components
- **Testing Framework**: Unit test patterns and best practices
- **Installation Scripts**: Template and customization guide
- **Advanced Features**: Custom metrics, OpenTelemetry attributes, multiple process monitoring
- **Troubleshooting**: Comprehensive common issues and debugging techniques

**🔍 Comprehensive Code Review**
- **All Sensor Modules Reviewed**: m8mulprc, m8prcsvr, m8refsvr, mstrsvr - all confirmed to follow identical, well-designed patterns
- **Framework Pattern Analysis**: Architecture perfectly suited for generic framework with excellent separation of concerns
- **Production Readiness Confirmed**: Professional-quality code with comprehensive error handling, logging, and security practices
- **Test Coverage Validation**: Complete test suite coverage with proper mock implementations

**📚 Documentation Restructuring**
- **Main README Transformation**: Repositioned as "Generic OpenTelemetry Process Monitoring Framework for Instana"
- **Framework Features Highlighted**: Emphasized generic capabilities over specific Strategy₿ implementations
- **Strategy₿ Repositioning**: Clearly labeled existing plugins as "Reference Implementations"
- **Developer Onboarding**: Prominent links to Developer's Guide for immediate plugin development
- **Universal Applicability**: Clear messaging that framework supports monitoring any process type

**🎯 Strategic Rebranding**
- **Complete Migration**: Updated all references from "MicroStrategy" to "Strategy₿" across documentation
- **Brand Consistency**: Maintained technical accuracy while implementing unified branding
- **Enhanced Visual Identity**: Updated architectural diagrams and feature descriptions

### Technical Improvements

**Daemon Mode Infrastructure:**
- Enhanced `base_sensor.py` with continuous monitoring loop functionality
- Proper signal handling for clean shutdowns and resource cleanup
- Configurable collection intervals via environment variables (`COLLECTION_INTERVAL`)
- Resource-efficient continuous monitoring with minimal overhead
- Installation script enhancements for automatic service creation and management

**Framework Components (Now Generic):**
- `common/base_sensor.py` - Universal sensor foundation supporting any process type
- `common/process_monitor.py` - Generic process detection and metrics collection
- `common/otel_connector.py` - OpenTelemetry integration layer with TLS support
- `common/metadata_store.py` - Thread-safe state management for persistent metadata

**Plugin Pattern Standardization:**
- Consistent configuration pattern across all implementations
- Clear separation between framework and plugin-specific settings
- Minimal implementation requirements (SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME)
- Standardized sensor entry points leveraging common framework

**📊 Metadata Schema Versioning System**
- **Version Tracking Infrastructure**: Added `METADATA_SCHEMA_VERSION = "1.0"` to `common/__init__.py` for centralized schema version management
- **Database Migration Framework**: Implemented comprehensive migration system with `schema_version` table for tracking version history
- **Automated Legacy Detection**: Intelligent detection of legacy databases with user warnings and clean migration to v1.0 schema
- **Future-Proofed Architecture**: Extensible design supports incremental schema versions (v1.1, v1.2, etc.)
- **Data Safety**: Complete preservation of existing v1.0 data while safely handling legacy database migration
- **Migration Test Suite**: Added `tests/test_schema_migration.py` with 6 comprehensive test cases covering all migration scenarios

**Migration Behavior:**
- **New Databases**: Created directly with v1.0 schema for optimal performance
- **Legacy Databases**: Detected automatically with user warning, previous metadata deleted, fresh v1.0 schema created
- **Current v1.0 Databases**: No migration needed, existing data fully preserved

### Breaking Changes

None. This release maintains full backward compatibility while adding significant new functionality.

### Migration Guide

Existing Strategy₿ installations continue to work unchanged. For developers wanting to create new plugins:

1. Read the new [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
2. Follow the 6-step Quick Start process
3. Use Strategy₿ plugins as reference implementations
4. Leverage the comprehensive testing and installation script templates

### Quality Assurance

- **Files Reviewed**: 43 files across all components
- **Architecture Validation**: Complete system design review confirming production readiness
- **Security Scan**: All security practices validated with TLS encryption support
- **Performance Analysis**: Resource usage optimized for continuous operation
- **Test Coverage**: 15 test files validated with comprehensive mock framework

---

## Version 0.0.18 (2025-06-05)

### feat: Improved OpenTelemetry metrics display and formatting

- **Enhanced Display**: CPU and memory usage now consistently displayed as percentages
- **Simplified Metric Names**: Metrics now show only the relevant portion (e.g., `cpu_usage`)
- **Improved Service Names**: Services display only the relevant portion after "python"
- **Proper Display Names**: Services use properly formatted display names instead of IDs
- **Consistent Formatting**: All values are now rounded mathematically to 2 decimal places
- **CPU Per-Core Metrics**: Added support for monitoring CPU usage per individual core
- **Persistent Metadata**: Added SQLite-based metadata store for consistent identifiers
- **Advanced Formatting**: Metrics are intelligently formatted based on their type
- **Dynamic Registration**: New metrics can be automatically registered at runtime
- Added comprehensive unit tests for the new metadata store functionality
- Updated process monitor to collect and format per-core CPU metrics
- Enhanced OpenTelemetry connector to work with the metadata store
- Updated base sensor to support metadata store configuration

## Version 0.0.17 (2025-06-05)

### fix: Improved logging configuration with automatic directory creation

- Refactored logging configuration to extract log path resolution into a helper method
- Added automatic creation of log directories if they don't exist
- Made log file paths configurable via command-line arguments
- Improved error handling for log file creation
- Updated .gitignore to exclude log files but track the logs directory structure
- Reduced code duplication in logging setup
- Eliminated "No such file or directory" errors when writing logs
- Improved user experience with better logging configuration
- Enhanced maintainability through better code organization
- Consistent logging behavior across all plugins
- Configurable log destinations via command-line

## Version 0.0.16 (2025-06-05)

### feat: Centralized version parameter and fixed OpenTelemetry Observation yield pattern

- Centralized version parameter in `common/__init__.py` as a single source of truth
- Created a shared `common/extract_version.sh` script to reduce duplication in installation scripts
- Modified all sensor files to import the VERSION from common
- Updated installation scripts to use the shared version extraction script
- Fixed OpenTelemetry Observable callbacks to use the yield Observation pattern
- Added proper import of Observation class at the top of the file
- Enhanced documentation of OpenTelemetry metrics observation with detailed comments
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
