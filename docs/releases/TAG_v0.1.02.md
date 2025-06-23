# TAG v0.1.02 - Metric Types Enforcement Implementation

## Release Information
- **Version**: v0.1.02
- **Release Date**: 2025-06-23
- **Previous Version**: v0.1.01
- **Type**: Bug Fix / Implementation

## Summary
Fixed critical issue where OpenTelemetry metrics were all created as GAUGE type regardless of TOML configuration. Implemented proper metric type enforcement and improved architecture following "register once, read many" principle.

## Key Changes

### Fixed Metric Type Enforcement
- **Issue**: All metrics appeared as GAUGE in Instana despite TOML `otel_type` configuration
- **Root Cause**: `_register_observable_metrics()` ignored `otel_type` and always called `create_observable_gauge()`
- **Solution**: Created unified `create_observable()` method that dynamically calls correct OpenTelemetry methods based on TOML `otel_type`

### Implemented "Register Once, Read Many" Architecture
- **Installation time**: TOML definitions synced to database
- **Service startup**: TOML changes detected and database updated
- **Runtime**: Only database registry used, no dynamic TOML reading

### Enhanced Metric Type Support
- **Gauge**: `create_observable_gauge()` for metrics like `cpu_usage`, `memory_usage`
- **Counter**: `create_observable_counter()` for metrics like `disk_read_bytes`, `voluntary_ctx_switches`
- **UpDownCounter**: `create_observable_up_down_counter()` for metrics like `process_count`, `thread_count`

### Strict TOML Compliance
- Removed dynamic metric registration functions (`_register_metric_if_new`, `_register_new_metric`)
- Runtime metric validation against database registry
- Clear rejection logging for undefined metrics

## Code Changes

### Modified Files
- `common/otel_connector.py`: Major refactoring of metric registration system
- `common/manifest.toml`: Version bump to 0.1.02

### New Methods
- `create_observable()`: Unified metric creation based on TOML `otel_type`
- `_sync_toml_to_database()`: Sync TOML changes to database registry
- Enhanced `_register_observable_metrics()`: Database-driven metric registration

### Removed Methods
- `_register_metric_if_new()`: No longer needed with strict TOML compliance
- `_register_new_metric()`: Replaced by database-driven approach

## Database Schema Requirements

### New MetadataStore Methods Required
```python
# These methods need to be implemented in MetadataStore
def sync_metric_from_toml(service_id, name, unit, otel_type, decimals, 
                         is_percentage, is_counter, description, 
                         pattern_type=None, pattern_source=None, pattern_range=None)

def remove_obsolete_metrics(service_id, current_metric_names)

def get_service_metrics(service_id)
```

## Testing

### Validation Steps
1. Start m8mulprc service with updated code
2. Verify metrics appear with correct types in Instana:
   - Gauges: `cpu_usage`, `memory_usage`, `avg_threads_per_process`
   - Counters: `disk_read_bytes`, `disk_write_bytes`, `voluntary_ctx_switches`
   - UpDownCounters: `process_count`, `thread_count`, `open_file_descriptors`
3. Test TOML changes: add/remove metrics and restart service
4. Verify runtime rejection of undefined metrics

## Impact

### Fixed Issues
- Metrics now appear with correct types in Instana UI
- Proper OpenTelemetry compliance
- Units and formatting correctly applied from TOML

### Architecture Improvements
- Database-driven metric registry
- Elimination of hardcoded metric classifications
- Clean separation of configuration and runtime concerns

## Breaking Changes
None. Existing metrics continue to work with correct types.

## Next Steps
1. Implement required MetadataStore database methods
2. Test comprehensive metric type enforcement
3. Validate across all Strategy₿ plugins (m8mulprc, m8prcsvr, m8refsvr, mstrsvr)

## Contributors
- Implementation: OpenTelemetry metric type enforcement system
- Architecture: Database-driven metric registry design
