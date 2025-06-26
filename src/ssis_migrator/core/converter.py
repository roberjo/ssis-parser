#!/usr/bin/env python3
"""
SSIS Package Converter - Core conversion logic
"""

import logging
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from .config import Config
from .logger import LoggerMixin
from .error_handler import (
    ErrorHandler, ConversionError, FileSystemError, ValidationError, create_error_context,
    ErrorSeverity, ErrorCategory
)
from ..parsers.dtsx_parser import DTSXParser, ParsingResult
from ..parsers.config_parser import ConfigParser
from ..generators.python_generator import PythonScriptGenerator, GenerationResult
from ..generators.data_flow_mapper import DataFlowMapper
from ..generators.connection_converter import ConnectionConverter
from ..generators.variable_handler import VariableHandler
from datetime import datetime


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
    
    def __init__(self, config: Config, error_handler: Optional[ErrorHandler] = None):
        self.config = config
        self.error_handler = error_handler or ErrorHandler()
        self.dtsx_parser = DTSXParser(error_handler=self.error_handler)
        self.python_generator = PythonScriptGenerator(error_handler=self.error_handler)
        self.data_flow_mapper = DataFlowMapper(error_handler=self.error_handler)
        self.connection_converter = ConnectionConverter(error_handler=self.error_handler)
        self.variable_handler = VariableHandler(error_handler=self.error_handler)
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
            file_path = Path(package_path)
            
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
                        component="SSISConverter",
                        operation="convert_package"
                    )
                )
                return ConversionResult(False, output_path, [str(error)])
            
            # Validate file extension
            if not file_path.suffix.lower() == '.dtsx':
                error = ConversionError(
                    f"File is not a .dtsx file: {file_path}",
                    severity=ErrorSeverity.MEDIUM,
                    file_path=str(file_path)
                )
                self.error_handler.handle_error(
                    error,
                    context=create_error_context(
                        file_path=str(file_path),
                        component="SSISConverter",
                        operation="convert_package"
                    )
                )
                return ConversionResult(False, output_path, [str(error)])
            
            # Create output directory
            output_dir = Path(output_path)
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except PermissionError as e:
                error = FileSystemError(
                    f"Cannot create output directory: {output_path}",
                    severity=ErrorSeverity.HIGH,
                    file_path=output_path
                )
                self.error_handler.handle_error(
                    error,
                    context=create_error_context(
                        file_path=output_path,
                        component="SSISConverter",
                        operation="create_output_directory"
                    )
                )
                return ConversionResult(False, output_path, [str(error)])
            
            # Parse SSIS package
            parsing_result = self.dtsx_parser.parse_file(package_path)
            
            if not parsing_result.success:
                return ConversionResult(False, output_path, parsing_result.errors)
            
            package = parsing_result.package
            if not package:
                error = ConversionError(
                    "Failed to parse package",
                    severity=ErrorSeverity.HIGH,
                    source_component="DTSXParser"
                )
                self.error_handler.handle_error(
                    error,
                    context=create_error_context(
                        file_path=package_path,
                        component="SSISConverter",
                        operation="parse_package"
                    )
                )
                return ConversionResult(False, output_path, [str(error)])
            
            self.logger.info(f"Successfully parsed package: {package.name}")
            self.logger.info(f"Found {len(package.connection_managers)} connection managers")
            self.logger.info(f"Found {len(package.variables)} variables")
            self.logger.info(f"Found {len(package.data_flow_components)} data flow components")
            self.logger.info(f"Found {len(package.control_flow_tasks)} control flow tasks")
            
            # Generate Python scripts
            generation_result = self.python_generator.generate_scripts(package, str(output_dir))
            
            if not generation_result.success:
                return ConversionResult(False, output_path, generation_result.errors)
            
            # Apply data flow mapping for enhanced transformations
            try:
                data_flow_mapping = self.data_flow_mapper.map_data_flow(package.data_flow_components)
                self.logger.info("Data flow mapping completed successfully")
                self.logger.info(f"Mapped {data_flow_mapping.metadata.get('component_count', 0)} components")
                
                # Enhance generation result with data flow mapping
                generation_result.metadata.update({
                    'data_flow_mapping': data_flow_mapping.metadata,
                    'transformation_rules_applied': len(data_flow_mapping.dependencies)
                })
                
            except Exception as e:
                self.logger.warning(f"Data flow mapping failed: {str(e)}")
                # Continue without data flow mapping
                data_flow_mapping = None
            
            # Apply connection conversion for enhanced connection management
            try:
                connection_result = self.connection_converter.convert_connections(package.connection_managers)
                self.logger.info("Connection conversion completed successfully")
                self.logger.info(f"Converted {connection_result.metadata.get('connection_count', 0)} connections")
                
                # Enhance generation result with connection conversion
                generation_result.metadata.update({
                    'connection_conversion': connection_result.metadata,
                    'database_connections': connection_result.metadata.get('database_connections', 0),
                    'file_connections': connection_result.metadata.get('file_connections', 0),
                    'web_connections': connection_result.metadata.get('web_connections', 0)
                })
                
            except Exception as e:
                self.logger.warning(f"Connection conversion failed: {str(e)}")
                # Continue without connection conversion
                connection_result = None
            
            # Apply variable and parameter handling
            try:
                variable_result = self.variable_handler.handle_variables_and_parameters(
                    variables=package.variables,
                    environment_variables=package.environment_variables
                )
                self.logger.info("Variable handling completed successfully")
                self.logger.info(f"Handled {variable_result.metadata.get('variable_count', 0)} variables")
                
                # Enhance generation result with variable handling
                generation_result.metadata.update({
                    'variable_handling': variable_result.metadata,
                    'variables_processed': variable_result.metadata.get('variable_count', 0),
                    'environment_variables': variable_result.metadata.get('environment_variable_count', 0)
                })
                
            except Exception as e:
                self.logger.warning(f"Variable handling failed: {str(e)}")
                # Continue without variable handling
                variable_result = None
            
            # Write generated scripts to files
            try:
                self._write_generated_scripts(generation_result.scripts, output_dir)
            except Exception as e:
                error = ConversionError(
                    f"Failed to write generated scripts: {str(e)}",
                    severity=ErrorSeverity.MEDIUM,
                    source_component="script_writer"
                )
                self.error_handler.handle_error(
                    error,
                    context=create_error_context(
                        file_path=str(output_dir),
                        component="SSISConverter",
                        operation="write_scripts"
                    )
                )
                return ConversionResult(False, output_path, [str(error)])
            
            # Create package summary
            summary_file = output_dir / f"{package.name}_summary.json"
            try:
                self._write_package_summary(package, summary_file, generation_result)
            except Exception as e:
                error = ConversionError(
                    f"Failed to write package summary: {str(e)}",
                    severity=ErrorSeverity.MEDIUM,
                    source_component="summary_writer"
                )
                self.error_handler.handle_error(
                    error,
                    context=create_error_context(
                        file_path=str(summary_file),
                        component="SSISConverter",
                        operation="write_summary"
                    )
                )
                return ConversionResult(False, output_path, [str(error)])
            
            self.logger.info(f"Package converted successfully to: {output_path}")
            self.logger.info(f"Generated {len(generation_result.scripts)} Python scripts")
            
            return ConversionResult(
                success=True, 
                output_path=output_path,
                warnings=generation_result.warnings,
                metadata={
                    "scripts_generated": len(generation_result.scripts),
                    "package_name": package.name,
                    "components_processed": len(package.data_flow_components) + len(package.control_flow_tasks)
                }
            )
            
        except Exception as e:
            error = ConversionError(
                f"Conversion failed: {str(e)}",
                severity=ErrorSeverity.CRITICAL,
                source_component="converter"
            )
            self.error_handler.handle_error(
                error,
                context=create_error_context(
                    file_path=package_path,
                    component="SSISConverter",
                    operation="convert_package"
                )
            )
            return ConversionResult(False, output_path, [str(error)])
    
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
            
            if not input_dir.exists():
                error = FileSystemError(
                    f"Input directory does not exist: {input_path}",
                    severity=ErrorSeverity.HIGH,
                    file_path=input_path
                )
                self.error_handler.handle_error(
                    error,
                    context=create_error_context(
                        file_path=input_path,
                        component="SSISConverter",
                        operation="convert_directory"
                    )
                )
                return ConversionResult(False, output_path, [str(error)])
            
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
            all_warnings = []
            total_scripts = 0
            
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
                    all_warnings.extend(result.warnings)
                    if result.metadata:
                        total_scripts += result.metadata.get("scripts_generated", 0)
                else:
                    failed_conversions += 1
                    all_errors.extend(result.errors)
            
            self.logger.info(f"Directory conversion completed: {successful_conversions} successful, {failed_conversions} failed")
            self.logger.info(f"Total scripts generated: {total_scripts}")
            
            if failed_conversions > 0:
                return ConversionResult(False, output_path, all_errors, all_warnings)
            else:
                return ConversionResult(
                    True, 
                    output_path, 
                    warnings=all_warnings,
                    metadata={
                        "packages_converted": successful_conversions,
                        "total_scripts": total_scripts
                    }
                )
            
        except Exception as e:
            error = ConversionError(
                f"Directory conversion failed: {str(e)}",
                severity=ErrorSeverity.CRITICAL,
                source_component="directory_converter"
            )
            self.error_handler.handle_error(
                error,
                context=create_error_context(
                    file_path=input_path,
                    component="SSISConverter",
                    operation="convert_directory"
                )
            )
            return ConversionResult(False, output_path, [str(error)])
    
    def _write_generated_scripts(self, scripts: list, output_dir: Path) -> None:
        """Write generated scripts to files"""
        for script in scripts:
            script_path = output_dir / script.name
            try:
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(script.content)
                self.logger.info(f"Written script: {script_path}")
            except Exception as e:
                raise ConversionError(
                    f"Failed to write script {script.name}: {str(e)}",
                    severity=ErrorSeverity.MEDIUM,
                    source_component="file_writer"
                )
    
    def _write_package_summary(self, package, summary_file: Path, generation_result: GenerationResult) -> None:
        """Write package summary to JSON file"""
        summary = {
            "package_info": {
                "name": package.name,
                "version": package.version,
                "description": package.description,
                "creation_date": package.creation_date,
                "creator": package.creator,
                "package_id": package.package_id
            },
            "components": {
                "connection_managers": len(package.connection_managers),
                "variables": len(package.variables),
                "data_flow_components": len(package.data_flow_components),
                "control_flow_tasks": len(package.control_flow_tasks),
                "configuration_files": len(package.configuration_files),
                "environment_variables": len(package.environment_variables)
            },
            "generated_scripts": {
                "total_count": len(generation_result.scripts),
                "scripts": [
                    {
                        "name": script.name,
                        "dependencies": script.dependencies,
                        "metadata": script.metadata
                    }
                    for script in generation_result.scripts
                ]
            },
            "conversion_info": {
                "conversion_date": str(datetime.now()),
                "tool_version": "1.0.0",
                "warnings": generation_result.warnings
            }
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Written package summary: {summary_file}")
    
    def validate_package_structure(self, package_path: str) -> bool:
        """Validate that a file has the basic structure of a DTSX file"""
        return self.dtsx_parser.validate_dtsx_structure(package_path) 