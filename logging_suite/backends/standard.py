# logging_suite/backends/standard.py - Fixed Standard Backend
"""
Standard library logging backend implementation with unified formatting
FIXED: Console format logic - format setting now takes precedence over use_json_handlers
"""

import logging
import sys
from typing import Any, Dict
from pathlib import Path

from .base import LoggingBackend
from ..unified_logger import UnifiedLogger

# Enhanced exception handling (with fallback)
try:
    from ..exceptions import create_exception_handler_for_backend
    HAS_ENHANCED_EXCEPTIONS = True
except ImportError:
    HAS_ENHANCED_EXCEPTIONS = False


class SafeLoggingFormatter(logging.Formatter):
    """
    Formatter that handles extra context safely without LogRecord conflicts
    FIXED: No circular imports - gets config as parameter
    """

    def __init__(self, backend_config: Dict[str, Any] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # LogRecord reserved attributes that we must not override
        self.reserved_attributes = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
            'thread', 'threadName', 'processName', 'process', 'getMessage',
            'exc_info', 'exc_text', 'stack_info', 'message', 'asctime'
        }

        # Setup exception handler for this formatter
        self.exception_handler = None
        if HAS_ENHANCED_EXCEPTIONS and backend_config:
            try:
                self.exception_handler = create_exception_handler_for_backend('standard', backend_config)
            except Exception:
                pass

    def format(self, record):
        """Format the record, handling extra attributes safely and enhanced exceptions"""
        # Store original attributes
        original_dict = record.__dict__.copy()

        # Handle exceptions with new system
        if record.exc_info and self.exception_handler:
            try:
                if self.exception_handler.should_process_exception():
                    # Get enhanced exception formatting
                    enhanced_message = self.exception_handler.format_exception(
                        exc_info=record.exc_info,
                        message=record.getMessage(),
                        logger_context=self._extract_logger_context(record)
                    )

                    if enhanced_message:
                        # Replace the record message with enhanced version
                        record.msg = enhanced_message
                        record.args = ()  # Clear args since we've formatted the message
                        # Don't include exc_info in standard formatting since we handled it
                        record.exc_info = None
                        record.exc_text = None
            except Exception:
                # Fall back to standard exception handling if enhancement fails
                pass

        # Temporarily remove conflicting attributes from extra
        conflicting_attrs = {}
        for attr_name in list(record.__dict__.keys()):
            if attr_name in self.reserved_attributes and attr_name in ['module', 'filename', 'funcName']:
                # These are commonly overwritten by context - preserve originals
                if hasattr(record, f'_original_{attr_name}'):
                    continue  # Already handled
                # Store original and rename the extra one
                setattr(record, f'_original_{attr_name}', getattr(record, attr_name))
                if attr_name in record.__dict__:
                    conflicting_attrs[f'ctx_{attr_name}'] = record.__dict__.pop(attr_name)

        # Add back as safe context
        for safe_name, value in conflicting_attrs.items():
            setattr(record, safe_name, value)

        try:
            # Format the record
            result = super().format(record)
        finally:
            # Restore original record state
            record.__dict__.clear()
            record.__dict__.update(original_dict)

        return result

    def _extract_logger_context(self, record) -> Dict[str, Any]:
        """Extract context from log record for exception handler"""
        context = {}
        for key, value in record.__dict__.items():
            if key not in self.reserved_attributes:
                context[key] = value
        return context


class StandardLoggingBackend(LoggingBackend):
    """Standard library logging backend using unified formatters and enhanced exceptions"""

    def create_logger(self, name: str, config: Dict[str, Any]) -> logging.Logger:
        """Create a standard library logger using unified formatters and enhanced exceptions"""
        logger = logging.getLogger(name)
        logger.handlers.clear()

        level = getattr(logging, config.get('level', 'INFO').upper())
        logger.setLevel(level)

        # Get unified formatters from renderer registry
        try:
            from ..renderer_registry import get_global_renderer_registry
            registry = get_global_renderer_registry()
        except ImportError:
            # Fallback to basic formatting if unified system not available
            return self._create_basic_logger(name, config)

        # Determine format type - FIXED: format setting takes precedence
        format_type = config.get('format', 'console')

        # File handler with unified formatting
        if 'file_path' in config:
            file_path = Path(config['file_path'])
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(config['file_path'])
            file_handler.setLevel(level)

            # Use unified file formatter with safe wrapper
            try:
                # For files, use JSON if explicitly configured or if format is json
                if format_type == 'json' or (format_type != 'console' and config.get('use_json_handlers', True)):
                    base_formatter = registry.get_renderer_for_backend('standard', 'json', config)
                else:
                    base_formatter = registry.get_renderer_for_backend('standard', 'file', config)

                # Wrap with safe formatter to handle conflicts and exceptions
                if hasattr(base_formatter, 'format'):
                    # Create a safe version that delegates to the unified formatter
                    class SafeUnifiedFormatter(SafeLoggingFormatter):
                        def __init__(self, base_fmt, backend_config):
                            super().__init__(backend_config)
                            self.base_formatter = base_fmt

                        def format(self, record):
                            # Let the safe formatter handle conflicts and exceptions first
                            super().format(record)  # This processes conflicts and exceptions
                            # Then delegate to the unified formatter
                            return self.base_formatter.format(record)

                    safe_formatter = SafeUnifiedFormatter(base_formatter, config)
                    file_handler.setFormatter(safe_formatter)
                else:
                    file_handler.setFormatter(base_formatter)

            except Exception:
                # Fallback formatter with exception handling
                fallback_formatter = SafeLoggingFormatter(
                    config,
                    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                file_handler.setFormatter(fallback_formatter)

            logger.addHandler(file_handler)

        # Console handler with unified formatting
        if config.get('console', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)

            # Use unified console formatter with safe wrapper
            try:
                # FIXED: Respect format setting - only use JSON if explicitly set to json
                if format_type == 'json':
                    base_formatter = registry.get_renderer_for_backend('standard', 'json', config)
                else:
                    # Use console formatter for any non-json format (console, etc.)
                    base_formatter = registry.get_renderer_for_backend('standard', 'console', config)

                # Wrap with safe formatter to handle conflicts and exceptions
                if hasattr(base_formatter, 'format'):
                    class SafeUnifiedFormatter(SafeLoggingFormatter):
                        def __init__(self, base_fmt, backend_config):
                            super().__init__(backend_config)
                            self.base_formatter = base_fmt

                        def format(self, record):
                            # Let the safe formatter handle conflicts and exceptions first
                            super().format(record)  # This processes conflicts and exceptions
                            # Then delegate to the unified formatter
                            return self.base_formatter.format(record)

                    safe_formatter = SafeUnifiedFormatter(base_formatter, config)
                    console_handler.setFormatter(safe_formatter)
                else:
                    console_handler.setFormatter(base_formatter)

            except Exception:
                # Fallback formatter with exception handling
                fallback_formatter = SafeLoggingFormatter(
                    config,
                    fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                console_handler.setFormatter(fallback_formatter)

            logger.addHandler(console_handler)

        # Custom handlers from config
        for handler in config.get('handlers', []):
            logger.addHandler(handler)

        return logger

    def _create_basic_logger(self, name: str, config: Dict[str, Any]) -> logging.Logger:
        """Fallback method for creating basic logger without unified system but with exception handling"""
        logger = logging.getLogger(name)
        logger.handlers.clear()

        level = getattr(logging, config.get('level', 'INFO').upper())
        logger.setLevel(level)

        # Use safe formatter for all basic logging with exception handling
        formatter = SafeLoggingFormatter(
            config,
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console handler
        if config.get('console', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # File handler
        if 'file_path' in config:
            file_path = Path(config['file_path'])
            file_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(config['file_path'])
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def create_unified_logger(self, name: str, config: Dict[str, Any]) -> UnifiedLogger:
        """Create a unified logger wrapper for standard logging with enhanced exceptions"""
        raw_logger = self.create_logger(name, config)
        unified_logger = UnifiedLogger(raw_logger, self, config)

        # Apply processor if configured
        processor_type = config.get('processor_type', 'development' if config.get('level') == 'DEBUG' else 'production')
        try:
            from ..processors import DefaultProcessors
            if processor_type == 'development':
                processor = DefaultProcessors.create_development_processor()
            else:
                processor = DefaultProcessors.create_production_processor()
            unified_logger.set_processor(processor)
        except ImportError:
            pass  # Processors not available

        return unified_logger

    def supports_context_binding(self) -> bool:
        """Standard logging doesn't natively support context binding"""
        return False

    def get_backend_name(self) -> str:
        """Get backend name"""
        return 'standard'

    def get_capabilities(self) -> Dict[str, bool]:
        """Get backend-specific capabilities"""
        return {
            'context_binding': False,
            'structured_logging': True,  # Via extra fields
            'file_logging': True,
            'console_logging': True,
            'safe_context_handling': True,  # Our enhancement
            'logrecord_conflict_resolution': True,  # Our enhancement
            'enhanced_exceptions': HAS_ENHANCED_EXCEPTIONS,
        }

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration for standard logging backend"""
        validation = super().validate_config(config)

        # Additional standard logging specific validation
        if 'handlers' in config:
            if not isinstance(config['handlers'], list):
                validation['errors'].append("'handlers' must be a list")
                validation['valid'] = False

        # Check for potentially problematic context keys
        if 'extra' in config:
            extra = config['extra']
            if isinstance(extra, dict):
                reserved = {'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                            'filename', 'module', 'lineno', 'funcName', 'created', 'msecs',
                            'relativeCreated', 'thread', 'threadName', 'processName', 'process'}

                conflicting_keys = set(extra.keys()) & reserved
                if conflicting_keys:
                    validation['warnings'].append(
                        f"Context keys {conflicting_keys} may conflict with LogRecord attributes. "
                        f"They will be automatically prefixed with 'ctx_' to avoid conflicts."
                    )

        # Validate exception handling configuration
        if HAS_ENHANCED_EXCEPTIONS:
            exception_keys = ['exception_diagnosis', 'exception_backtrace', 'exception_depth']
            for key in exception_keys:
                if key in config:
                    if key == 'exception_depth' and not isinstance(config[key], int):
                        validation['warnings'].append(f"'{key}' should be an integer")
                    elif key in ['exception_diagnosis', 'exception_backtrace']:
                        valid_values = [True, False, 'auto']
                        if config[key] not in valid_values:
                            validation['warnings'].append(f"'{key}' should be one of {valid_values}")

        return validation