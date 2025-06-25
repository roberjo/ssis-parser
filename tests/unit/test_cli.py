#!/usr/bin/env python3
"""
Unit tests for CLI functionality
"""

import pytest
from click.testing import CliRunner
from ssis_migrator.cli import main


class TestCLI:
    """Test CLI functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    def test_help_command(self):
        """Test help command"""
        result = self.runner.invoke(main, ['--help'])
        assert result.exit_code == 0
        assert "SSIS Migration Tool" in result.output
        assert "convert" in result.output
        assert "validate" in result.output
    
    def test_version_command(self):
        """Test version command"""
        result = self.runner.invoke(main, ['--version'])
        assert result.exit_code == 0
        assert "2.0.0" in result.output
    
    def test_convert_help(self):
        """Test convert command help"""
        result = self.runner.invoke(main, ['convert', '--help'])
        assert result.exit_code == 0
        assert "Convert SSIS package" in result.output
    
    def test_validate_help(self):
        """Test validate command help"""
        result = self.runner.invoke(main, ['validate', '--help'])
        assert result.exit_code == 0
        assert "Validate converted Python code" in result.output
    
    def test_test_help(self):
        """Test test command help"""
        result = self.runner.invoke(main, ['test', '--help'])
        assert result.exit_code == 0
        assert "Run tests on converted Python code" in result.output
    
    def test_benchmark_help(self):
        """Test benchmark command help"""
        result = self.runner.invoke(main, ['benchmark', '--help'])
        assert result.exit_code == 0
        assert "Run performance benchmarking" in result.output
    
    def test_rollback_help(self):
        """Test rollback command help"""
        result = self.runner.invoke(main, ['rollback', '--help'])
        assert result.exit_code == 0
        assert "Rollback migration to original SSIS package" in result.output
    
    def test_plan_help(self):
        """Test plan command help"""
        result = self.runner.invoke(main, ['plan', '--help'])
        assert result.exit_code == 0
        assert "Generate migration plan for all packages" in result.output 