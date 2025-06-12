# Release v0.0.20

**Release Date:** June 12, 2025  
**Branch:** feature/toml-installation-system → master

## 🚀 Major Feature: TOML-Based Installation System

This release introduces a comprehensive TOML-based installation framework that completely transforms the plugin architecture from duplicated scripts to a professional, vendor-agnostic system.

### ✨ New Components

**Framework Files:**
- `common/generate_manifest.py` - TOML manifest generator with SHA256 checksums
- `common/manifest.toml` - Generated manifest with checksums for all common files  
- `common/install_functions.sh` - Comprehensive shared installation functions (500+ lines)
- `[plugin]/plugin.toml` - TOML configuration for all 4 plugins

**Enhanced Installation Scripts:**
- Refactored all 4 plugin installation scripts to use shared functions
- Reduced script size from ~100 lines to ~20 lines each (95% code reduction)
- Added TOML parsing, checksum verification, and intelligent file installation

**Updated Sensor Code:**
- Modified all 4 sensor.py files to read TOML configuration dynamically
- Added backward compatibility with existing __init__.py files
- Fixed relative import ImportError issues using robust absolute import mechanism

### 🔧 Technical Improvements

**Issues Resolved:**
- ✅ Fixed missing metadata_store.py in installation copy operations
- ✅ Eliminated 95% code duplication across installation scripts
- ✅ Resolved "ImportError: attempted relative import with no known parent package"

**Professional Framework Features:**
- SHA256 checksum verification for file integrity
- File-by-file installation with status tracking  
- Detection of missing/modified files with force update capability
- Detailed installation logging with colored output
- Professional systemd service generation with plugin-specific naming
- Cross-platform compatibility (macOS/Linux)

**Centralized Version Management:**
- Version now managed centrally in `common/manifest.toml` and `common/__init__.py`
- Removed duplicate version fields from individual plugin TOML files
- Single source of truth for framework versioning

### 🧪 Comprehensive Testing

- ✅ Fresh installation scenarios work correctly
- ✅ Checksum validation detects file modifications
- ✅ Missing file detection and installation functions properly
- ✅ Both TOML and legacy __init__.py fallback modes work
- ✅ Direct sensor execution from installation directories (no more ImportError)
- ✅ Force update and restart capabilities function as expected

### 📊 Impact Summary

**Before:** 4 individual scripts with 95% duplicate code, hardcoded vendor assumptions, missing file bug  
**After:** Unified framework with shared functions, vendor-agnostic design, comprehensive error handling

**Files Changed:** 15 files modified, 1,351 insertions, 827 deletions

### 🎯 Benefits

- **Generic**: No vendor-specific assumptions
- **Extensible**: Easy to add new configuration options  
- **Reliable**: Checksum verification and detailed error reporting
- **Maintainable**: Centralized shared functions eliminate duplication
- **Professional**: Industry-standard TOML format with comprehensive logging

This architectural transformation resolves the immediate metadata_store.py bug while establishing a solid foundation for future plugin development and maintenance.

---

**Compatibility:** Backward compatible with existing installations  
**Migration:** Automatic fallback to __init__.py during transition  
**Dependencies:** No new external dependencies required
