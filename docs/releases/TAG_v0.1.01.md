# TAG_v0.1.01

## Version: v0.1.01
## Date: 2025-06-17
## Type: Feature Release - Database Connection Management & Metric Formatting

### Summary
Enhanced database connection management with centralized context managers and critical metric formatting fixes for improved reliability and user experience. This release addresses GitHub Copilot code review recommendations and ensures proper resource management.

### Database Connection Management (New)
- **Centralized Connection Manager**: Implemented `_get_db_connection()` method for single point of control
- **Context Manager Pattern**: All database operations now use proper `with` statements for automatic resource cleanup
- **Exception Safety**: Improved error handling and connection cleanup in case of exceptions
- **Code Consistency**: Standardized database connection pattern across all methods in `MetadataStore` class
- **Resource Management**: Automatic cleanup prevents connection leaks and improves system stability
- **GitHub Copilot Review**: Addressed code review recommendation for using context managers in SQLite connections

### Metric Formatting Fixes (Existing)
- **Metric Names**: Removed trailing braces from metric names in Instana UI
- **Integer Decimals**: Fixed integer values displaying with unnecessary decimal places
- **Percentage Display**: Corrected percentage metrics to show proper decimal precision

### Changes Made
- **Enhanced `common/metadata_store.py`**: 
  - Added centralized `_get_db_connection()` context manager method
  - Updated critical database methods: `_cache_metrics_schema()`, `_get_current_schema_version()`, `_set_schema_version()`, migration methods, and CRUD operations
  - Replaced manual connection/close patterns with context managers
  - Maintained all existing functionality while improving reliability
- **Enhanced `common/otel_connector.py`**: 
  - Added `decimals` field reading from manifest.toml
  - Implemented proper formatting based on metric configuration
  - Fixed metric name cleaning to remove trailing braces
- **Documentation**: Created ADR-001 for architectural decision record
- **Updated metric formatting logic**: Applied manifest-specified decimal places instead of hardcoded values
- **Maintained backward compatibility**: Existing installations continue to work unchanged

### Technical Impact

**Database Connection Management:**
- **Before**: Manual connection patterns with potential resource leaks
  ```python
  conn = sqlite3.connect(self.db_path)
  cursor = conn.cursor()
  # ... operations ...
  conn.close()
  ```
- **After**: Centralized context manager with automatic cleanup
  ```python
  with self._get_db_connection() as conn:
      cursor = conn.cursor()
      # ... operations ...
      # Automatic cleanup
  ```

**Metric Display:**
- **Before**: Metrics displayed as `cpu_usage{}` with `42.678912` (excessive decimals)
- **After**: Metrics display as `cpu_usage` with `42.68` (proper formatting)
- **Integer metrics**: Now display as `15` instead of `15.000`
- **Percentages**: Display with specified precision (e.g., `85.23%` instead of `85.234567`)

### Compatibility
- **Backward Compatible**: No breaking changes
- **Migration Required**: None
- **Dependencies**: No changes to external dependencies
- **Database**: All existing functionality preserved with improved reliability

### Testing
- ✅ All database tests pass with new connection manager implementation
- ✅ Verified formatting fixes with comprehensive test suite
- ✅ Confirmed proper decimal handling for all metric types (Gauge, Counter, UpDownCounter)
- ✅ Validated metric name cleaning functionality
- ✅ Exception safety verified with database operations

### Architecture Decision Record
- **ADR-001**: Created comprehensive architectural decision record documenting the database connection management changes
- **Documentation**: Enhanced release notes with technical implementation details
- **Code Quality**: Addresses GitHub Copilot code review recommendations for better resource management

### Deployment
Ready for immediate deployment to all environments. No downtime required, improvements visible immediately after deployment.
