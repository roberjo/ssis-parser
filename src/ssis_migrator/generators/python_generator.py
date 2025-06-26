#!/usr/bin/env python3
"""
Python Script Generator - Generate Python ETL scripts from SSIS packages
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from ..core.logger import LoggerMixin
from ..core.error_handler import (
    ErrorHandler, ConversionError, create_error_context,
    ErrorSeverity, ErrorCategory
)
from ..parsers.dtsx_parser import SSISPackage
from .data_flow_mapper import DataFlowMapper, DataFlowMapping


@dataclass
class PythonScript:
    """Represents a generated Python ETL script"""
    name: str
    content: str
    dependencies: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Result of script generation"""
    success: bool
    scripts: List[PythonScript] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PythonScriptGenerator(LoggerMixin):
    """Generator for Python ETL scripts from SSIS packages"""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or ErrorHandler()
        self.logger.info("Python Script Generator initialized")
        
        # Initialize data flow mapper
        self.data_flow_mapper = DataFlowMapper(error_handler=self.error_handler)
        
        # Standard ETL dependencies
        self.standard_dependencies = [
            "pandas",
            "sqlalchemy",
            "psycopg2-binary",  # PostgreSQL
            "pymssql",          # SQL Server
            "pymysql",          # MySQL
            "cx_Oracle",        # Oracle
            "pyodbc",           # ODBC connections
            "configparser",     # Configuration management
            "logging",          # Logging
            "datetime",         # Date/time handling
            "pathlib",          # Path handling
            "json",             # JSON processing
            "xml.etree.ElementTree",  # XML processing
        ]
        
        # Template for main script structure
        self.main_template = '''#!/usr/bin/env python3
"""
{script_name} - Generated ETL script from SSIS package: {package_name}
Original SSIS Package: {package_name}
Generated: {generation_date}
Description: {description}
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime
import traceback

{imports}

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('{log_file}'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

# Configuration
class Config:
    """Configuration management"""
    def __init__(self, config_file: str = None):
        self.config_file = config_file
        self.settings = {{}}
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or environment"""
        # TODO: Implement configuration loading
        pass
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.settings.get(key, default)

# Connection management
class ConnectionManager:
    """Manage database connections"""
    
    def __init__(self, config: Config):
        self.config = config
        self.connections = {{}}
    
    def get_connection(self, connection_name: str):
        """Get database connection by name"""
        if connection_name not in self.connections:
            # TODO: Implement connection creation based on SSIS connection manager
            pass
        return self.connections.get(connection_name)
    
    def close_all(self):
        """Close all connections"""
        for conn in self.connections.values():
            if hasattr(conn, 'close'):
                conn.close()
        self.connections.clear()

# Data processing functions
{data_processing_functions}

# Main execution
def main():
    """Main execution function"""
    logger = setup_logging()
    logger.info("Starting ETL process for package: {package_name}")
    
    try:
        # Initialize configuration
        config = Config()
        
        # Initialize connection manager
        conn_manager = ConnectionManager(config)
        
        # Execute ETL steps
        logger.info("Executing ETL steps...")
        
        {main_execution_steps}
        
        logger.info("ETL process completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"ETL process failed: {{str(e)}}")
        logger.error(traceback.format_exc())
        return 1
    
    finally:
        # Cleanup
        if 'conn_manager' in locals():
            conn_manager.close_all()

if __name__ == "__main__":
    sys.exit(main())
'''
        
        # Template for data flow components
        self.data_flow_template = '''
def process_data_flow_{component_id}(data_source, data_destination, config):
    """Process data flow component: {component_name}"""
    logger = logging.getLogger(__name__)
    logger.info(f"Processing data flow: {{component_name}}")
    
    try:
        # TODO: Implement specific data flow logic
        # This is a placeholder for the actual data processing logic
        
        # Example: Read from source
        # df = pd.read_sql(query, connection)
        
        # Example: Transform data
        # df = transform_data(df)
        
        # Example: Write to destination
        # df.to_sql(table_name, connection, if_exists='append', index=False)
        
        logger.info(f"Data flow {{component_name}} completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Data flow {{component_name}} failed: {{str(e)}}")
        raise
'''
        
        # Template for control flow tasks
        self.control_flow_template = '''
def execute_control_flow(config):
    """Execute control flow tasks"""
    logger = logging.getLogger(__name__)
    logger.info("Executing control flow tasks")
    
    try:
        # TODO: Implement control flow logic
        # This is a placeholder for the actual control flow execution
        
        logger.info("Control flow execution completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Control flow execution failed: {{str(e)}}")
        raise
'''
    
    def generate_scripts(self, package: SSISPackage, output_dir: str) -> GenerationResult:
        """
        Generate Python ETL scripts from SSIS package
        
        Args:
            package: Parsed SSIS package
            output_dir: Output directory for generated scripts
            
        Returns:
            GenerationResult with generated scripts
        """
        try:
            self.logger.info(f"Generating Python scripts for package: {package.name}")
            
            scripts = []
            
            # Generate main ETL script
            main_script = self._generate_main_script(package)
            scripts.append(main_script)
            
            # Generate data flow scripts
            for component in package.data_flow_components:
                component_script = self._generate_data_flow_script(component, package)
                if component_script:
                    scripts.append(component_script)
            
            # Generate control flow scripts
            for task in package.control_flow_tasks:
                task_script = self._generate_control_flow_script(task, package)
                if task_script:
                    scripts.append(task_script)
            
            # Generate configuration script
            config_script = self._generate_config_script(package)
            if config_script:
                scripts.append(config_script)
            
            # Generate requirements.txt
            requirements_script = self._generate_requirements_script(package)
            if requirements_script:
                scripts.append(requirements_script)
            
            self.logger.info(f"Generated {len(scripts)} Python scripts")
            
            return GenerationResult(
                success=True,
                scripts=scripts,
                warnings=[f"Generated {len(scripts)} scripts for package {package.name}"]
            )
            
        except Exception as e:
            error = ConversionError(
                f"Failed to generate Python scripts: {str(e)}",
                severity=ErrorSeverity.HIGH,
                source_component="PythonGenerator"
            )
            self.error_handler.handle_error(
                error,
                context=create_error_context(
                    component="PythonGenerator",
                    operation="generate_scripts"
                )
            )
            return GenerationResult(False, errors=[str(error)])
    
    def _generate_main_script(self, package: SSISPackage) -> PythonScript:
        """Generate main ETL script"""
        script_name = f"{package.name.replace(' ', '_')}_main.py"
        
        # Collect imports based on package components
        imports = self._collect_imports(package)
        
        # Generate data processing functions
        data_processing_functions = self._generate_data_processing_functions(package)
        
        # Generate main execution steps
        main_execution_steps = self._generate_main_execution_steps(package)
        
        # Format the template
        content = self.main_template.format(
            script_name=script_name,
            package_name=package.name,
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            description=package.description or "ETL script generated from SSIS package",
            imports="\n".join(imports),
            log_file=f"{package.name.lower().replace(' ', '_')}.log",
            data_processing_functions=data_processing_functions,
            main_execution_steps=main_execution_steps
        )
        
        return PythonScript(
            name=script_name,
            content=content,
            dependencies=self._collect_dependencies(package),
            imports=imports,
            metadata={
                "package_name": package.name,
                "package_version": package.version,
                "component_count": len(package.data_flow_components) + len(package.control_flow_tasks)
            }
        )
    
    def _collect_imports(self, package: SSISPackage) -> List[str]:
        """Collect required imports based on package components"""
        imports = [
            "pandas",
            "sqlalchemy",
            "configparser",
            "logging",
            "datetime",
            "traceback"
        ]
        
        # Add imports based on connection managers
        for conn in package.connection_managers:
            conn_type = conn.get('connection_type', '').lower()
            if 'sqlserver' in conn_type or 'mssql' in conn_type:
                imports.append("pymssql")
            elif 'postgresql' in conn_type or 'postgres' in conn_type:
                imports.append("psycopg2")
            elif 'mysql' in conn_type:
                imports.append("pymysql")
            elif 'oracle' in conn_type:
                imports.append("cx_Oracle")
            elif 'odbc' in conn_type:
                imports.append("pyodbc")
        
        # Add imports based on data flow components
        for component in package.data_flow_components:
            component_type = component.get('component_type', '').lower()
            if 'file' in component_type:
                imports.extend([
                    "csv",
                    "json",
                    "xml.etree.ElementTree"
                ])
            elif 'transform' in component_type:
                imports.append("numpy")
        
        # Remove duplicates and sort
        return sorted(list(set(imports)))
    
    def _collect_dependencies(self, package: SSISPackage) -> List[str]:
        """Collect required dependencies"""
        dependencies = self.standard_dependencies.copy()
        
        # Add specific dependencies based on components
        for component in package.data_flow_components:
            component_type = component.get('component_type', '').lower()
            if 'file' in component_type:
                dependencies.extend(['openpyxl', 'xlrd'])  # Excel support
            elif 'api' in component_type:
                dependencies.append('requests')
            elif 'ftp' in component_type:
                dependencies.append('ftplib')
        
        return sorted(list(set(dependencies)))
    
    def _generate_data_processing_functions(self, package: SSISPackage) -> str:
        """Generate data processing functions using data flow mapper"""
        try:
            # Use data flow mapper to generate enhanced transformation code
            data_flow_mapping = self.data_flow_mapper.map_data_flow(package.data_flow_components)
            
            # Combine all the generated code
            functions = []
            
            # Add error handling functions
            if data_flow_mapping.error_handling:
                functions.append(data_flow_mapping.error_handling)
            
            # Add transformation functions from data flow mapper
            if data_flow_mapping.source_code:
                functions.append(data_flow_mapping.source_code)
            
            if data_flow_mapping.transformation_code:
                functions.append(data_flow_mapping.transformation_code)
            
            if data_flow_mapping.destination_code:
                functions.append(data_flow_mapping.destination_code)
            
            # Add validation functions
            if data_flow_mapping.validation_code:
                functions.append(data_flow_mapping.validation_code)
            
            return "\n".join(functions) if functions else "# No data flow components found"
            
        except Exception as e:
            self.logger.warning(f"Data flow mapping failed: {str(e)}, using basic template")
            # Fall back to basic template
            functions = []
            for i, component in enumerate(package.data_flow_components):
                component_id = component.get('component_id', f'component_{i}')
                component_name = component.get('component_name', f'DataFlow_{i}')
                
                function_content = self.data_flow_template.format(
                    component_id=component_id,
                    component_name=component_name
                )
                functions.append(function_content)
            
            return "\n".join(functions)
    
    def _generate_main_execution_steps(self, package: SSISPackage) -> str:
        """Generate main execution steps"""
        steps = []
        
        # Add data flow execution steps
        for i, component in enumerate(package.data_flow_components):
            component_id = component.get('component_id', f'component_{i}')
            component_name = component.get('name', f'DataFlow_{i}')
            steps.append(f"        process_data_flow_{component_id}(None, None, config)")
        
        # Add control flow execution steps
        for i, task in enumerate(package.control_flow_tasks):
            task_id = task.get('task_id', f'task_{i}')
            task_name = task.get('name', f'Task_{i}')
            steps.append(f"        execute_task_{task_id}(config)")
        
        # Add execute_control_flow call if there are control flow tasks
        if package.control_flow_tasks:
            steps.append("        execute_control_flow(config)")
        
        return "\n".join(steps)
    
    def _generate_data_flow_script(self, component: Dict[str, Any], package: SSISPackage) -> Optional[PythonScript]:
        """Generate script for a specific data flow component"""
        try:
            component_name = component.get('component_name', 'UnknownComponent')
            script_name = f"{component_name.lower().replace(' ', '_')}_dataflow.py"
            
            # Generate component-specific logic
            content = self._generate_component_specific_logic(component, package)
            
            return PythonScript(
                name=script_name,
                content=content,
                metadata={
                    "component_type": component.get('component_type'),
                    "component_id": component.get('component_id'),
                    "package_name": package.name
                }
            )
            
        except Exception as e:
            error = ConversionError(
                f"Failed to generate data flow script: {str(e)}",
                severity=ErrorSeverity.MEDIUM,
                source_component="DataFlowGenerator"
            )
            self.error_handler.handle_error(error)
            return None
    
    def _generate_control_flow_script(self, task: Dict[str, Any], package: SSISPackage) -> Optional[PythonScript]:
        """Generate script for a specific control flow task"""
        try:
            task_name = task.get('task_name', 'UnknownTask')
            script_name = f"{task_name.lower().replace(' ', '_')}_task.py"
            
            # Generate task-specific logic
            content = self._generate_task_specific_logic(task, package)
            
            return PythonScript(
                name=script_name,
                content=content,
                metadata={
                    "task_type": task.get('task_type'),
                    "task_id": task.get('task_id'),
                    "package_name": package.name
                }
            )
            
        except Exception as e:
            error = ConversionError(
                f"Failed to generate control flow script: {str(e)}",
                severity=ErrorSeverity.MEDIUM,
                source_component="ControlFlowGenerator"
            )
            self.error_handler.handle_error(error)
            return None
    
    def _generate_config_script(self, package: SSISPackage) -> Optional[PythonScript]:
        """Generate configuration script"""
        try:
            script_name = f"{package.name.lower().replace(' ', '_')}_config.py"
            
            content = f'''#!/usr/bin/env python3
"""
Configuration for {package.name} ETL package
"""

# Database connections
DATABASE_CONNECTIONS = {{
    {self._format_connections(package.connection_managers)}
}}

# Variables
VARIABLES = {{
    {self._format_variables(package.variables)}
}}

# Environment variables
ENVIRONMENT_VARIABLES = {{
    {self._format_environment_variables(package.environment_variables)}
}}

# Package metadata
PACKAGE_METADATA = {{
    "name": "{package.name}",
    "version": "{package.version}",
    "description": "{package.description}",
    "creation_date": "{package.creation_date}",
    "creator": "{package.creator}"
}}
'''
            
            return PythonScript(
                name=script_name,
                content=content,
                metadata={
                    "package_name": package.name,
                    "connection_count": len(package.connection_managers),
                    "variable_count": len(package.variables)
                }
            )
            
        except Exception as e:
            error = ConversionError(
                f"Failed to generate config script: {str(e)}",
                severity=ErrorSeverity.MEDIUM,
                source_component="ConfigGenerator"
            )
            self.error_handler.handle_error(error)
            return None
    
    def _generate_requirements_script(self, package: SSISPackage) -> PythonScript:
        """Generate requirements.txt file"""
        dependencies = self._collect_dependencies(package)
        
        content = "# Requirements for {package.name} ETL package\n"
        content += "# Generated from SSIS package\n\n"
        content += "\n".join(dependencies)
        
        return PythonScript(
            name="requirements.txt",
            content=content,
            dependencies=dependencies,
            metadata={
                "package_name": package.name,
                "dependency_count": len(dependencies)
            }
        )
    
    def _generate_component_specific_logic(self, component: Dict[str, Any], package: SSISPackage) -> str:
        """Generate component-specific logic"""
        component_type = component.get('component_type', '').lower()
        
        if 'source' in component_type:
            return self._generate_source_component_logic(component, package)
        elif 'destination' in component_type:
            return self._generate_destination_component_logic(component, package)
        elif 'transform' in component_type:
            return self._generate_transform_component_logic(component, package)
        else:
            return self._generate_generic_component_logic(component, package)
    
    def _generate_task_specific_logic(self, task: Dict[str, Any], package: SSISPackage) -> str:
        """Generate task-specific logic"""
        task_type = task.get('task_type', '').lower()
        
        if 'sql' in task_type:
            return self._generate_sql_task_logic(task, package)
        elif 'script' in task_type:
            return self._generate_script_task_logic(task, package)
        elif 'file' in task_type:
            return self._generate_file_task_logic(task, package)
        else:
            return self._generate_generic_task_logic(task, package)
    
    def _format_connections(self, connections: List[Dict[str, Any]]) -> str:
        """Format connection managers for config"""
        formatted = []
        for conn in connections:
            conn_name = conn.get('name', 'Unknown')
            conn_type = conn.get('type', conn.get('connection_type', 'Unknown'))
            conn_string = conn.get('connection_string', '')
            formatted.append(f'    "{conn_name}": {{"type": "{conn_type}", "connection_string": "{conn_string}"}}')
        return ",\n".join(formatted) if formatted else "    # No connections defined"
    
    def _format_variables(self, variables: List[Dict[str, Any]]) -> str:
        """Format variables for config"""
        formatted = []
        for var in variables:
            var_name = var.get('name', 'Unknown')
            var_value = var.get('value', '')
            var_type = var.get('type', 'String')
            formatted.append(f'    "{var_name}": "{{"value": "{var_value}", "type": "{var_type}"}}"')
        return ",\n".join(formatted) if formatted else "    # No variables defined"
    
    def _format_environment_variables(self, env_vars: Dict[str, str]) -> str:
        """Format environment variables for config"""
        formatted = []
        for key, value in env_vars.items():
            formatted.append(f'    "{key}": "{value}"')
        return ",\n".join(formatted) if formatted else "    # No environment variables defined"
    
    def _generate_data_flow_functions(self, package: SSISPackage) -> str:
        """Generate data flow functions"""
        functions = []
        for i, component in enumerate(package.data_flow_components):
            component_id = component.get('component_id', f'component_{i}')
            component_name = component.get('name', f'DataFlow_{i}')
            
            function_content = f'''
def process_data_flow_{component_id}(data_source, data_destination, config):
    """Process data flow component: {component_name}"""
    logger = logging.getLogger(__name__)
    logger.info(f"Processing data flow: {{component_name}}")
    
    try:
        # TODO: Implement specific data flow logic for {component_name}
        # This is a placeholder for the actual data processing logic
        
        logger.info(f"Data flow {{component_name}} completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Data flow {{component_name}} failed: {{str(e)}}")
        raise
'''
            functions.append(function_content)
        
        return "\n".join(functions) if functions else "# No data flow components found"
    
    def _generate_control_flow_functions(self, package: SSISPackage) -> str:
        """Generate control flow functions"""
        functions = []
        
        # Add individual task functions
        for i, task in enumerate(package.control_flow_tasks):
            task_id = task.get('task_id', f'task_{i}')
            task_name = task.get('name', f'Task_{i}')
            
            function_content = f'''
def execute_task_{task_id}(config):
    """Execute control flow task: {task_name}"""
    logger = logging.getLogger(__name__)
    logger.info(f"Executing task: {{task_name}}")
    
    try:
        # TODO: Implement specific task logic for {task_name}
        # This is a placeholder for the actual task execution logic
        
        logger.info(f"Task {{task_name}} completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Task {{task_name}} failed: {{str(e)}}")
        raise
'''
            functions.append(function_content)
        
        # Add the main execute_control_flow function
        if package.control_flow_tasks:
            control_flow_function = '''
def execute_control_flow(config):
    """Execute all control flow tasks"""
    logger = logging.getLogger(__name__)
    logger.info("Executing control flow tasks")
    
    try:
        # Execute all tasks in sequence
'''
            for i, task in enumerate(package.control_flow_tasks):
                task_id = task.get('task_id', f'task_{i}')
                task_name = task.get('name', f'Task_{i}')
                control_flow_function += f'''
        # Execute task: {task_name}
        execute_task_{task_id}(config)
'''
            control_flow_function += '''
        logger.info("All control flow tasks completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Control flow execution failed: {str(e)}")
        raise
'''
            functions.append(control_flow_function)
        
        return "\n".join(functions) if functions else "# No control flow tasks found"
    
    # Placeholder methods for specific component/task logic generation
    def _generate_source_component_logic(self, component: Dict[str, Any], package: SSISPackage) -> str:
        """Generate source component logic"""
        return f'''
# Source component: {component.get('component_name', 'Unknown')}
def read_from_source():
    """Read data from source"""
    # TODO: Implement source-specific logic
    pass
'''
    
    def _generate_destination_component_logic(self, component: Dict[str, Any], package: SSISPackage) -> str:
        """Generate destination component logic"""
        return f'''
# Destination component: {component.get('component_name', 'Unknown')}
def write_to_destination(data):
    """Write data to destination"""
    # TODO: Implement destination-specific logic
    pass
'''
    
    def _generate_transform_component_logic(self, component: Dict[str, Any], package: SSISPackage) -> str:
        """Generate transform component logic"""
        return f'''
# Transform component: {component.get('component_name', 'Unknown')}
def transform_data(data):
    """Transform data"""
    # TODO: Implement transform-specific logic
    pass
'''
    
    def _generate_generic_component_logic(self, component: Dict[str, Any], package: SSISPackage) -> str:
        """Generate generic component logic"""
        return f'''
# Component: {component.get('component_name', 'Unknown')}
def process_component():
    """Process component"""
    # TODO: Implement component-specific logic
    pass
'''
    
    def _generate_sql_task_logic(self, task: Dict[str, Any], package: SSISPackage) -> str:
        """Generate SQL task logic"""
        return f'''
# SQL Task: {task.get('task_name', 'Unknown')}
def execute_sql_task():
    """Execute SQL task"""
    # TODO: Implement SQL task logic
    pass
'''
    
    def _generate_script_task_logic(self, task: Dict[str, Any], package: SSISPackage) -> str:
        """Generate script task logic"""
        return f'''
# Script Task: {task.get('task_name', 'Unknown')}
def execute_script_task():
    """Execute script task"""
    # TODO: Implement script task logic
    pass
'''
    
    def _generate_file_task_logic(self, task: Dict[str, Any], package: SSISPackage) -> str:
        """Generate file task logic"""
        return f'''
# File Task: {task.get('task_name', 'Unknown')}
def execute_file_task():
    """Execute file task"""
    # TODO: Implement file task logic
    pass
'''
    
    def _generate_generic_task_logic(self, task: Dict[str, Any], package: SSISPackage) -> str:
        """Generate generic task logic"""
        return f'''
# Task: {task.get('task_name', 'Unknown')}
def execute_task():
    """Execute task"""
    # TODO: Implement task-specific logic
    pass
''' 