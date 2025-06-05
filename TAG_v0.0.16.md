# TAG v0.0.16

## feat: Centralized version parameter and fixed OpenTelemetry Observation yield pattern

This release builds on v0.0.15 by centralizing the version parameter across all plugin components and further enhancing the OpenTelemetry implementation.

### Changes

- Centralized version parameter in `common/__init__.py` as a single source of truth
- Modified all sensor files to import the VERSION from common
- Updated installation scripts to extract the version dynamically from Python
- Fixed OpenTelemetry Observable callbacks to use the yield Observation pattern
- Added proper import of Observation class at the top of the file

### Impact

- Simplified version management: version only needs to be updated in one place
- Eliminated potential version inconsistencies between different components
- Improved maintainability for future releases
- Further enhanced compatibility with latest OpenTelemetry API for metrics observation

### Affected Files

- `common/__init__.py` - Added centralized VERSION constant
- `common/otel_connector.py` - Updated observable metric callbacks to use yield pattern
- `m8mulprc/sensor.py` - Removed hardcoded version, now imports from common
- `m8prcsvr/sensor.py` - Removed hardcoded version, now imports from common
- `m8refsvr/sensor.py` - Removed hardcoded version, now imports from common
- `mstrsvr/sensor.py` - Removed hardcoded version, now imports from common
- All installation scripts - Updated to extract version from Python

### Contributors

- Instana Plugins Team
