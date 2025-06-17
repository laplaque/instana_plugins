# v0.0.11 Release

This tag marks the release of version 0.0.11 of the Instana Plugins Collection.

## Changes in this release

- Added `-d/--directory` parameter to all plugin installation scripts for specifying custom installation directories
- Updated m8refsvr/install-instana-m8refsvr-plugin.sh to support the `-d` parameter
- Updated m8prcsvr/install-instana-m8prcsvr-plugin.sh to support the `-d` parameter
- Added `-r/--restart` parameter for consistent service control across all plugins
- Updated documentation in affected README files
- Ensured all plugins now have consistent command-line parameters and behavior

This release improves installation flexibility across all plugins, enabling users to install sensors in custom locations, particularly useful for installations with non-standard paths.
