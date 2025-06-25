#!/usr/bin/env python3
"""
Simple test script for Python generator
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ssis_migrator.generators.python_generator import PythonScriptGenerator
from ssis_migrator.parsers.dtsx_parser import SSISPackage
from ssis_migrator.core.error_handler import ErrorHandler

def test_python_generator():
    """Test the Python generator with a sample package"""
    
    # Create a sample SSIS package
    sample_package = SSISPackage(
        name="TestETLPackage",
        version="1.0.0",
        description="Test ETL package for Python generation",
        creation_date="2024-01-01",
        creator="TestUser",
        package_id="test-etl-123",
        connection_managers=[
            {
                "connection_name": "SourceDB",
                "connection_type": "OLEDB",
                "connection_string": "Server=source;Database=sourcedb"
            },
            {
                "connection_name": "TargetDB", 
                "connection_type": "OLEDB",
                "connection_string": "Server=target;Database=targetdb"
            }
        ],
        variables=[
            {
                "variable_name": "BatchSize",
                "variable_value": "1000",
                "variable_type": "Int32"
            },
            {
                "variable_name": "LogLevel",
                "variable_value": "INFO",
                "variable_type": "String"
            }
        ],
        data_flow_components=[
            {
                "component_id": "source_1",
                "component_name": "CustomerSource",
                "component_type": "OLE DB Source",
                "description": "Read customer data from source"
            },
            {
                "component_id": "transform_1",
                "component_name": "DataCleansing",
                "component_type": "Data Conversion",
                "description": "Clean and transform customer data"
            },
            {
                "component_id": "dest_1",
                "component_name": "CustomerTarget",
                "component_type": "OLE DB Destination",
                "description": "Write customer data to target"
            }
        ],
        control_flow_tasks=[
            {
                "task_id": "sql_1",
                "task_name": "TruncateTarget",
                "task_type": "Execute SQL Task",
                "description": "Truncate target table before load"
            },
            {
                "task_id": "script_1",
                "task_name": "SendNotification",
                "task_type": "Script Task",
                "description": "Send completion notification"
            }
        ],
        configuration_files=[],
        environment_variables={
            "ENV_DB_SERVER": "prod-server",
            "ENV_LOG_PATH": "/var/log/etl"
        }
    )
    
    # Initialize generator
    error_handler = ErrorHandler()
    generator = PythonScriptGenerator(error_handler=error_handler)
    
    # Generate scripts
    print("Generating Python scripts...")
    result = generator.generate_scripts(sample_package, "./test_output")
    
    if result.success:
        print(f"✅ Successfully generated {len(result.scripts)} scripts")
        
        for script in result.scripts:
            print(f"📄 {script.name}")
            print(f"   Dependencies: {len(script.dependencies)}")
            print(f"   Imports: {len(script.imports)}")
            print(f"   Content length: {len(script.content)} characters")
            print()
        
        # Write scripts to files
        os.makedirs("./test_output", exist_ok=True)
        for script in result.scripts:
            with open(f"./test_output/{script.name}", 'w') as f:
                f.write(script.content)
            print(f"💾 Written: ./test_output/{script.name}")
        
        print("\n🎉 Python generation test completed successfully!")
        
    else:
        print(f"❌ Generation failed: {result.errors}")
        return False
    
    return True

if __name__ == "__main__":
    test_python_generator() 