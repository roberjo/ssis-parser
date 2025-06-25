#!/usr/bin/env python3
"""
Error handling framework for SSIS Migration Tool
"""

import traceback
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
from enum import Enum
from .logger import LoggerMixin


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories"""
    PARSING = "parsing"
    CONFIGURATION = "configuration"
    VALIDATION = "validation"
    CONVERSION = "conversion"
    SYSTEM = "system"
    NETWORK = "network"
    PERMISSION = "permission"
    DEPENDENCY = "dependency"


@dataclass
class ErrorContext:
    """Context information for an error"""
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    function_name: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    user_input: Optional[str] = None
    system_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorReport:
    """Comprehensive error report"""
    error_id: str
    timestamp: datetime
    error_type: str
    message: str
    severity: ErrorSeverity
    category: ErrorCategory
    context: ErrorContext
    stack_trace: str
    suggestions: List[str] = field(default_factory=list)
    recovery_action: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SSISMigrationError(Exception):
    """Base exception for SSIS Migration Tool"""
    
    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        context: Optional[ErrorContext] = None,
        suggestions: Optional[List[str]] = None,
        recovery_action: Optional[str] = None
    ):
        super().__init__(message)
        self.severity = severity
        self.category = category
        self.context = context or ErrorContext()
        self.suggestions = suggestions or []
        self.recovery_action = recovery_action


class ParsingError(SSISMigrationError):
    """Exception raised for parsing errors"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        context = ErrorContext(file_path=file_path, component="parser")
        super().__init__(message, category=ErrorCategory.PARSING, context=context, **kwargs)


class ConfigurationError(SSISMigrationError):
    """Exception raised for configuration errors"""
    
    def __init__(self, message: str, config_file: Optional[str] = None, **kwargs):
        context = ErrorContext(file_path=config_file, component="configuration")
        super().__init__(message, category=ErrorCategory.CONFIGURATION, context=context, **kwargs)


class ValidationError(SSISMigrationError):
    """Exception raised for validation errors"""
    
    def __init__(self, message: str, component: Optional[str] = None, **kwargs):
        context = ErrorContext(component=component)
        super().__init__(message, category=ErrorCategory.VALIDATION, context=context, **kwargs)


class ConversionError(SSISMigrationError):
    """Exception raised for conversion errors"""
    
    def __init__(self, message: str, source_component: Optional[str] = None, **kwargs):
        context = ErrorContext(component=source_component, operation="conversion")
        super().__init__(message, category=ErrorCategory.CONVERSION, context=context, **kwargs)


class FileSystemError(SSISMigrationError):
    """Exception raised for file system errors"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        context = ErrorContext(file_path=file_path, component="filesystem")
        super().__init__(message, category=ErrorCategory.SYSTEM, context=context, **kwargs)


class ErrorHandler(LoggerMixin):
    """Comprehensive error handler for SSIS Migration Tool"""
    
    def __init__(self, log_errors: bool = True, save_reports: bool = True):
        self.log_errors = log_errors
        self.save_reports = save_reports
        self.error_reports: List[ErrorReport] = []
        self.error_count = 0
        
        # Create error reports directory
        if self.save_reports:
            self.reports_dir = Path("error_reports")
            self.reports_dir.mkdir(exist_ok=True)
    
    def handle_error(
        self,
        error: Exception,
        context: Optional[ErrorContext] = None,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None,
        suggestions: Optional[List[str]] = None,
        recovery_action: Optional[str] = None
    ) -> ErrorReport:
        """
        Handle an error and create a comprehensive error report
        
        Args:
            error: The exception that occurred
            context: Additional context information
            severity: Error severity level
            category: Error category
            suggestions: Suggested solutions
            recovery_action: Recommended recovery action
            
        Returns:
            ErrorReport object
        """
        # Determine error type and severity
        error_type = type(error).__name__
        
        if isinstance(error, SSISMigrationError):
            severity = severity or error.severity
            category = category or error.category
            context = context or error.context
            suggestions = suggestions or error.suggestions
            recovery_action = recovery_action or error.recovery_action
        else:
            severity = severity or self._determine_severity(error)
            category = category or self._determine_category(error)
            context = context or ErrorContext()
            suggestions = suggestions or self._generate_suggestions(error)
            recovery_action = recovery_action or self._generate_recovery_action(error)
        
        # Create error report
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.error_count:04d}"
        self.error_count += 1
        
        error_report = ErrorReport(
            error_id=error_id,
            timestamp=datetime.now(),
            error_type=error_type,
            message=str(error),
            severity=severity,
            category=category,
            context=context,
            stack_trace=traceback.format_exc(),
            suggestions=suggestions,
            recovery_action=recovery_action,
            metadata=self._collect_metadata()
        )
        
        # Log error
        if self.log_errors:
            self._log_error(error_report)
        
        # Save error report
        if self.save_reports:
            self._save_error_report(error_report)
        
        # Store in memory
        self.error_reports.append(error_report)
        
        return error_report
    
    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity based on error type"""
        if isinstance(error, (FileNotFoundError, PermissionError)):
            return ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.MEDIUM
        elif isinstance(error, (KeyboardInterrupt, SystemExit)):
            return ErrorSeverity.CRITICAL
        else:
            return ErrorSeverity.MEDIUM
    
    def _determine_category(self, error: Exception) -> ErrorCategory:
        """Determine error category based on error type"""
        if isinstance(error, (FileNotFoundError, PermissionError)):
            return ErrorCategory.SYSTEM
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorCategory.VALIDATION
        elif isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK
        else:
            return ErrorCategory.SYSTEM
    
    def _generate_suggestions(self, error: Exception) -> List[str]:
        """Generate suggestions for fixing the error"""
        suggestions = []
        
        if isinstance(error, FileNotFoundError):
            suggestions.extend([
                "Check if the file path is correct",
                "Verify that the file exists in the specified location",
                "Ensure you have read permissions for the file"
            ])
        elif isinstance(error, PermissionError):
            suggestions.extend([
                "Check file permissions",
                "Run the application with appropriate privileges",
                "Verify that the file is not locked by another process"
            ])
        elif isinstance(error, ValueError):
            suggestions.extend([
                "Check input data format",
                "Verify that required parameters are provided",
                "Ensure data types match expected formats"
            ])
        elif isinstance(error, TypeError):
            suggestions.extend([
                "Check function parameter types",
                "Verify that objects have required attributes",
                "Ensure compatibility between different data types"
            ])
        
        return suggestions
    
    def _generate_recovery_action(self, error: Exception) -> str:
        """Generate recovery action for the error"""
        if isinstance(error, FileNotFoundError):
            return "Provide correct file path or create missing file"
        elif isinstance(error, PermissionError):
            return "Adjust file permissions or run with elevated privileges"
        elif isinstance(error, (ValueError, TypeError)):
            return "Correct input data format and retry operation"
        else:
            return "Review error details and retry operation"
    
    def _collect_metadata(self) -> Dict[str, Any]:
        """Collect system metadata for error reports"""
        import platform
        import psutil
        
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "memory_usage": psutil.virtual_memory().percent if hasattr(psutil, 'virtual_memory') else None,
            "cpu_usage": psutil.cpu_percent() if hasattr(psutil, 'cpu_percent') else None,
            "working_directory": str(Path.cwd()),
            "command_line": " ".join(sys.argv)
        }
    
    def _log_error(self, error_report: ErrorReport) -> None:
        """Log error with appropriate level"""
        log_message = f"[{error_report.error_id}] {error_report.message}"
        
        if error_report.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_report.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_report.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
        
        # Log stack trace for high severity errors
        if error_report.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.debug(f"Stack trace: {error_report.stack_trace}")
    
    def _save_error_report(self, error_report: ErrorReport) -> None:
        """Save error report to file"""
        try:
            report_file = self.reports_dir / f"{error_report.error_id}.json"
            
            # Convert datetime to string for JSON serialization
            report_data = {
                "error_id": error_report.error_id,
                "timestamp": error_report.timestamp.isoformat(),
                "error_type": error_report.error_type,
                "message": error_report.message,
                "severity": error_report.severity.value,
                "category": error_report.category.value,
                "context": {
                    "file_path": error_report.context.file_path,
                    "line_number": error_report.context.line_number,
                    "function_name": error_report.context.function_name,
                    "component": error_report.context.component,
                    "operation": error_report.context.operation,
                    "user_input": error_report.context.user_input,
                    "system_info": error_report.context.system_info
                },
                "stack_trace": error_report.stack_trace,
                "suggestions": error_report.suggestions,
                "recovery_action": error_report.recovery_action,
                "metadata": error_report.metadata
            }
            
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            self.logger.debug(f"Error report saved to: {report_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save error report: {e}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of all errors"""
        if not self.error_reports:
            return {"total_errors": 0}
        
        severity_counts = {}
        category_counts = {}
        
        for report in self.error_reports:
            severity_counts[report.severity.value] = severity_counts.get(report.severity.value, 0) + 1
            category_counts[report.category.value] = category_counts.get(report.category.value, 0) + 1
        
        return {
            "total_errors": len(self.error_reports),
            "severity_distribution": severity_counts,
            "category_distribution": category_counts,
            "latest_error": self.error_reports[-1].error_id if self.error_reports else None
        }
    
    def clear_errors(self) -> None:
        """Clear all stored error reports"""
        self.error_reports.clear()
        self.error_count = 0
        self.logger.info("Error reports cleared")


def create_error_context(
    file_path: Optional[str] = None,
    line_number: Optional[int] = None,
    function_name: Optional[str] = None,
    component: Optional[str] = None,
    operation: Optional[str] = None,
    user_input: Optional[str] = None
) -> ErrorContext:
    """Helper function to create error context"""
    return ErrorContext(
        file_path=file_path,
        line_number=line_number,
        function_name=function_name,
        component=component,
        operation=operation,
        user_input=user_input
    ) 