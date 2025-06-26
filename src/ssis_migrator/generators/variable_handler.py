#!/usr/bin/env python3
"""
Variable and Parameter Handler - Handle SSIS variables and parameters in Python
"""

import re
import os
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from ..core.logger import LoggerMixin
from ..core.error_handler import (
    ErrorHandler, ConversionError, create_error_context,
    ErrorSeverity, ErrorCategory
)


class VariableScope(Enum):
    """Variable scope types"""
    PACKAGE = "package"
    SYSTEM = "system"
    USER = "user"
    ENVIRONMENT = "environment"
    UNKNOWN = "unknown"


class VariableType(Enum):
    """Variable data types"""
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    OBJECT = "object"
    UNKNOWN = "unknown"


@dataclass
class VariableConfig:
    """Variable configuration"""
    name: str
    value: Any
    variable_type: VariableType
    scope: VariableScope
    description: Optional[str] = None
    is_read_only: bool = False
    is_required: bool = False
    default_value: Optional[Any] = None
    validation_rules: Optional[str] = None


@dataclass
class ParameterConfig:
    """Parameter configuration"""
    name: str
    value: Any
    parameter_type: VariableType
    direction: str = "input"  # input, output, input_output
    description: Optional[str] = None
    is_required: bool = False
    default_value: Optional[Any] = None
    validation_rules: Optional[str] = None


@dataclass
class EnvironmentVariable:
    """Environment variable representation"""
    name: str
    value: str
    description: Optional[str] = None
    is_secret: bool = False


@dataclass
class VariableHandlingResult:
    """Result of variable and parameter handling"""
    variables: List[VariableConfig]
    parameters: List[ParameterConfig]
    environment_variables: List[EnvironmentVariable]
    python_code: str
    config_code: str
    validation_code: str
    imports: List[str]
    dependencies: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


class VariableHandler(LoggerMixin):
    """Handle SSIS variables and parameters in Python"""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or ErrorHandler()
        self.logger.info("Variable Handler initialized")
        
        # Variable type mappings
        self.type_mappings = {
            'String': VariableType.STRING,
            'Int32': VariableType.INT,
            'Int64': VariableType.INT,
            'Double': VariableType.FLOAT,
            'Boolean': VariableType.BOOLEAN,
            'DateTime': VariableType.DATETIME,
            'Object': VariableType.OBJECT
        }
        
        # Scope mappings
        self.scope_mappings = {
            'Package': VariableScope.PACKAGE,
            'System': VariableScope.SYSTEM,
            'User': VariableScope.USER,
            'Environment': VariableScope.ENVIRONMENT
        }
    
    def handle_variables_and_parameters(
        self,
        variables: List[Dict[str, Any]],
        parameters: List[Dict[str, Any]] = None,
        environment_variables: Dict[str, str] = None
    ) -> VariableHandlingResult:
        """
        Handle SSIS variables and parameters
        
        Args:
            variables: List of SSIS variables
            parameters: List of SSIS parameters (optional)
            environment_variables: Dictionary of environment variables (optional)
            
        Returns:
            VariableHandlingResult with Python variable handling code
        """
        try:
            self.logger.info(f"Handling {len(variables)} variables and {len(parameters or [])} parameters")
            
            # Convert variables
            variable_configs = []
            for var in variables:
                try:
                    var_config = self._convert_variable(var)
                    variable_configs.append(var_config)
                except Exception as e:
                    error = ConversionError(
                        f"Failed to convert variable {var.get('name', 'Unknown')}: {str(e)}",
                        severity=ErrorSeverity.MEDIUM,
                        source_component="VariableHandler"
                    )
                    self.error_handler.handle_error(error)
                    continue
            
            # Convert parameters
            parameter_configs = []
            if parameters:
                for param in parameters:
                    try:
                        param_config = self._convert_parameter(param)
                        parameter_configs.append(param_config)
                    except Exception as e:
                        error = ConversionError(
                            f"Failed to convert parameter {param.get('name', 'Unknown')}: {str(e)}",
                            severity=ErrorSeverity.MEDIUM,
                            source_component="VariableHandler"
                        )
                        self.error_handler.handle_error(error)
                        continue
            
            # Convert environment variables
            env_vars = []
            if environment_variables:
                for name, value in environment_variables.items():
                    try:
                        env_var = self._convert_environment_variable(name, value)
                        env_vars.append(env_var)
                    except Exception as e:
                        error = ConversionError(
                            f"Failed to convert environment variable {name}: {str(e)}",
                            severity=ErrorSeverity.MEDIUM,
                            source_component="VariableHandler"
                        )
                        self.error_handler.handle_error(error)
                        continue
            
            # Generate Python code
            python_code = self._generate_variable_code(variable_configs, parameter_configs, env_vars)
            config_code = self._generate_config_code(variable_configs, parameter_configs, env_vars)
            validation_code = self._generate_validation_code(variable_configs, parameter_configs)
            
            # Collect imports and dependencies
            imports = ["import os", "import configparser", "from typing import Any, Optional"]
            dependencies = ["configparser"]
            
            result = VariableHandlingResult(
                variables=variable_configs,
                parameters=parameter_configs,
                environment_variables=env_vars,
                python_code=python_code,
                config_code=config_code,
                validation_code=validation_code,
                imports=imports,
                dependencies=dependencies,
                metadata={
                    'variable_count': len(variable_configs),
                    'parameter_count': len(parameter_configs),
                    'environment_variable_count': len(env_vars),
                    'total_configs': len(variable_configs) + len(parameter_configs) + len(env_vars)
                }
            )
            
            self.logger.info("Variable and parameter handling completed successfully")
            return result
            
        except Exception as e:
            error = ConversionError(
                f"Failed to handle variables and parameters: {str(e)}",
                severity=ErrorSeverity.HIGH,
                source_component="VariableHandler"
            )
            self.error_handler.handle_error(
                error,
                context=create_error_context(
                    component="VariableHandler",
                    operation="handle_variables_and_parameters"
                )
            )
            raise
    
    def _convert_variable(self, variable: Dict[str, Any]) -> VariableConfig:
        """Convert SSIS variable to VariableConfig"""
        name = variable.get('name', 'Unknown')
        value = variable.get('value', '')
        var_type = variable.get('type', 'String')
        scope = variable.get('scope', 'Package')
        description = variable.get('description', '')
        
        # Determine variable type
        variable_type = self.type_mappings.get(var_type, VariableType.UNKNOWN)
        
        # Determine scope
        variable_scope = self.scope_mappings.get(scope, VariableScope.UNKNOWN)
        
        # Convert value based on type
        converted_value = self._convert_value(value, variable_type)
        
        return VariableConfig(
            name=name,
            value=converted_value,
            variable_type=variable_type,
            scope=variable_scope,
            description=description,
            is_read_only=variable.get('read_only', False),
            is_required=variable.get('required', False),
            default_value=variable.get('default_value'),
            validation_rules=variable.get('validation_rules')
        )
    
    def _convert_parameter(self, parameter: Dict[str, Any]) -> ParameterConfig:
        """Convert SSIS parameter to ParameterConfig"""
        name = parameter.get('name', 'Unknown')
        value = parameter.get('value', '')
        param_type = parameter.get('type', 'String')
        direction = parameter.get('direction', 'input')
        description = parameter.get('description', '')
        
        # Determine parameter type
        parameter_type = self.type_mappings.get(param_type, VariableType.UNKNOWN)
        
        # Convert value based on type
        converted_value = self._convert_value(value, parameter_type)
        
        return ParameterConfig(
            name=name,
            value=converted_value,
            parameter_type=parameter_type,
            direction=direction,
            description=description,
            is_required=parameter.get('required', False),
            default_value=parameter.get('default_value'),
            validation_rules=parameter.get('validation_rules')
        )
    
    def _convert_environment_variable(self, name: str, value: str) -> EnvironmentVariable:
        """Convert environment variable to EnvironmentVariable"""
        # Check if it's a secret (password, key, etc.)
        is_secret = any(secret_word in name.lower() for secret_word in [
            'password', 'passwd', 'pwd', 'secret', 'key', 'token', 'auth'
        ])
        
        return EnvironmentVariable(
            name=name,
            value=value,
            description=f"Environment variable: {name}",
            is_secret=is_secret
        )
    
    def _convert_value(self, value: Any, value_type: VariableType) -> Any:
        """Convert value based on type"""
        if value is None or value == '':
            return None
        
        try:
            if value_type == VariableType.INT:
                return int(value)
            elif value_type == VariableType.FLOAT:
                return float(value)
            elif value_type == VariableType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ['true', '1', 'yes', 'on']
                return bool(value)
            elif value_type == VariableType.DATETIME:
                # Handle datetime conversion
                from datetime import datetime
                if isinstance(value, str):
                    return datetime.fromisoformat(value.replace('Z', '+00:00'))
                return value
            else:
                return str(value)
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Failed to convert value {value} to type {value_type}: {str(e)}")
            return str(value)
    
    def _generate_variable_code(
        self,
        variables: List[VariableConfig],
        parameters: List[ParameterConfig],
        environment_variables: List[EnvironmentVariable]
    ) -> str:
        """Generate Python code for variable handling"""
        code_lines = [
            "# Variable and Parameter Handling",
            "",
            "class VariableManager:",
            "    \"\"\"Manage SSIS variables and parameters\"\"\"",
            "",
            "    def __init__(self):",
            "        self.variables = {}",
            "        self.parameters = {}",
            "        self._load_variables()",
            "        self._load_parameters()",
            "        self._load_environment_variables()",
            "",
            "    def _load_variables(self):",
            "        \"\"\"Load variables from configuration\"\"\""
        ]
        
        # Add variable loading code
        for var in variables:
            code_lines.extend([
                f"        # {var.name}: {var.description or 'No description'}",
                f"        self.variables['{var.name}'] = {repr(var.value)}"
            ])
        
        code_lines.extend([
            "",
            "    def _load_parameters(self):",
            "        \"\"\"Load parameters from configuration\"\"\""
        ])
        
        # Add parameter loading code
        for param in parameters:
            code_lines.extend([
                f"        # {param.name}: {param.description or 'No description'}",
                f"        self.parameters['{param.name}'] = {repr(param.value)}"
            ])
        
        code_lines.extend([
            "",
            "    def _load_environment_variables(self):",
            "        \"\"\"Load environment variables\"\"\""
        ])
        
        # Add environment variable loading code
        for env_var in environment_variables:
            if env_var.is_secret:
                code_lines.extend([
                    f"        # {env_var.name}: {env_var.description} (SECRET)",
                    f"        self.variables['{env_var.name}'] = os.getenv('{env_var.name}', '')"
                ])
            else:
                code_lines.extend([
                    f"        # {env_var.name}: {env_var.description}",
                    f"        self.variables['{env_var.name}'] = os.getenv('{env_var.name}', '')"
                ])
        
        code_lines.extend([
            "",
            "    def get_variable(self, name: str, default=None):",
            "        \"\"\"Get variable value\"\"\"",
            "        return self.variables.get(name, default)",
            "",
            "    def set_variable(self, name: str, value: Any):",
            "        \"\"\"Set variable value\"\"\"",
            "        self.variables[name] = value",
            "",
            "    def get_parameter(self, name: str, default=None):",
            "        \"\"\"Get parameter value\"\"\"",
            "        return self.parameters.get(name, default)",
            "",
            "    def set_parameter(self, name: str, value: Any):",
            "        \"\"\"Set parameter value\"\"\"",
            "        self.parameters[name] = value",
            "",
            "    def get_environment_variable(self, name: str, default=None):",
            "        \"\"\"Get environment variable value\"\"\"",
            "        return os.getenv(name, default)",
            "",
            "    def set_environment_variable(self, name: str, value: str):",
            "        \"\"\"Set environment variable value\"\"\"",
            "        os.environ[name] = value",
            "",
            "    def validate_configuration(self):",
            "        \"\"\"Validate all variables and parameters\"\"\"",
            "        errors = []",
            "",
            "        # Validate required variables",
            "        for var in self.variables:",
            "            if var.is_required and not var.value:",
            "                errors.append(f\"Required variable {var.name} is missing or empty\")",
            "",
            "        # Validate required parameters",
            "        for param in self.parameters:",
            "            if param.is_required and not param.value:",
            "                errors.append(f\"Required parameter {param.name} is missing or empty\")",
            "",
            "        if errors:",
            "            raise ValueError(f\"Configuration validation failed: {'; '.join(errors)}\")",
            "",
            "        return True",
            ""
        ])
        
        return "\n".join(code_lines)
    
    def _generate_config_code(
        self,
        variables: List[VariableConfig],
        parameters: List[ParameterConfig],
        environment_variables: List[EnvironmentVariable]
    ) -> str:
        """Generate configuration code"""
        code_lines = [
            "# Configuration for variables and parameters",
            "",
            "# Variables",
            "VARIABLES = {"
        ]
        
        for var in variables:
            code_lines.append(f"    '{var.name}': {repr(var.value)},  # {var.description or 'No description'}")
        
        code_lines.extend([
            "}",
            "",
            "# Parameters",
            "PARAMETERS = {"
        ])
        
        for param in parameters:
            code_lines.append(f"    '{param.name}': {repr(param.value)},  # {param.description or 'No description'}")
        
        code_lines.extend([
            "}",
            "",
            "# Environment Variables",
            "ENVIRONMENT_VARIABLES = {"
        ])
        
        for env_var in environment_variables:
            if env_var.is_secret:
                code_lines.append(f"    '{env_var.name}': '***SECRET***',  # {env_var.description}")
            else:
                code_lines.append(f"    '{env_var.name}': '{env_var.value}',  # {env_var.description}")
        
        code_lines.append("}")
        
        return "\n".join(code_lines)
    
    def _generate_validation_code(
        self,
        variables: List[VariableConfig],
        parameters: List[ParameterConfig]
    ) -> str:
        """Generate validation code"""
        code_lines = [
            "# Validation functions",
            "",
            "def validate_variable_type(value: Any, expected_type: str) -> bool:",
            "    \"\"\"Validate variable type\"\"\"",
            "    try:",
            "        if expected_type == 'int':",
            "            int(value)",
            "        elif expected_type == 'float':",
            "            float(value)",
            "        elif expected_type == 'boolean':",
            "            if isinstance(value, str):",
            "                return value.lower() in ['true', 'false', '1', '0', 'yes', 'no']",
            "            return isinstance(value, bool)",
            "        elif expected_type == 'datetime':",
            "            from datetime import datetime",
            "            if isinstance(value, str):",
            "                datetime.fromisoformat(value.replace('Z', '+00:00'))",
            "        return True",
            "    except (ValueError, TypeError):",
            "        return False",
            "",
            "def validate_required_variables(variables: dict, required_vars: list) -> list:",
            "    \"\"\"Validate required variables\"\"\"",
            "    missing = []",
            "    for var_name in required_vars:",
            "        if var_name not in variables or not variables[var_name]:",
            "            missing.append(var_name)",
            "    return missing",
            "",
            "def validate_parameter_substitution(text: str, parameters: dict) -> str:",
            "    \"\"\"Validate and perform parameter substitution\"\"\"",
            "    import re",
            "",
            "    # Pattern for parameter substitution: $(ParameterName) or @[User::VariableName]",
            "    param_pattern = r'\\$\\(([^)]+)\\)|@\\[User::([^\\]]+)\\]'",
            "",
            "    def replace_param(match):",
            "        param_name = match.group(1) or match.group(2)",
            "        if param_name in parameters:",
            "            return str(parameters[param_name])",
            "        else:",
            "            raise ValueError(f\"Parameter {param_name} not found\")",
            "",
            "    return re.sub(param_pattern, replace_param, text)",
            ""
        ]
        
        return "\n".join(code_lines)
    
    def substitute_parameters(self, text: str, parameters: Dict[str, Any]) -> str:
        """Substitute parameters in text"""
        if not text or not parameters:
            return text
        
        # Pattern for parameter substitution: $(ParameterName) or @[User::VariableName]
        param_pattern = r'\$\(([^)]+)\)|@\[User::([^\]]+)\]'
        
        def replace_param(match):
            param_name = match.group(1) or match.group(2)
            if param_name in parameters:
                return str(parameters[param_name])
            else:
                self.logger.warning(f"Parameter {param_name} not found for substitution")
                return match.group(0)  # Keep original if not found
        
        return re.sub(param_pattern, replace_param, text)
    
    def validate_configuration(
        self,
        variables: List[VariableConfig],
        parameters: List[ParameterConfig]
    ) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate required variables
        for var in variables:
            if var.is_required and (var.value is None or var.value == ''):
                errors.append(f"Required variable {var.name} is missing or empty")
        
        # Validate required parameters
        for param in parameters:
            if param.is_required and (param.value is None or param.value == ''):
                errors.append(f"Required parameter {param.name} is missing or empty")
        
        # Validate variable types
        for var in variables:
            if var.value is not None and var.validation_rules:
                # Basic type validation
                if not self._validate_value_type(var.value, var.variable_type):
                    errors.append(f"Variable {var.name} has invalid type for {var.variable_type.value}")
        
        return errors
    
    def _validate_value_type(self, value: Any, value_type: VariableType) -> bool:
        """Validate value type"""
        try:
            if value_type == VariableType.INT:
                int(value)
            elif value_type == VariableType.FLOAT:
                float(value)
            elif value_type == VariableType.BOOLEAN:
                if isinstance(value, str):
                    return value.lower() in ['true', 'false', '1', '0', 'yes', 'no']
                return isinstance(value, bool)
            elif value_type == VariableType.DATETIME:
                from datetime import datetime
                if isinstance(value, str):
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
            return True
        except (ValueError, TypeError):
            return False 