#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MIT License

Copyright (c) 2025 laplaque/instana_plugins Contributors

Tests for the process_monitor module with psutil-based implementation.
"""
import unittest
from unittest.mock import patch, MagicMock, mock_open
import psutil

# Import the module under test
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from common.process_monitor import (
    get_process_metrics, get_disk_io_for_pid, get_file_descriptor_count,
    get_thread_count, get_context_switches
)

class TestProcessMonitor(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create mock process objects with the required attributes
        self.mock_proc = MagicMock()
        self.mock_proc.pid = 1234
        self.mock_proc.ppid.return_value = 1
        self.mock_proc.name.return_value = "TestProcess"
        self.mock_proc.cpu_percent.return_value = 25.5
        self.mock_proc.memory_percent.return_value = 15.2

    @patch('common.process_monitor.psutil.process_iter')
    @patch('common.process_monitor.get_disk_io_for_pid')
    @patch('common.process_monitor.get_file_descriptor_count')
    @patch('common.process_monitor.get_thread_count')
    @patch('common.process_monitor.get_context_switches')
    def test_get_process_metrics_success(self, mock_ctx_switches,
                                       mock_thread_count, mock_fd_count, mock_disk_io, 
                                       mock_process_iter):
        """Test successful process metrics collection."""
        # Mock process_iter to return our test process
        mock_process_iter.return_value = [self.mock_proc]
        
        # Mock the process info structure
        self.mock_proc.info = {
            'pid': 1234,
            'ppid': 1,
            'name': 'TestProcess',
            'cpu_percent': 25.5,
            'memory_percent': 15.2
        }
        
        # Mock the helper functions
        mock_disk_io.return_value = (1000, 2000)
        mock_fd_count.return_value = 10
        mock_thread_count.return_value = 5
        mock_ctx_switches.return_value = (100, 50)
        
        # Call the function
        result = get_process_metrics("TestProcess")
        
        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result["cpu_usage"], 25.5)
        self.assertEqual(result["memory_usage"], 15.2)
        self.assertEqual(result["process_count"], 1)
        self.assertEqual(result["disk_read_bytes"], 1000)
        self.assertEqual(result["disk_write_bytes"], 2000)
        self.assertEqual(result["open_file_descriptors"], 10)
        self.assertEqual(result["thread_count"], 5)
        self.assertEqual(result["voluntary_ctx_switches"], 100)
        self.assertEqual(result["nonvoluntary_ctx_switches"], 50)
        
        # Verify helper functions were called
        mock_disk_io.assert_called_once_with(self.mock_proc)
        mock_fd_count.assert_called_once_with(self.mock_proc)
        mock_thread_count.assert_called_once_with(self.mock_proc)
        mock_ctx_switches.assert_called_once_with(self.mock_proc)

    @patch('common.process_monitor.psutil.process_iter')
    def test_get_process_metrics_no_match(self, mock_process_iter):
        """Test get_process_metrics when no matching processes are found."""
        # Mock empty process list
        mock_process_iter.return_value = []
        
        result = get_process_metrics("NonexistentProcess")
        
        self.assertIsNone(result)

    @patch('common.process_monitor.psutil.process_iter')
    def test_get_process_metrics_psutil_error(self, mock_process_iter):
        """Test get_process_metrics when psutil raises an exception."""
        # Mock psutil to raise NoSuchProcess exception
        mock_process_iter.side_effect = psutil.NoSuchProcess(1234)
        
        result = get_process_metrics("TestProcess")
        
        self.assertIsNone(result)

    def test_get_disk_io_for_pid_success(self):
        """Test successful disk I/O retrieval for a process."""
        # Mock I/O counters
        mock_io = MagicMock()
        mock_io.read_bytes = 1000
        mock_io.write_bytes = 2000
        self.mock_proc.io_counters.return_value = mock_io
        
        read_bytes, write_bytes = get_disk_io_for_pid(self.mock_proc)
        
        self.assertEqual(read_bytes, 1000)
        self.assertEqual(write_bytes, 2000)

    def test_get_disk_io_for_pid_no_such_process(self):
        """Test disk I/O retrieval when process doesn't exist."""
        self.mock_proc.io_counters.side_effect = psutil.NoSuchProcess(1234)
        
        read_bytes, write_bytes = get_disk_io_for_pid(self.mock_proc)
        
        self.assertEqual(read_bytes, 0)
        self.assertEqual(write_bytes, 0)

    def test_get_file_descriptor_count_success(self):
        """Test successful file descriptor counting."""
        # Mock open files and connections
        self.mock_proc.open_files.return_value = [MagicMock(), MagicMock(), MagicMock()]
        self.mock_proc.connections.return_value = [MagicMock(), MagicMock()]
        
        count = get_file_descriptor_count(self.mock_proc)
        
        self.assertEqual(count, 5)  # 3 files + 2 connections

    def test_get_file_descriptor_count_access_denied(self):
        """Test file descriptor counting when access is denied."""
        self.mock_proc.open_files.side_effect = psutil.AccessDenied(1234)
        
        count = get_file_descriptor_count(self.mock_proc)
        
        self.assertEqual(count, 0)

    def test_get_thread_count_success(self):
        """Test successful thread counting."""
        self.mock_proc.num_threads.return_value = 8
        
        count = get_thread_count(self.mock_proc)
        
        self.assertEqual(count, 8)

    def test_get_thread_count_no_such_process(self):
        """Test thread counting when process doesn't exist."""
        self.mock_proc.num_threads.side_effect = psutil.NoSuchProcess(1234)
        
        count = get_thread_count(self.mock_proc)
        
        self.assertEqual(count, 0)

    def test_get_context_switches_success(self):
        """Test successful context switch retrieval."""
        mock_ctx = MagicMock()
        mock_ctx.voluntary = 1500
        mock_ctx.involuntary = 500
        self.mock_proc.num_ctx_switches.return_value = mock_ctx
        
        vol_ctx, nonvol_ctx = get_context_switches(self.mock_proc)
        
        self.assertEqual(vol_ctx, 1500)
        self.assertEqual(nonvol_ctx, 500)

    def test_get_context_switches_zombie_process(self):
        """Test context switch retrieval for zombie process."""
        self.mock_proc.num_ctx_switches.side_effect = psutil.ZombieProcess(1234)
        
        vol_ctx, nonvol_ctx = get_context_switches(self.mock_proc)
        
        self.assertEqual(vol_ctx, 0)
        self.assertEqual(nonvol_ctx, 0)


    @patch('common.process_monitor.psutil.process_iter')
    def test_empty_process_output(self, mock_process_iter):
        """Test handling of empty process list."""
        mock_process_iter.return_value = []
        
        result = get_process_metrics("TestProcess")
        
        self.assertIsNone(result)

    @patch('common.process_monitor.psutil.process_iter')
    def test_process_with_special_chars(self, mock_process_iter):
        """Test handling of process names with special characters."""
        # Create a mock process with special characters in name
        mock_proc = MagicMock()
        mock_proc.pid = 5678
        mock_proc.ppid.return_value = 1
        mock_proc.name.return_value = "Test-Process_1.2"
        mock_proc.cpu_percent.return_value = 10.0
        mock_proc.memory_percent.return_value = 5.0
        mock_proc.info = {
            'pid': 5678,
            'ppid': 1,
            'name': 'Test-Process_1.2',
            'cpu_percent': 10.0,
            'memory_percent': 5.0
        }
        
        mock_process_iter.return_value = [mock_proc]
        
        # Mock helper functions to return basic values
        with patch('common.process_monitor.get_disk_io_for_pid') as mock_disk_io, \
             patch('common.process_monitor.get_file_descriptor_count') as mock_fd_count, \
             patch('common.process_monitor.get_thread_count') as mock_thread_count, \
             patch('common.process_monitor.get_context_switches') as mock_ctx_switches:
            
            mock_disk_io.return_value = (0, 0)
            mock_fd_count.return_value = 0
            mock_thread_count.return_value = 1
            mock_ctx_switches.return_value = (0, 0)
            
            result = get_process_metrics("Test-Process")
            
            self.assertIsNotNone(result)
            self.assertEqual(result["cpu_usage"], 10.0)
            self.assertEqual(result["memory_usage"], 5.0)

if __name__ == '__main__':
    unittest.main()
