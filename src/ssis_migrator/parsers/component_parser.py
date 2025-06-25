#!/usr/bin/env python3
"""
Component Parser - Parse SSIS data flow components
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional
from ..core.logger import LoggerMixin


class ComponentParser(LoggerMixin):
    """Parser for SSIS data flow components"""
    
    def __init__(self):
        self.logger.info("Component Parser initialized")
        
        # Component type mappings
        self.component_types = {
            # Sources
            '{E9216C7C-4A8A-4F77-8948-60C5D8C75F70}': 'OLE DB Source',
            '{A560E93D-4177-4C8B-9F5F-96F8FD959C4B}': 'Flat File Source',
            '{C27664E8-786E-4EB0-9A94-D2CCF1AFE4EE}': 'Excel Source',
            '{C8C8C883-0E37-4C98-A094-E4B6BB9E42B5}': 'XML Source',
            
            # Destinations
            '{E9216C7C-4A8A-4F77-8948-60C5D8C75F70}': 'OLE DB Destination',
            '{A560E93D-4177-4C8B-9F5F-96F8FD959C4B}': 'Flat File Destination',
            '{C27664E8-786E-4EB0-9A94-D2CCF1AFE4EE}': 'Excel Destination',
            
            # Transformations
            '{C9C7375C-8340-4F56-A550-919B1E4F4C66}': 'Derived Column',
            '{149447B8-8A7C-4FC7-B4E6-5DD2687916C1}': 'Data Conversion',
            '{1E7B0B8A-8A7C-4FC7-B4E6-5DD2687916C1}': 'Lookup',
            '{2E7B0B8A-8A7C-4FC7-B4E6-5DD2687916C1}': 'Merge Join',
            '{3E7B0B8A-8A7C-4FC7-B4E6-5DD2687916C1}': 'Union All',
            '{4E7B0B8A-8A7C-4FC7-B4E6-5DD2687916C1}': 'Sort',
            '{5E7B0B8A-8A7C-4FC7-B4E6-5DD2687916C1}': 'Aggregate',
            '{6E7B0B8A-8A7C-4FC7-B4E6-5DD2687916C1}': 'Conditional Split',
            '{7E7B0B8A-8A7C-4FC7-B4E6-5DD2687916C1}': 'Multicast',
            '{8E7B0B8A-8A7C-4FC7-B4E6-5DD2687916C1}': 'Script Component'
        }
    
    def parse_data_flow_component(self, comp_elem: ET.Element, namespaces: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Parse a data flow component element
        
        Args:
            comp_elem: XML element representing the component
            namespaces: XML namespaces dictionary
            
        Returns:
            Dictionary with component information
        """
        try:
            component_id = comp_elem.get('pipeline:componentClassID', '')
            component_name = comp_elem.get('pipeline:name', 'Unknown')
            component_desc = comp_elem.get('pipeline:description', '')
            
            # Determine component type
            component_type = self.component_types.get(component_id, 'Unknown')
            
            # Parse properties
            properties = self._parse_component_properties(comp_elem, namespaces)
            
            # Parse inputs and outputs
            inputs = self._parse_component_inputs(comp_elem, namespaces)
            outputs = self._parse_component_outputs(comp_elem, namespaces)
            
            component_info = {
                'id': component_id,
                'name': component_name,
                'description': component_desc,
                'type': component_type,
                'properties': properties,
                'inputs': inputs,
                'outputs': outputs,
                'metadata': {
                    'version': comp_elem.get('pipeline:version', ''),
                    'creation_name': comp_elem.get('pipeline:creationName', '')
                }
            }
            
            return component_info
            
        except Exception as e:
            self.logger.error(f"Error parsing component {comp_elem.get('pipeline:name', 'Unknown')}: {str(e)}")
            return None
    
    def _parse_component_properties(self, comp_elem: ET.Element, namespaces: Dict[str, str]) -> Dict[str, Any]:
        """Parse component properties"""
        properties = {}
        
        props_elem = comp_elem.find('pipeline:properties', namespaces)
        if props_elem is not None:
            for prop_elem in props_elem.findall('pipeline:property', namespaces):
                prop_name = prop_elem.get('pipeline:name', '')
                prop_value = prop_elem.get('pipeline:value', '')
                if prop_name:
                    properties[prop_name] = prop_value
        
        return properties
    
    def _parse_component_inputs(self, comp_elem: ET.Element, namespaces: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse component inputs"""
        inputs = []
        
        inputs_elem = comp_elem.find('pipeline:inputs', namespaces)
        if inputs_elem is not None:
            for input_elem in inputs_elem.findall('pipeline:input', namespaces):
                input_info = self._parse_input_output(input_elem, namespaces, 'input')
                if input_info:
                    inputs.append(input_info)
        
        return inputs
    
    def _parse_component_outputs(self, comp_elem: ET.Element, namespaces: Dict[str, str]) -> List[Dict[str, Any]]:
        """Parse component outputs"""
        outputs = []
        
        outputs_elem = comp_elem.find('pipeline:outputs', namespaces)
        if outputs_elem is not None:
            for output_elem in outputs_elem.findall('pipeline:output', namespaces):
                output_info = self._parse_input_output(output_elem, namespaces, 'output')
                if output_info:
                    outputs.append(output_info)
        
        return outputs
    
    def _parse_input_output(self, io_elem: ET.Element, namespaces: Dict[str, str], io_type: str) -> Optional[Dict[str, Any]]:
        """Parse input or output element"""
        try:
            io_info = {
                'name': io_elem.get(f'pipeline:{io_type.capitalize()}Name', 'Unknown'),
                'description': io_elem.get('pipeline:description', ''),
                'id': io_elem.get('pipeline:id', ''),
                'is_error_out': io_elem.get('pipeline:isErrorOut', 'False').lower() == 'true',
                'is_sorted': io_elem.get('pipeline:isSorted', 'False').lower() == 'true',
                'synchronous': io_elem.get('pipeline:synchronous', 'True').lower() == 'true',
                'columns': []
            }
            
            # Parse columns
            columns_elem = io_elem.find(f'pipeline:{io_type}Columns', namespaces)
            if columns_elem is not None:
                for col_elem in columns_elem.findall(f'pipeline:{io_type}Column', namespaces):
                    col_info = self._parse_column(col_elem, namespaces)
                    if col_info:
                        io_info['columns'].append(col_info)
            
            return io_info
            
        except Exception as e:
            self.logger.error(f"Error parsing {io_type}: {str(e)}")
            return None
    
    def _parse_column(self, col_elem: ET.Element, namespaces: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse column information"""
        try:
            col_info = {
                'name': col_elem.get('pipeline:name', ''),
                'description': col_elem.get('pipeline:description', ''),
                'lineage_id': col_elem.get('pipeline:lineageId', ''),
                'data_type': col_elem.get('pipeline:dataType', ''),
                'precision': int(col_elem.get('pipeline:precision', '0')),
                'scale': int(col_elem.get('pipeline:scale', '0')),
                'length': int(col_elem.get('pipeline:length', '0')),
                'external_metadata_column_name': col_elem.get('pipeline:externalMetadataColumnName', ''),
                'expression': col_elem.get('pipeline:expression', '')
            }
            
            return col_info
            
        except Exception as e:
            self.logger.error(f"Error parsing column: {str(e)}")
            return None
    
    def get_component_type_name(self, component_id: str) -> str:
        """Get human-readable component type name from component ID"""
        return self.component_types.get(component_id, 'Unknown')
    
    def is_source_component(self, component_type: str) -> bool:
        """Check if component is a source"""
        source_types = ['OLE DB Source', 'Flat File Source', 'Excel Source', 'XML Source']
        return component_type in source_types
    
    def is_destination_component(self, component_type: str) -> bool:
        """Check if component is a destination"""
        dest_types = ['OLE DB Destination', 'Flat File Destination', 'Excel Destination']
        return component_type in dest_types
    
    def is_transformation_component(self, component_type: str) -> bool:
        """Check if component is a transformation"""
        transform_types = [
            'Derived Column', 'Data Conversion', 'Lookup', 'Merge Join',
            'Union All', 'Sort', 'Aggregate', 'Conditional Split',
            'Multicast', 'Script Component'
        ]
        return component_type in transform_types 