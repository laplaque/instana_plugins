# TAG v0.0.14

## fix: Fixed OpenTelemetry metric recording with ObservableGauge

This release fixes a critical issue with OpenTelemetry metric recording, specifically addressing the error:
`'_Gauge' object has no attribute 'record'`

### Changes

- Replaced direct `Gauge.record()` calls with `ObservableGauge` and appropriate callbacks
- Updated the metric recording system to store metrics in a state dictionary and observe them via callbacks
- Each metric now has its own ObservableGauge with proper description for better visualization in Instana
- Improved error handling for non-numeric metrics
- Enhanced testing of the OpenTelemetry connector
- Added comprehensive test cases for the new metric observation pattern
- Updated release notes with detailed information about the fix

### Impact

This change makes the plugins compatible with the OpenTelemetry metric API, which requires using `ObservableGauge` with callbacks rather than directly recording values with `Gauge.record()`.

### Affected Files

- `common/otel_connector.py` - Major refactoring of the metric recording system
- `tests/test_otel_connector.py` - Updated tests to verify the new implementation
- `RELEASE_NOTES.md` - Added information about the fix

### Contributors

- Instana Plugins Team
