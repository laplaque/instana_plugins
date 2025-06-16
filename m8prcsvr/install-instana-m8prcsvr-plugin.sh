#!/bin/bash
#
# MIT License
#
# Copyright (c) 2025 laplaque/instana_plugins Contributors
#
# This file is part of the Instana Plugins collection.
#

# M8PrcSvr Instana Plugin Installer
# ---------------------------------

# Set error handling
set -e

# Define script directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$( dirname "$SCRIPT_DIR" )"

# Source shared installation functions
source "${PARENT_DIR}/common/install_functions.sh"

# Default installation directory
DEFAULT_BASE_DIR="/opt/instana_plugins"

# Parse command line arguments
BASE_DIR=$DEFAULT_BASE_DIR
FORCE_UPDATE=false
RESTART_SERVICE=false

function show_usage {
    echo "Usage: $0 [OPTIONS]"
    echo "Install the MicroStrategy M8PrcSvr monitoring plugin for Instana"
    echo ""
    echo "Options:"
    echo "  -d, --directory DIR    Base installation directory (default: ${DEFAULT_BASE_DIR})"
    echo "  -f, --force-update     Force update of existing files"
    echo "  -r, --restart          Start/restart service after installation"
    echo "  -h, --help             Show this help message and exit"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--directory)
            BASE_DIR="$2"
            shift 2
            ;;
        -f|--force-update)
            FORCE_UPDATE=true
            shift
            ;;
        -r|--restart)
            RESTART_SERVICE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Call the main installation function
install_plugin "$SCRIPT_DIR" "$BASE_DIR" "$FORCE_UPDATE" "$RESTART_SERVICE"
