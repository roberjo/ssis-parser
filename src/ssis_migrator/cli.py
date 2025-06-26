#!/usr/bin/env python3
"""
SSIS Migration Tool - CLI Module

This module provides the command-line interface using Click.
"""

import click
import logging
import sys
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from .core.config import Config
from .core.logger import setup_logging, get_logger
from .core.error_handler import ErrorHandler, ErrorSeverity
from .core.converter import SSISConverter, ConversionResult
from .validators.code_validator import CodeValidator
from .validators.test_runner import TestRunner
from .validators.performance_benchmarker import PerformanceBenchmarker
from .core.migration_planner import MigrationPlanner
from .core.rollback_manager import RollbackManager
from .utils.version import get_version

# Set up logging
logger = logging.getLogger(__name__)

# Initialize Rich console
console = Console()


def create_error_summary_table(error_handler: ErrorHandler) -> Table:
    """Create a Rich table showing error summary"""
    summary = error_handler.get_error_summary()
    
    table = Table(title="Error Summary")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Total Errors", str(summary.get("total_errors", 0)))
    
    if summary.get("severity_distribution"):
        for severity, count in summary["severity_distribution"].items():
            table.add_row(f"  {severity.title()} Severity", str(count))
    
    if summary.get("category_distribution"):
        for category, count in summary["category_distribution"].items():
            table.add_row(f"  {category.title()} Category", str(count))
    
    if summary.get("latest_error"):
        table.add_row("Latest Error ID", summary["latest_error"])
    
    return table


def display_error_report(error_handler: ErrorHandler, verbose: bool = False):
    """Display error report in CLI"""
    summary = error_handler.get_error_summary()
    
    if summary.get("total_errors", 0) == 0:
        console.print("✅ No errors encountered", style="green")
        return
    
    # Display error summary table
    error_table = create_error_summary_table(error_handler)
    console.print(error_table)
    
    if verbose and error_handler.error_reports:
        console.print("\n[bold red]Detailed Error Reports:[/bold red]")
        for report in error_handler.error_reports[-5:]:  # Show last 5 errors
            panel = Panel(
                f"[bold]{report.error_type}[/bold]\n"
                f"[red]{report.message}[/red]\n"
                f"Severity: {report.severity.value}\n"
                f"Category: {report.category.value}\n"
                f"Component: {report.context.component or 'Unknown'}\n"
                f"File: {report.context.file_path or 'N/A'}\n"
                f"Recovery: {report.recovery_action or 'None provided'}",
                title=f"Error {report.error_id}",
                border_style="red"
            )
            console.print(panel)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Path to configuration file')
@click.option('--log-file', type=click.Path(), help='Path to log file')
@click.option('--log-level', 
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
              default='INFO', help='Logging level')
@click.version_option(version=get_version(), prog_name='SSIS Migration Tool')
@click.pass_context
def cli(ctx, verbose, config, log_file, log_level):
    """
    SSIS Migration Tool - Convert SSIS packages to Python ETL scripts.
    
    This tool automates the conversion of SQL Server Integration Services (SSIS)
    packages (.dtsx files) to modern Python-based ETL scripts with validation,
    testing, and rollback capabilities.
    """
    # Ensure context object exists
    ctx.ensure_object(dict)
    
    # Setup logging
    log_level_int = getattr(logging, log_level.upper())
    setup_logging(level=log_level_int, log_file=log_file)
    
    # Initialize error handler
    error_handler = ErrorHandler(log_errors=True, save_reports=True)
    ctx.obj['error_handler'] = error_handler
    
    # Load configuration
    config_obj = Config(config_file=config) if config else Config()
    ctx.obj['config'] = config_obj
    
    # Initialize converter with error handler
    converter = SSISConverter(config_obj, error_handler=error_handler)
    ctx.obj['converter'] = converter
    
    # Set verbose flag
    ctx.obj['verbose'] = verbose
    
    # Display startup message
    if verbose:
        console.print(f"[bold blue]SSIS Migration Tool v{get_version()}[/bold blue]")
        console.print(f"Log Level: {log_level}")
        if log_file:
            console.print(f"Log File: {log_file}")


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.option('--validate', is_flag=True, default=True, help='Validate converted code')
@click.option('--test', is_flag=True, help='Run tests on converted code')
@click.option('--benchmark', is_flag=True, help='Run performance benchmarking')
@click.option('--backup', is_flag=True, default=True, help='Create backup of original files')
@click.pass_context
def convert(ctx, input_path, output_path, validate, test, benchmark, backup):
    """Convert SSIS package(s) to Python ETL scripts."""
    error_handler = ctx.obj['error_handler']
    converter = ctx.obj['converter']
    verbose = ctx.obj['verbose']
    
    try:
        input_path = Path(input_path)
        output_path = Path(output_path)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            if input_path.is_file():
                # Convert single file
                progress.add_task("Converting SSIS package...", total=None)
                result = converter.convert_package(
                    str(input_path), str(output_path),
                    validate=validate, test=test, benchmark=benchmark, backup=backup
                )
            else:
                # Convert directory
                progress.add_task("Converting SSIS packages...", total=None)
                result = converter.convert_directory(
                    str(input_path), str(output_path),
                    validate=validate, test=test, benchmark=benchmark, backup=backup
                )
        
        if result.success:
            console.print(f"✅ Conversion completed successfully!", style="green")
            console.print(f"📁 Output saved to: {output_path}")
            
            # Display error summary if any errors occurred
            if error_handler.error_reports:
                console.print("\n[bold yellow]⚠️  Some errors occurred during conversion:[/bold yellow]")
                display_error_report(error_handler, verbose)
        else:
            console.print(f"❌ Conversion failed!", style="red")
            console.print(f"Errors: {result.errors}")
            
            # Display detailed error report
            display_error_report(error_handler, verbose=True)
            
            sys.exit(1)
            
    except Exception as e:
        error_handler.handle_error(
            e,
            context=create_error_context(
                file_path=str(input_path),
                component="CLI",
                operation="convert"
            )
        )
        console.print(f"❌ Unexpected error: {str(e)}", style="red")
        display_error_report(error_handler, verbose=True)
        sys.exit(1)


@cli.command()
@click.argument('package_path', type=click.Path(exists=True))
@click.pass_context
def validate(ctx, package_path):
    """Validate converted Python code."""
    error_handler = ctx.obj['error_handler']
    verbose = ctx.obj['verbose']
    
    try:
        validator = CodeValidator()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("Validating converted code...", total=None)
            result = validator.validate_package(package_path)
        
        if result.is_valid:
            console.print("✅ Validation passed!", style="green")
        else:
            console.print("❌ Validation failed!", style="red")
            for error in result.errors:
                console.print(f"  - {error}")
        
        # Display error summary
        display_error_report(error_handler, verbose)
        
    except Exception as e:
        error_handler.handle_error(
            e,
            context=create_error_context(
                file_path=package_path,
                component="CLI",
                operation="validate"
            )
        )
        console.print(f"❌ Validation error: {str(e)}", style="red")
        display_error_report(error_handler, verbose=True)
        sys.exit(1)


@cli.command()
@click.argument('package_path', type=click.Path(exists=True))
@click.pass_context
def test(ctx, package_path):
    """Run tests on converted Python code."""
    error_handler = ctx.obj['error_handler']
    verbose = ctx.obj['verbose']
    
    try:
        runner = TestRunner()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("Running tests...", total=None)
            result = runner.run_tests(package_path)
        
        if result.success:
            console.print(f"✅ Tests completed successfully!", style="green")
            console.print(f"📊 Tests passed: {result.tests_passed}")
            console.print(f"📊 Tests failed: {result.tests_failed}")
        else:
            console.print("❌ Tests failed!", style="red")
            for error in result.errors:
                console.print(f"  - {error}")
        
        # Display error summary
        display_error_report(error_handler, verbose)
        
    except Exception as e:
        error_handler.handle_error(
            e,
            context=create_error_context(
                file_path=package_path,
                component="CLI",
                operation="test"
            )
        )
        console.print(f"❌ Test error: {str(e)}", style="red")
        display_error_report(error_handler, verbose=True)
        sys.exit(1)


@cli.command()
@click.argument('package_path', type=click.Path(exists=True))
@click.pass_context
def benchmark(ctx, package_path):
    """Run performance benchmarking."""
    error_handler = ctx.obj['error_handler']
    verbose = ctx.obj['verbose']
    
    try:
        benchmarker = PerformanceBenchmarker()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("Running performance benchmark...", total=None)
            result = benchmarker.benchmark_package(package_path)
        
        # Display benchmark results
        table = Table(title="Performance Benchmark Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Execution Time", f"{result.execution_time:.2f}s")
        table.add_row("Memory Usage", f"{result.memory_usage:.2f}MB")
        table.add_row("Throughput", f"{result.throughput:.2f} rows/sec")
        
        console.print(table)
        
        # Display error summary
        display_error_report(error_handler, verbose)
        
    except Exception as e:
        error_handler.handle_error(
            e,
            context=create_error_context(
                file_path=package_path,
                component="CLI",
                operation="benchmark"
            )
        )
        console.print(f"❌ Benchmark error: {str(e)}", style="red")
        display_error_report(error_handler, verbose=True)
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.pass_context
def plan(ctx, input_dir):
    """Generate migration plan for all packages."""
    error_handler = ctx.obj['error_handler']
    verbose = ctx.obj['verbose']
    
    try:
        planner = MigrationPlanner()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            progress.add_task("Generating migration plan...", total=None)
            plan = planner.create_migration_plan(input_dir)
        
        # Display migration plan
        console.print("[bold blue]Migration Plan:[/bold blue]")
        console.print(f"📦 Total packages: {plan.total_packages}")
        console.print(f"⏱️  Estimated time: {plan.estimated_time}")
        console.print(f"⚠️  High-risk packages: {len(plan.high_risk_packages)}")
        
        if plan.high_risk_packages:
            console.print("\n[bold yellow]High-Risk Packages:[/bold yellow]")
            for package in plan.high_risk_packages:
                console.print(f"  - {package}")
        
        # Display error summary
        display_error_report(error_handler, verbose)
        
    except Exception as e:
        error_handler.handle_error(
            e,
            context=create_error_context(
                file_path=input_dir,
                component="CLI",
                operation="plan"
            )
        )
        console.print(f"❌ Planning error: {str(e)}", style="red")
        display_error_report(error_handler, verbose=True)
        sys.exit(1)


@cli.command()
@click.argument('package_path', type=click.Path(exists=True))
@click.option('--all', is_flag=True, help='Rollback all packages')
@click.option('--validate-only', is_flag=True, help='Only validate rollback, don\'t execute')
@click.pass_context
def rollback(ctx, package_path, all, validate_only):
    """Rollback migration to original SSIS package."""
    error_handler = ctx.obj['error_handler']
    verbose = ctx.obj['verbose']
    
    try:
        rollback_manager = RollbackManager()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            if all:
                progress.add_task("Rolling back all packages...", total=None)
                result = rollback_manager.rollback_all(validate_only=validate_only)
            else:
                progress.add_task("Rolling back package...", total=None)
                result = rollback_manager.rollback_package(package_path, validate_only=validate_only)
        
        if result.success:
            console.print("✅ Rollback completed successfully!", style="green")
        else:
            console.print("❌ Rollback failed!", style="red")
            for error in result.errors:
                console.print(f"  - {error}")
        
        # Display error summary
        display_error_report(error_handler, verbose)
        
    except Exception as e:
        error_handler.handle_error(
            e,
            context=create_error_context(
                file_path=package_path,
                component="CLI",
                operation="rollback"
            )
        )
        console.print(f"❌ Rollback error: {str(e)}", style="red")
        display_error_report(error_handler, verbose=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def errors(ctx):
    """Display error summary and reports."""
    error_handler = ctx.obj['error_handler']
    verbose = ctx.obj['verbose']
    
    display_error_report(error_handler, verbose)


if __name__ == '__main__':
    cli() 