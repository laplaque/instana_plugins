#!/bin/bash
#
# MIT License
#
# Copyright (c) 2025 laplaque/instana_plugins Contributors
#
# Demo script to show how to install and test the plugins with shared common directory
#

# Colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Define base directory for the installation
BASE_DIR="./installed_plugins"

# Set error handling
set -e

echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}   Instana Plugins Installation Demo                   ${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo -e "${YELLOW}This script demonstrates how to install all plugins with a shared common directory${NC}"
echo -e "${YELLOW}Base installation directory: ${BASE_DIR}${NC}"
echo

# Clean up any previous installation
if [ -d "${BASE_DIR}" ]; then
    echo -e "${YELLOW}Cleaning up previous installation...${NC}"
    rm -rf "${BASE_DIR}"
    echo -e "${GREEN}Previous installation removed.${NC}"
fi

# Create base directory
mkdir -p "${BASE_DIR}"
echo -e "${GREEN}Created base directory: ${BASE_DIR}${NC}"
echo

# Install each plugin to the base directory
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}   Installing plugins with shared common directory     ${NC}"
echo -e "${BLUE}=======================================================${NC}"

echo -e "${YELLOW}1. Installing M8MulPrc plugin...${NC}"
./m8mulprc/install-instana-m8mulprc-plugin.sh -d "${BASE_DIR}"
echo -e "${GREEN}M8MulPrc plugin installed.${NC}"
echo

echo -e "${YELLOW}2. Installing M8PrcSvr plugin...${NC}"
./m8prcsvr/install-instana-m8prcsvr-plugin.sh -d "${BASE_DIR}"
echo -e "${GREEN}M8PrcSvr plugin installed.${NC}"
echo

echo -e "${YELLOW}3. Installing M8RefSvr plugin...${NC}"
./m8refsvr/install-instana-m8refsvr-plugin.sh -d "${BASE_DIR}"
echo -e "${GREEN}M8RefSvr plugin installed.${NC}"
echo

echo -e "${YELLOW}4. Installing MstrSvr plugin...${NC}"
./mstrsvr/install-instana-mstrsvr-plugin.sh -d "${BASE_DIR}"
echo -e "${GREEN}MstrSvr plugin installed.${NC}"
echo

# List the resulting directory structure
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}   Resulting Directory Structure                       ${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo -e "${YELLOW}Directory structure of ${BASE_DIR}:${NC}"
ls -la "${BASE_DIR}"

echo -e "${YELLOW}Common directory contents:${NC}"
ls -la "${BASE_DIR}/common"

echo -e "${YELLOW}Plugin directories:${NC}"
for plugin in m8mulprc m8prcsvr m8refsvr mstrsvr; do
    echo -e "${GREEN}${plugin}:${NC}"
    ls -la "${BASE_DIR}/${plugin}"
done

# Run the installation test
echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}   Running Installation Tests                          ${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo -e "${YELLOW}Testing the installation with the test script:${NC}"
python3 ./tests/test_installation.py

echo
echo -e "${GREEN}Demo completed! The plugins have been installed with a shared common directory.${NC}"
echo -e "${GREEN}All plugins are installed in: ${BASE_DIR}${NC}"
echo -e "${GREEN}Common files are shared at: ${BASE_DIR}/common${NC}"
echo
echo -e "${YELLOW}To test in a production environment, use:${NC}"
echo -e "  ./m8mulprc/install-instana-m8mulprc-plugin.sh -d /opt/instana_plugins"
echo -e "  ./m8prcsvr/install-instana-m8prcsvr-plugin.sh -d /opt/instana_plugins"
echo -e "  ./m8refsvr/install-instana-m8refsvr-plugin.sh -d /opt/instana_plugins"
echo -e "  ./mstrsvr/install-instana-mstrsvr-plugin.sh -d /opt/instana_plugins"
echo

exit 0
