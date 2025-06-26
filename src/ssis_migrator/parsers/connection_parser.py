#!/usr/bin/env python3
"""
Connection Parser - Parse SSIS connection managers
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from ..core.logger import LoggerMixin


class ConnectionParser(LoggerMixin):
    """Parser for SSIS connection managers"""
    
    def __init__(self):
        self.logger.info("Connection Parser initialized")
        
        # Connection manager type mappings
        self.connection_types = {
            'OLEDB': 'OLE DB Connection',
            'FLATFILE': 'Flat File Connection',
            'EXCEL': 'Excel Connection',
            'FTP': 'FTP Connection',
            'HTTP': 'HTTP Connection',
            'SMTP': 'SMTP Connection',
            'WMI': 'WMI Connection',
            'MSMQ': 'MSMQ Connection',
            'FILE': 'File Connection',
            'CACHE': 'Cache Connection'
        }
    
    def parse_connection_manager(self, conn_elem: ET.Element, namespaces: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Parse a connection manager element
        
        Args:
            conn_elem: XML element representing the connection manager
            namespaces: XML namespaces dictionary
            
        Returns:
            Dictionary with connection manager information
        """
        try:
            conn_id = self._get_attr(conn_elem, 'DTSID', namespaces)
            conn_name = self._get_attr(conn_elem, 'ObjectName', namespaces)
            creation_name = self._get_attr(conn_elem, 'CreationName', namespaces)
            
            # Determine connection type
            conn_type = self._get_connection_type(creation_name)
            
            # Parse connection string and properties
            connection_string = self._get_attr(conn_elem, 'ConnectionString', namespaces)
            properties = self._parse_connection_properties(conn_elem, namespaces)
            
            # Parse object data for additional properties
            object_data = self._parse_connection_object_data(conn_elem, namespaces)
            
            conn_info = {
                'id': conn_id,
                'name': conn_name,
                'type': conn_type,
                'creation_name': creation_name,
                'connection_string': connection_string,
                'properties': properties,
                'object_data': object_data,
                'metadata': {
                    'description': self._get_attr(conn_elem, 'Description', namespaces),
                    'retain_same_connection': self._get_attr(conn_elem, 'RetainSameConnection', namespaces).lower() == 'true'
                }
            }
            
            return conn_info
            
        except Exception as e:
            self.logger.error(f"Error parsing connection manager {self._get_attr(conn_elem, 'ObjectName', namespaces, 'Unknown')}: {str(e)}")
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
    
    def _get_connection_type(self, creation_name: str) -> str:
        """Get human-readable connection type from creation name"""
        # Extract the type from creation name (e.g., "OLEDB" from "Microsoft.OLEDB")
        if '.' in creation_name:
            type_part = creation_name.split('.')[-1]
            return self.connection_types.get(type_part, type_part)
        return creation_name
    
    def _parse_connection_properties(self, conn_elem: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Parse connection manager properties"""
        properties = {}
        
        # Look for properties in various locations
        for prop_elem in conn_elem.findall('.//DTS:Property', namespaces):
            prop_name = self._get_attr(prop_elem, 'Name', namespaces)
            prop_value = self._get_attr(prop_elem, 'Value', namespaces)
            if prop_name:
                properties[prop_name] = prop_value
        
        return properties
    
    def _parse_connection_object_data(self, conn_elem: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Parse connection manager object data"""
        object_data = {}
        
        obj_data_elem = conn_elem.find('DTS:ObjectData', namespaces)
        if obj_data_elem is None:
            obj_data_elem = conn_elem.find('ObjectData')
        
        if obj_data_elem is not None:
            # Look for nested connection manager elements
            nested_conn = obj_data_elem.find('DTS:ConnectionManager', namespaces)
            if nested_conn is None:
                nested_conn = obj_data_elem.find('ConnectionManager')
            
            if nested_conn is not None:
                object_data['nested_connection_string'] = self._get_attr(nested_conn, 'ConnectionString', namespaces)
                
                # Parse nested properties
                for prop_elem in nested_conn.findall('DTS:Property', namespaces):
                    prop_name = self._get_attr(prop_elem, 'Name', namespaces)
                    prop_value = self._get_attr(prop_elem, 'Value', namespaces)
                    if prop_name:
                        object_data[prop_name] = prop_value
        
        return object_data
    
    def extract_connection_parameters(self, connection_string: str) -> Dict[str, str]:
        """
        Extract parameters from a connection string
        
        Args:
            connection_string: The connection string to parse
            
        Returns:
            Dictionary of connection parameters
        """
        params = {}
        
        if not connection_string:
            return params
        
        # Split by semicolon and parse key-value pairs
        parts = connection_string.split(';')
        for part in parts:
            if '=' in part:
                key, value = part.split('=', 1)
                params[key.strip()] = value.strip()
        
        return params
    
    def is_database_connection(self, conn_type: str) -> bool:
        """Check if connection is a database connection"""
        db_types = ['OLE DB Connection', 'ADO.NET Connection', 'ODBC Connection']
        return conn_type in db_types
    
    def is_file_connection(self, conn_type: str) -> bool:
        """Check if connection is a file connection"""
        file_types = ['Flat File Connection', 'Excel Connection', 'File Connection']
        return conn_type in file_types
    
    def is_web_connection(self, conn_type: str) -> bool:
        """Check if connection is a web service connection"""
        web_types = ['HTTP Connection', 'FTP Connection', 'SMTP Connection']
        return conn_type in web_types
    
    def get_connection_summary(self, conn_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get a summary of connection information
        
        Args:
            conn_info: Connection manager information
            
        Returns:
            Summary dictionary
        """
        summary = {
            'name': conn_info.get('name', 'Unknown'),
            'type': conn_info.get('type', 'Unknown'),
            'connection_string': conn_info.get('connection_string', ''),
            'parameters': self.extract_connection_parameters(conn_info.get('connection_string', '')),
            'is_database': self.is_database_connection(conn_info.get('type', '')),
            'is_file': self.is_file_connection(conn_info.get('type', '')),
            'is_web': self.is_web_connection(conn_info.get('type', ''))
        }
        
        return summary 