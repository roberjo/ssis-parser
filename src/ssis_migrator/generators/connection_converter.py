#!/usr/bin/env python3
"""
Connection Manager Converter - Convert SSIS connection managers to Python connection configurations
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from ..core.logger import LoggerMixin
from ..core.error_handler import (
    ErrorHandler, ConversionError, create_error_context,
    ErrorSeverity, ErrorCategory
)


class ConnectionType(Enum):
    """SSIS Connection Types"""
    OLEDB = "oledb"
    ADO_NET = "ado_net"
    FLAT_FILE = "flat_file"
    EXCEL = "excel"
    XML = "xml"
    HTTP = "http"
    FTP = "ftp"
    SMTP = "smtp"
    FILE = "file"
    UNKNOWN = "unknown"


class DatabaseProvider(Enum):
    """Database Provider Types"""
    SQL_SERVER = "sql_server"
    ORACLE = "oracle"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    DB2 = "db2"
    SYBASE = "sybase"
    UNKNOWN = "unknown"


@dataclass
class ConnectionConfig:
    """Connection configuration for Python"""
    name: str
    connection_type: ConnectionType
    provider: DatabaseProvider
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    connection_string: Optional[str] = None
    file_path: Optional[str] = None
    url: Optional[str] = None
    timeout: Optional[int] = None
    ssl_mode: Optional[str] = None
    charset: Optional[str] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PythonConnection:
    """Python connection representation"""
    name: str
    connection_type: str
    config: ConnectionConfig
    python_code: str
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    error_handling: str = ""


@dataclass
class ConnectionConversionResult:
    """Result of connection conversion"""
    connections: List[PythonConnection]
    imports: List[str]
    dependencies: List[str]
    error_handling: str
    config_code: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConnectionConverter(LoggerMixin):
    """Convert SSIS connection managers to Python connection configurations"""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or ErrorHandler()
        self.logger.info("Connection Converter initialized")
        
        # Provider mappings
        self.provider_mappings = {
            'SQLNCLI': DatabaseProvider.SQL_SERVER,
            'SQLNCLI11': DatabaseProvider.SQL_SERVER,
            'MSOLEDBSQL': DatabaseProvider.SQL_SERVER,
            'OLEDB': DatabaseProvider.SQL_SERVER,
            'Oracle': DatabaseProvider.ORACLE,
            'OraOLEDB.Oracle': DatabaseProvider.ORACLE,
            'MySQL': DatabaseProvider.MYSQL,
            'MySQL ODBC': DatabaseProvider.MYSQL,
            'PostgreSQL': DatabaseProvider.POSTGRESQL,
            'SQLite': DatabaseProvider.SQLITE,
            'DB2': DatabaseProvider.DB2,
            'Sybase': DatabaseProvider.SYBASE
        }
        
        # Connection type mappings
        self.connection_type_mappings = {
            'OLEDB': ConnectionType.OLEDB,
            'ADO.NET': ConnectionType.ADO_NET,
            'FlatFile': ConnectionType.FLAT_FILE,
            'Excel': ConnectionType.EXCEL,
            'XML': ConnectionType.XML,
            'HTTP': ConnectionType.HTTP,
            'FTP': ConnectionType.FTP,
            'SMTP': ConnectionType.SMTP,
            'FILE': ConnectionType.FILE
        }
    
    def convert_connections(self, connection_managers: List[Dict[str, Any]]) -> ConnectionConversionResult:
        """
        Convert SSIS connection managers to Python connection configurations
        
        Args:
            connection_managers: List of SSIS connection managers
            
        Returns:
            ConnectionConversionResult with Python connection configurations
        """
        try:
            self.logger.info(f"Converting {len(connection_managers)} connection managers")
            
            python_connections = []
            all_imports = set()
            all_dependencies = set()
            
            for conn_manager in connection_managers:
                try:
                    python_conn = self._convert_single_connection(conn_manager)
                    python_connections.append(python_conn)
                    
                    # Collect imports and dependencies
                    all_imports.update(python_conn.imports)
                    all_dependencies.update(python_conn.dependencies)
                    
                except Exception as e:
                    error = ConversionError(
                        f"Failed to convert connection {conn_manager.get('name', 'Unknown')}: {str(e)}",
                        severity=ErrorSeverity.MEDIUM,
                        source_component="ConnectionConverter"
                    )
                    self.error_handler.handle_error(
                        error,
                        context=create_error_context(
                            component="ConnectionConverter",
                            operation="convert_single_connection",
                            connection_name=conn_manager.get('name', 'Unknown')
                        )
                    )
                    continue
            
            # Generate error handling code
            error_handling = self._generate_error_handling()
            
            # Generate configuration code
            config_code = self._generate_config_code(python_connections)
            
            result = ConnectionConversionResult(
                connections=python_connections,
                imports=sorted(list(all_imports)),
                dependencies=sorted(list(all_dependencies)),
                error_handling=error_handling,
                config_code=config_code,
                metadata={
                    'connection_count': len(python_connections),
                    'database_connections': len([c for c in python_connections if c.connection_type in ['database', 'oledb', 'ado_net']]),
                    'file_connections': len([c for c in python_connections if c.connection_type in ['flat_file', 'excel', 'xml', 'file']]),
                    'web_connections': len([c for c in python_connections if c.connection_type in ['http', 'ftp', 'smtp']])
                }
            )
            
            self.logger.info("Connection conversion completed successfully")
            return result
            
        except Exception as e:
            error = ConversionError(
                f"Failed to convert connections: {str(e)}",
                severity=ErrorSeverity.HIGH,
                source_component="ConnectionConverter"
            )
            self.error_handler.handle_error(
                error,
                context=create_error_context(
                    component="ConnectionConverter",
                    operation="convert_connections"
                )
            )
            raise
    
    def _convert_single_connection(self, conn_manager: Dict[str, Any]) -> PythonConnection:
        """Convert a single connection manager to Python connection"""
        conn_name = conn_manager.get('name', 'Unknown')
        conn_type = conn_manager.get('connection_type', 'Unknown')
        
        # Determine connection type
        connection_type = self._get_connection_type(conn_type)
        
        if connection_type == ConnectionType.OLEDB:
            return self._convert_oledb_connection(conn_manager)
        elif connection_type == ConnectionType.ADO_NET:
            return self._convert_ado_net_connection(conn_manager)
        elif connection_type == ConnectionType.FLAT_FILE:
            return self._convert_flat_file_connection(conn_manager)
        elif connection_type == ConnectionType.EXCEL:
            return self._convert_excel_connection(conn_manager)
        elif connection_type == ConnectionType.XML:
            return self._convert_xml_connection(conn_manager)
        elif connection_type == ConnectionType.HTTP:
            return self._convert_http_connection(conn_manager)
        elif connection_type == ConnectionType.FTP:
            return self._convert_ftp_connection(conn_manager)
        elif connection_type == ConnectionType.SMTP:
            return self._convert_smtp_connection(conn_manager)
        elif connection_type == ConnectionType.FILE:
            return self._convert_file_connection(conn_manager)
        else:
            return self._convert_unknown_connection(conn_manager)
    
    def _get_connection_type(self, conn_type: str) -> ConnectionType:
        """Get connection type from SSIS connection type"""
        conn_type_lower = conn_type.lower()
        
        for key, value in self.connection_type_mappings.items():
            if key.lower() in conn_type_lower:
                return value
        
        return ConnectionType.UNKNOWN
    
    def _get_database_provider(self, provider: str) -> DatabaseProvider:
        """Get database provider from connection string or provider name"""
        provider_upper = provider.upper()
        
        for key, value in self.provider_mappings.items():
            if key.upper() in provider_upper:
                return value
        
        return DatabaseProvider.UNKNOWN
    
    def _parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """Parse connection string into components"""
        params = {}
        
        try:
            # Handle different connection string formats
            if ';' in connection_string:
                # OLE DB style connection string
                pairs = connection_string.split(';')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        params[key.strip().lower()] = value.strip()
            elif '://' in connection_string:
                # URL style connection string
                parsed = urlparse(connection_string)
                params['scheme'] = parsed.scheme
                params['host'] = parsed.hostname
                params['port'] = parsed.port
                params['path'] = parsed.path
                params['username'] = parsed.username
                params['password'] = parsed.password
                params['query'] = parse_qs(parsed.query)
            
        except Exception as e:
            self.logger.warning(f"Failed to parse connection string: {str(e)}")
        
        return params
    
    def _convert_oledb_connection(self, conn_manager: Dict[str, Any]) -> PythonConnection:
        """Convert OLE DB connection to Python"""
        conn_name = conn_manager.get('name', 'Unknown')
        connection_string = conn_manager.get('connection_string', '')
        
        # Parse connection string
        params = self._parse_connection_string(connection_string)
        
        # Determine provider
        provider = self._get_database_provider(params.get('provider', ''))
        
        # Create connection config
        config = ConnectionConfig(
            name=conn_name,
            connection_type=ConnectionType.OLEDB,
            provider=provider,
            connection_string=connection_string,
            host=params.get('server') or params.get('host'),
            database=params.get('database') or params.get('initial catalog'),
            username=params.get('user id') or params.get('username'),
            password=params.get('password'),
            timeout=params.get('timeout'),
            additional_params=params
        )
        
        # Generate Python code based on provider
        if provider == DatabaseProvider.SQL_SERVER:
            python_code = self._generate_sql_server_connection(config)
            imports = ["import pyodbc", "import sqlalchemy"]
            dependencies = ["pyodbc", "sqlalchemy"]
        elif provider == DatabaseProvider.ORACLE:
            python_code = self._generate_oracle_connection(config)
            imports = ["import cx_Oracle", "import sqlalchemy"]
            dependencies = ["cx_Oracle", "sqlalchemy"]
        elif provider == DatabaseProvider.MYSQL:
            python_code = self._generate_mysql_connection(config)
            imports = ["import pymysql", "import sqlalchemy"]
            dependencies = ["pymysql", "sqlalchemy"]
        elif provider == DatabaseProvider.POSTGRESQL:
            python_code = self._generate_postgresql_connection(config)
            imports = ["import psycopg2", "import sqlalchemy"]
            dependencies = ["psycopg2-binary", "sqlalchemy"]
        else:
            python_code = self._generate_generic_connection(config)
            imports = ["import sqlalchemy"]
            dependencies = ["sqlalchemy"]
        
        return PythonConnection(
            name=conn_name,
            connection_type="database",
            config=config,
            python_code=python_code,
            imports=imports,
            dependencies=dependencies
        )
    
    def _convert_flat_file_connection(self, conn_manager: Dict[str, Any]) -> PythonConnection:
        """Convert Flat File connection to Python"""
        conn_name = conn_manager.get('name', 'Unknown')
        file_path = conn_manager.get('file_path', '')
        
        config = ConnectionConfig(
            name=conn_name,
            connection_type=ConnectionType.FLAT_FILE,
            provider=DatabaseProvider.UNKNOWN,
            file_path=file_path
        )
        
        python_code = self._generate_flat_file_connection(config)
        
        return PythonConnection(
            name=conn_name,
            connection_type="file",
            config=config,
            python_code=python_code,
            imports=["import pandas as pd"],
            dependencies=["pandas"]
        )
    
    def _convert_excel_connection(self, conn_manager: Dict[str, Any]) -> PythonConnection:
        """Convert Excel connection to Python"""
        conn_name = conn_manager.get('name', 'Unknown')
        file_path = conn_manager.get('file_path', '')
        
        config = ConnectionConfig(
            name=conn_name,
            connection_type=ConnectionType.EXCEL,
            provider=DatabaseProvider.UNKNOWN,
            file_path=file_path
        )
        
        python_code = self._generate_excel_connection(config)
        
        return PythonConnection(
            name=conn_name,
            connection_type="file",
            config=config,
            python_code=python_code,
            imports=["import pandas as pd", "import openpyxl"],
            dependencies=["pandas", "openpyxl"]
        )
    
    def _convert_http_connection(self, conn_manager: Dict[str, Any]) -> PythonConnection:
        """Convert HTTP connection to Python"""
        conn_name = conn_manager.get('name', 'Unknown')
        url = conn_manager.get('url', '')
        
        config = ConnectionConfig(
            name=conn_name,
            connection_type=ConnectionType.HTTP,
            provider=DatabaseProvider.UNKNOWN,
            url=url
        )
        
        python_code = self._generate_http_connection(config)
        
        return PythonConnection(
            name=conn_name,
            connection_type="web",
            config=config,
            python_code=python_code,
            imports=["import requests"],
            dependencies=["requests"]
        )
    
    def _convert_unknown_connection(self, conn_manager: Dict[str, Any]) -> PythonConnection:
        """Convert unknown connection type to Python"""
        conn_name = conn_manager.get('name', 'Unknown')
        
        config = ConnectionConfig(
            name=conn_name,
            connection_type=ConnectionType.UNKNOWN,
            provider=DatabaseProvider.UNKNOWN
        )
        
        python_code = f"""
def get_{conn_name.lower().replace(' ', '_')}_connection():
    \"\"\"Get connection for {conn_name}\"\"\"
    # TODO: Implement connection logic for {conn_name}
    # Connection type: {conn_manager.get('connection_type', 'Unknown')}
    raise NotImplementedError("Connection type not yet supported")
"""
        
        return PythonConnection(
            name=conn_name,
            connection_type="unknown",
            config=config,
            python_code=python_code,
            imports=[],
            dependencies=[]
        )
    
    def _generate_sql_server_connection(self, config: ConnectionConfig) -> str:
        """Generate SQL Server connection code"""
        return f"""
def get_{config.name.lower().replace(' ', '_')}_connection():
    \"\"\"Get SQL Server connection for {config.name}\"\"\"
    import pyodbc
    from sqlalchemy import create_engine
    
    try:
        # Connection string: {config.connection_string}
        connection_string = "{config.connection_string}"
        
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return engine
        
    except Exception as e:
        raise Exception(f"Failed to connect to SQL Server: {{str(e)}}")
"""
    
    def _generate_oracle_connection(self, config: ConnectionConfig) -> str:
        """Generate Oracle connection code"""
        return f"""
def get_{config.name.lower().replace(' ', '_')}_connection():
    \"\"\"Get Oracle connection for {config.name}\"\"\"
    import cx_Oracle
    from sqlalchemy import create_engine
    
    try:
        # Connection string: {config.connection_string}
        connection_string = "{config.connection_string}"
        
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1 FROM DUAL")
        
        return engine
        
    except Exception as e:
        raise Exception(f"Failed to connect to Oracle: {{str(e)}}")
"""
    
    def _generate_mysql_connection(self, config: ConnectionConfig) -> str:
        """Generate MySQL connection code"""
        return f"""
def get_{config.name.lower().replace(' ', '_')}_connection():
    \"\"\"Get MySQL connection for {config.name}\"\"\"
    import pymysql
    from sqlalchemy import create_engine
    
    try:
        # Connection string: {config.connection_string}
        connection_string = "{config.connection_string}"
        
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return engine
        
    except Exception as e:
        raise Exception(f"Failed to connect to MySQL: {{str(e)}}")
"""
    
    def _generate_postgresql_connection(self, config: ConnectionConfig) -> str:
        """Generate PostgreSQL connection code"""
        return f"""
def get_{config.name.lower().replace(' ', '_')}_connection():
    \"\"\"Get PostgreSQL connection for {config.name}\"\"\"
    import psycopg2
    from sqlalchemy import create_engine
    
    try:
        # Connection string: {config.connection_string}
        connection_string = "{config.connection_string}"
        
        # Create SQLAlchemy engine
        engine = create_engine(connection_string)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return engine
        
    except Exception as e:
        raise Exception(f"Failed to connect to PostgreSQL: {{str(e)}}")
"""
    
    def _generate_flat_file_connection(self, config: ConnectionConfig) -> str:
        """Generate flat file connection code"""
        return f"""
def get_{config.name.lower().replace(' ', '_')}_connection():
    \"\"\"Get flat file connection for {config.name}\"\"\"
    import pandas as pd
    from pathlib import Path
    
    try:
        file_path = Path("{config.file_path}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {{file_path}}")
        
        # Read file based on extension
        if file_path.suffix.lower() == '.csv':
            return pd.read_csv(file_path)
        elif file_path.suffix.lower() in ['.txt', '.dat']:
            return pd.read_csv(file_path, sep='\\t')
        else:
            return pd.read_csv(file_path)
        
    except Exception as e:
        raise Exception(f"Failed to read flat file: {{str(e)}}")
"""
    
    def _generate_excel_connection(self, config: ConnectionConfig) -> str:
        """Generate Excel connection code"""
        return f"""
def get_{config.name.lower().replace(' ', '_')}_connection():
    \"\"\"Get Excel connection for {config.name}\"\"\"
    import pandas as pd
    from pathlib import Path
    
    try:
        file_path = Path("{config.file_path}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {{file_path}}")
        
        # Read Excel file
        return pd.read_excel(file_path)
        
    except Exception as e:
        raise Exception(f"Failed to read Excel file: {{str(e)}}")
"""
    
    def _generate_http_connection(self, config: ConnectionConfig) -> str:
        """Generate HTTP connection code"""
        return f"""
def get_{config.name.lower().replace(' ', '_')}_connection():
    \"\"\"Get HTTP connection for {config.name}\"\"\"
    import requests
    
    try:
        url = "{config.url}"
        
        # Make HTTP request
        response = requests.get(url)
        response.raise_for_status()
        
        return response
        
    except Exception as e:
        raise Exception(f"Failed to connect to HTTP endpoint: {{str(e)}}")
"""
    
    def _generate_generic_connection(self, config: ConnectionConfig) -> str:
        """Generate generic connection code"""
        return f"""
def get_{config.name.lower().replace(' ', '_')}_connection():
    \"\"\"Get generic connection for {config.name}\"\"\"
    from sqlalchemy import create_engine
    
    try:
        connection_string = "{config.connection_string}"
        engine = create_engine(connection_string)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        
        return engine
        
    except Exception as e:
        raise Exception(f"Failed to establish connection: {{str(e)}}")
"""
    
    def _generate_error_handling(self) -> str:
        """Generate error handling code for connections"""
        return """
def handle_connection_error(error, connection_name=""):
    \"\"\"Handle connection errors\"\"\"
    import logging
    
    logger = logging.getLogger(__name__)
    logger.error(f"Connection error in {connection_name}: {str(error)}")
    raise error

def validate_connection(connection, connection_name=""):
    \"\"\"Validate connection\"\"\"
    try:
        if hasattr(connection, 'connect'):
            with connection.connect() as conn:
                conn.execute("SELECT 1")
        return True
    except Exception as e:
        handle_connection_error(e, connection_name)
        return False
"""
    
    def _generate_config_code(self, connections: List[PythonConnection]) -> str:
        """Generate configuration code for all connections"""
        config_lines = ["# Connection configurations", ""]
        
        for conn in connections:
            config_lines.extend([
                f"# {conn.name}",
                f"# Type: {conn.connection_type}",
                f"# Dependencies: {', '.join(conn.dependencies)}",
                ""
            ])
        
        return "\n".join(config_lines) 