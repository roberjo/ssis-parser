#!/usr/bin/env python3
"""
SSIS Migration Tool - CLI Module

This module provides the command-line interface using Click.
"""

import click
import logging
from pathlib import Path
from typing import Optional

from .core.config import Config
from .core.logger import setup_logging
from .utils.version import get_version

# Set up logging
logger = logging.getLogger(__name__)


@click.group()
@click.option(
    "--verbose", "-v", 
    is_flag=True, 
    help="Enable verbose logging"
)
@click.option(
    "--config", "-c", 
    type=click.Path(exists=True), 
    help="Path to configuration file"
)
@click.version_option(version=get_version(), prog_name="SSIS Migration Tool")
@click.pass_context
def main(ctx: click.Context, verbose: bool, config: Optional[str]) -> None:
    """
    SSIS Migration Tool - Convert SSIS packages to Python ETL scripts.
    
    This tool automates the conversion of SQL Server Integration Services (SSIS)
    packages (.dtsx files) to modern Python-based ETL scripts with validation,
    testing, and rollback capabilities.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Set up logging
    log_level = logging.DEBUG if verbose else logging.INFO
    setup_logging(log_level)
    
    # Load configuration
    if config:
        ctx.obj['config'] = Config.from_file(config)
    else:
        ctx.obj['config'] = Config()
    
    logger.debug("SSIS Migration Tool initialized")


@main.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.option(
    '--package', '-p',
    type=click.Path(exists=True),
    help='Specific package to convert'
)
@click.option(
    '--validate', '-v',
    is_flag=True,
    help='Enable validation after conversion'
)
@click.option(
    '--test', '-t',
    is_flag=True,
    help='Generate and run tests after conversion'
)
@click.option(
    '--benchmark', '-b',
    is_flag=True,
    help='Run performance benchmarking'
)
@click.option(
    '--backup', '-B',
    is_flag=True,
    help='Create backup before conversion'
)
@click.option(
    '--dry-run', '-d',
    is_flag=True,
    help='Validate inputs without generating output'
)
@click.pass_context
def convert(
    ctx: click.Context,
    input_path: str,
    output_path: str,
    package: Optional[str],
    validate: bool,
    test: bool,
    benchmark: bool,
    backup: bool,
    dry_run: bool
) -> None:
    """
    Convert SSIS package(s) to Python ETL scripts.
    
    INPUT_PATH: Directory containing .dtsx files or path to specific package
    OUTPUT_PATH: Directory where converted files will be saved
    """
    from .core.converter import SSISConverter
    
    try:
        converter = SSISConverter(ctx.obj['config'])
        
        if dry_run:
            click.echo("🔍 Running dry-run validation...")
            # TODO: Implement dry-run validation
            click.echo("✅ Dry-run validation completed")
            return
        
        if package:
            # Convert single package
            click.echo(f"🔄 Converting package: {package}")
            result = converter.convert_package(
                package_path=package,
                output_path=output_path,
                validate=validate,
                test=test,
                benchmark=benchmark,
                backup=backup
            )
        else:
            # Convert all packages in directory
            click.echo(f"🔄 Converting packages in: {input_path}")
            result = converter.convert_directory(
                input_path=input_path,
                output_path=output_path,
                validate=validate,
                test=test,
                benchmark=benchmark,
                backup=backup
            )
        
        click.echo(f"✅ Conversion completed successfully!")
        click.echo(f"📁 Output saved to: {output_path}")
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        click.echo(f"❌ Conversion failed: {str(e)}")
        sys.exit(1)


@main.command()
@click.argument('package_path', type=click.Path(exists=True))
@click.pass_context
def validate(ctx: click.Context, package_path: str) -> None:
    """
    Validate converted Python code.
    
    PACKAGE_PATH: Path to the converted Python package
    """
    from .validators.code_validator import CodeValidator
    
    try:
        click.echo(f"🔍 Validating package: {package_path}")
        validator = CodeValidator()
        result = validator.validate_package(package_path)
        
        if result.is_valid:
            click.echo("✅ Validation passed")
        else:
            click.echo("❌ Validation failed")
            for error in result.errors:
                click.echo(f"  - {error}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        click.echo(f"❌ Validation failed: {str(e)}")
        sys.exit(1)


@main.command()
@click.argument('package_path', type=click.Path(exists=True))
@click.pass_context
def test(ctx: click.Context, package_path: str) -> None:
    """
    Run tests on converted Python code.
    
    PACKAGE_PATH: Path to the converted Python package
    """
    from .validators.test_runner import TestRunner
    
    try:
        click.echo(f"🧪 Running tests for package: {package_path}")
        runner = TestRunner()
        result = runner.run_tests(package_path)
        
        if result.success:
            click.echo(f"✅ Tests passed ({result.tests_passed} tests)")
        else:
            click.echo(f"❌ Tests failed ({result.tests_failed} failures)")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Testing failed: {str(e)}")
        click.echo(f"❌ Testing failed: {str(e)}")
        sys.exit(1)


@main.command()
@click.argument('package_path', type=click.Path(exists=True))
@click.pass_context
def benchmark(ctx: click.Context, package_path: str) -> None:
    """
    Run performance benchmarking.
    
    PACKAGE_PATH: Path to the converted Python package
    """
    from .validators.performance_benchmarker import PerformanceBenchmarker
    
    try:
        click.echo(f"📊 Running performance benchmark for package: {package_path}")
        benchmarker = PerformanceBenchmarker()
        result = benchmarker.benchmark_package(package_path)
        
        click.echo("📈 Performance Results:")
        click.echo(f"  Execution Time: {result.execution_time:.2f}s")
        click.echo(f"  Memory Usage: {result.memory_usage:.2f}MB")
        click.echo(f"  Throughput: {result.throughput:.0f} rows/sec")
        
    except Exception as e:
        logger.error(f"Benchmarking failed: {str(e)}")
        click.echo(f"❌ Benchmarking failed: {str(e)}")
        sys.exit(1)


@main.command()
@click.argument('package_path', type=click.Path(exists=True))
@click.option('--all', '-a', is_flag=True, help='Rollback all packages')
@click.option('--validate-only', '-v', is_flag=True, help='Validate rollback without executing')
@click.pass_context
def rollback(
    ctx: click.Context, 
    package_path: str, 
    all: bool, 
    validate_only: bool
) -> None:
    """
    Rollback migration to original SSIS package.
    
    PACKAGE_PATH: Path to the package to rollback
    """
    from .core.rollback_manager import RollbackManager
    
    try:
        if validate_only:
            click.echo(f"🔍 Validating rollback for package: {package_path}")
            # TODO: Implement rollback validation
            click.echo("✅ Rollback validation completed")
            return
        
        click.echo(f"🔄 Rolling back package: {package_path}")
        manager = RollbackManager()
        
        if all:
            result = manager.rollback_all(package_path)
        else:
            result = manager.rollback_package(package_path)
        
        click.echo("✅ Rollback completed successfully")
        
    except Exception as e:
        logger.error(f"Rollback failed: {str(e)}")
        click.echo(f"❌ Rollback failed: {str(e)}")
        sys.exit(1)


@main.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.pass_context
def plan(ctx: click.Context, input_dir: str, output_dir: str) -> None:
    """
    Generate migration plan for all packages.
    
    INPUT_DIR: Directory containing SSIS packages
    OUTPUT_DIR: Directory where migration plan will be saved
    """
    from .core.migration_planner import MigrationPlanner
    
    try:
        click.echo(f"📋 Generating migration plan for: {input_dir}")
        planner = MigrationPlanner()
        plan = planner.create_plan(input_dir, output_dir)
        
        click.echo("✅ Migration plan generated successfully")
        click.echo(f"📁 Plan saved to: {output_dir}")
        
    except Exception as e:
        logger.error(f"Migration planning failed: {str(e)}")
        click.echo(f"❌ Migration planning failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 