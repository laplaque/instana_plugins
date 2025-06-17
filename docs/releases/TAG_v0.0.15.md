# TAG v0.0.15

## fix: Updated ObservableGauge API usage for OpenTelemetry >= 1.20.0

- Fixed `'_ObservableGauge' object has no attribute 'observe'` error
- Updated implementation to use the newer OpenTelemetry API pattern
- Changed to pass callbacks directly to create_observable_gauge method
- Improved metric observation with proper callback parameter handling
- Updated tests to match the new implementation pattern
- Ensures compatibility with OpenTelemetry version 1.20.0 and newer
