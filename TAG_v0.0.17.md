# TAG v0.0.17

## fix: Improved logging configuration with automatic directory creation

This release addresses a logging issue by enhancing the logging configuration to ensure log directories exist and improving the code structure based on code review feedback.

### Changes

- Refactored logging configuration to extract log path resolution into a helper method
- Added automatic creation of log directories if they don't exist
- Made log file paths configurable via command-line arguments
- Improved error handling for log file creation
- Updated .gitignore to exclude log files but track the logs directory structure
- Reduced code duplication in logging setup

### Impact

- Eliminated "No such file or directory" errors when writing logs
- Improved user experience with better logging configuration
- Enhanced maintainability through better code organization
- Consistent logging behavior across all plugins
- Configurable log destinations via command-line

### Affected Files

- `common/logging_config.py` - Refactored with new `_resolve_log_file_path` helper function
- `common/base_sensor.py` - Added `--log-file` command-line argument
- `.gitignore` - Updated to exclude log files but include logs directory
- `logs/.gitkeep` - Added to track the logs directory in git

### Contributors

- Instana Plugins Team
