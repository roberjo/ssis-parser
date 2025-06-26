#!/usr/bin/env python3
"""
Unit tests for Python script generator
"""

import unittest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.ssis_migrator.generators.python_generator import (
    PythonScriptGenerator, PythonScript, GenerationResult
)
from src.ssis_migrator.parsers.dtsx_parser import SSISPackage
from src.ssis_migrator.core.error_handler import ErrorHandler


class TestPythonScript(unittest.TestCase):
    """Test PythonScript dataclass"""
    
    def test_python_script_creation(self):
        """Test creating PythonScript"""
        script = PythonScript(
            name="test_script.py",
            content="# Test script content",
            dependencies=["pandas", "sqlalchemy"],
            imports=["import pandas as pd"],
            functions=["def test_function():"],
            metadata={"type": "main", "package": "test"}
        )
        
        self.assertEqual(script.name, "test_script.py")
        self.assertEqual(script.content, "# Test script content")
        self.assertEqual(script.dependencies, ["pandas", "sqlalchemy"])
        self.assertEqual(script.imports, ["import pandas as pd"])
        self.assertEqual(script.functions, ["def test_function():"])
        self.assertEqual(script.metadata, {"type": "main", "package": "test"})


class TestGenerationResult(unittest.TestCase):
    """Test GenerationResult dataclass"""
    
    def test_generation_result_creation(self):
        """Test creating GenerationResult"""
        scripts = [PythonScript("test.py", "content")]
        result = GenerationResult(
            success=True,
            scripts=scripts,
            errors=["Error 1"],
            warnings=["Warning 1"]
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.scripts), 1)
        self.assertEqual(result.errors, ["Error 1"])
        self.assertEqual(result.warnings, ["Warning 1"])


class TestPythonScriptGenerator(unittest.TestCase):
    """Test PythonScriptGenerator class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.error_handler = ErrorHandler()
        self.generator = PythonScriptGenerator(error_handler=self.error_handler)
        
        # Create a sample SSIS package for testing
        self.sample_package = SSISPackage(
            name="TestPackage",
            version="1.0.0",
            description="Test package for unit testing",
            creation_date="2024-01-01",
            creator="TestUser",
            package_id="test-id-123",
            connection_managers=[
                {
                    "name": "TestConnection",
                    "type": "OLEDB",
                    "connection_string": "Server=test;Database=testdb"
                }
            ],
            variables=[
                {
                    "name": "TestVariable",
                    "value": "test_value",
                    "type": "String"
                }
            ],
            data_flow_components=[
                {
                    "name": "TestSource",
                    "type": "OLE DB Source",
                    "description": "Test data source"
                },
                {
                    "name": "TestDestination",
                    "type": "OLE DB Destination",
                    "description": "Test data destination"
                }
            ],
            control_flow_tasks=[
                {
                    "name": "TestTask",
                    "type": "Execute SQL Task",
                    "description": "Test SQL task"
                }
            ],
            configuration_files=[],
            environment_variables={}
        )
    
    def test_generator_initialization(self):
        """Test PythonScriptGenerator initialization"""
        generator = PythonScriptGenerator()
        
        self.assertIsNotNone(generator.error_handler)
        self.assertIsNotNone(generator.standard_dependencies)
        self.assertIsNotNone(generator.main_template)
        self.assertIsNotNone(generator.data_flow_template)
        self.assertIsNotNone(generator.control_flow_template)
    
    def test_generate_scripts_success(self):
        """Test successful script generation"""
        result = self.generator.generate_scripts(self.sample_package, "/tmp/test")
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.scripts), 0)
        self.assertEqual(len(result.errors), 0)
        
        # Check that main script was generated
        main_script = next((s for s in result.scripts if s.name.endswith('_main.py')), None)
        self.assertIsNotNone(main_script)
        self.assertIn("def main():", main_script.content)
        self.assertIn("TestPackage", main_script.content)
    
    def test_generate_scripts_with_empty_package(self):
        """Test script generation with empty package"""
        empty_package = SSISPackage(
            name="EmptyPackage",
            version="1.0.0",
            description="Empty package",
            creation_date="2024-01-01",
            creator="TestUser",
            package_id="empty-id"
        )
        
        result = self.generator.generate_scripts(empty_package, "/tmp/test")
        
        self.assertTrue(result.success)
        self.assertGreater(len(result.scripts), 0)
        # Should still generate main script and requirements
    
    def test_collect_imports(self):
        """Test import collection"""
        imports = self.generator._collect_imports(self.sample_package)
        
        # Should include standard ETL imports
        self.assertIn("pandas", imports)
        self.assertIn("sqlalchemy", imports)
        self.assertIn("logging", imports)
    
    def test_collect_dependencies(self):
        """Test dependency collection"""
        dependencies = self.generator._collect_dependencies(self.sample_package)
        
        # Should include standard dependencies
        self.assertIn("pandas", dependencies)
        self.assertIn("sqlalchemy", dependencies)
    
    def test_generate_main_script(self):
        """Test main script generation"""
        script = self.generator._generate_main_script(self.sample_package)
        
        self.assertIsInstance(script, PythonScript)
        self.assertIn("TestPackage", script.name)
        self.assertIn("def main():", script.content)
        self.assertIn("TestPackage", script.content)
        self.assertIn("logging", script.content)
    
    def test_generate_config_script(self):
        """Test configuration script generation"""
        script = self.generator._generate_config_script(self.sample_package)
        
        self.assertIsInstance(script, PythonScript)
        self.assertIn("config", script.name.lower())
        self.assertIn("TestConnection", script.content)
        self.assertIn("TestVariable", script.content)
    
    def test_generate_requirements_script(self):
        """Test requirements script generation"""
        script = self.generator._generate_requirements_script(self.sample_package)
        
        self.assertIsInstance(script, PythonScript)
        self.assertEqual(script.name, "requirements.txt")
        self.assertIn("pandas", script.content)
        self.assertIn("sqlalchemy", script.content)
    
    def test_format_connections(self):
        """Test connection formatting"""
        connections = [
            {
                "name": "TestConnection",
                "type": "OLEDB",
                "connection_string": "Server=test;Database=testdb"
            }
        ]
        
        formatted = self.generator._format_connections(connections)
        
        self.assertIn("TestConnection", formatted)
        self.assertIn("OLEDB", formatted)
        self.assertIn("Server=test", formatted)
    
    def test_format_variables(self):
        """Test variable formatting"""
        variables = [
            {
                "name": "TestVariable",
                "value": "test_value",
                "type": "String"
            }
        ]
        
        formatted = self.generator._format_variables(variables)
        
        self.assertIn("TestVariable", formatted)
        self.assertIn("test_value", formatted)
        self.assertIn("String", formatted)
    
    def test_generate_data_flow_functions(self):
        """Test data flow function generation"""
        functions = self.generator._generate_data_flow_functions(self.sample_package)
        
        self.assertIsInstance(functions, str)
        self.assertIn("def process_data_flow", functions)
        self.assertIn("TestSource", functions)
        self.assertIn("TestDestination", functions)
    
    def test_generate_control_flow_functions(self):
        """Test control flow function generation"""
        functions = self.generator._generate_control_flow_functions(self.sample_package)
        
        self.assertIsInstance(functions, str)
        self.assertIn("def execute_control_flow", functions)
        self.assertIn("TestTask", functions)
    
    def test_generate_main_execution_steps(self):
        """Test main execution steps generation"""
        steps = self.generator._generate_main_execution_steps(self.sample_package)
        
        self.assertIsInstance(steps, str)
        self.assertIn("process_data_flow", steps)
        self.assertIn("execute_control_flow", steps)
    
    def test_error_handling_in_generation(self):
        """Test error handling during generation"""
        # Create a package with invalid data to trigger errors
        invalid_package = SSISPackage(
            name="InvalidPackage",
            version="1.0.0",
            description="Invalid package",
            creation_date="2024-01-01",
            creator="TestUser",
            package_id="invalid-id"
        )
        # Add some invalid data that might cause issues
        invalid_package.data_flow_components = [{"invalid": "data"}]
        
        result = self.generator.generate_scripts(invalid_package, "/tmp/test")
        
        # Should still succeed but might have warnings
        self.assertTrue(result.success)
        # Should still generate basic scripts


if __name__ == '__main__':
    unittest.main() 