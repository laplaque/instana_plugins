#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.
"""
import sys
import os

# Add the parent directory to the path to import the common modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.base_sensor import run_sensor
from common.version import get_version
from common.toml_utils import load_plugin_config

# Load configuration using shared utility
SERVICE_NAMESPACE, PROCESS_NAME, PLUGIN_NAME, DESCRIPTION = load_plugin_config(os.path.dirname(__file__))

if __name__ == "__main__":
    run_sensor(PROCESS_NAME, PLUGIN_NAME, get_version(), service_namespace=SERVICE_NAMESPACE)
