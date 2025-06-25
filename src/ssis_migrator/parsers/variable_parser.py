#!/usr/bin/env python3
"""
Variable Parser - Parse SSIS variables and parameters
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from ..core.logger import LoggerMixin


class VariableParser(LoggerMixin):
    """Parser for SSIS variables and parameters"""
    
    def __init__(self):
        self.logger.info("Variable Parser initialized")
        
        # SSIS data type mappings
        self.data_types = {
            '0': 'Empty',
            '1': 'Null',
            '2': 'Int16',
            '3': 'Int32',
            '4': 'Single',
            '5': 'Double',
            '6': 'Currency',
            '7': 'Date',
            '8': 'String',
            '9': 'Object',
            '10': 'Error',
            '11': 'Boolean',
            '12': 'Variant',
            '13': 'Decimal',
            '14': 'Byte',
            '16': 'Int64',
            '17': 'UInt64',
            '18': 'UInt32',
            '19': 'UInt16',
            '20': 'UInt8',
            '21': 'Int8',
            '22': 'Guid',
            '23': 'Date',
            '24': 'DBDate',
            '25': 'DBTime',
            '26': 'DBTimeStamp',
            '27': 'Numeric',
            '28': 'DBFileTime',
            '29': 'DBTime2',
            '30': 'DBTimeStamp2',
            '31': 'DBTimeStampOffset'
        }
    
    def parse_variable(self, var_elem: ET.Element, namespaces: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Parse a variable element
        
        Args:
            var_elem: XML element representing the variable
            namespaces: XML namespaces dictionary
            
        Returns:
            Dictionary with variable information
        """
        try:
            var_id = self._get_attr(var_elem, 'DTSID', namespaces)
            var_name = self._get_attr(var_elem, 'ObjectName', namespaces)
            data_type = self._get_attr(var_elem, 'DataType', namespaces, '8')  # Default to String
            value = self._get_attr(var_elem, 'Value', namespaces)
            
            # Get data type name
            data_type_name = self.data_types.get(data_type, f'Unknown({data_type})')
            
            # Parse variable properties
            properties = self._parse_variable_properties(var_elem, namespaces)
            
            var_info = {
                'id': var_id,
                'name': var_name,
                'data_type': data_type,
                'data_type_name': data_type_name,
                'value': value,
                'properties': properties,
                'metadata': {
                    'description': self._get_attr(var_elem, 'Description', namespaces),
                    'namespace': self._get_attr(var_elem, 'Namespace', namespaces, 'User'),
                    'read_only': self._get_attr(var_elem, 'ReadOnly', namespaces).lower() == 'true',
                    'raise_changed_event': self._get_attr(var_elem, 'RaiseChangedEvent', namespaces).lower() == 'true'
                }
            }
            
            return var_info
            
        except Exception as e:
            self.logger.error(f"Error parsing variable {self._get_attr(var_elem, 'ObjectName', namespaces, 'Unknown')}: {str(e)}")
            return None
    
    def _get_attr(self, element: ET.Element, attr_name: str, namespaces: Dict[str, str], default: str = '') -> str:
        """Get attribute value with namespace handling"""
        # Try with namespace first
        ns_attr = f'{{{namespaces["DTS"]}}}{attr_name}'
        value = element.get(ns_attr)
        if value is not None:
            return value
        # Try without namespace
        return element.get(attr_name, default)
    
    def _parse_variable_properties(self, var_elem: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Parse variable properties"""
        properties = {}
        
        # Look for properties in various locations
        for prop_elem in var_elem.findall('.//DTS:Property', namespaces):
            prop_name = self._get_attr(prop_elem, 'Name', namespaces)
            prop_value = self._get_attr(prop_elem, 'Value', namespaces)
            if prop_name:
                properties[prop_name] = prop_value
        
        return properties
    
    def parse_parameters(self, root: ET.Element, namespaces: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Parse parameters from the package (if any)
        
        Args:
            root: Root element of the package
            namespaces: XML namespaces dictionary
            
        Returns:
            List of parameter dictionaries
        """
        parameters = []
        
        # Look for parameters in various locations
        # SSIS parameters are often stored as special variables or in package properties
        
        # Check for parameter variables (variables with Parameter namespace)
        variables_elem = root.find('DTS:Variables', namespaces)
        if variables_elem is None:
            variables_elem = root.find('Variables')
        
        if variables_elem is not None:
            var_elems = variables_elem.findall('DTS:Variable', namespaces)
            if not var_elems:
                var_elems = variables_elem.findall('Variable')
            
            for var_elem in var_elems:
                namespace = self._get_attr(var_elem, 'Namespace', namespaces)
                if namespace == 'Parameter':
                    param_info = self.parse_variable(var_elem, namespaces)
                    if param_info:
                        param_info['is_parameter'] = True
                        parameters.append(param_info)
        
        return parameters
    
    def get_variable_value_by_name(self, variables: List[Dict[str, Any]], name: str) -> Optional[str]:
        """
        Get variable value by name
        
        Args:
            variables: List of variable dictionaries
            name: Variable name to search for
            
        Returns:
            Variable value if found, None otherwise
        """
        for var in variables:
            if var.get('name') == name:
                return var.get('value')
        return None
    
    def get_variables_by_namespace(self, variables: List[Dict[str, Any]], namespace: str) -> List[Dict[str, Any]]:
        """
        Get variables by namespace
        
        Args:
            variables: List of variable dictionaries
            namespace: Namespace to filter by
            
        Returns:
            List of variables in the specified namespace
        """
        return [var for var in variables if var.get('metadata', {}).get('namespace') == namespace]
    
    def get_user_variables(self, variables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get user-defined variables"""
        return self.get_variables_by_namespace(variables, 'User')
    
    def get_system_variables(self, variables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get system variables"""
        return self.get_variables_by_namespace(variables, 'System')
    
    def get_parameter_variables(self, variables: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get parameter variables"""
        return self.get_variables_by_namespace(variables, 'Parameter')
    
    def is_numeric_type(self, data_type: str) -> bool:
        """Check if data type is numeric"""
        numeric_types = ['Int16', 'Int32', 'Int64', 'Single', 'Double', 'Currency', 'Decimal', 'Numeric']
        return data_type in numeric_types
    
    def is_string_type(self, data_type: str) -> bool:
        """Check if data type is string"""
        string_types = ['String', 'Variant']
        return data_type in string_types
    
    def is_date_type(self, data_type: str) -> bool:
        """Check if data type is date/time"""
        date_types = ['Date', 'DBDate', 'DBTime', 'DBTimeStamp', 'DBFileTime', 'DBTime2', 'DBTimeStamp2', 'DBTimeStampOffset']
        return data_type in date_types
    
    def is_boolean_type(self, data_type: str) -> bool:
        """Check if data type is boolean"""
        return data_type == 'Boolean'
    
    def get_variable_summary(self, variables: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get a summary of variables
        
        Args:
            variables: List of variable dictionaries
            
        Returns:
            Summary dictionary
        """
        summary = {
            'total_variables': len(variables),
            'user_variables': len(self.get_user_variables(variables)),
            'system_variables': len(self.get_system_variables(variables)),
            'parameter_variables': len(self.get_parameter_variables(variables)),
            'data_types': {},
            'namespaces': {}
        }
        
        # Count data types
        for var in variables:
            data_type = var.get('data_type_name', 'Unknown')
            summary['data_types'][data_type] = summary['data_types'].get(data_type, 0) + 1
            
            namespace = var.get('metadata', {}).get('namespace', 'Unknown')
            summary['namespaces'][namespace] = summary['namespaces'].get(namespace, 0) + 1
        
        return summary 