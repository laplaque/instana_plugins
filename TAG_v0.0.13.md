# Version 0.0.13 Release Notes

This release adds installation testing capability, dependency management improvements, and simplifies the installation process.

## New Features
- Added installation testing system to verify plugin installations
- Created dependency checking to avoid reinstalling packages
- Updated all installation scripts with dependency verification
- Simplified installation directory structure with standalone plugins approach

## Improvements
- Installation scripts now skip package installation when dependencies are satisfied
- Added comprehensive testing documentation
- Added demonstration script for installation testing
- Changed default installation directory to `/opt/instana_plugins/`
- Removed dependency on Instana agent directories
- Improved service naming convention to `instana-microstrategy-{process}-monitor`
- Removed unnecessary plugin.json files

## Technical Details
- Created `check_dependencies.py` to verify Python dependencies before installation
- Added `test_installation.py` to verify plugin installations work correctly
- Created comprehensive testing documentation in `tests/README.md`
- Added `demo_installation_test.sh` as a guided walkthrough of installation testing
- Updated all installation scripts to use the new directory structure
- Modified test framework to support both old and new directory structures
- Simplified plugin detection in installation test

# This file is part of the Instana Plugins collection.
