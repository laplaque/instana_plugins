#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

This file is part of the Instana Plugins collection.
Version: 0.0.13

Script to check if all dependencies from requirements.txt are already installed.
Returns 0 if all dependencies are satisfied, 1 otherwise.
"""
import sys
import pkg_resources
import importlib.util
import argparse
import logging

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_dependency(package_line):
    """Check if a specific dependency is installed and meets the version requirements"""
    try:
        # Skip comments and empty lines
        if not package_line.strip() or package_line.strip().startswith('#'):
            return True
        
        # Parse the package requirement
        req = pkg_resources.Requirement.parse(package_line)
        pkg_name = req.name
        
        # Check if the package is installed
        pkg_resources.get_distribution(req)
        
        logger.info(f"✅ {pkg_name} is installed and meets version requirements")
        return True
    except pkg_resources.DistributionNotFound:
        logger.error(f"❌ {pkg_name} is not installed")
        return False
    except pkg_resources.VersionConflict:
        logger.error(f"❌ {pkg_name} is installed but version requirement not met")
        return False
    except Exception as e:
        logger.error(f"❌ Error checking {package_line}: {str(e)}")
        return False

def check_requirements_file(requirements_file):
    """Check if all dependencies in a requirements.txt file are satisfied"""
    try:
        with open(requirements_file, 'r') as f:
            requirements = [line.strip() for line in f.readlines()]
        
        all_satisfied = True
        for req in requirements:
            if req and not req.startswith('#'):
                if not check_dependency(req):
                    all_satisfied = False
        
        return all_satisfied
    except Exception as e:
        logger.error(f"Error reading requirements file: {str(e)}")
        return False

def main():
    """Main function to check dependencies"""
    parser = argparse.ArgumentParser(description='Check if all dependencies are already installed')
    parser.add_argument('--requirements', '-r', 
                        default='requirements.txt',
                        help='Path to requirements.txt file')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Only output errors')
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    if check_requirements_file(args.requirements):
        if not args.quiet:
            print("✅ All dependencies are already satisfied.")
        return 0
    else:
        if not args.quiet:
            print("❌ Some dependencies are missing or don't meet version requirements.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
