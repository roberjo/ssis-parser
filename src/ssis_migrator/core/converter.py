#!/usr/bin/env python3
"""
SSIS Package Converter - Core conversion logic
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional
from .config import Config
from .logger import LoggerMixin
from ..parsers.dtsx_parser import DTSXParser, ParsingResult


class ConversionResult:
    """Result of a conversion operation"""
    
    def __init__(self, success: bool, output_path: str, errors: list = None):
        self.success = success
        self.output_path = output_path
        self.errors = errors or []
        self.warnings = []
        self.metadata = {}


class SSISConverter(LoggerMixin):
    """Main converter class for SSIS packages"""
    
    def __init__(self, config: Config):
        self.config = config
        self.dtsx_parser = DTSXParser()
        self.logger.info("SSIS Converter initialized")
    
    def convert_package(
        self,
        package_path: str,
        output_path: str,
        validate: bool = True,
        test: bool = False,
        benchmark: bool = False,
        backup: bool = True
    ) -> ConversionResult:
        """Convert a single SSIS package"""
        self.logger.info(f"Converting package: {package_path}")
        
        try:
            # Create output directory
            output_dir = Path(output_path)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Parse SSIS package
            parsing_result = self.dtsx_parser.parse_file(package_path)
            
            if not parsing_result.success:
                return ConversionResult(False, output_path, parsing_result.errors)
            
            package = parsing_result.package
            if not package:
                return ConversionResult(False, output_path, ["Failed to parse package"])
            
            self.logger.info(f"Successfully parsed package: {package.name}")
            self.logger.info(f"Found {len(package.connection_managers)} connection managers")
            self.logger.info(f"Found {len(package.variables)} variables")
            self.logger.info(f"Found {len(package.data_flow_components)} data flow components")
            self.logger.info(f"Found {len(package.control_flow_tasks)} control flow tasks")
            
            # TODO: Generate Python code based on parsed components
            # TODO: Write output files
            
            # For now, just create a summary file
            summary_file = output_dir / f"{package.name}_summary.json"
            self._write_package_summary(package, summary_file)
            
            self.logger.info(f"Package converted successfully to: {output_path}")
            return ConversionResult(True, output_path)
            
        except Exception as e:
            self.logger.error(f"Conversion failed: {str(e)}")
            return ConversionResult(False, output_path, [str(e)])
    
    def convert_directory(
        self,
        input_path: str,
        output_path: str,
        validate: bool = True,
        test: bool = False,
        benchmark: bool = False,
        backup: bool = True
    ) -> ConversionResult:
        """Convert all SSIS packages in a directory"""
        self.logger.info(f"Converting packages in directory: {input_path}")
        
        try:
            input_dir = Path(input_path)
            output_dir = Path(output_path)
            
            # Find all .dtsx files
            dtsx_files = list(input_dir.glob("**/*.dtsx"))
            
            if not dtsx_files:
                self.logger.warning(f"No .dtsx files found in: {input_path}")
                return ConversionResult(True, output_path)
            
            self.logger.info(f"Found {len(dtsx_files)} packages to convert")
            
            # Convert each package
            successful_conversions = 0
            failed_conversions = 0
            all_errors = []
            
            for dtsx_file in dtsx_files:
                self.logger.info(f"Converting package: {dtsx_file.name}")
                
                # Create subdirectory for this package
                package_output_dir = output_dir / dtsx_file.stem
                
                result = self.convert_package(
                    package_path=str(dtsx_file),
                    output_path=str(package_output_dir),
                    validate=validate,
                    test=test,
                    benchmark=benchmark,
                    backup=backup
                )
                
                if result.success:
                    successful_conversions += 1
                else:
                    failed_conversions += 1
                    all_errors.extend(result.errors)
            
            self.logger.info(f"Directory conversion completed: {successful_conversions} successful, {failed_conversions} failed")
            
            if failed_conversions > 0:
                return ConversionResult(False, output_path, all_errors)
            else:
                return ConversionResult(True, output_path)
            
        except Exception as e:
            self.logger.error(f"Directory conversion failed: {str(e)}")
            return ConversionResult(False, output_path, [str(e)])
    
    def _write_package_summary(self, package, summary_file: Path) -> None:
        """Write package summary to JSON file"""
        import json
        
        summary = {
            'package_name': package.name,
            'version': package.version,
            'description': package.description,
            'creation_date': package.creation_date,
            'creator': package.creator,
            'package_id': package.package_id,
            'connection_managers': [
                {
                    'name': conn['name'],
                    'type': conn['type'],
                    'connection_string': conn['connection_string']
                }
                for conn in package.connection_managers
            ],
            'variables': [
                {
                    'name': var['name'],
                    'data_type': var['data_type_name'],
                    'value': var['value'],
                    'namespace': var['metadata']['namespace']
                }
                for var in package.variables
            ],
            'data_flow_components': [
                {
                    'name': comp['name'],
                    'type': comp['type'],
                    'description': comp['description']
                }
                for comp in package.data_flow_components
            ],
            'control_flow_tasks': [
                {
                    'name': task['name'],
                    'type': task['type'],
                    'description': task['description']
                }
                for task in package.control_flow_tasks
            ],
            'configuration_files': [
                {
                    'file_path': config.file_path,
                    'entries_count': len(config.entries),
                    'environment_variables': list(config.environment_variables.keys()),
                    'encrypted_entries': [
                        entry.path for entry in config.entries if entry.is_encrypted
                    ]
                }
                for config in package.configuration_files
            ],
            'environment_variables': package.environment_variables,
            'metadata': package.metadata
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        self.logger.info(f"Package summary written to: {summary_file}")
    
    def validate_package_structure(self, package_path: str) -> bool:
        """Validate that a file has the basic structure of a DTSX file"""
        return self.dtsx_parser.validate_dtsx_structure(package_path) 