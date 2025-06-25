# Release v0.1.03

## Fixes and Improvements

This release fixes several critical bugs related to how metrics are reported and displayed in Instana. It also adds new, more detailed metrics for better process monitoring.

**Key Fixes:**

*   **Cleaner Service Names:** Service names in Instana will no longer have a repetitive prefix (e.g., `m8mulprc/m8mulprc` is now just `m8mulprc`).
*   **Accurate CPU Usage:** The `cpu_usage` metric now correctly shows the *average* CPU usage across all monitored processes, not the sum.
*   **Better Metric Names:** Metric names with parameters are now displayed correctly.
*   **Correct Metric Types:** Metrics now appear with their proper types (e.g., `Gauge`, `Counter`) as defined in the configuration.
*   **Proper Percentage Formatting:** Percentage-based metrics are now sent correctly, so they display properly in Instana. Special handling has been added for CPU metrics that can exceed 100% in multi-core systems.

**New Features:**

*   **More Detailed Metrics:** We've added new metrics for more in-depth analysis, including:
    *   Total CPU user time
    *   Total CPU system time
    *   Total RSS memory
    *   Total virtual memory

**Technical Improvements:**

*   The code for monitoring processes and sending metrics has been reorganized to be more modular, readable, and easier to maintain.

## Database Schema Management Improvements

This release also includes significant improvements to the database schema creation and migration logic:

**Key Improvements:**

*   **Simplified Schema Creation Logic:** Replaced complex migration paths with a straightforward 5-step process that handles all database states consistently.
*   **Better Code Organization:** Clustered functions into logical sections (Database Initialization, Schema Version Management, Database Connection Management, Core CRUD Operations) for improved readability and maintenance.
*   **Enhanced Reliability:** Clear handling of edge cases including legacy databases without version tables and new database creation.
*   **Improved Performance:** New databases are created directly with the latest schema version (2.0) without unnecessary intermediate steps.
*   **Reduced Complexity:** Eliminated redundant code paths and duplicate method definitions.

**Technical Changes:**

*   **Database Initialization**: New `_init_db()` method implements simplified 5-step logic: detect schema existence, check version, migrate from 1.0 to 2.0 if needed, drop and recreate legacy databases, or create version 2.0 directly.
*   **Schema Detection**: Added `_schema_exists()` and `_drop_database()` methods for reliable database state management.
*   **Code Organization**: Functions are now grouped into logical sections with clear separation of concerns.
*   **Migration Strategy**: Only one migration path (1.0 → 2.0) with automatic handling of legacy databases.

**Migration Behavior:**
*   **Schema 1.0**: Automatically migrated to version 2.0
*   **Legacy databases (no version)**: Dropped and recreated with version 2.0
*   **New installations**: Created directly with version 2.0
*   **Existing version 2.0**: No changes required

**Testing:**
*   All existing tests continue to pass (6/6 for metadata_store, 8/8 for schema_migration)
*   Comprehensive test coverage validates new database creation, migration scenarios, and legacy database handling

**Architecture Decision Record:**
*   Added ADR-003 documenting the simplified database schema creation approach
*   Detailed rationale for moving from complex migration logic to simplified 5-step process
