#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

Script to test if the Instana plugins installation was successful.
"""
import os
import sys
import subprocess
import importlib.util
import logging
import argparse

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Plugin configurations
PLUGINS = [
    {
        "name": "m8mulprc",
        "process_name": "M8MulPrc",
        "sensor_path": None,
        "plugin_path": None,
        "status": "Not tested"
    },
    {
        "name": "m8prcsvr",
        "process_name": "M8PrcSvr",
        "sensor_path": None,
        "plugin_path": None,
        "status": "Not tested"
    },
    {
        "name": "m8refsvr",
        "process_name": "M8RefSvr",
        "sensor_path": None,
        "plugin_path": None,
        "status": "Not tested"
    },
    {
        "name": "mstrsvr",
        "process_name": "MSTRSvr",
        "sensor_path": None,
        "plugin_path": None,
        "status": "Not tested"
    }
]

def check_module(module_name):
    """Check if a module is installed"""
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        logger.error(f"❌ Module {module_name} is NOT installed")
        return False
    else:
        logger.info(f"✅ Module {module_name} is installed")
        return True

def check_dependencies():
    """Check required Python dependencies"""
    print("\n📋 Checking Python dependencies...")
    
    required_modules = [
        "opentelemetry.api",
        "opentelemetry.sdk",
        "opentelemetry.exporter.otlp",
        "psutil"
    ]
    
    all_installed = True
    for module in required_modules:
        if not check_module(module):
            all_installed = False
    
    if all_installed:
        print("✅ All required Python modules are installed!")
    else:
        print("❌ Some required modules are missing.")
        print("Please install the required dependencies:")
        print("  pip install -r common/requirements.txt")
    
    # Check if multiple requirement files exist across plugins
    check_requirements_across_modules()
    
    return all_installed

def check_requirements_across_modules():
    """Check if requirements need to be installed for each plugin or just once"""
    print("\n📋 Checking requirements across modules...")
    
    # Root requirements file
    root_req_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "common/requirements.txt")
    
    if not os.path.exists(root_req_file):
        logger.warning(f"❌ Common requirements file not found at {root_req_file}")
        return
    
    with open(root_req_file, 'r') as f:
        root_requirements = f.readlines()
    
    # Check if each plugin has its own requirements
    plugin_req_files = []
    for plugin in PLUGINS:
        plugin_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), plugin["name"])
        req_file = os.path.join(plugin_dir, "requirements.txt")
        
        if os.path.exists(req_file):
            plugin_req_files.append(req_file)
    
    if not plugin_req_files:
        print("✅ Only one central requirements file found in common/requirements.txt")
        print("   You only need to install requirements once for all plugins:")
        print("   pip install -r common/requirements.txt")
        return
    
    # Compare requirements
    different_requirements = False
    for req_file in plugin_req_files:
        with open(req_file, 'r') as f:
            plugin_requirements = f.readlines()
        
        extra_reqs = [r for r in plugin_requirements if r.strip() and r not in root_requirements]
        if extra_reqs:
            different_requirements = True
            logger.warning(f"❗ {req_file} contains extra requirements: {extra_reqs}")
    
    if different_requirements:
        print("⚠️ Some plugins have their own requirements.txt files with additional dependencies")
        print("   You may need to install requirements for each plugin separately:")
        for req_file in plugin_req_files:
            print(f"   pip install -r {req_file}")
    else:
        print("✅ All plugins share the same requirements")
        print("   Installing common/requirements.txt is sufficient for all plugins")

def find_plugin_installations():
    """Find plugin installations in default and custom locations"""
    print("\n📋 Looking for plugin installations...")
    
    # Check default locations
    default_paths = [
        "/opt/instana/agent/plugins/custom_sensors/",  # Default Instana location
        os.path.expanduser("~/.local/share/instana/plugins/"),  # User-level location
        "./installed_plugins/"  # Local development location
    ]
    
    for plugin in PLUGINS:
        # Look for plugin installations
        for base_path in default_paths:
            plugin_dir = f"microstrategy_{plugin['name']}"
            full_path = os.path.join(base_path, plugin_dir)
            
            if os.path.exists(full_path) and os.path.isdir(full_path):
                sensor_path = os.path.join(full_path, "sensor.py")
                plugin_json = os.path.join(full_path, "plugin.json")
                
                if os.path.exists(sensor_path) and os.path.exists(plugin_json):
                    plugin["sensor_path"] = sensor_path
                    plugin["plugin_path"] = full_path
                    plugin["status"] = "Found"
                    logger.info(f"✅ Found {plugin['process_name']} plugin at {full_path}")
                    break
        
        if plugin["sensor_path"] is None:
            plugin["status"] = "Not found"
            logger.warning(f"❌ Could not find {plugin['process_name']} plugin installation")
    
    # Count found plugins
    found_count = sum(1 for p in PLUGINS if p["status"] == "Found")
    print(f"✅ Found {found_count} of {len(PLUGINS)} plugin installations")
    
    return found_count == len(PLUGINS)

def test_plugin(plugin):
    """Test if a plugin's sensor runs properly"""
    if plugin["sensor_path"] is None:
        logger.warning(f"⚠️ Skipping test for {plugin['process_name']} - not installed")
        return False
    
    print(f"\n📋 Testing {plugin['process_name']} sensor...")
    
    try:
        # Set up environment variables for testing
        env = os.environ.copy()
        env["PYTHONPATH"] = plugin["plugin_path"]
        
        # Run the sensor with --run-once and --log-level=DEBUG
        cmd = [sys.executable, plugin["sensor_path"], "--run-once", "--log-level=DEBUG"]
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Run the command with a timeout (30 seconds)
        result = subprocess.run(
            cmd,
            env=env,
            timeout=30,
            capture_output=True,
            text=True
        )
        
        # Check the result
        if result.returncode == 0:
            logger.info(f"✅ {plugin['process_name']} sensor ran successfully")
            plugin["status"] = "Tested OK"
            return True
        else:
            logger.error(f"❌ {plugin['process_name']} sensor failed with code {result.returncode}")
            logger.error(f"Output: {result.stdout}")
            logger.error(f"Error: {result.stderr}")
            plugin["status"] = "Test failed"
            return False
    
    except subprocess.TimeoutExpired:
        logger.error(f"❌ {plugin['process_name']} sensor test timed out")
        plugin["status"] = "Test timed out"
        return False
    except Exception as e:
        logger.error(f"❌ {plugin['process_name']} sensor test failed with exception: {str(e)}")
        plugin["status"] = f"Error: {str(e)}"
        return False

def run_plugin_tests(args):
    """Run tests on the installed plugins"""
    print("\n📋 Running plugin tests...")
    
    all_tests_passed = True
    
    # Only test specified plugins or all if none specified
    plugins_to_test = [p for p in PLUGINS if p["name"] in args.plugins] if args.plugins else PLUGINS
    
    for plugin in plugins_to_test:
        if plugin["status"] == "Found":
            success = test_plugin(plugin)
            if not success:
                all_tests_passed = False
    
    return all_tests_passed

def print_summary():
    """Print a summary of the test results"""
    print("\n📋 Installation Test Summary:")
    print("=" * 60)
    print(f"{'Plugin':<12} {'Process Name':<12} {'Status':<15} {'Path'}")
    print("-" * 60)
    
    for plugin in PLUGINS:
        path = plugin["plugin_path"] or "N/A"
        status_emoji = "✅" if "OK" in plugin["status"] else "❌"
        print(f"{plugin['name']:<12} {plugin['process_name']:<12} {status_emoji} {plugin['status']:<12} {path}")
    
    print("=" * 60)

def main():
    """Main function to test plugin installations"""
    parser = argparse.ArgumentParser(description='Test Instana plugins installation')
    parser.add_argument('--dependencies-only', action='store_true', 
                        help='Only check dependencies, skip plugin tests')
    parser.add_argument('--plugin', dest='plugins', action='append',
                        choices=[p['name'] for p in PLUGINS],
                        help='Test specific plugin(s) only')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Instana Plugins Installation Test".center(60))
    print("=" * 60)
    
    # Step 1: Check dependencies
    deps_ok = check_dependencies()
    
    if args.dependencies_only:
        return 0 if deps_ok else 1
    
    # Step 2: Find plugin installations
    installations_ok = find_plugin_installations()
    
    # Step 3: Test each plugin
    tests_ok = run_plugin_tests(args)
    
    # Step 4: Print summary
    print_summary()
    
    # Return status
    overall_success = deps_ok and (installations_ok or not args.plugins)
    if tests_ok:
        print("\n✅ Installation test completed successfully!")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
