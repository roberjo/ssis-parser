# SSIS Migration Tool

A comprehensive command-line tool designed to parse, analyze, and migrate SQL Server Integration Services (SSIS) packages to modern Python-based ETL platforms.

## 🎯 Project Status

**Current Phase:** MVP Development  
**Version:** 2.0  
**Status:** In Development

## 📋 Overview

The SSIS Migration Tool automates the conversion of .dtsx files into production-ready Python ETL scripts, significantly reducing the time and effort required for SSIS to modern ETL platform migrations.

### Key Features

- **🔄 Automated Conversion:** Convert SSIS data flow components to Python
- **✅ Validation & Testing:** Comprehensive code validation and test generation
- **🔄 Rollback Capabilities:** Safe migration with one-click rollback
- **📊 Performance Benchmarking:** Compare SSIS vs. Python performance
- **📈 Incremental Migration:** Package-by-package processing with dependency resolution
- **📚 Documentation:** Auto-generated documentation with data lineage

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
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
ssis-migrator convert --package package1.dtsx --validate --test --benchmark

# Generate migration plan for all packages
ssis-migrator plan --input-dir ./ssis-packages --output-dir ./migration-plan

# Rollback a specific package
ssis-migrator rollback --package package1.dtsx
```

## 📁 Output Structure

```
output/
├── package1.py              # Generated Python ETL script
├── package1.md              # Documentation with data lineage
├── package1_tests.py        # Generated unit tests
├── package1_validation.json # Validation results
├── package1_performance.json # Performance comparison
└── migration_summary.md     # Overall migration summary
```

## 🔧 Commands

| Command | Description |
|---------|-------------|
| `convert` | Convert SSIS package to Python |
| `validate` | Validate converted code |
| `test` | Run tests on converted code |
| `benchmark` | Compare performance |
| `rollback` | Rollback migration |
| `plan` | Generate migration plan |

## 📊 Component Support

| Component Type | MVP Support | Phase 2 |
|----------------|-------------|---------|
| Data Flow Sources | ✅ Full | ✅ Full |
| Data Flow Destinations | ✅ Full | ✅ Full |
| Data Flow Transformations | ✅ Full | ✅ Full |
| Execute SQL Tasks | ❌ | ✅ Full |
| Script Tasks (C#) | ❌ | ⚠️ Basic |
| Connection Managers | ✅ Full | ✅ Full |
| Variables/Parameters | ✅ Full | ✅ Full |

## 🎯 Success Criteria

- ✅ Process single .dtsx file in under 5 minutes
- ✅ Generate syntactically correct Python scripts
- ✅ 95%+ data flow component parsing accuracy
- ✅ Comprehensive validation and testing
- ✅ Zero data loss during migration
- ✅ 80% reduction in manual migration effort

## 🛣️ Roadmap

### Phase 1 (MVP) - Current
- CLI tool with data flow component support
- Validation and testing framework
- Rollback capabilities
- Performance benchmarking

### Phase 2
- Web application interface
- Control flow component support
- Advanced script task conversion

### Phase 3
- ETL orchestration platform integration
- AI-assisted C# to Python conversion
- Cloud deployment templates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
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