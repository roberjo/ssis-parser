# SSIS Migration Tool

A comprehensive command-line tool designed to parse, analyze, and migrate SQL Server Integration Services (SSIS) packages to modern Python-based ETL platforms.

## 🎯 Project Status

**Current Phase:** MVP Development  
**Version:** 2.0  
**Status:** In Development

## 📋 Overview

The SSIS Migration Tool automates the conversion of .dtsx files into production-ready Python ETL scripts, significantly reducing the time and effort required for SSIS to modern ETL platform migrations.

### Key Features

- 🔄 Automated Conversion: Convert SSIS data flow components to Python
- ✅ Validation & Testing: Comprehensive code validation and test generation
- 🔄 Rollback Capabilities: Safe migration with one-click rollback
- 📈 Performance Benchmarking: Compare SSIS vs. Python performance
- 📊 Incremental Migration: Package-by-package processing with dependency resolution
- 🛡️ Robust Error Handling: Centralized error handler, JSON error reports, CLI error summaries
- 🧩 Modular Architecture: Extensible parser, generator, and validator modules
- 🧪 Full Test Coverage: All core modules and generators are covered by unit tests
- 📝 Documentation: Auto-generated documentation with data lineage

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Access to SSIS packages (.dtsx files)
- Database connectivity for testing

### Installation
```bash
# Clone the repository
git clone https://github.com/your-org/ssis-parser.git
cd ssis-parser

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage
```bash
# Convert a single SSIS package
ssis-migrator convert package1.dtsx output_dir --validate --test --benchmark

# Generate migration plan for all packages
ssis-migrator plan ./ssis-packages

# Rollback a specific package
ssis-migrator rollback package1.dtsx
```

## 📁 Output Structure
```
output/
├── TestPackage_main.py         # Main generated Python ETL script
├── TestPackage_config.py       # Configuration script (connections, variables, env)
├── requirements.txt            # Requirements for the generated ETL
├── TestPackage_dataflow.py     # Data flow component scripts
├── TestPackage_task.py         # Control flow task scripts
├── TestPackage_validation.json # Validation results
├── TestPackage_performance.json # Performance comparison
├── migration_summary.md        # Overall migration summary
```

## 🧪 Testing & Coverage

Run all unit tests:
```bash
pytest tests/unit
```

- 100% test coverage for PythonScriptGenerator, CLI, and core modules
- All new features require corresponding unit tests

## 🛠️ Troubleshooting & Error Reports
- All errors are logged and saved as JSON in `error_reports/`
- Use `ssis-migrator errors` to view error summaries in the CLI
- For debugging, check logs and error reports for stack traces and recovery suggestions

## 🧩 Component Support
| Component Type         | MVP Support | Phase 2 |
|-----------------------|-------------|---------|
| Data Flow Sources     | ✅ Full     | ✅ Full |
| Data Flow Destinations| ✅ Full     | ✅ Full |
| Data Flow Transformations | ✅ Full | ✅ Full |
| Execute SQL Tasks     | ❌          | ✅ Full |
| Script Tasks (C#)     | ❌          | ⚠️ Basic |
| Connection Managers   | ✅ Full     | ✅ Full |
| Variables/Parameters  | ✅ Full     | ✅ Full |

## 🏆 Success Criteria
- ✅ Process single .dtsx file in under 5 minutes
- ✅ Generate syntactically correct Python scripts
- ✅ 95%+ data flow component parsing accuracy
- ✅ Comprehensive validation and testing
- ✅ Zero data loss during migration
- ✅ 80% reduction in manual migration effort
- ✅ All core modules covered by unit tests

## 🗺️ Roadmap
### Phase 1 (MVP) - Current
- CLI tool with data flow, connection, and variable support
- Validation and testing framework
- Rollback capabilities
- Performance benchmarking
- Robust error handling and reporting
- Full test coverage for core modules

### Phase 2
- Web application interface
- Advanced control flow and script task conversion
- Enhanced documentation and reporting

### Phase 3
- ETL orchestration platform integration
- AI-assisted C# to Python conversion
- Cloud deployment templates

## 🤝 Contributing
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes and tests (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support
For questions and support:
- Create an issue in the GitHub repository
- Review the [Product Requirements Document](docs/prd.md)
- Check the [Executive Summary](docs/executive-summary.md) for business context

## 🔗 Related Documents
- [Product Requirements Document](docs/prd.md) - Detailed technical specifications
- [Executive Summary](docs/executive-summary.md) - Business case and implementation plan 