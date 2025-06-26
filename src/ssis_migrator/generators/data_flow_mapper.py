#!/usr/bin/env python3
"""
Data Flow Mapper - Convert SSIS data flow components to Python/Pandas operations
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from ..core.logger import LoggerMixin
from ..core.error_handler import (
    ErrorHandler, ConversionError, create_error_context,
    ErrorSeverity, ErrorCategory
)


class ComponentType(Enum):
    """SSIS Data Flow Component Types"""
    SOURCE = "source"
    DESTINATION = "destination"
    TRANSFORMATION = "transformation"
    LOOKUP = "lookup"
    MERGE = "merge"
    UNION = "union"
    SORT = "sort"
    AGGREGATE = "aggregate"
    DERIVED_COLUMN = "derived_column"
    CONDITIONAL_SPLIT = "conditional_split"
    MULTICAST = "multicast"
    AUDIT = "audit"
    SCRIPT_COMPONENT = "script_component"
    DATA_CONVERSION = "data_conversion"
    CHARACTER_MAP = "character_map"
    COPY_COLUMN = "copy_column"
    OLE_DB_COMMAND = "ole_db_command"
    CACHE_TRANSFORM = "cache_transform"
    FUZZY_LOOKUP = "fuzzy_lookup"
    FUZZY_GROUPING = "fuzzy_grouping"
    TERM_EXTRACTION = "term_extraction"
    TERM_LOOKUP = "term_lookup"
    DATA_MINING_QUERY = "data_mining_query"
    ROW_COUNT = "row_count"
    ROW_SAMPLING = "row_sampling"
    PERCENTAGE_SAMPLING = "percentage_sampling"
    UNKNOWN = "unknown"


class ConnectionType(Enum):
    """Database Connection Types"""
    SQL_SERVER = "sql_server"
    ORACLE = "oracle"
    MYSQL = "mysql"
    POSTGRESQL = "postgresql"
    SQLITE = "sqlite"
    EXCEL = "excel"
    CSV = "csv"
    FLAT_FILE = "flat_file"
    XML = "xml"
    JSON = "json"
    UNKNOWN = "unknown"


@dataclass
class ColumnMapping:
    """Column mapping information"""
    source_column: str
    target_column: str
    data_type: str
    transformation: Optional[str] = None
    is_key: bool = False
    is_nullable: bool = True
    default_value: Optional[str] = None


@dataclass
class TransformationRule:
    """Transformation rule for data flow components"""
    component_type: ComponentType
    python_code: str
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    error_handling: str = ""
    validation: str = ""


@dataclass
class DataFlowMapping:
    """Complete data flow mapping result"""
    source_code: str
    transformation_code: str
    destination_code: str
    imports: List[str]
    dependencies: List[str]
    error_handling: str
    validation_code: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataFlowMapper(LoggerMixin):
    """Maps SSIS data flow components to Python/Pandas operations"""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        self.error_handler = error_handler or ErrorHandler()
        self.logger.info("Data Flow Mapper initialized")
        
        # Initialize transformation rules
        self.transformation_rules = self._initialize_transformation_rules()
        
        # Connection type mappings
        self.connection_mappings = {
            'OLEDB': ConnectionType.SQL_SERVER,
            'SQLNCLI': ConnectionType.SQL_SERVER,
            'SQLNCLI11': ConnectionType.SQL_SERVER,
            'MSOLEDBSQL': ConnectionType.SQL_SERVER,
            'Oracle': ConnectionType.ORACLE,
            'MySQL': ConnectionType.MYSQL,
            'PostgreSQL': ConnectionType.POSTGRESQL,
            'SQLite': ConnectionType.SQLITE,
            'Excel': ConnectionType.EXCEL,
            'FlatFile': ConnectionType.FLAT_FILE,
            'XML': ConnectionType.XML,
            'JSON': ConnectionType.JSON
        }
    
    def map_data_flow(self, components: List[Dict[str, Any]]) -> DataFlowMapping:
        """
        Map SSIS data flow components to Python code
        
        Args:
            components: List of SSIS data flow components
            
        Returns:
            DataFlowMapping with generated Python code
        """
        try:
            self.logger.info(f"Mapping {len(components)} data flow components")
            
            # Separate components by type
            sources = [c for c in components if self._is_source_component(c)]
            destinations = [c for c in components if self._is_destination_component(c)]
            transformations = [c for c in components if self._is_transformation_component(c)]
            
            # Generate source code
            source_code = self._generate_source_code(sources)
            
            # Generate transformation code
            transformation_code = self._generate_transformation_code(transformations)
            
            # Generate destination code
            destination_code = self._generate_destination_code(destinations)
            
            # Collect all imports and dependencies
            all_imports = self._collect_imports(sources, transformations, destinations)
            all_dependencies = self._collect_dependencies(sources, transformations, destinations)
            
            # Generate error handling
            error_handling = self._generate_error_handling()
            
            # Generate validation code
            validation_code = self._generate_validation_code(components)
            
            mapping = DataFlowMapping(
                source_code=source_code,
                transformation_code=transformation_code,
                destination_code=destination_code,
                imports=all_imports,
                dependencies=all_dependencies,
                error_handling=error_handling,
                validation_code=validation_code,
                metadata={
                    'component_count': len(components),
                    'source_count': len(sources),
                    'transformation_count': len(transformations),
                    'destination_count': len(destinations)
                }
            )
            
            self.logger.info("Data flow mapping completed successfully")
            return mapping
            
        except Exception as e:
            error = ConversionError(
                f"Failed to map data flow: {str(e)}",
                severity=ErrorSeverity.HIGH,
                source_component="DataFlowMapper"
            )
            self.error_handler.handle_error(
                error,
                context=create_error_context(
                    component="DataFlowMapper",
                    operation="map_data_flow"
                )
            )
            raise
    
    def _initialize_transformation_rules(self) -> Dict[ComponentType, TransformationRule]:
        """Initialize transformation rules for different component types"""
        rules = {}
        
        # Source components
        rules[ComponentType.SOURCE] = TransformationRule(
            component_type=ComponentType.SOURCE,
            python_code="""
def read_source_data(connection_string, query=None, table_name=None):
    \"\"\"Read data from source\"\"\"
    import pandas as pd
    from sqlalchemy import create_engine
    
    try:
        engine = create_engine(connection_string)
        if query:
            df = pd.read_sql(query, engine)
        elif table_name:
            df = pd.read_sql_table(table_name, engine)
        else:
            raise ValueError("Either query or table_name must be provided")
        
        return df
    except Exception as e:
        raise Exception(f"Error reading source data: {str(e)}")
""",
            imports=["pandas as pd", "sqlalchemy"],
            dependencies=["pandas", "sqlalchemy"]
        )
        
        # Destination components
        rules[ComponentType.DESTINATION] = TransformationRule(
            component_type=ComponentType.DESTINATION,
            python_code="""
def write_destination_data(df, connection_string, table_name, if_exists='replace'):
    \"\"\"Write data to destination\"\"\"
    import pandas as pd
    from sqlalchemy import create_engine
    
    try:
        engine = create_engine(connection_string)
        df.to_sql(table_name, engine, if_exists=if_exists, index=False)
        return True
    except Exception as e:
        raise Exception(f"Error writing destination data: {str(e)}")
""",
            imports=["pandas as pd", "sqlalchemy"],
            dependencies=["pandas", "sqlalchemy"]
        )
        
        # Derived Column transformation
        rules[ComponentType.DERIVED_COLUMN] = TransformationRule(
            component_type=ComponentType.DERIVED_COLUMN,
            python_code="""
def apply_derived_columns(df, column_expressions):
    \"\"\"Apply derived column expressions\"\"\"
    import pandas as pd
    
    try:
        for col_name, expression in column_expressions.items():
            df[col_name] = df.eval(expression)
        return df
    except Exception as e:
        raise Exception(f"Error applying derived columns: {str(e)}")
""",
            imports=["pandas as pd"],
            dependencies=["pandas"]
        )
        
        # Lookup transformation
        rules[ComponentType.LOOKUP] = TransformationRule(
            component_type=ComponentType.LOOKUP,
            python_code="""
def perform_lookup(df, lookup_df, left_on, right_on, how='left'):
    \"\"\"Perform lookup operation\"\"\"
    import pandas as pd
    
    try:
        result = df.merge(lookup_df, left_on=left_on, right_on=right_on, how=how)
        return result
    except Exception as e:
        raise Exception(f"Error performing lookup: {str(e)}")
""",
            imports=["pandas as pd"],
            dependencies=["pandas"]
        )
        
        # Sort transformation
        rules[ComponentType.SORT] = TransformationRule(
            component_type=ComponentType.SORT,
            python_code="""
def sort_data(df, sort_columns, ascending=True):
    \"\"\"Sort data by specified columns\"\"\"
    import pandas as pd
    
    try:
        return df.sort_values(by=sort_columns, ascending=ascending)
    except Exception as e:
        raise Exception(f"Error sorting data: {str(e)}")
""",
            imports=["pandas as pd"],
            dependencies=["pandas"]
        )
        
        # Aggregate transformation
        rules[ComponentType.AGGREGATE] = TransformationRule(
            component_type=ComponentType.AGGREGATE,
            python_code="""
def aggregate_data(df, group_columns, agg_functions):
    \"\"\"Aggregate data by specified columns\"\"\"
    import pandas as pd
    
    try:
        return df.groupby(group_columns).agg(agg_functions).reset_index()
    except Exception as e:
        raise Exception(f"Error aggregating data: {str(e)}")
""",
            imports=["pandas as pd"],
            dependencies=["pandas"]
        )
        
        # Conditional Split transformation
        rules[ComponentType.CONDITIONAL_SPLIT] = TransformationRule(
            component_type=ComponentType.CONDITIONAL_SPLIT,
            python_code="""
def conditional_split(df, conditions):
    \"\"\"Split data based on conditions\"\"\"
    import pandas as pd
    
    try:
        results = {}
        for condition_name, condition_expr in conditions.items():
            mask = df.eval(condition_expr)
            results[condition_name] = df[mask].copy()
        return results
    except Exception as e:
        raise Exception(f"Error in conditional split: {str(e)}")
""",
            imports=["pandas as pd"],
            dependencies=["pandas"]
        )
        
        # Data Conversion transformation
        rules[ComponentType.DATA_CONVERSION] = TransformationRule(
            component_type=ComponentType.DATA_CONVERSION,
            python_code="""
def convert_data_types(df, type_mappings):
    \"\"\"Convert data types of columns\"\"\"
    import pandas as pd
    
    try:
        for column, target_type in type_mappings.items():
            if target_type == 'int':
                df[column] = pd.to_numeric(df[column], errors='coerce').astype('Int64')
            elif target_type == 'float':
                df[column] = pd.to_numeric(df[column], errors='coerce')
            elif target_type == 'datetime':
                df[column] = pd.to_datetime(df[column], errors='coerce')
            elif target_type == 'string':
                df[column] = df[column].astype(str)
            elif target_type == 'bool':
                df[column] = df[column].astype(bool)
        return df
    except Exception as e:
        raise Exception(f"Error converting data types: {str(e)}")
""",
            imports=["pandas as pd"],
            dependencies=["pandas"]
        )
        
        return rules
    
    def _is_source_component(self, component: Dict[str, Any]) -> bool:
        """Check if component is a source component"""
        component_type = component.get('component_type', '').lower()
        return any(source_type in component_type for source_type in [
            'source', 'ole db source', 'excel source', 'flat file source',
            'xml source', 'adapter', 'reader'
        ])
    
    def _is_destination_component(self, component: Dict[str, Any]) -> bool:
        """Check if component is a destination component"""
        component_type = component.get('component_type', '').lower()
        return any(dest_type in component_type for dest_type in [
            'destination', 'ole db destination', 'excel destination', 
            'flat file destination', 'xml destination', 'writer'
        ])
    
    def _is_transformation_component(self, component: Dict[str, Any]) -> bool:
        """Check if component is a transformation component"""
        return not (self._is_source_component(component) or self._is_destination_component(component))
    
    def _generate_source_code(self, sources: List[Dict[str, Any]]) -> str:
        """Generate Python code for source components"""
        if not sources:
            return "# No source components found"
        
        code_lines = ["# Source Components", ""]
        
        for i, source in enumerate(sources):
            component_name = source.get('name', f'source_{i}')
            connection_string = source.get('connection_string', '')
            query = source.get('query', '')
            table_name = source.get('table_name', '')
            
            code_lines.extend([
                f"# {component_name}",
                f"def read_{component_name.lower().replace(' ', '_')}():",
                f"    \"\"\"Read data from {component_name}\"\"\"",
                f"    connection_string = '{connection_string}'"
            ])
            
            if query:
                code_lines.append(f"    query = '''{query}'''")
                code_lines.append("    return read_source_data(connection_string, query=query)")
            elif table_name:
                code_lines.append(f"    table_name = '{table_name}'")
                code_lines.append("    return read_source_data(connection_string, table_name=table_name)")
            else:
                code_lines.append("    # No query or table specified")
                code_lines.append("    return None")
            
            code_lines.append("")
        
        return "\n".join(code_lines)
    
    def _generate_transformation_code(self, transformations: List[Dict[str, Any]]) -> str:
        """Generate Python code for transformation components"""
        if not transformations:
            return "# No transformation components found"
        
        code_lines = ["# Transformation Components", ""]
        
        for i, transform in enumerate(transformations):
            component_name = transform.get('name', f'transform_{i}')
            component_type = self._get_component_type(transform)
            
            code_lines.extend([
                f"# {component_name} ({component_type.value})",
                f"def apply_{component_name.lower().replace(' ', '_')}(df):",
                f"    \"\"\"Apply {component_type.value} transformation\"\"\""
            ])
            
            # Add specific transformation logic based on component type
            if component_type == ComponentType.DERIVED_COLUMN:
                code_lines.extend(self._generate_derived_column_code(transform))
            elif component_type == ComponentType.LOOKUP:
                code_lines.extend(self._generate_lookup_code(transform))
            elif component_type == ComponentType.SORT:
                code_lines.extend(self._generate_sort_code(transform))
            elif component_type == ComponentType.AGGREGATE:
                code_lines.extend(self._generate_aggregate_code(transform))
            elif component_type == ComponentType.CONDITIONAL_SPLIT:
                code_lines.extend(self._generate_conditional_split_code(transform))
            elif component_type == ComponentType.DATA_CONVERSION:
                code_lines.extend(self._generate_data_conversion_code(transform))
            else:
                code_lines.extend([
                    "    # Generic transformation",
                    "    # TODO: Implement specific transformation logic",
                    "    return df"
                ])
            
            code_lines.append("")
        
        return "\n".join(code_lines)
    
    def _generate_destination_code(self, destinations: List[Dict[str, Any]]) -> str:
        """Generate Python code for destination components"""
        if not destinations:
            return "# No destination components found"
        
        code_lines = ["# Destination Components", ""]
        
        for i, destination in enumerate(destinations):
            component_name = destination.get('name', f'destination_{i}')
            connection_string = destination.get('connection_string', '')
            table_name = destination.get('table_name', '')
            if_exists = destination.get('if_exists', 'replace')
            
            code_lines.extend([
                f"# {component_name}",
                f"def write_{component_name.lower().replace(' ', '_')}(df):",
                f"    \"\"\"Write data to {component_name}\"\"\"",
                f"    connection_string = '{connection_string}'",
                f"    table_name = '{table_name}'",
                f"    return write_destination_data(df, connection_string, table_name, if_exists='{if_exists}')",
                ""
            ])
        
        return "\n".join(code_lines)
    
    def _get_component_type(self, component: Dict[str, Any]) -> ComponentType:
        """Get the component type from component data"""
        component_type = component.get('component_type', '').lower()
        
        if 'derived column' in component_type:
            return ComponentType.DERIVED_COLUMN
        elif 'lookup' in component_type:
            return ComponentType.LOOKUP
        elif 'sort' in component_type:
            return ComponentType.SORT
        elif 'aggregate' in component_type:
            return ComponentType.AGGREGATE
        elif 'conditional split' in component_type:
            return ComponentType.CONDITIONAL_SPLIT
        elif 'data conversion' in component_type:
            return ComponentType.DATA_CONVERSION
        else:
            return ComponentType.UNKNOWN
    
    def _generate_derived_column_code(self, component: Dict[str, Any]) -> List[str]:
        """Generate code for derived column transformation"""
        expressions = component.get('expressions', {})
        
        if not expressions:
            return ["    return df"]
        
        code_lines = ["    column_expressions = {"]
        for col_name, expression in expressions.items():
            code_lines.append(f"        '{col_name}': '{expression}',")
        code_lines.extend([
            "    }",
            "    return apply_derived_columns(df, column_expressions)"
        ])
        
        return code_lines
    
    def _generate_lookup_code(self, component: Dict[str, Any]) -> List[str]:
        """Generate code for lookup transformation"""
        lookup_columns = component.get('lookup_columns', {})
        
        if not lookup_columns:
            return ["    return df"]
        
        code_lines = [
            "    # TODO: Load lookup data",
            "    lookup_df = None  # Load from lookup source",
            "    left_on = list(lookup_columns.keys())",
            "    right_on = list(lookup_columns.values())",
            "    return perform_lookup(df, lookup_df, left_on, right_on)"
        ]
        
        return code_lines
    
    def _generate_sort_code(self, component: Dict[str, Any]) -> List[str]:
        """Generate code for sort transformation"""
        sort_columns = component.get('sort_columns', [])
        ascending = component.get('ascending', True)
        
        if not sort_columns:
            return ["    return df"]
        
        code_lines = [
            f"    sort_columns = {sort_columns}",
            f"    ascending = {ascending}",
            "    return sort_data(df, sort_columns, ascending)"
        ]
        
        return code_lines
    
    def _generate_aggregate_code(self, component: Dict[str, Any]) -> List[str]:
        """Generate code for aggregate transformation"""
        group_columns = component.get('group_columns', [])
        agg_functions = component.get('agg_functions', {})
        
        if not group_columns and not agg_functions:
            return ["    return df"]
        
        code_lines = [
            f"    group_columns = {group_columns}",
            f"    agg_functions = {agg_functions}",
            "    return aggregate_data(df, group_columns, agg_functions)"
        ]
        
        return code_lines
    
    def _generate_conditional_split_code(self, component: Dict[str, Any]) -> List[str]:
        """Generate code for conditional split transformation"""
        conditions = component.get('conditions', {})
        
        if not conditions:
            return ["    return df"]
        
        code_lines = ["    conditions = {"]
        for condition_name, condition_expr in conditions.items():
            code_lines.append(f"        '{condition_name}': '{condition_expr}',")
        code_lines.extend([
            "    }",
            "    return conditional_split(df, conditions)"
        ])
        
        return code_lines
    
    def _generate_data_conversion_code(self, component: Dict[str, Any]) -> List[str]:
        """Generate code for data conversion transformation"""
        type_mappings = component.get('type_mappings', {})
        
        if not type_mappings:
            return ["    return df"]
        
        code_lines = ["    type_mappings = {"]
        for column, target_type in type_mappings.items():
            code_lines.append(f"        '{column}': '{target_type}',")
        code_lines.extend([
            "    }",
            "    return convert_data_types(df, type_mappings)"
        ])
        
        return code_lines
    
    def _collect_imports(self, sources: List[Dict], transformations: List[Dict], destinations: List[Dict]) -> List[str]:
        """Collect all required imports"""
        imports = set()
        
        # Add imports from transformation rules
        for transform in transformations:
            component_type = self._get_component_type(transform)
            if component_type in self.transformation_rules:
                rule = self.transformation_rules[component_type]
                imports.update(rule.imports)
        
        # Add common imports
        imports.update([
            "pandas as pd",
            "sqlalchemy",
            "logging"
        ])
        
        return sorted(list(imports))
    
    def _collect_dependencies(self, sources: List[Dict], transformations: List[Dict], destinations: List[Dict]) -> List[str]:
        """Collect all required dependencies"""
        dependencies = set()
        
        # Add dependencies from transformation rules
        for transform in transformations:
            component_type = self._get_component_type(transform)
            if component_type in self.transformation_rules:
                rule = self.transformation_rules[component_type]
                dependencies.update(rule.dependencies)
        
        # Add common dependencies
        dependencies.update([
            "pandas",
            "sqlalchemy"
        ])
        
        return sorted(list(dependencies))
    
    def _generate_error_handling(self) -> str:
        """Generate error handling code"""
        return """
def handle_etl_error(error, context=""):
    \"\"\"Handle ETL errors\"\"\"
    import logging
    
    logger = logging.getLogger(__name__)
    logger.error(f"ETL Error in {context}: {str(error)}")
    raise error

def validate_dataframe(df, expected_columns=None, min_rows=0):
    \"\"\"Validate dataframe\"\"\"
    if df is None:
        raise ValueError("DataFrame is None")
    
    if len(df) < min_rows:
        raise ValueError(f"DataFrame has {len(df)} rows, minimum required: {min_rows}")
    
    if expected_columns:
        missing_columns = set(expected_columns) - set(df.columns)
        if missing_columns:
            raise ValueError(f"Missing columns: {missing_columns}")
    
    return True
"""
    
    def _generate_validation_code(self, components: List[Dict[str, Any]]) -> str:
        """Generate validation code for the data flow"""
        return """
def validate_data_flow(df):
    \"\"\"Validate the complete data flow\"\"\"
    try:
        validate_dataframe(df)
        # Add specific validation rules here
        return True
    except Exception as e:
        handle_etl_error(e, "Data Flow Validation")
        return False
""" 