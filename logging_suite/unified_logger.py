# logging_suite/unified_logger.py - Enhanced Unified Logger with Configuration Management
"""
Unified logger interface that provides consistent API across all backends
ENHANCED: Added configuration management and inheritance capabilities
"""

from typing import Any, Dict, Union, Optional, TYPE_CHECKING
import json
import inspect
import sys

# Use TYPE_CHECKING to avoid circular imports
if TYPE_CHECKING:
    from .factory import LoggerFactory
    from .processors import LogEntryProcessor

# Enhanced exception handling (with fallback)
try:
    from .exceptions import (
        get_unified_caller_context,
        get_exception_context,
        create_exception_handler_for_backend
    )

    HAS_ENHANCED_EXCEPTIONS = True
except ImportError:
    HAS_ENHANCED_EXCEPTIONS = False

# Logger configuration registry for per-logger config overrides
_logger_configs: Dict[str, Dict[str, Any]] = {}


class UnifiedLogger:
    """
    Unified logger that provides a consistent interface across different backends.
    ENHANCED: Added configuration management and inheritance capabilities
    """

    def __init__(self, raw_logger: Any, backend: 'LoggingBackend', config: Dict[str, Any] = None):
        self._raw_logger = raw_logger
        self._backend = backend
        self._context: Dict[str, Any] = {}
        self._processor = None  # Optional log processor
        self._config = config or {}  # Store config passed from factory
        self._logger_name = getattr(raw_logger, 'name', 'unknown')

        # Exception handler setup
        self._exception_handler = None
        self._setup_exception_handler()

    def _setup_exception_handler(self):
        """Setup backend-aware exception handler"""
        if not HAS_ENHANCED_EXCEPTIONS:
            return

        try:
            backend_name = self._backend.get_backend_name()
            self._exception_handler = create_exception_handler_for_backend(backend_name, self._config)
        except Exception:
            # Exception enhancement setup failed, continue without it
            pass

    def set_processor(self, processor):
        """Set a log processor for this logger instance"""
        try:
            from .processors import LogEntryProcessor
            if isinstance(processor, LogEntryProcessor):
                self._processor = processor
        except ImportError:
            # Processors module not available
            pass

    def set_config(self, new_config: Dict[str, Any], merge: bool = True) -> 'UnifiedLogger':
        """
        Set configuration for this logger instance and recreate it

        Args:
            new_config: New configuration dictionary
            merge: Whether to merge with existing config (True) or replace entirely (False)

        Returns:
            New UnifiedLogger instance with updated configuration
        """
        # Import here to avoid circular imports
        from .factory import LoggerFactory

        if merge:
            # Merge new config with existing config
            effective_config = {**self._config, **new_config}
        else:
            # Replace config entirely
            effective_config = new_config.copy()

        # Store the per-logger config override
        _logger_configs[self._logger_name] = effective_config

        # Create new logger instance with updated config
        new_logger = LoggerFactory.create_logger(self._logger_name, config=effective_config)

        # Preserve existing context and processor
        new_logger._context = self._context.copy()
        if self._processor:
            new_logger.set_processor(self._processor)

        return new_logger

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration for this logger"""
        return self._config.copy()

    def reset_config(self) -> 'UnifiedLogger':
        """
        Reset logger configuration to global defaults

        Returns:
            New UnifiedLogger instance with global configuration
        """
        # Remove any per-logger config override
        if self._logger_name in _logger_configs:
            del _logger_configs[self._logger_name]

        # Import here to avoid circular imports
        from .factory import LoggerFactory
        from .config import get_effective_config

        # Get fresh global config
        global_config = get_effective_config()

        # Create new logger instance with global config
        new_logger = LoggerFactory.create_logger(self._logger_name, config=global_config)

        # Preserve existing context and processor
        new_logger._context = self._context.copy()
        if self._processor:
            new_logger.set_processor(self._processor)

        return new_logger

    def _should_use_pretty_json(self) -> bool:
        """Determine if we should use pretty JSON formatting based on configuration"""
        return (self._config.get('pretty_json', False) and
                self._config.get('level') == 'DEBUG')

    def _get_unified_caller_context(self, skip_frames: int = 2) -> Dict[str, Any]:
        """
        Get unified caller context using the enhanced exception system
        FIXED: Uses stored config instead of importing
        """
        if not HAS_ENHANCED_EXCEPTIONS:
            # Fallback to basic context
            return self._get_basic_caller_context(skip_frames)

        try:
            return get_unified_caller_context(
                skip_frames=skip_frames + 1,
                config=self._config
            )
        except Exception:
            return {}

    def _get_basic_caller_context(self, skip_frames: int = 2) -> Dict[str, Any]:
        """
        Fallback caller context detection (if enhanced exceptions not available)
        """
        try:
            frame = inspect.currentframe()

            # Skip the specified number of frames
            for _ in range(skip_frames):
                if frame is None:
                    break
                frame = frame.f_back

            if frame is None:
                return {}

            code = frame.f_code
            return {
                'caller_function': code.co_name,
                'caller_module': frame.f_globals.get('__name__', 'unknown'),
                'caller_file': code.co_filename.split('/')[-1] if code.co_filename else 'unknown',
                'caller_line': frame.f_lineno
            }

        except Exception:
            return {}

    def _format_message_with_context(self, message: str, **kwargs) -> str:
        """Format message with context for backends that don't support kwargs"""
        if not kwargs and not self._context:
            return message

        all_context = {**self._context, **kwargs}

        if self._backend.supports_context_binding():
            # Backend supports structured logging, don't modify message
            return message
        else:
            # Backend doesn't support structured logging, embed context in message
            if all_context:
                # Use pretty JSON formatting if configured for development
                if self._should_use_pretty_json():
                    context_str = json.dumps(all_context, default=str, indent=2, separators=(', ', ': '))
                    return f"{message}\nContext:\n{context_str}"
                else:
                    # Compact JSON with proper spacing for readability
                    context_str = json.dumps(all_context, default=str, separators=(', ', ': '))
                    return f"{message} | Context: {context_str}"
            return message

    def _process_log_data(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process log data through configured processor if available"""
        if self._processor:
            try:
                log_data = self._processor.process_entry(log_data)
            except Exception as e:
                # Don't let processing errors break logging
                log_data['_processing_error'] = str(e)

        return log_data

    def _sanitize_extra_for_logging(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize context data to avoid conflicts with LogRecord attributes
        FIXED: This prevents the "Attempt to overwrite 'module' in LogRecord" error
        """
        # LogRecord reserved attributes that we must not override
        reserved_attributes = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
            'thread', 'threadName', 'processName', 'process', 'getMessage',
            'exc_info', 'exc_text', 'stack_info', 'message', 'asctime'
        }

        sanitized = {}
        for key, value in context.items():
            if key in reserved_attributes:
                # Prefix reserved attributes to avoid conflicts
                sanitized[f'ctx_{key}'] = value
            else:
                sanitized[key] = value

        return sanitized

    def _log_with_backend(self, level: str, message: str, **kwargs):
        """
        Log using the appropriate backend method with unified processing and formatting
        FIXED: Uses stored config instead of importing
        """
        backend_name = self._backend.get_backend_name()

        # Get unified caller context
        caller_context = self._get_unified_caller_context(skip_frames=3)

        # Step 1: Process log data through processors
        log_data = {
            'level': level.upper(),
            'message': message,
            'logger': getattr(self._raw_logger, 'name', 'unknown'),
            'context': {**self._context, **kwargs, **caller_context},
            'backend': backend_name
        }

        if self._processor:
            try:
                log_data = self._processor.process_entry(log_data)
                # Update message and context from processed data
                message = log_data.get('message', message)
                processed_context = log_data.get('context', {})
                # Merge processed context back
                kwargs = {**kwargs, **processed_context}
            except Exception as e:
                # Don't let processing errors break logging
                kwargs['_processing_error'] = str(e)

        # Step 2: Apply unified formatting based on backend configuration
        all_context = {**self._context, **kwargs, **caller_context}

        if backend_name == 'structlog':
            # Structlog supports keyword arguments natively
            log_method = getattr(self._raw_logger, level.lower())
            log_method(message, **all_context)

        elif backend_name == 'loguru':
            # Loguru supports bind() for context
            logger = self._raw_logger
            if all_context:
                logger = logger.bind(**all_context)
            log_method = getattr(logger, level.lower())
            log_method(message)

        else:  # standard logging
            # Standard logging - sanitize context to avoid LogRecord conflicts
            log_method = getattr(self._raw_logger, level.lower())

            if all_context:
                # FIXED: Sanitize context to prevent LogRecord attribute conflicts
                sanitized_context = self._sanitize_extra_for_logging(all_context)
                log_method(message, extra=sanitized_context)
            else:
                log_method(message)

    def bind(self, **context) -> 'UnifiedLogger':
        """Bind context to create a new logger with additional context"""
        if self._backend.supports_context_binding():
            # Backend supports binding, use it directly
            backend_name = self._backend.get_backend_name()

            if backend_name == 'structlog':
                new_raw_logger = self._raw_logger.bind(**context)
                new_logger = UnifiedLogger(new_raw_logger, self._backend, self._config)
                new_logger._processor = self._processor
                new_logger._exception_handler = self._exception_handler
                return new_logger

            elif backend_name == 'loguru':
                new_raw_logger = self._raw_logger.bind(**context)
                new_logger = UnifiedLogger(new_raw_logger, self._backend, self._config)
                new_logger._processor = self._processor
                new_logger._exception_handler = self._exception_handler
                return new_logger

        # For backends without binding support, store context internally
        new_logger = UnifiedLogger(self._raw_logger, self._backend, self._config)
        new_logger._context = {**self._context, **context}
        new_logger._processor = self._processor
        new_logger._exception_handler = self._exception_handler
        new_logger._logger_name = self._logger_name
        return new_logger

    # Logging methods with consistent API
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log_with_backend('debug', message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log_with_backend('info', message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log_with_backend('warning', message, **kwargs)

    def warn(self, message: str, **kwargs):
        """Alias for warning"""
        self.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log_with_backend('error', message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log_with_backend('critical', message, **kwargs)

    def exception(self, message: str, **kwargs):
        """
        Log exception with enhanced traceback and context
        FIXED: Uses stored config instead of importing
        """
        exc_info = kwargs.pop('exc_info', True)

        # Get current exception info if not provided
        if exc_info is True:
            exc_info = sys.exc_info()

        # Use exception handler if available
        if self._exception_handler and HAS_ENHANCED_EXCEPTIONS:
            try:
                # Get enhanced exception context
                exception_context = self._exception_handler.get_exception_context(exc_info)

                # Add to kwargs
                kwargs.update(exception_context)

                # Check if we should let the backend handle enhanced formatting
                if self._exception_handler.should_process_exception():
                    # Format enhanced exception
                    enhanced_message = self._exception_handler.format_exception(
                        exc_info=exc_info,
                        message=message,
                        logger_context=kwargs
                    )

                    if enhanced_message:
                        # Use enhanced formatting
                        self._log_with_backend('error', enhanced_message, **kwargs)
                        return

            except Exception:
                # Don't let exception enhancement break exception logging
                pass

        # Fallback to standard exception logging
        if self._backend.get_backend_name() == 'standard':
            kwargs['exc_info'] = exc_info

        self._log_with_backend('error', message, **kwargs)

    # Enhanced styling and formatting methods
    def with_style(self, **style_options) -> 'UnifiedLogger':
        """Create a new logger instance with specific styling options"""
        new_logger = UnifiedLogger(self._raw_logger, self._backend, self._config)
        new_logger._context = self._context.copy()
        new_logger._processor = self._processor
        new_logger._exception_handler = self._exception_handler
        new_logger._logger_name = self._logger_name

        # Store style preferences in context for formatters to use
        style_context = {f'_style_{k}': v for k, v in style_options.items()}
        new_logger._context.update(style_context)

        return new_logger

    def highlight(self, message: str, **kwargs) -> 'UnifiedLogger':
        """Log with highlighting (useful for important messages)"""
        kwargs['_highlight'] = True
        self.info(message, **kwargs)
        return self

    def performance(self, message: str, execution_time: float, **kwargs) -> 'UnifiedLogger':
        """Log performance information with proper categorization"""
        kwargs.update({
            'execution_time_seconds': execution_time,
            'execution_time_ms': execution_time * 1000,
            'performance_log': True
        })

        # Choose appropriate level based on execution time
        if execution_time > 5.0:
            self.warning(message, **kwargs)
        elif execution_time > 1.0:
            self.info(message, **kwargs)
        else:
            self.debug(message, **kwargs)

        return self

    @property
    def raw_logger(self):
        """Access to the underlying raw logger if needed"""
        return self._raw_logger

    @property
    def backend_name(self) -> str:
        """Get the name of the backend being used"""
        return self._backend.get_backend_name()

    @property
    def context(self) -> Dict[str, Any]:
        """Get current context"""
        return self._context.copy()

    @property
    def processor(self):
        """Get current processor"""
        return self._processor

    @property
    def exception_handler(self):
        """Get current exception handler"""
        return self._exception_handler

    @property
    def config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self._config.copy()

    @property
    def name(self) -> str:
        """Get logger name"""
        return self._logger_name

    def __del__(self):
        """Ensure proper cleanup of resources when the logger is garbage collected"""
        try:
            # Close any handlers associated with this logger
            if hasattr(self, '_raw_logger') and hasattr(self._raw_logger, 'handlers'):
                for handler in list(self._raw_logger.handlers):
                    try:
                        handler.flush()
                        handler.close()
                    except Exception:
                        pass
        except Exception:
            pass  # Never let destructor throw exceptions


# =============================================================================
# GLOBAL LOGGER CONFIGURATION MANAGEMENT
# =============================================================================

def set_logger_config(logger_name: str, config: Dict[str, Any], merge: bool = True) -> None:
    """
    Set configuration for a specific logger by name

    Args:
        logger_name: Name of the logger to configure
        config: Configuration dictionary
        merge: Whether to merge with existing config (True) or replace entirely (False)
    """
    if merge and logger_name in _logger_configs:
        # Merge with existing per-logger config
        _logger_configs[logger_name] = {**_logger_configs[logger_name], **config}
    else:
        # Set new config (potentially replacing existing)
        _logger_configs[logger_name] = config.copy()


def get_logger_config(logger_name: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific logger by name

    Args:
        logger_name: Name of the logger

    Returns:
        Configuration dictionary or None if no override exists
    """
    return _logger_configs.get(logger_name)


def clear_logger_config(logger_name: str) -> bool:
    """
    Clear configuration override for a specific logger

    Args:
        logger_name: Name of the logger

    Returns:
        True if config was cleared, False if no config existed
    """
    if logger_name in _logger_configs:
        del _logger_configs[logger_name]
        return True
    return False


def get_all_logger_configs() -> Dict[str, Dict[str, Any]]:
    """
    Get all per-logger configuration overrides

    Returns:
        Dictionary mapping logger names to their configurations
    """
    return _logger_configs.copy()


def clear_all_logger_configs() -> None:
    """Clear all per-logger configuration overrides"""
    _logger_configs.clear()


def get_effective_logger_config(logger_name: str) -> Dict[str, Any]:
    """
    Get the effective configuration for a logger (global + per-logger overrides)

    Args:
        logger_name: Name of the logger

    Returns:
        Effective configuration dictionary
    """
    from .config import get_effective_config

    # Start with global config
    effective_config = get_effective_config()

    # Apply per-logger override if it exists
    logger_override = _logger_configs.get(logger_name)
    if logger_override:
        effective_config.update(logger_override)

    return effective_config


# Enhanced factory for creating loggers with styling support
def create_styled_logger(name: str,
                         style_preset: str = 'development',
                         config: Dict[str, Any] = None) -> UnifiedLogger:
    """
    Create a UnifiedLogger with predefined styling configuration
    ENHANCED: Now respects per-logger config overrides
    """
    from .factory import LoggerFactory

    # Get effective config including any per-logger overrides
    effective_config = get_effective_logger_config(name)

    # Merge with provided config
    if config:
        effective_config.update(config)

    # Create base logger with effective config
    logger = LoggerFactory.create_logger(name, config=effective_config)

    # Apply processor based on preset
    if style_preset == 'development':
        try:
            from .processors import DefaultProcessors
            processor = DefaultProcessors.create_development_processor()
            logger.set_processor(processor)
        except ImportError:
            pass  # Processors not available

    elif style_preset == 'production':
        try:
            from .processors import DefaultProcessors
            processor = DefaultProcessors.create_production_processor()
            logger.set_processor(processor)
        except ImportError:
            pass  # Processors not available

    return logger


__all__ = [
    'UnifiedLogger',
    'create_styled_logger',
    'set_logger_config',
    'get_logger_config',
    'clear_logger_config',
    'get_all_logger_configs',
    'clear_all_logger_configs',
    'get_effective_logger_config'
]