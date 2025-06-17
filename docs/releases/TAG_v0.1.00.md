# Release v0.1.00

**Release Date:** June 16, 2025  
**Branch:** fix/psutil-migration-ps-compatibility → master

## 🚀 Major Enhancement: --once Flag Console Output & User Experience

This release introduces significant improvements to the `--once` flag functionality, transforming it from a silent execution mode into a user-friendly debugging and testing tool with immediate console feedback.

### ✨ New Features

**Enhanced Console Output:**
- **Success Case**: Displays collected metrics with visual indicators (✓)
- **Failure Case**: Provides helpful diagnostic messages with explanations (✗)
- **Real-time Feedback**: Immediate console output without requiring log file inspection

**Argument Validation:**
- **Warning System**: Alerts when `--once` and `--interval` flags conflict
- **Help Text Updates**: Clear documentation of flag interactions and behaviors
- **User Guidance**: Self-documenting command line interface

### 🔧 Technical Improvements

**Core Functionality Changes:**
- ✅ Skip daemonization when using `--once` flag to preserve console output
- ✅ Enhanced console output for both success and failure scenarios
- ✅ Argument validation with warning when `--once` and `--interval` are combined
- ✅ Updated help text to clarify flag interactions and behaviors

**User Experience Enhancements:**
```bash
# Success case example
$ python3 sensor.py --once
✓ Successfully collected 21 metrics for 'python':
  cpu_usage: 90.2
  memory_usage: 0.37
  process_count: 5
  [... all metrics displayed]

# Failure case example  
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

### 📊 Benefits Summary

**Before v0.1.00:**
- `--once` flag executed silently with no console feedback
- Users had to check log files to see results
- No validation of conflicting arguments
- Confusing user experience for debugging

**After v0.1.00:**
- Immediate, visual console feedback with ✓/✗ indicators
- Clear diagnostic messages for troubleshooting
- Argument validation prevents user confusion
- Self-documenting help text explains behaviors

### 🎯 Use Cases Enhanced

**Debugging & Testing:**
- Immediate feedback for process monitoring validation
- Quick verification of metric collection without log parsing
- Clear error messages for troubleshooting connectivity issues

**Development Workflow:**
- Fast iteration testing during plugin development
- Visual confirmation of successful metric collection
- Easy identification of configuration problems

**Production Validation:**
- One-time health checks with clear success/failure indicators
- Quick verification of plugin functionality
- Diagnostic information for system administrators

### 🛠️ Technical Implementation

**Files Modified:**
- `common/base_sensor.py` - Core functionality enhancements

**Key Changes:**
1. **Conditional Daemonization**: Skip daemon mode for `--once` to preserve stdout/stderr
2. **Console Output Logic**: Add formatted output with visual indicators and metric display
3. **Argument Validation**: Check for conflicting flags and provide user warnings
4. **Help Text Updates**: Document flag interactions and expected behaviors

### 🔄 Version Management

**Centralized Versioning:**
- Version updated to `0.1.00` in `common/manifest.toml`
- Dynamic version reading from TOML configuration
- Fallback default maintained for error scenarios

**Backward Compatibility:**
- All existing functionality preserved
- No breaking changes to existing workflows
- Enhanced behavior only affects `--once` flag usage

---

**Impact:** Transforms `--once` from a silent execution mode into a powerful debugging and testing tool  
**Compatibility:** Fully backward compatible with existing installations  
**Migration:** No migration required - enhancements are automatically available  
**Dependencies:** No new external dependencies required

This release significantly improves the developer and operator experience when using the plugins for testing, debugging, and one-time metric collection scenarios.
