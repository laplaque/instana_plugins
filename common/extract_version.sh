#!/bin/bash
#
# MIT License
#
# Copyright (c) 2025 laplaque/instana_plugins Contributors
#
# This file is part of the Instana Plugins collection.
#

# Extract version from common/__init__.py
# This script is sourced by installation scripts to reduce code duplication

# Usage: Source this script from any installer script
# The caller should define PARENT_DIR before sourcing this script

# Ensure PARENT_DIR is defined
if [ -z "${PARENT_DIR}" ]; then
    # Try to determine PARENT_DIR from the sourced script location
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    PARENT_DIR="$( dirname "$SCRIPT_DIR" )"
    echo "Warning: PARENT_DIR was not defined, assuming ${PARENT_DIR}"
fi

# Extract version from common/__init__.py
if [ -f "${PARENT_DIR}/common/__init__.py" ]; then
    VERSION=$(python3 -c "import sys; sys.path.insert(0, '${PARENT_DIR}'); from common import VERSION; print(VERSION)")
    echo "Plugin version: ${VERSION}"
else
    echo "Warning: Could not find common/__init__.py to extract version"
    VERSION="unknown"
fi

export VERSION
