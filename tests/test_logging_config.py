#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the logging_config module.
"""
import unittest
import os
import logging
from unittest.mock import patch, MagicMock
import tempfile
import shutil
from common.logging_config import setup_logging

class TestLoggingConfig(unittest.TestCase):
    """Test cases for the logging_config module."""
    
    def setUp(self):
        # Create a temporary directory for log files
        self.test_dir = tempfile.mkdtemp()
        self.log_file = os.path.join(self.test_dir, 'test.log')
        
        # Store original loggers to restore after tests
        self.root_handlers = logging.root.handlers.copy()
        self.root_level = logging.root.level
    
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)
        
        # Restore original logging configuration
        logging.root.handlers = self.root_handlers
        logging.root.setLevel(self.root_level)
    
    def test_setup_logging_default(self):
        """Test setup_logging with default parameters."""
        # Clear existing handlers
        logging.root.handlers = []
        
        # Call the function
        setup_logging()
        
        # Check that root logger is configured correctly
        self.assertEqual(logging.root.level, logging.INFO)
        self.assertEqual(len(logging.root.handlers), 2)  # Console and file handler
        
        # Check handler types
        handler_types = [type(h) for h in logging.root.handlers]
        self.assertIn(logging.StreamHandler, handler_types)
        self.assertIn(logging.handlers.RotatingFileHandler, handler_types)
    
    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom log level."""
        # Clear existing handlers
        logging.root.handlers = []
        
        # Call the function with DEBUG level
        setup_logging(log_level=logging.DEBUG)
        
        # Check that root logger is configured correctly
        self.assertEqual(logging.root.level, logging.DEBUG)
    
    def test_setup_logging_custom_file(self):
        """Test setup_logging with custom log file."""
        # Clear existing handlers
        logging.root.handlers = []
        
        # Call the function with custom log file
        setup_logging(log_file=self.log_file)
        
        # Find the file handler
        file_handler = None
        for handler in logging.root.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                file_handler = handler
                break
        
        # Check that file handler uses the correct file
        self.assertIsNotNone(file_handler)
        self.assertEqual(file_handler.baseFilename, self.log_file)
    
    def test_log_rotation_settings(self):
        """Test that log rotation settings are applied correctly."""
        # Clear existing handlers
        logging.root.handlers = []
        
        # Call the function
        setup_logging(log_file=self.log_file)
        
        # Find the file handler
        file_handler = None
        for handler in logging.root.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                file_handler = handler
                break
        
        # Check rotation settings
        self.assertIsNotNone(file_handler)
        self.assertEqual(file_handler.maxBytes, 5 * 1024 * 1024)  # 5 MB
        self.assertEqual(file_handler.backupCount, 3)
    
    @patch('logging.handlers.RotatingFileHandler')
    def test_file_handler_creation_error(self, mock_handler):
        """Test handling of errors when creating file handler."""
        # Make the handler raise an exception
        mock_handler.side_effect = PermissionError("Permission denied")
        
        # Clear existing handlers
        logging.root.handlers = []
        
        # Call the function
        setup_logging(log_file=self.log_file)
        
        # Should still have console handler
        self.assertEqual(len(logging.root.handlers), 1)
        self.assertIsInstance(logging.root.handlers[0], logging.StreamHandler)

if __name__ == '__main__':
    unittest.main()
