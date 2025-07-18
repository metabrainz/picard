# -*- coding: utf-8 -*-
"""
Enhanced Error Handling System for Picard

Provides better error reporting, recovery mechanisms, and user guidance.
"""

import traceback
from contextlib import contextmanager
from enum import Enum
from pathlib import Path

from picard import log


class ErrorSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PicardError(Exception):
    """Base class for all Picard-specific errors."""
    
    def __init__(self, message, severity=ErrorSeverity.ERROR, context=None, 
                 recovery_suggestion=None, error_code=None):
        super().__init__(message)
        self.severity = severity
        self.context = context or {}
        self.recovery_suggestion = recovery_suggestion
        self.error_code = error_code


class FileProcessingError(PicardError):
    """Error during file processing operations."""
    pass


class PluginError(PicardError):
    """Error related to plugin operations."""
    pass


class NetworkError(PicardError):
    """Network-related errors."""
    pass


class ErrorReporter:
    """Advanced error reporting and recovery system."""
    
    def __init__(self):
        self.error_history = []
        self.recovery_attempts = {}
    
    @contextmanager
    def error_context(self, operation, **context):
        """Context manager for enhanced error reporting."""
        try:
            yield
        except Exception as e:
            enhanced_error = self._enhance_error(e, operation, context)
            self._log_error(enhanced_error)
            self._suggest_recovery(enhanced_error)
            raise enhanced_error from e
    
    def _enhance_error(self, original_error, operation, context):
        """Enhance an error with additional context and suggestions."""
        error_message = f"Error during {operation}: {str(original_error)}"
        
        # Determine severity based on error type
        if isinstance(original_error, (FileNotFoundError, PermissionError)):
            severity = ErrorSeverity.ERROR
            recovery = self._get_file_error_recovery(original_error, context)
        elif isinstance(original_error, (ConnectionError, TimeoutError)):
            severity = ErrorSeverity.WARNING
            recovery = "Check your internet connection and try again"
        else:
            severity = ErrorSeverity.ERROR
            recovery = "Please check the error details and try again"
        
        return PicardError(
            error_message,
            severity=severity,
            context=context,
            recovery_suggestion=recovery,
            error_code=self._generate_error_code(original_error, operation)
        )
    
    def _get_file_error_recovery(self, error, context):
        """Get recovery suggestions for file-related errors."""
        if isinstance(error, FileNotFoundError):
            return "Ensure the file exists and the path is correct"
        elif isinstance(error, PermissionError):
            return "Check file permissions and ensure Picard has read/write access"
        else:
            return "Check file integrity and try again"
    
    def _generate_error_code(self, error, operation):
        """Generate a unique error code for easier support."""
        error_type = type(error).__name__
        operation_hash = hash(operation) % 10000
        return f"PIC-{error_type[:3].upper()}-{operation_hash:04d}"
    
    def _log_error(self, error):
        """Log the error with appropriate severity."""
        log_func = {
            ErrorSeverity.INFO: log.info,
            ErrorSeverity.WARNING: log.warning,
            ErrorSeverity.ERROR: log.error,
            ErrorSeverity.CRITICAL: log.error
        }.get(error.severity, log.error)
        
        log_func(f"[{error.error_code}] {error}")
        if error.context:
            log.debug(f"Error context: {error.context}")
        if error.recovery_suggestion:
            log.info(f"Recovery suggestion: {error.recovery_suggestion}")
    
    def _suggest_recovery(self, error):
        """Suggest recovery actions to the user."""
        if error.recovery_suggestion:
            log.info(f"💡 Suggestion: {error.recovery_suggestion}")


# Global instance
error_reporter = ErrorReporter()


# Decorator for easy error handling
def handle_errors(operation_name):
    """Decorator to add enhanced error handling to functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with error_reporter.error_context(operation_name, 
                                            function=func.__name__,
                                            args_count=len(args)):
                return func(*args, **kwargs)
        return wrapper
    return decorator
