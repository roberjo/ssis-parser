#!/usr/bin/env python3
"""
Configuration Parser - Parse SSIS .dtsConfig files and handle environment variables
"""

import xml.etree.ElementTree as ET
import os
import base64
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from ..core.logger import LoggerMixin


@dataclass
class ConfigEntry:
    """Represents a configuration entry from .dtsConfig file"""
    path: str
    value: str
    is_encrypted: bool = False
    encrypted_value: Optional[str] = None
    target_type: str = "String"
    description: str = ""


@dataclass
class ConfigFile:
    """Represents a parsed .dtsConfig file"""
    file_path: str
    entries: List[ConfigEntry] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigParser(LoggerMixin):
    """Parser for SSIS .dtsConfig files and environment variables"""
    
    def __init__(self):
        self.logger.info("Configuration Parser initialized")
        
        # Configuration types mapping
        self.config_types = {
            'String': str,
            'Int32': int,
            'Boolean': bool,
            'DateTime': str,
            'Double': float
        }
        
        # Common environment variable patterns
        self.env_patterns = [
            r'\$\([A-Za-z_][A-Za-z0-9_]*\)',  # $(VARIABLE_NAME)
            r'%[A-Za-z_][A-Za-z0-9_]*%',       # %VARIABLE_NAME%
            r'@\[User::[A-Za-z_][A-Za-z0-9_]*\]'  # @[User::VariableName]
        ]
    
    def parse_config_file(self, file_path: str) -> Optional[ConfigFile]:
        """
        Parse a .dtsConfig file
        
        Args:
            file_path: Path to the .dtsConfig file
            
        Returns:
            ConfigFile object with parsed configuration entries
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                self.logger.error(f"Configuration file does not exist: {file_path}")
                return None
            
            if not file_path.suffix.lower() == '.dtsconfig':
                self.logger.error(f"File is not a .dtsConfig file: {file_path}")
                return None
            
            # Parse XML
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            config_file = ConfigFile(file_path=str(file_path))
            
            # Parse configuration entries
            config_file.entries = self._parse_config_entries(root)
            
            # Extract environment variables
            config_file.environment_variables = self._extract_environment_variables(config_file.entries)
            
            # Parse metadata
            config_file.metadata = self._parse_metadata(root)
            
            self.logger.info(f"Successfully parsed configuration file: {file_path}")
            self.logger.info(f"Found {len(config_file.entries)} configuration entries")
            self.logger.info(f"Found {len(config_file.environment_variables)} environment variables")
            
            return config_file
            
        except ET.ParseError as e:
            error_msg = f"XML parsing error in config file: {str(e)}"
            self.logger.error(error_msg)
            return None
        except Exception as e:
            error_msg = f"Unexpected error parsing config file: {str(e)}"
            self.logger.error(error_msg)
            return None
    
    def _parse_config_entries(self, root: ET.Element) -> List[ConfigEntry]:
        """Parse configuration entries from the root element"""
        entries = []
        
        # Look for Configuration elements
        config_elems = root.findall('.//Configuration')
        
        for config_elem in config_elems:
            entry = self._parse_config_entry(config_elem)
            if entry:
                entries.append(entry)
        
        return entries
    
    def _parse_config_entry(self, config_elem: ET.Element) -> Optional[ConfigEntry]:
        """Parse a single configuration entry"""
        try:
            # Get required attributes
            path = config_elem.get('Path', '')
            target_type = config_elem.get('ValueType', 'String')
            description = config_elem.get('Description', '')
            
            # Get value from ConfiguredValue element
            configured_value_elem = config_elem.find('ConfiguredValue')
            value = configured_value_elem.text if configured_value_elem is not None else ''
            
            # Check if value is encrypted
            is_encrypted = config_elem.get('Encrypted', 'false').lower() == 'true'
            encrypted_value = None
            
            if is_encrypted:
                encrypted_value = value
                # Try to decrypt if possible
                try:
                    value = self._decrypt_value(value)
                except Exception as e:
                    self.logger.warning(f"Could not decrypt value for {path}: {str(e)}")
                    value = "[ENCRYPTED]"
            
            entry = ConfigEntry(
                path=path,
                value=value,
                is_encrypted=is_encrypted,
                encrypted_value=encrypted_value,
                target_type=target_type,
                description=description
            )
            
            return entry
            
        except Exception as e:
            self.logger.error(f"Error parsing configuration entry: {str(e)}")
            return None
    
    def _extract_environment_variables(self, entries: List[ConfigEntry]) -> Dict[str, str]:
        """Extract environment variables from configuration entries"""
        env_vars = {}
        
        for entry in entries:
            # Look for environment variable patterns in the value
            env_vars_in_value = self._find_environment_variables(entry.value)
            for env_var in env_vars_in_value:
                env_vars[env_var] = os.environ.get(env_var, '')
        
        return env_vars
    
    def _find_environment_variables(self, value: str) -> List[str]:
        """Find environment variables in a string value"""
        import re
        env_vars = []
        
        # Pattern 1: $(VARIABLE_NAME)
        matches = re.findall(r'\$\(([A-Za-z_][A-Za-z0-9_]*)\)', value)
        env_vars.extend(matches)
        
        # Pattern 2: %VARIABLE_NAME%
        matches = re.findall(r'%([A-Za-z_][A-Za-z0-9_]*)%', value)
        env_vars.extend(matches)
        
        # Pattern 3: @[User::VariableName]
        matches = re.findall(r'@\[User::([A-Za-z_][A-Za-z0-9_]*)\]', value)
        env_vars.extend(matches)
        
        return list(set(env_vars))  # Remove duplicates
    
    def _parse_metadata(self, root: ET.Element) -> Dict[str, Any]:
        """Parse metadata from the configuration file"""
        metadata = {}
        
        # Extract file-level metadata
        metadata['root_element'] = root.tag
        metadata['namespaces'] = root.nsmap if hasattr(root, 'nsmap') else {}
        
        # Look for any metadata elements
        for elem in root.iter():
            if elem.tag.endswith('Metadata') or elem.tag.endswith('Info'):
                metadata[elem.tag] = elem.text or ''
        
        return metadata
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """
        Attempt to decrypt an encrypted configuration value
        
        Note: This is a basic implementation. SSIS uses a specific encryption
        method that may require additional implementation details.
        """
        try:
            # Try base64 decoding first
            decoded = base64.b64decode(encrypted_value)
            
            # For now, return a placeholder indicating decryption is needed
            # In a full implementation, this would use SSIS-specific decryption
            return f"[DECRYPTED: {len(decoded)} bytes]"
            
        except Exception as e:
            self.logger.warning(f"Decryption failed: {str(e)}")
            return "[DECRYPTION_FAILED]"
    
    def resolve_configuration_dependencies(self, config_file: ConfigFile, 
                                         base_path: Optional[str] = None) -> List[str]:
        """
        Resolve configuration dependencies
        
        Args:
            config_file: The parsed configuration file
            base_path: Base path for resolving relative paths
            
        Returns:
            List of dependency file paths
        """
        dependencies = []
        
        if not base_path:
            base_path = str(Path(config_file.file_path).parent)
        
        # Look for references to other configuration files
        for entry in config_file.entries:
            if entry.path.endswith('.dtsconfig'):
                # This might be a reference to another config file
                dep_path = Path(base_path) / entry.path
                if dep_path.exists():
                    dependencies.append(str(dep_path))
        
        # Look for references in environment variables
        for env_var, value in config_file.environment_variables.items():
            if value.endswith('.dtsconfig'):
                dep_path = Path(base_path) / value
                if dep_path.exists():
                    dependencies.append(str(dep_path))
        
        return dependencies
    
    def validate_configuration(self, config_file: ConfigFile) -> Dict[str, Any]:
        """
        Validate configuration entries
        
        Args:
            config_file: The parsed configuration file
            
        Returns:
            Validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'encrypted_entries': [],
            'missing_env_vars': []
        }
        
        for entry in config_file.entries:
            # Check for encrypted entries
            if entry.is_encrypted:
                validation_results['encrypted_entries'].append(entry.path)
                validation_results['warnings'].append(f"Encrypted entry found: {entry.path}")
            
            # Check for missing environment variables
            env_vars = self._find_environment_variables(entry.value)
            for env_var in env_vars:
                if not os.environ.get(env_var):
                    validation_results['missing_env_vars'].append(env_var)
                    validation_results['warnings'].append(f"Missing environment variable: {env_var}")
            
            # Validate target type
            if entry.target_type not in self.config_types:
                validation_results['warnings'].append(f"Unknown target type: {entry.target_type}")
        
        if validation_results['errors']:
            validation_results['is_valid'] = False
        
        return validation_results
    
    def merge_configurations(self, config_files: List[ConfigFile]) -> ConfigFile:
        """
        Merge multiple configuration files into a single configuration
        
        Args:
            config_files: List of configuration files to merge
            
        Returns:
            Merged configuration file
        """
        if not config_files:
            return ConfigFile(file_path="merged")
        
        merged = ConfigFile(file_path="merged")
        
        # Merge entries (later files override earlier ones)
        for config_file in config_files:
            for entry in config_file.entries:
                # Check if entry already exists
                existing_entry = next((e for e in merged.entries if e.path == entry.path), None)
                if existing_entry:
                    # Replace existing entry
                    merged.entries.remove(existing_entry)
                merged.entries.append(entry)
        
        # Merge environment variables
        for config_file in config_files:
            merged.environment_variables.update(config_file.environment_variables)
        
        # Merge metadata
        for config_file in config_files:
            merged.metadata.update(config_file.metadata)
        
        return merged 