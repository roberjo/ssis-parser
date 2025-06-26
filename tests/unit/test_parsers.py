#!/usr/bin/env python3
"""
Unit tests for parser modules
"""

import pytest
import tempfile
import os
from pathlib import Path
from ssis_migrator.core.converter import SSISConverter
from ssis_migrator.validators.code_validator import CodeValidator
from ssis_migrator.validators.test_runner import TestRunner
from ssis_migrator.validators.performance_benchmarker import PerformanceBenchmarker
from ssis_migrator.core.config import Config


class TestParsers:
    """Test parser functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = Config()
        self.sample_dtsx_content = """<?xml version="1.0"?>
<DTS:Executable xmlns:DTS="www.microsoft.com/SqlServer/Dts">
  <DTS:Property DTS:Name="PackageFormatVersion">8</DTS:Property>
  <DTS:Property DTS:Name="VersionMajor">1</DTS:Property>
  <DTS:Property DTS:Name="VersionMinor">0</DTS:Property>
  <DTS:Property DTS:Name="VersionBuild">0</DTS:Property>
  <DTS:Property DTS:Name="VersionComments"></DTS:Property>
  <DTS:Property DTS:Name="CreatorName">TestUser</DTS:Property>
  <DTS:Property DTS:Name="CreatorComputerName">TESTCOMPUTER</DTS:Property>
  <DTS:Property DTS:Name="CreationDate">2025-01-01</DTS:Property>
  <DTS:Property DTS:Name="PackageType">5</DTS:Property>
  <DTS:Property DTS:Name="ProtectionLevel">0</DTS:Property>
  <DTS:Property DTS:Name="MaxConcurrentExecutables">4</DTS:Property>
  <DTS:Property DTS:Name="PackagePriorityClass">0</DTS:Property>
  <DTS:Property DTS:Name="VersionGUID">{12345678-1234-1234-1234-123456789ABC}</DTS:Property>
  <DTS:Property DTS:Name="EnableConfig">0</DTS:Property>
  <DTS:Property DTS:Name="CheckpointFileName"></DTS:Property>
  <DTS:Property DTS:Name="SaveCheckpoints">0</DTS:Property>
  <DTS:Property DTS:Name="CheckpointUsage">0</DTS:Property>
  <DTS:Property DTS:Name="SuppressConfigurationWarnings">0</DTS:Property>
  <DTS:Property DTS:Name="ShowEventLogs">0</DTS:Property>
  <DTS:Property DTS:Name="ShowProgress">0</DTS:Property>
  <DTS:Property DTS:Name="LoggingMode">0</DTS:Property>
  <DTS:Property DTS:Name="FilterKind">0</DTS:Property>
  <DTS:Property DTS:Name="EventFilter"></DTS:Property>
  <DTS:Property DTS:Name="ObjectName">TestPackage</DTS:Property>
  <DTS:Property DTS:Name="DTSID">{87654321-4321-4321-4321-CBA987654321}</DTS:Property>
  <DTS:Property DTS:Name="Description"></DTS:Property>
  <DTS:Property DTS:Name="CreationName">Microsoft.Package</DTS:Property>
  <DTS:Property DTS:Name="DisableEventHandlers">0</DTS:Property>
</DTS:Executable>"""
    
    def test_converter_initialization(self):
        """Test SSISConverter initialization"""
        converter = SSISConverter(self.config)
        assert converter.config == self.config
    
    def test_converter_convert_package_success(self):
        """Test successful package conversion"""
        converter = SSISConverter(self.config)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.dtsx', delete=False) as f:
            f.write(self.sample_dtsx_content)
            temp_file = f.name
        
        try:
            result = converter.convert_package(temp_file, "test_output")
            assert result.success is True
            assert result.output_path == "test_output"
            assert len(result.errors) == 0
        finally:
            os.unlink(temp_file)
    
    def test_converter_convert_package_failure(self):
        """Test package conversion failure"""
        converter = SSISConverter(self.config)
        
        result = converter.convert_package("nonexistent_file.dtsx", "test_output")
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_code_validator_initialization(self):
        """Test CodeValidator initialization"""
        validator = CodeValidator()
        assert validator is not None
    
    def test_code_validator_validate_package_success(self):
        """Test successful package validation"""
        validator = CodeValidator()
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            result = validator.validate_package(temp_dir)
            assert result.is_valid is True
    
    def test_code_validator_validate_package_failure(self):
        """Test package validation failure"""
        validator = CodeValidator()
        
        result = validator.validate_package("nonexistent_directory")
        assert result.is_valid is False
        assert len(result.errors) > 0
    
    def test_test_runner_initialization(self):
        """Test TestRunner initialization"""
        runner = TestRunner()
        assert runner is not None
    
    def test_test_runner_run_tests_success(self):
        """Test successful test execution"""
        runner = TestRunner()
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            result = runner.run_tests(temp_dir)
            assert result.success is True
            assert result.tests_passed >= 0
    
    def test_test_runner_run_tests_failure(self):
        """Test test execution failure"""
        runner = TestRunner()
        
        result = runner.run_tests("nonexistent_directory")
        assert result.success is False
        assert len(result.errors) > 0
    
    def test_performance_benchmarker_initialization(self):
        """Test PerformanceBenchmarker initialization"""
        benchmarker = PerformanceBenchmarker()
        assert benchmarker is not None
    
    def test_performance_benchmarker_benchmark_package(self):
        """Test performance benchmarking"""
        benchmarker = PerformanceBenchmarker()
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            result = benchmarker.benchmark_package(temp_dir)
            assert result.execution_time >= 0
            assert result.memory_usage >= 0
            assert result.throughput >= 0
    
    def test_performance_benchmarker_benchmark_nonexistent_package(self):
        """Test benchmarking nonexistent package"""
        benchmarker = PerformanceBenchmarker()
        
        result = benchmarker.benchmark_package("nonexistent_directory")
        assert result.execution_time == 0.0
        assert result.memory_usage == 0.0
        assert result.throughput == 0.0 