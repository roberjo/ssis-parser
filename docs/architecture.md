# SSIS Migration Tool Architecture

## Overview

The SSIS Migration Tool is a CLI-based utility that parses SSIS packages (.dtsx files) and converts them into Python ETL scripts. The MVP focuses on extracting and summarizing data flow components, connection managers, variables, and control flow tasks from SSIS packages.

---

## Architecture

### Core Parser Modules

- **DTSXParser**: Main entry point for parsing .dtsx files. Orchestrates extraction of package metadata, connection managers, variables, data flow components, and control flow tasks.
- **ComponentParser**: Extracts and classifies data flow components (sources, destinations, transformations) from the data flow pipeline.
- **ConnectionParser**: Extracts connection manager details (name, type, connection string, ID).
- **VariableParser**: Extracts variables (name, value, data type, namespace).

#### Module Responsibilities

| Module            | Responsibility                                                                 |
|-------------------|-------------------------------------------------------------------------------|
| DTSXParser        | Orchestrates parsing, handles namespaces, builds package summary               |
| ComponentParser   | Parses data flow components, determines type/name/description                  |
| ConnectionParser  | Parses connection manager elements                                             |
| VariableParser    | Parses variable elements, infers data type and namespace                      |

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
    },
    {
      "name": "DestinationConnection",
      "type": "OLEDB",
      "connection_string": "Data Source=localhost;Initial Catalog=TestDB;Integrated Security=True;",
      "id": "{22222222-2222-2222-2222-222222222222}"
    }
  ],
  "variables": [
    {
      "name": "SourceTable",
      "value": "dbo.SourceTable",
      "data_type_name": "String",
      "metadata": { "namespace": "User" }
    },
    {
      "name": "DestinationTable",
      "value": "dbo.DestinationTable",
      "data_type_name": "String",
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
    },
    {
      "id": "{C9C7375C-8340-4F56-A550-919B1E4F4C66}",
      "name": "Derived Column",
      "description": "Derived Column",
      "type": "Derived Column",
      "properties": { "FriendlyExpression": "False" },
      "inputs": [],
      "outputs": [],
      "metadata": { "version": "1", "creation_name": "" }
    },
    {
      "id": "{E9216C7C-4A8A-4F77-8948-60C5D8C75F70}",
      "name": "OLE DB Destination",
      "description": "OLE DB Destination",
      "type": "OLE DB Destination",
      "properties": { "Connection": "{22222222-2222-2222-2222-222222222222}", "OpenRowset": "@[User::DestinationTable]" },
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

## How to Download, Setup, and Run

### Prerequisites
- Python 3.10+
- [pip](https://pip.pypa.io/en/stable/)

### 1. Clone the Repository
```sh
git clone <your-repo-url>
cd ssis-parser
```

### 2. Create and Activate a Virtual Environment
```sh
python3.10 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```sh
pip install -r requirements.txt
```

### 4. Install the Package in Editable Mode (for development)
```sh
pip install -e .
```

---

## CLI Usage

### Show CLI Help
```sh
ssis-migrator --help
```

### Parse and Summarize a .dtsx Package
```sh
ssis-migrator parse examples/input/sample_package.dtsx --output examples/output/SamplePackage_summary.json
```

### Example Output
The output will be a JSON file as shown above, summarizing the package structure and components.

---

## Testing

Run all unit tests:
```sh
pytest tests/unit
```

---

## Extending the Tool
- Add new component mappings in `ComponentParser` as needed.
- Add new CLI commands in `src/ssis_migrator/cli.py`.
- See `docs/prd.md` for roadmap and future features. 