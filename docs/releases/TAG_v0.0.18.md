# v0.0.18 Release Notes

## Improvements to OpenTelemetry Metrics Display

This release focuses on improving how metrics are displayed in the Instana instance when using OpenTelemetry:

### Metrics Display Enhancements

- **CPU and Memory as Percentages**: CPU and memory usage metrics are now consistently displayed as percentages.
- **Simplified Metric Names**: Metric names in Instana now show only the relevant portion (e.g., `cpu_usage` instead of `com.instana.plugin.python.microstrategy_m8mulprc/cpu_usage{}`).
- **Improved Service Names**: Service names now display only the relevant portion after "python" (e.g., `microstrategy_m8mulprc` instead of `com.instana.plugin.python.microstrategy_m8mulprc`).
- **Proper Display Names**: Services now use a properly formatted display name instead of just the ID.
- **Consistent Decimal Formatting**: All values are now rounded mathematically to 2 decimal places for consistency.
- **CPU Per-Core Metrics**: Added support for monitoring CPU usage per individual core.

### New Features

- **Persistent Metadata Storage**: Added a SQLite-based metadata store to maintain consistent identifiers and display names across restarts.
- **Advanced Metric Formatting**: Metrics are now intelligently formatted based on their type (percentage, numeric, etc.).
- **Dynamic Metric Registration**: New metrics can be automatically registered at runtime with proper formatting.

### Code Improvements

- Added comprehensive unit tests for the new metadata store functionality.
- Updated the process monitor to collect and format per-core CPU metrics.
- Enhanced the OpenTelemetry connector to work with the metadata store.
- Updated base sensor to support metadata store configuration.

### Requirements

- A new dependency on SQLite (already included in standard Python installations).
- The metadata database is stored by default in `~/.instana_plugins/metadata.db`.
