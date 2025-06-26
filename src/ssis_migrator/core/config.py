#!/usr/bin/env python3
"""
Configuration management for SSIS Migration Tool
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseConfig(BaseModel):
    """Database connection configuration"""
    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=1433, description="Database port")
    database: str = Field(default="", description="Database name")
    username: str = Field(default="", description="Database username")
    password: str = Field(default="", description="Database password")
    driver: str = Field(default="ODBC Driver 17 for SQL Server", description="ODBC driver")
    timeout: int = Field(default=30, description="Connection timeout in seconds")
    
    @property
    def connection_string(self) -> str:
        """Generate connection string for SQL Server"""
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.host},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            f"TIMEOUT={self.timeout};"
        )


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )
    file: Optional[str] = Field(default=None, description="Log file path")
    max_size: int = Field(default=10 * 1024 * 1024, description="Max log file size in bytes")
    backup_count: int = Field(default=5, description="Number of backup log files")


class ConversionConfig(BaseModel):
    """Conversion configuration"""
    output_format: str = Field(default="python", description="Output format")
    include_tests: bool = Field(default=True, description="Include test generation")
    include_docs: bool = Field(default=True, description="Include documentation")
    backup_original: bool = Field(default=True, description="Backup original files")
    validate_output: bool = Field(default=True, description="Validate converted code")
    parallel_processing: bool = Field(default=False, description="Enable parallel processing")
    max_workers: int = Field(default=4, description="Maximum number of worker processes")


class Config(BaseModel):
    """Main configuration class"""
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    conversion: ConversionConfig = Field(default_factory=ConversionConfig)
    
    # Environment-specific settings
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")
    
    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from file"""
        import yaml
        
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)
        
        return cls(**config_data)
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        config_data = {
            "database": {
                "host": os.getenv("DB_HOST", "localhost"),
                "port": int(os.getenv("DB_PORT", "1433")),
                "database": os.getenv("DB_NAME", ""),
                "username": os.getenv("DB_USER", ""),
                "password": os.getenv("DB_PASSWORD", ""),
                "driver": os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
                "timeout": int(os.getenv("DB_TIMEOUT", "30")),
            },
            "logging": {
                "level": os.getenv("LOG_LEVEL", "INFO"),
                "file": os.getenv("LOG_FILE"),
                "max_size": int(os.getenv("LOG_MAX_SIZE", str(10 * 1024 * 1024))),
                "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5")),
            },
            "conversion": {
                "output_format": os.getenv("CONVERSION_FORMAT", "python"),
                "include_tests": os.getenv("INCLUDE_TESTS", "true").lower() == "true",
                "include_docs": os.getenv("INCLUDE_DOCS", "true").lower() == "true",
                "backup_original": os.getenv("BACKUP_ORIGINAL", "true").lower() == "true",
                "validate_output": os.getenv("VALIDATE_OUTPUT", "true").lower() == "true",
                "parallel_processing": os.getenv("PARALLEL_PROCESSING", "false").lower() == "true",
                "max_workers": int(os.getenv("MAX_WORKERS", "4")),
            },
            "environment": os.getenv("ENVIRONMENT", "development"),
            "debug": os.getenv("DEBUG", "false").lower() == "true",
        }
        
        return cls(**config_data)
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to file"""
        import yaml
        
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, indent=2)
    
    def get_database_url(self) -> str:
        """Get SQLAlchemy database URL"""
        return (
            f"mssql+pyodbc://{self.database.username}:{self.database.password}"
            f"@{self.database.host}:{self.database.port}/{self.database.database}"
            f"?driver={self.database.driver.replace(' ', '+')}"
        ) 