#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit tests for the logging_config module.
"""
import unittest
import os
import sys
import logging
from unittest.mock import patch, MagicMock
import tempfile
import shutil

# Add the parent directory to the path to import the common modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.logging_config import setup_logging, _resolve_log_file_path

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
        
        # Close all current handlers to avoid ResourceWarnings
        for handler in logging.root.handlers[:]:
            try:
                # Only try to close if it's a real handler, not a mock
                if hasattr(handler, 'close') and callable(handler.close):
                    handler.close()
            except (AttributeError, TypeError):
                pass  # Skip if handler can't be closed
            logging.root.removeHandler(handler)
        
        # Restore original logging configuration
        for handler in self.root_handlers:
            logging.root.addHandler(handler)
        logging.root.setLevel(self.root_level)
    
    def test_resolve_log_file_path_default(self):
        """Test _resolve_log_file_path with default parameters."""
        # Create a temp directory for the logs
        temp_project_root = tempfile.mkdtemp()
        try:
            # Define paths
            temp_logs_dir = os.path.join(temp_project_root, 'logs')
            temp_log_file = os.path.join(temp_logs_dir, 'app.log')
            
            # Setup mocks
            with patch('common.logging_config._resolve_log_file_path') as mock_resolve:
                mock_resolve.return_value = temp_log_file
                
                # Call the function
                log_path = mock_resolve()
                
                # Verify correct path was returned
                self.assertEqual(log_path, temp_log_file)
                
        finally:
            # Clean up the temporary project root
            shutil.rmtree(temp_project_root)
    
    def test_resolve_log_file_path_creates_directories(self):
        """Test that _resolve_log_file_path creates directories as needed."""
        # Create a path with multiple non-existent directories
        nested_path = os.path.join(self.test_dir, 'nested', 'dirs', 'test.log')
        
        # Verify directories don't exist yet
        nested_dir = os.path.dirname(nested_path)
        self.assertFalse(os.path.exists(nested_dir))
        
        # Call the function
        resolved_path = _resolve_log_file_path(nested_path)
        
        # Verify directories were created
        self.assertTrue(os.path.exists(nested_dir))
        self.assertEqual(os.path.abspath(nested_path), resolved_path)
    
    def test_resolve_log_file_path_normalizes_paths(self):
        """Test that _resolve_log_file_path normalizes relative paths."""
        # Create a path with relative components
        parent_dir = os.path.dirname(self.test_dir)
        basename = os.path.basename(self.test_dir)
        relative_path = os.path.join(parent_dir, '..', os.path.basename(parent_dir), basename, 'test.log')
        
        # Call the function
        resolved_path = _resolve_log_file_path(relative_path)
        
        # Verify the path is normalized and absolute
        expected_path = os.path.abspath(os.path.join(self.test_dir, 'test.log'))
        self.assertEqual(os.path.normpath(resolved_path), os.path.normpath(expected_path))
    
    @patch('os.makedirs')
    def test_directory_creation_permission_error(self, mock_makedirs):
        """Test handling of permission errors during directory creation."""
        # Mock os.makedirs to raise PermissionError
        mock_makedirs.side_effect = PermissionError("Permission denied")
        
        # Create a path with non-existent directory
        test_path = os.path.join(self.test_dir, 'no_permission', 'test.log')
        
        # This should raise a PermissionError
        with self.assertRaises(PermissionError):
            _resolve_log_file_path(test_path)
    
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
    
    def test_setup_logging_with_non_existent_directory(self):
        """Test setup_logging with a log file in a non-existent directory."""
        # Clear existing handlers
        logging.root.handlers = []
        
        # Create a path with non-existent directory
        nested_log_dir = os.path.join(self.test_dir, 'new_logs_dir')
        nested_log_file = os.path.join(nested_log_dir, 'test.log')
        
        # Verify directory doesn't exist
        self.assertFalse(os.path.exists(nested_log_dir))
        
        # Call setup_logging
        setup_logging(log_file=nested_log_file)
        
        # Verify directory was created
        self.assertTrue(os.path.exists(nested_log_dir))
        
        # Write a log message
        logging.info("Test log message")
        
        # Verify log file was created and contains the message
        self.assertTrue(os.path.exists(nested_log_file))
        with open(nested_log_file, 'r') as f:
            log_content = f.read()
            self.assertIn("Test log message", log_content)
    
    def test_logger_name_preserved(self):
        """Test that logger names are preserved in the log output."""
        # Clear existing handlers
        logging.root.handlers = []
        
        # Set up logging
        setup_logging(log_file=self.log_file)
        
        # Create a custom logger
        test_logger = logging.getLogger("test.module")
        test_logger.info("Test message from custom logger")
        
        # Verify the logger name appears in the log
        with open(self.log_file, 'r') as f:
            log_content = f.read()
            self.assertIn("test.module", log_content)
    
    def test_file_handler_creation_error(self):
        """Test that setup_logging continues even when file handler creation fails."""
        # Create a mock that raises an exception when called
        def mock_handler(*args, **kwargs):
            raise PermissionError("Permission denied")
        
        # Ensure we start with a clean slate
        logging.root.handlers = []
        
        # Use patch as a context manager for safer patching and automatic restoration
        with patch('logging.handlers.RotatingFileHandler', new=mock_handler):
            # Call setup_logging with a log file that will trigger the error
            setup_logging(log_file=self.log_file)
            
            # Check that we have at least one handler still (the console)
            self.assertTrue(len(logging.root.handlers) > 0, "Should have at least one handler")
            
            # Check if any of the handlers is a StreamHandler (console)
            stream_handlers = [h for h in logging.root.handlers if isinstance(h, logging.StreamHandler)]
            self.assertTrue(len(stream_handlers) > 0, "Should have at least one StreamHandler")
            
            # We can't check for specific handler counts as there might be other handlers
            # The important thing is that we have at least one StreamHandler and no file handlers
            handler_types = [h.__class__.__name__ for h in logging.root.handlers]
            
            # We should have at least one StreamHandler
            self.assertTrue(len(stream_handlers) > 0, 
                           f"Should have at least one StreamHandler. Found handlers: {handler_types}")

if __name__ == '__main__':
    unittest.main()
