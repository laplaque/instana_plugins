# TAG v0.0.16

## feat: Centralized version parameter and fixed OpenTelemetry Observation yield pattern

This release builds on v0.0.15 by centralizing the version parameter across all plugin components and further enhancing the OpenTelemetry implementation.

### Changes

- Centralized version parameter in `common/__init__.py` as a single source of truth
- Created a shared `common/extract_version.sh` script to reduce duplication in installation scripts
- Modified all sensor files to import the VERSION from common
- Updated installation scripts to use the shared version extraction script
- Fixed OpenTelemetry Observable callbacks to use the yield Observation pattern
- Added proper import of Observation class at the top of the file
- Enhanced documentation of OpenTelemetry metrics observation with detailed comments

### Impact

- Simplified version management: version only needs to be updated in one place
- Eliminated potential version inconsistencies between different components
- Improved maintainability for future releases
- Further enhanced compatibility with latest OpenTelemetry API for metrics observation

### Affected Files

- `common/__init__.py` - Added centralized VERSION constant
- `common/extract_version.sh` - New shared script for version extraction
- `common/otel_connector.py` - Updated observable metric callbacks to use yield pattern and improved documentation
- `m8mulprc/sensor.py` - Removed hardcoded version, now imports from common
- `m8prcsvr/sensor.py` - Removed hardcoded version, now imports from common
- `m8refsvr/sensor.py` - Removed hardcoded version, now imports from common
- `mstrsvr/sensor.py` - Removed hardcoded version, now imports from common
- All installation scripts - Updated to use the shared version extraction script

### Contributors

- Instana Plugins Team
