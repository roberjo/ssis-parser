#!/usr/bin/env python3
"""
DTSX Parser - Main parser for SSIS .dtsx files
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from ..core.logger import LoggerMixin
from ..core.error_handler import (
    ErrorHandler, ParsingError, FileSystemError, create_error_context,
    ErrorSeverity, ErrorCategory
)
from .component_parser import ComponentParser
from .connection_parser import ConnectionParser
from .variable_parser import VariableParser
from .config_parser import ConfigParser, ConfigFile
import os


@dataclass
class SSISPackage:
    """Represents a parsed SSIS package"""
    name: str
    version: str
    description: str
    creation_date: str
    creator: str
    package_id: str
    connection_managers: List[Dict[str, Any]] = field(default_factory=list)
    variables: List[Dict[str, Any]] = field(default_factory=list)
    data_flow_components: List[Dict[str, Any]] = field(default_factory=list)
    control_flow_tasks: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    configuration_files: List[ConfigFile] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class ParsingResult:
    """Result of parsing a DTSX file"""
    success: bool
    package: Optional[SSISPackage] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DTSXParser(LoggerMixin):
    """Main parser for SSIS .dtsx files"""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.logger.info("DTSX Parser initialized")
        self.component_parser = ComponentParser()
        self.connection_parser = ConnectionParser()
        self.variable_parser = VariableParser()
        self.config_parser = ConfigParser()
        self.error_handler = error_handler or ErrorHandler()
        
        # SSIS XML namespaces
        self.namespaces = {
            'DTS': 'www.microsoft.com/SqlServer/Dts',
            'pipeline': 'www.microsoft.com/sqlserver/dts/pipeline',
            'SQLTask': 'www.microsoft.com/sqlserver/dts/tasks/sqltask'
        }
    
    def parse_file(self, file_path: str) -> ParsingResult:
        """
        Parse a .dtsx file and extract all components
        
        Args:
            file_path: Path to the .dtsx file
            
        Returns:
            ParsingResult with parsed package information
        """
        self.logger.info(f"Parsing DTSX file: {file_path}")
        
        try:
            file_path = Path(file_path)
            
            # Validate file existence
            if not file_path.exists():
                error = FileSystemError(
                    f"File does not exist: {file_path}",
                    severity=ErrorSeverity.HIGH,
                    file_path=str(file_path)
                )
                self.error_handler.handle_error(
                    error,
                    context=create_error_context(
                        file_path=str(file_path),
                        component="DTSXParser",
                        operation="parse_file"
                    )
                )
                return ParsingResult(False, errors=[str(error)])
            
            # Validate file extension
            if not file_path.suffix.lower() == '.dtsx':
                error = ParsingError(
                    f"File is not a .dtsx file: {file_path}",
                    severity=ErrorSeverity.MEDIUM,
                    file_path=str(file_path)
                )
                self.error_handler.handle_error(
                    error,
                    context=create_error_context(
                        file_path=str(file_path),
                        component="DTSXParser",
                        operation="parse_file"
                    )
                )
                return ParsingResult(False, errors=[str(error)])
            
            # Parse XML
            try:
                tree = ET.parse(file_path)
                root = tree.getroot()
            except ET.ParseError as e:
                error = ParsingError(
                    f"XML parsing error: {str(e)}",
                    severity=ErrorSeverity.HIGH,
                    file_path=str(file_path)
                )
                self.error_handler.handle_error(
                    error,
                    context=create_error_context(
                        file_path=str(file_path),
                        component="DTSXParser",
                        operation="parse_xml"
                    )
                )
                return ParsingResult(False, errors=[str(error)])
            
            # Extract package metadata
            package = self._extract_package_metadata(root)
            
            # Parse connection managers
            package.connection_managers = self._parse_connection_managers(root)
            
            # Parse variables
            package.variables = self._parse_variables(root)
            
            # Parse executables (tasks and data flows)
            self._parse_executables(root, package)
            
            # Parse configuration files
            package.configuration_files = self._parse_configuration_files(file_path)
            
            # Extract environment variables from all sources
            package.environment_variables = self._extract_all_environment_variables(package)
            
            self.logger.info(f"Successfully parsed package: {package.name}")
            return ParsingResult(True, package=package)
            
        except Exception as e:
            error = ParsingError(
                f"Unexpected error parsing DTSX file: {str(e)}",
                severity=ErrorSeverity.CRITICAL,
                file_path=str(file_path) if 'file_path' in locals() else None
            )
            self.error_handler.handle_error(
                error,
                context=create_error_context(
                    file_path=str(file_path) if 'file_path' in locals() else None,
                    component="DTSXParser",
                    operation="parse_file"
                )
            )
            return ParsingResult(False, errors=[str(error)])
    
    def _extract_package_metadata(self, root: ET.Element) -> SSISPackage:
        """Extract basic package metadata from the root element"""
        # Handle both namespaced and non-namespaced attributes
        def get_attr(element, attr_name):
            # Try with namespace first
            ns_attr = f'{{{self.namespaces["DTS"]}}}{attr_name}'
            value = element.get(ns_attr)
            if value is not None:
                return value
            # Try without namespace
            return element.get(attr_name, '')
        
        package = SSISPackage(
            name=get_attr(root, 'ObjectName'),
            version=f"{get_attr(root, 'VersionMajor')}.{get_attr(root, 'VersionMinor')}.{get_attr(root, 'VersionBuild')}",
            description=get_attr(root, 'Description'),
            creation_date=get_attr(root, 'CreationDate'),
            creator=get_attr(root, 'CreatorName'),
            package_id=get_attr(root, 'DTSID'),
            metadata={
                'executable_type': get_attr(root, 'ExecutableType'),
                'creation_name': get_attr(root, 'CreationName'),
                'creator_computer': get_attr(root, 'CreatorComputerName'),
                'package_type': get_attr(root, 'PackageType'),
                'version_guid': get_attr(root, 'VersionGUID')
            }
        )
        return package
    
    def _parse_connection_managers(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Parse connection managers from the package"""
        connection_managers = []
        
        # Find connection managers section - try both namespaced and non-namespaced
        conn_managers_elem = root.find('DTS:ConnectionManagers', self.namespaces)
        if conn_managers_elem is None:
            conn_managers_elem = root.find('ConnectionManagers')
        
        if conn_managers_elem is not None:
            # Look for connection manager elements
            conn_elems = conn_managers_elem.findall('DTS:ConnectionManager', self.namespaces)
            if not conn_elems:
                conn_elems = conn_managers_elem.findall('ConnectionManager')
            
            for conn_elem in conn_elems:
                conn_info = self.connection_parser.parse_connection_manager(conn_elem, self.namespaces)
                if conn_info:
                    connection_managers.append(conn_info)
        
        self.logger.info(f"Found {len(connection_managers)} connection managers")
        return connection_managers
    
    def _parse_variables(self, root: ET.Element) -> List[Dict[str, Any]]:
        """Parse variables from the package"""
        variables = []
        
        # Find variables section - try both namespaced and non-namespaced
        variables_elem = root.find('DTS:Variables', self.namespaces)
        if variables_elem is None:
            variables_elem = root.find('Variables')
        
        if variables_elem is not None:
            # Look for variable elements
            var_elems = variables_elem.findall('DTS:Variable', self.namespaces)
            if not var_elems:
                var_elems = variables_elem.findall('Variable')
            
            for var_elem in var_elems:
                var_info = self.variable_parser.parse_variable(var_elem, self.namespaces)
                if var_info:
                    variables.append(var_info)
        
        self.logger.info(f"Found {len(variables)} variables")
        return variables
    
    def _parse_executables(self, root: ET.Element, package: SSISPackage) -> None:
        """Parse executables (tasks and data flows) from the package"""
        # Find executables section - try both namespaced and non-namespaced
        executables_elem = root.find('DTS:Executables', self.namespaces)
        if executables_elem is None:
            executables_elem = root.find('Executables')
        
        if executables_elem is None:
            return
        
        # Look for executable elements
        exec_elems = executables_elem.findall('DTS:Executable', self.namespaces)
        if not exec_elems:
            exec_elems = executables_elem.findall('Executable')
        
        for exec_elem in exec_elems:
            exec_type = self._get_attr(exec_elem, 'ExecutableType')
            
            if exec_type == 'Microsoft.DataFlowTask':
                # Parse data flow task
                data_flow_components = self._parse_data_flow_task(exec_elem)
                package.data_flow_components.extend(data_flow_components)
                self.logger.info(f"Found {len(data_flow_components)} data flow components")
                
            elif exec_type == 'Microsoft.PackageTask':
                # Parse control flow task
                task_info = self._parse_control_flow_task(exec_elem)
                if task_info:
                    package.control_flow_tasks.append(task_info)
                    self.logger.info(f"Found control flow task: {task_info.get('name', 'Unknown')}")
    
    def _parse_data_flow_task(self, task_elem: ET.Element) -> List[Dict[str, Any]]:
        """Parse data flow task and extract components"""
        components = []
        
        # Find the data flow pipeline
        object_data = task_elem.find('DTS:ObjectData', self.namespaces)
        if object_data is None:
            object_data = task_elem.find('ObjectData')
        
        if object_data is None:
            return components
        
        # Look for pipeline:dataflow element
        dataflow_elem = object_data.find('pipeline:dataflow', self.namespaces)
        if dataflow_elem is None:
            return components
        
        # Parse components
        components_elem = dataflow_elem.find('pipeline:components', self.namespaces)
        if components_elem is not None:
            for comp_elem in components_elem.findall('pipeline:component', self.namespaces):
                comp_info = self.component_parser.parse_data_flow_component(comp_elem, self.namespaces)
                if comp_info:
                    components.append(comp_info)
        
        return components
    
    def _parse_control_flow_task(self, task_elem: ET.Element) -> Optional[Dict[str, Any]]:
        """Parse control flow task"""
        task_info = {
            'name': self._get_attr(task_elem, 'ObjectName'),
            'type': self._get_attr(task_elem, 'ExecutableType'),
            'creation_name': self._get_attr(task_elem, 'CreationName'),
            'description': self._get_attr(task_elem, 'Description'),
            'task_id': self._get_attr(task_elem, 'DTSID'),
            'properties': {}
        }
        
        # Parse task-specific properties
        object_data = task_elem.find('DTS:ObjectData', self.namespaces)
        if object_data is None:
            object_data = task_elem.find('ObjectData')
        
        if object_data is not None:
            # Handle different task types
            if task_info['creation_name'] == 'Microsoft.ExecuteSQLTask':
                sql_task_data = object_data.find('SQLTask:SqlTaskData', self.namespaces)
                if sql_task_data is not None:
                    # Get SQL task properties with proper namespace handling
                    def get_sql_attr(element, attr_name):
                        # Try with namespace first
                        ns_attr = f'{{{self.namespaces["SQLTask"]}}}{attr_name}'
                        value = element.get(ns_attr)
                        if value is not None:
                            return value
                        # Try without namespace
                        return element.get(attr_name, '')
                    
                    task_info['properties'] = {
                        'connection': get_sql_attr(sql_task_data, 'Connection'),
                        'sql_statement': get_sql_attr(sql_task_data, 'SqlStatementSource'),
                        'result_type': get_sql_attr(sql_task_data, 'ResultType')
                    }
        
        return task_info
    
    def _get_attr(self, element: ET.Element, attr_name: str) -> str:
        """Get attribute value with namespace handling"""
        # Try with namespace first
        ns_attr = f'{{{self.namespaces["DTS"]}}}{attr_name}'
        value = element.get(ns_attr)
        if value is not None:
            return value
        # Try without namespace
        return element.get(attr_name, '')
    
    def validate_dtsx_structure(self, file_path: str) -> bool:
        """
        Validate that a file has the basic structure of a DTSX file
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if the file appears to be a valid DTSX file
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Check for required DTS namespace and Executable element
            if root.tag.endswith('Executable') and self._get_attr(root, 'ExecutableType'):
                return True
            
            return False
            
        except Exception:
            return False
    
    def _parse_configuration_files(self, dtsx_file_path: Path) -> List[ConfigFile]:
        """Parse associated configuration files"""
        config_files = []
        found_paths = set()
        
        # Look for .dtsConfig files in the same directory
        config_dir = dtsx_file_path.parent
        package_name = dtsx_file_path.stem
        
        # Common configuration file patterns
        config_patterns = [
            f"{package_name}.dtsConfig",
            f"{package_name}.dtsconfig",
            "package.dtsConfig",
            "package.dtsconfig"
        ]
        
        for pattern in config_patterns:
            config_file_path = config_dir / pattern
            if config_file_path.exists() and str(config_file_path.absolute()) not in found_paths:
                self.logger.info(f"Found configuration file: {config_file_path}")
                config_file = self.config_parser.parse_config_file(str(config_file_path))
                if config_file:
                    config_files.append(config_file)
                    found_paths.add(str(config_file_path.absolute()))
        
        # Also look for any .dtsConfig files in the directory
        for config_file_path in config_dir.glob("*.dtsConfig"):
            if str(config_file_path.absolute()) not in found_paths:
                self.logger.info(f"Found additional configuration file: {config_file_path}")
                config_file = self.config_parser.parse_config_file(str(config_file_path))
                if config_file:
                    config_files.append(config_file)
                    found_paths.add(str(config_file_path.absolute()))
        
        self.logger.info(f"Found {len(config_files)} configuration files")
        return config_files
    
    def _extract_all_environment_variables(self, package: SSISPackage) -> Dict[str, str]:
        """Extract environment variables from all sources"""
        env_vars = {}
        
        # Extract from configuration files
        for config_file in package.configuration_files:
            env_vars.update(config_file.environment_variables)
        
        # Extract from connection strings
        for conn in package.connection_managers:
            conn_string = conn.get('connection_string', '')
            env_vars_in_conn = self.config_parser._find_environment_variables(conn_string)
            for env_var in env_vars_in_conn:
                env_vars[env_var] = os.environ.get(env_var, '')
        
        # Extract from variables
        for var in package.variables:
            var_value = var.get('value', '')
            env_vars_in_var = self.config_parser._find_environment_variables(var_value)
            for env_var in env_vars_in_var:
                env_vars[env_var] = os.environ.get(env_var, '')
        
        # Extract from control flow tasks
        for task in package.control_flow_tasks:
            task_props = task.get('properties', {})
            for prop_value in task_props.values():
                if isinstance(prop_value, str):
                    env_vars_in_prop = self.config_parser._find_environment_variables(prop_value)
                    for env_var in env_vars_in_prop:
                        env_vars[env_var] = os.environ.get(env_var, '') 