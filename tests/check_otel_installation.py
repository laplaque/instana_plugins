#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

Script to check OpenTelemetry installation and dependencies.
"""
import sys
import importlib.util
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_module(module_name):
    """Check if a module is installed"""
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        logger.error(f"❌ Module {module_name} is NOT installed")
        return False
    else:
        logger.info(f"✅ Module {module_name} is installed")
        return True

def main():
    """Check OpenTelemetry dependencies"""
    print("Checking OpenTelemetry dependencies...")
    
    required_modules = [
        "opentelemetry.api",
        "opentelemetry.sdk",
        "opentelemetry.exporter.otlp"
    ]
    
    all_installed = True
    for module in required_modules:
        if not check_module(module):
            all_installed = False
    
    if all_installed:
        print("\n✅ All required OpenTelemetry modules are installed!")
        print("\nYou can now use the TLS features with:")
        print("  USE_TLS=true \\")
        print("  CA_CERT_PATH=/path/to/ca.crt \\")
        print("  python -m your_sensor_script")
    else:
        print("\n❌ Some required modules are missing.")
        print("\nPlease install the required dependencies:")
        print("  pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp")
    
    return 0 if all_installed else 1

if __name__ == "__main__":
    sys.exit(main())
