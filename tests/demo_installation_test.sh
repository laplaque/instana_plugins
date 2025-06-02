#!/bin/bash
#
# MIT License
#
# Copyright (c) 2025 laplaque/instana_plugins Contributors
#
# This file is part of the Instana Plugins collection.
# Version: 0.0.13
#
# Demonstration script for testing Instana plugin installations
#

# Set error handling
set -e

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print header
function print_header {
    echo -e "\n${BLUE}=================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}=================================================================${NC}\n"
}

# Print section
function print_section {
    echo -e "\n${CYAN}--- $1 ---${NC}\n"
}

# Change to the project root directory
cd "$(dirname "$0")/.."
REPO_ROOT="$(pwd)"

print_header "Instana Plugins Installation Test Demonstration"
echo -e "This script demonstrates how to test if your Instana plugins installation worked correctly."
echo -e "Current directory: ${REPO_ROOT}"

# Step 1: Install dependencies if needed
print_section "Step 1: Checking dependencies"
echo -e "First, let's make sure all required dependencies are installed:"
echo -e "${YELLOW}python3 -m pip install -r common/requirements.txt${NC}"
echo -e "In this demo, we'll check if the dependencies are installed and whether you need"
echo -e "to install requirements for each plugin separately or just once for all plugins."

cd "${REPO_ROOT}/tests"
echo -e "\nRunning dependency check..."
echo -e "${YELLOW}./test_installation.py --dependencies-only${NC}"
./test_installation.py --dependencies-only || {
    echo -e "\n${RED}Some dependencies are missing. Please install them with:${NC}"
    echo -e "${YELLOW}python3 -m pip install -r ../common/requirements.txt${NC}"
    echo -e "Then run this demo again."
    exit 1
}

echo -e "\n${MAGENTA}Note: The test will tell you if you need to install requirements for each plugin separately${NC}"
echo -e "${MAGENTA}or if installing the common requirements is sufficient for all plugins.${NC}"

# Step 2: Check for plugin installations
print_section "Step 2: Checking for plugin installations"
echo -e "Now, let's check if any plugins are installed:"
echo -e "${YELLOW}./test_installation.py${NC}"
echo -e "\nThis will check for installations in standard locations:"
echo -e "  - /opt/instana/agent/plugins/custom_sensors/"
echo -e "  - ~/.local/share/instana/plugins/"
echo -e "  - ./installed_plugins/"
echo -e "\n${MAGENTA}Note: You may need to create a local test environment first${NC}"

# Step 3: Installing plugins for local testing
print_section "Step 3: Creating a local test environment (optional)"
echo -e "If you don't want to install the plugins system-wide, you can create a local test environment:"

echo -e "\n1. Create a local plugins directory:"
echo -e "${YELLOW}mkdir -p ./installed_plugins${NC}"

echo -e "\n2. Install plugins locally (for example, m8mulprc):"
echo -e "${YELLOW}cd m8mulprc${NC}"
echo -e "${YELLOW}./install-instana-m8mulprc-plugin.sh -d ../../installed_plugins/microstrategy_m8mulprc${NC}"

echo -e "\n3. Run the test against the local installation:"
echo -e "${YELLOW}cd ../tests${NC}"
echo -e "${YELLOW}./test_installation.py${NC}"

# Step 4: Testing specific plugins
print_section "Step 4: Testing specific plugins"
echo -e "You can also test only specific plugins:"
echo -e "${YELLOW}./test_installation.py --plugin m8mulprc${NC}"
echo -e "\nOr multiple specific plugins:"
echo -e "${YELLOW}./test_installation.py --plugin m8mulprc --plugin mstrsvr${NC}"

# Step 5: Manual testing
print_section "Step 5: Manual testing (if needed)"
echo -e "If the automatic test fails, you can also test a plugin manually:"
echo -e "\n1. Set the PYTHONPATH to the installation directory:"
echo -e "${YELLOW}export PYTHONPATH=/path/to/installation/microstrategy_m8mulprc${NC}"

echo -e "\n2. Run the sensor directly with debug logging:"
echo -e "${YELLOW}python3 /path/to/installation/microstrategy_m8mulprc/sensor.py --run-once --log-level=DEBUG${NC}"

# Conclusion
print_header "Conclusion"
echo -e "These steps will help you verify that your Instana plugin installation is working correctly."
echo -e "For detailed information about testing options, see: ${GREEN}tests/README.md${NC}"
echo -e "\nIf you encounter issues, check the following:"
echo -e "1. Make sure Python 3 and required dependencies are installed"
echo -e "2. Verify the plugin installation paths are correct"
echo -e "3. Check that the Instana agent is configured correctly"
echo -e "4. Look for errors in the test output"
echo -e "\nFor troubleshooting, run the test with the --log-level=DEBUG flag:"
echo -e "${YELLOW}./test_installation.py --plugin m8mulprc --log-level=DEBUG${NC}"

echo -e "\n${GREEN}Happy monitoring!${NC}\n"

exit 0
