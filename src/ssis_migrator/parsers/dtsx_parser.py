#!/usr/bin/env python3
"""
DTSX Parser - Main parser for SSIS .dtsx files
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from ..core.logger import LoggerMixin
from .component_parser import ComponentParser
from .connection_parser import ConnectionParser
from .variable_parser import VariableParser


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


@dataclass
class ParsingResult:
    """Result of parsing a DTSX file"""
    success: bool
    package: Optional[SSISPackage] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class DTSXParser(LoggerMixin):
    """Main parser for SSIS .dtsx files"""
    
    def __init__(self):
        self.logger.info("DTSX Parser initialized")
        self.component_parser = ComponentParser()
        self.connection_parser = ConnectionParser()
        self.variable_parser = VariableParser()
        
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
            
            if not file_path.exists():
                return ParsingResult(False, errors=[f"File does not exist: {file_path}"])
            
            if not file_path.suffix.lower() == '.dtsx':
                return ParsingResult(False, errors=[f"File is not a .dtsx file: {file_path}"])
            
            # Parse XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Extract package metadata
            package = self._extract_package_metadata(root)
            
            # Parse connection managers
            package.connection_managers = self._parse_connection_managers(root)
            
            # Parse variables
            package.variables = self._parse_variables(root)
            
            # Parse executables (tasks and data flows)
            self._parse_executables(root, package)
            
            self.logger.info(f"Successfully parsed package: {package.name}")
            return ParsingResult(True, package=package)
            
        except ET.ParseError as e:
            error_msg = f"XML parsing error: {str(e)}"
            self.logger.error(error_msg)
            return ParsingResult(False, errors=[error_msg])
        except Exception as e:
            error_msg = f"Unexpected error parsing DTSX file: {str(e)}"
            self.logger.error(error_msg)
            return ParsingResult(False, errors=[error_msg])
    
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
                    task_info['properties'] = {
                        'connection': self._get_attr(sql_task_data, 'Connection'),
                        'sql_statement': self._get_attr(sql_task_data, 'SqlStatementSource'),
                        'result_type': self._get_attr(sql_task_data, 'ResultType')
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