#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

Script to test TLS configuration without requiring OpenTelemetry.
"""
import os
import sys
import logging
import argparse
from distutils.util import strtobool

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_env_variables():
    """Test environment variables for TLS configuration"""
    # Set environment variables
    os.environ['USE_TLS'] = 'true'
    os.environ['CA_CERT_PATH'] = '/path/to/ca.crt'
    os.environ['CLIENT_CERT_PATH'] = '/path/to/client.crt'
    os.environ['CLIENT_KEY_PATH'] = '/path/to/client.key'
    
    # Read and parse them back
    use_tls = bool(strtobool(os.environ.get('USE_TLS', 'false')))
    ca_cert_path = os.environ.get('CA_CERT_PATH')
    client_cert_path = os.environ.get('CLIENT_CERT_PATH')
    client_key_path = os.environ.get('CLIENT_KEY_PATH')
    
    logger.info(f"USE_TLS parsed as: {use_tls}")
    logger.info(f"CA_CERT_PATH: {ca_cert_path}")
    logger.info(f"CLIENT_CERT_PATH: {client_cert_path}")
    logger.info(f"CLIENT_KEY_PATH: {client_key_path}")
    
    # Use assertions instead of return values for pytest
    assert use_tls is True, "USE_TLS should be True"
    assert ca_cert_path == '/path/to/ca.crt', "CA_CERT_PATH not set correctly"
    assert client_cert_path == '/path/to/client.crt', "CLIENT_CERT_PATH not set correctly"
    assert client_key_path == '/path/to/client.key', "CLIENT_KEY_PATH not set correctly"
    
    logger.info("✅ All TLS environment variables are correctly set and parsed")

def test_url_construction():
    """Test URL construction with TLS"""
    agent_host = "localhost"
    agent_port = 4317
    
    # Test with TLS enabled
    use_tls = True
    protocol = "https://" if use_tls else "http://"
    otlp_endpoint = f"{protocol}{agent_host}:{agent_port}"
    
    logger.info(f"TLS endpoint: {otlp_endpoint}")
    
    # Use assertion instead of return value for pytest
    assert otlp_endpoint == "https://localhost:4317", "TLS URL construction is incorrect"
    logger.info("✅ TLS URL construction is correct")

def main():
    """Run the tests"""
    parser = argparse.ArgumentParser(description='Test TLS configuration without OpenTelemetry')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    print("Testing TLS configuration...")
    
    tests_passed = 0
    tests_total = 2
    
    if test_env_variables():
        tests_passed += 1
    
    if test_url_construction():
        tests_passed += 1
    
    print(f"\nTests completed: {tests_passed}/{tests_total} passed")
    
    if tests_passed == tests_total:
        print("✅ All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
