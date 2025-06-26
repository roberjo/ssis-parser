# SSIS Migration Tool Architecture

## Overview

The SSIS Migration Tool is a CLI-based utility that parses SSIS packages (.dtsx files) and converts them into Python ETL scripts. The MVP focuses on extracting and summarizing data flow components, connection managers, variables, and control flow tasks from SSIS packages, and generating robust, testable Python code.

---

## Architecture

### Core Parser & Generator Modules

- **DTSXParser**: Main entry point for parsing .dtsx files. Orchestrates extraction of package metadata, connection managers, variables, data flow components, and control flow tasks.
- **ComponentParser**: Extracts and classifies data flow components (sources, destinations, transformations) from the data flow pipeline.
- **ConnectionParser**: Extracts connection manager details (name, type, connection string, ID).
- **VariableParser**: Extracts variables (name, value, data type, namespace).
- **PythonScriptGenerator**: Converts parsed package objects into Python ETL scripts, config scripts, requirements, and testable modules. Handles formatting of connections, variables, and environment variables.
- **DataFlowMapper**: Maps SSIS data flow components to Python/Pandas operations and generates transformation code.
- **ConnectionConverter**: Converts SSIS connection managers to Python connection configs and code.
- **VariableHandler**: Converts SSIS variables/parameters to Python config and code.
- **ErrorHandler**: Centralized error handling, logging, and JSON error report generation.

#### Module Responsibilities

| Module                | Responsibility                                                                 |
|-----------------------|-------------------------------------------------------------------------------|
| DTSXParser            | Orchestrates parsing, handles namespaces, builds package summary               |
| ComponentParser       | Parses data flow components, determines type/name/description                  |
| ConnectionParser      | Parses connection manager elements                                             |
| VariableParser        | Parses variable elements, infers data type and namespace                      |
| PythonScriptGenerator | Generates Python ETL, config, requirements, and test scripts                  |
| DataFlowMapper        | Maps SSIS data flow to Python/Pandas code                                      |
| ConnectionConverter   | Converts connection managers to Python configs and code                        |
| VariableHandler       | Converts variables/parameters to Python configs and code                       |
| ErrorHandler          | Handles errors, logs, and generates error reports                              |

---

## Example: Parsed Output Structure

A parsed SSIS package is summarized as a JSON object with the following structure:

```json
{
  "name": "TestPackage",
  "version": "1.0.0",
  "description": "",
  "creation_date": "2025-01-01T00:00:00.000",
  "creator": "Developer",
  "package_id": "{87654321-4321-4321-4321-210987654321}",
  "connection_managers": [
    {
      "name": "SourceConnection",
      "type": "OLEDB",
      "connection_string": "Data Source=localhost;Initial Catalog=TestDB;Integrated Security=True;",
      "id": "{11111111-1111-1111-1111-111111111111}"
    }
  ],
  "variables": [
    {
      "name": "SourceTable",
      "value": "dbo.SourceTable",
      "type": "String",
      "metadata": { "namespace": "User" }
    }
  ],
  "data_flow_components": [
    {
      "id": "{E9216C7C-4A8A-4F77-8948-60C5D8C75F70}",
      "name": "OLE DB Source",
      "description": "OLE DB Source",
      "type": "OLE DB Source",
      "properties": { "Connection": "{11111111-1111-1111-1111-111111111111}", "SqlCommand": "SELECT * FROM @[User::SourceTable]" },
      "inputs": [],
      "outputs": [],
      "metadata": { "version": "1", "creation_name": "" }
    }
  ],
  "control_flow_tasks": [
    {
      "name": "Execute SQL Task 1",
      "type": "Microsoft.PackageTask",
      "creation_name": "Microsoft.ExecuteSQLTask",
      "description": "",
      "task_id": "{66666666-6666-6666-6666-666666666666}",
      "properties": {
        "connection": "{11111111-1111-1111-1111-111111111111}",
        "sql_statement": "SELECT * FROM @[User::SourceTable] WHERE @[User::FilterCondition]",
        "result_type": "ResultSetType_None"
      }
    }
  ],
  "metadata": {
    "executable_type": "Microsoft.Package",
    "creation_name": "Microsoft.Package",
    "creator_computer": "DESKTOP-ABC123",
    "package_type": "5",
    "version_guid": "{12345678-1234-1234-1234-123456789012}"
  }
}
```

---

## Example: Generated Config Script

```python
# TestPackage_config.py
DATABASE_CONNECTIONS = {
    "SourceConnection": {"type": "OLEDB", "connection_string": "Data Source=localhost;Initial Catalog=TestDB;Integrated Security=True;"}
}
VARIABLES = {
    "SourceTable": {"value": "dbo.SourceTable", "type": "String"}
}
ENVIRONMENT_VARIABLES = {
    # No environment variables defined
}
```

---

## Output Files
- `TestPackage_main.py`: Main ETL script
- `TestPackage_config.py`: Config script (connections, variables, env)
- `requirements.txt`: Requirements for the generated ETL
- `*_dataflow.py`: Data flow component scripts
- `*_task.py`: Control flow task scripts
- `*_validation.json`: Validation results
- `*_performance.json`: Performance comparison
- `migration_summary.md`: Overall migration summary

---

## Error Handling & Troubleshooting
- All errors are logged and saved as JSON in `error_reports/`
- Use `ssis-migrator errors` to view error summaries in the CLI
- Error reports include stack traces, severity, category, and recovery suggestions
- For debugging, check logs and error reports for details

---

## Testing

Run all unit tests:
```sh
pytest tests/unit
```
- 100% test coverage for PythonScriptGenerator, CLI, and core modules
- All new features require corresponding unit tests

---

## CLI Usage

Show CLI Help:
```sh
ssis-migrator --help
```

Convert a package:
```sh
ssis-migrator convert examples/input/sample_package.dtsx examples/output/
```

View error reports:
```sh
ssis-migrator errors
```

---

## Development Process & User Stories
- User Story 1.2: XML Parser Foundation (DTSXParser, ComponentParser, etc.)
- User Story 1.3: Configuration Management (ConfigParser, config integration)
- User Story 1.4: Error Handling and Logging (ErrorHandler, error reports)
- User Story 2.1: Basic Python Script Generation (PythonScriptGenerator)
- User Story 2.2: Data Flow Mapping and Transformation Logic (DataFlowMapper)
- User Story 2.3: Connection Manager Conversion (ConnectionConverter)
- User Story 2.4: Variable and Parameter Handling (VariableHandler)
- All core modules now have full unit test coverage

---

## Extending the Tool
- Add new component mappings in `ComponentParser` or `DataFlowMapper`
- Add new CLI commands in `src/ssis_migrator/cli.py`
- Add new tests in `tests/unit/`
- See `docs/prd.md` for roadmap and future features 