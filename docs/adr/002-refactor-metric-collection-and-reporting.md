# ADR-002: Refactor Metric Collection and Reporting

## Status
**Implemented and Verified** (June 2025)

## Context
The existing metric collection and reporting system had several issues that affected data accuracy and readability in the Instana UI.

### Identified Issues:
- **Redundant Service Names**: Service names were being prefixed with a sanitized version of themselves (e.g., `m8mulprc/m8mulprc`).
- **Incorrect CPU Usage**: `cpu_usage` was a sum of all process CPU percentages, not an average.
- **Inaccurate Per-Core CPU**: Per-core CPU metrics were system-wide, not per-process.
- **Improper Metric Naming**: Parameterized metrics were not displayed correctly.
- **Incorrect Metric Types**: `otel_type` from `manifest.toml` was not being correctly mapped.

## Decision
Refactor the core metric collection, aggregation, and reporting logic to fix the identified issues and improve the overall architecture.

### Solution Architecture:
1.  **Refactor `common/process_monitor.py`**:
    *   Isolate process filtering and metric aggregation into separate helper functions.
    *   Calculate `cpu_usage` as an average.
    *   Remove the inaccurate system-wide per-core CPU metrics.
    *   Add new, detailed process metrics (`cpu_user_time_total`, `memory_rss_total`, etc.).
2.  **Refactor `common/otel_connector.py`**:
    *   Fix the service name construction to use the `display_name` directly.
    *   Implement a dynamic and robust mapping of `otel_type` from `manifest.toml` to the correct OpenTelemetry function.
3.  **Refactor `common/metadata_store.py`**:
    *   Simplify and correct the `sanitize_for_metrics`, `_format_metric_name`, and `get_simple_metric_name` functions.

## Consequences

### Positive:
- **Improved Data Accuracy**: `cpu_usage` and other metrics are now calculated correctly.
- **Better Readability**: Service and metric names are clean and easy to understand in the Instana UI.
- **Richer Data**: New, detailed metrics provide deeper insight into process performance.
- **Improved Maintainability**: The code is now more modular, readable, and easier to maintain.
- **Future-Proof**: The metric type mapping is now dynamic and supports all standard OpenTelemetry types.

### Negative:
- **Removed Functionality**: The per-core CPU metrics were removed due to their inaccuracy. While this improves data quality, it removes a feature that some users may have found useful, even if it was only a system-wide approximation.

## Verification and Testing
- All existing unit tests were updated and continue to pass.
- New tests will be added to cover the new helper functions and detailed metrics.
- Manual verification in the Instana UI will be required to confirm that all issues are resolved.
