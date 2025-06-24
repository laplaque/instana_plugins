# ADR-003: Simplify Database Schema Creation and Migration Logic

## Status
**Implemented** (June 2025)

## Context
The existing database schema creation and migration logic in `common/metadata_store.py` was complex and had several issues:

### Identified Issues:
- **Complex Migration Logic**: The original implementation used a complex `_run_migrations()` method that tried to handle all possible migration paths.
- **Redundant Code**: Multiple methods were duplicated, making maintenance difficult.
- **Poor Code Organization**: Functions were scattered throughout the file without logical grouping.
- **Inconsistent Schema Handling**: Different code paths for new databases vs. existing databases led to potential inconsistencies.
- **Overly Complex Decision Trees**: The migration logic was difficult to follow and prone to edge case bugs.

## Decision
Refactor the database schema creation logic to use a simplified, generic approach that is easier to understand, maintain, and test.

### Solution Architecture:

#### New 5-Step Schema Creation Logic:
1. **Determine if a schema is available** using `_schema_exists()`
2. **Determine the schema version if available** using `_get_current_schema_version()`
3. **If schema exists and is version 1.0**, migrate to version 2.0
4. **If schema exists but has no version table**, drop database and create version 2.0
5. **If no schema exists**, create version 2.0 directly

#### Code Organization Improvements:
- **DATABASE INITIALIZATION**: All schema creation and initialization logic
- **SCHEMA VERSION MANAGEMENT**: Version detection and setting methods
- **DATABASE CONNECTION MANAGEMENT**: Connection handling and schema caching
- **CORE CRUD OPERATIONS**: Business logic methods for data access

#### Simplified Migration Strategy:
- **Only one migration path**: 1.0 → 2.0
- **Drop and recreate** for legacy databases without version information
- **Direct creation** for new databases (skip intermediate versions)

## Implementation Details

### Key Changes:
1. **Replaced complex `_run_migrations()`** with simple `_init_db()` logic
2. **Added `_schema_exists()`** to reliably detect existing schemas
3. **Added `_drop_database()`** for clean legacy database removal
4. **Reorganized all methods** into logical functional groups
5. **Removed duplicate methods** and redundant code paths
6. **Kept `_run_migrations()`** for backward compatibility (marked as deprecated)

### Migration Logic:
```python
def _init_db(self):
    schema_exists = self._schema_exists()
    
    if schema_exists:
        current_version = self._get_current_schema_version()
        
        if current_version == "1.0":
            # Step 3: Migrate to version 2.0
            self._migrate_to_version_2_0()
        elif current_version is None:
            # Step 4: Drop and recreate
            self._drop_database()
            self._create_schema_version_2_0()
        else:
            # Already at target version
            pass
    else:
        # Step 5: Create version 2.0
        self._create_schema_version_2_0()
```

## Consequences

### Positive:
- **Simplified Logic**: Easy to understand and follow 5-step process
- **Better Maintainability**: Logical code organization with clear functional groups
- **Reduced Complexity**: Eliminated complex decision trees and redundant code paths
- **Improved Reliability**: Clear handling of edge cases (legacy databases, new databases)
- **Enhanced Testability**: Simpler logic is easier to test and verify
- **Better Performance**: Direct schema creation for new databases (no intermediate steps)

### Negative:
- **Breaking Change for Legacy Systems**: Systems with very old schema versions (pre-1.0) will have their databases dropped and recreated
- **Data Loss**: Legacy databases without version tables will lose existing data (acceptable trade-off for reliability)

## Verification and Testing
- **Unit Tests**: All existing tests pass (6/6 for metadata_store, 8/8 for schema_migration)
- **Integration Tests**: Verified new database creation, migration from 1.0 to 2.0, and legacy database handling
- **Backward Compatibility**: Existing functionality preserved while improving the underlying implementation

## Migration Guide
For users upgrading from previous versions:
- **Schema 1.0**: Will automatically migrate to 2.0
- **Legacy schemas**: Will be dropped and recreated (data loss expected)
- **New installations**: Will create schema 2.0 directly

This change ensures robust, predictable database schema management going forward.
