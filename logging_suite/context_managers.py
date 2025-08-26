# logging_suite/context_managers.py
"""
Context managers for temporary logging configuration and execution tracking
"""

import time
import logging
from typing import Dict, Any, Optional, Union, ContextManager
from contextlib import contextmanager
from .factory import LoggerFactory
from .unified_logger import UnifiedLogger


class log_execution_context:
    """
    Context manager for logging execution of code blocks with timing and error handling
    """

    def __init__(self,
                 logger: Union[str, UnifiedLogger] = None,
                 message: str = "Executing code block",
                 level: str = 'info',
                 include_timing: bool = True,
                 include_result: bool = False,
                 log_entry: bool = True,
                 log_exit: bool = True,
                 log_errors: bool = True,
                 **context):
        """
        Initialize execution context manager

        Args:
            logger: Logger instance or name
            message: Message to log
            level: Log level
            include_timing: Whether to include execution timing
            include_result: Whether to include block result in exit log
            log_entry: Whether to log block entry
            log_exit: Whether to log block exit
            log_errors: Whether to log exceptions
            **context: Additional context to include in logs
        """
        self.message = message
        self.level = level.lower()
        self.include_timing = include_timing
        self.include_result = include_result
        self.log_entry = log_entry
        self.log_exit = log_exit
        self.log_errors = log_errors
        self.context = context

        # Initialize logger
        if isinstance(logger, UnifiedLogger):
            self.logger = logger
        elif isinstance(logger, str):
            self.logger = LoggerFactory.create_logger(logger)
        else:
            self.logger = LoggerFactory.create_logger('execution_context')

        # Runtime state
        self.start_time = None
        self.result = None
        self.exception = None

    def __enter__(self):
        """Enter the execution context"""
        self.start_time = time.time()

        if self.log_entry:
            log_method = getattr(self.logger, self.level)
            log_method(
                f"Starting: {self.message}",
                action="context_enter",
                **self.context
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the execution context"""
        execution_time = time.time() - self.start_time if self.start_time else 0

        # Handle exceptions
        if exc_type is not None:
            self.exception = {
                'type': exc_type.__name__,
                'message': str(exc_val),
                'traceback': exc_tb
            }

            if self.log_errors:
                error_context = {
                    'action': 'context_error',
                    'execution_time_seconds': execution_time,
                    'exception_type': exc_type.__name__,
                    'exception_message': str(exc_val),
                    **self.context
                }

                self.logger.error(
                    f"Error in: {self.message}",
                    **error_context
                )

        # Log successful completion
        elif self.log_exit:
            exit_context = {
                'action': 'context_exit',
                'success': True,
                **self.context
            }

            if self.include_timing:
                exit_context.update({
                    'execution_time_seconds': execution_time,
                    'execution_time_ms': execution_time * 1000
                })

            if self.include_result and self.result is not None:
                exit_context['result'] = str(self.result)[:200]  # Truncate result

            log_method = getattr(self.logger, self.level)
            timing_info = f" in {execution_time:.3f}s" if self.include_timing else ""
            log_method(
                f"Completed: {self.message}{timing_info}",
                **exit_context
            )

        # Don't suppress exceptions
        return False

    def set_result(self, result):
        """Set the result to be logged on exit"""
        self.result = result
        return result


class temporary_log_level:
    """
    Context manager for temporarily changing log level
    """

    def __init__(self,
                 logger: Union[str, UnifiedLogger, logging.Logger],
                 level: str,
                 restore_on_exit: bool = True):
        """
        Initialize temporary log level context

        Args:
            logger: Logger instance, name, or standard logger
            level: Temporary log level
            restore_on_exit: Whether to restore original level on exit
        """
        self.level = level.upper()
        self.restore_on_exit = restore_on_exit
        self.original_level = None

        # Handle different logger types
        if isinstance(logger, str):
            self.logger = LoggerFactory.create_logger(logger)
            self.logger_type = 'unified'
        elif isinstance(logger, UnifiedLogger):
            self.logger = logger
            self.logger_type = 'unified'
        elif isinstance(logger, logging.Logger):
            self.logger = logger
            self.logger_type = 'standard'
        else:
            raise ValueError(f"Unsupported logger type: {type(logger)}")

    def __enter__(self):
        """Enter temporary log level context"""
        # Store original level
        if self.logger_type == 'unified':
            # For UnifiedLogger, work with the raw logger
            raw_logger = getattr(self.logger, '_raw_logger', None)
            if raw_logger and hasattr(raw_logger, 'level'):
                self.original_level = raw_logger.level
            elif raw_logger and hasattr(raw_logger, 'getEffectiveLevel'):
                self.original_level = raw_logger.getEffectiveLevel()
        else:
            # For standard logger
            self.original_level = self.logger.level

        # Set new level
        try:
            if self.logger_type == 'unified':
                raw_logger = getattr(self.logger, '_raw_logger', None)
                if raw_logger and hasattr(raw_logger, 'setLevel'):
                    raw_logger.setLevel(getattr(logging, self.level))
            else:
                self.logger.setLevel(getattr(logging, self.level))
        except AttributeError:
            # Some loggers might not support level setting
            pass

        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit temporary log level context"""
        if self.restore_on_exit and self.original_level is not None:
            try:
                if self.logger_type == 'unified':
                    raw_logger = getattr(self.logger, '_raw_logger', None)
                    if raw_logger and hasattr(raw_logger, 'setLevel'):
                        raw_logger.setLevel(self.original_level)
                else:
                    self.logger.setLevel(self.original_level)
            except AttributeError:
                pass

        return False


class temporary_logger_context:
    """
    Context manager for temporarily adding context to a logger
    """

    def __init__(self, logger: UnifiedLogger, **context):
        """
        Initialize temporary context manager

        Args:
            logger: UnifiedLogger instance
            **context: Context to temporarily add
        """
        self.logger = logger
        self.context = context
        self.bound_logger = None

    def __enter__(self):
        """Enter temporary context"""
        self.bound_logger = self.logger.bind(**self.context)
        return self.bound_logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit temporary context"""
        # Context is automatically removed when bound logger goes out of scope
        return False


class log_performance:
    """
    Context manager for performance monitoring and logging
    """

    def __init__(self,
                 logger: Union[str, UnifiedLogger] = None,
                 operation_name: str = "operation",
                 level: str = 'info',
                 threshold_seconds: float = 1.0,
                 log_memory: bool = False,
                 **context):
        """
        Initialize performance logging context

        Args:
            logger: Logger instance or name
            operation_name: Name of the operation being monitored
            level: Log level for performance logs
            threshold_seconds: Only log if execution time exceeds this
            log_memory: Whether to include memory usage information
            **context: Additional context
        """
        self.operation_name = operation_name
        self.level = level.lower()
        self.threshold_seconds = threshold_seconds
        self.log_memory = log_memory
        self.context = context

        # Initialize logger
        if isinstance(logger, UnifiedLogger):
            self.logger = logger
        elif isinstance(logger, str):
            self.logger = LoggerFactory.create_logger(logger)
        else:
            self.logger = LoggerFactory.create_logger('performance')

        # Performance tracking
        self.start_time = None
        self.start_memory = None

    def __enter__(self):
        """Enter performance monitoring context"""
        self.start_time = time.time()

        if self.log_memory:
            try:
                from .utils import get_memory_usage
                self.start_memory = get_memory_usage()
            except ImportError:
                self.start_memory = None

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit performance monitoring context"""
        if self.start_time is None:
            return False

        execution_time = time.time() - self.start_time

        # Only log if threshold is met
        if execution_time >= self.threshold_seconds:
            perf_context = {
                'operation': self.operation_name,
                'execution_time_seconds': round(execution_time, 4),
                'execution_time_ms': round(execution_time * 1000, 2),
                'threshold_seconds': self.threshold_seconds,
                'performance_log': True,
                **self.context
            }

            # Add memory information if available
            if self.log_memory and self.start_memory:
                try:
                    from .utils import get_memory_usage
                    end_memory = get_memory_usage()
                    if 'rss_mb' in self.start_memory and 'rss_mb' in end_memory:
                        perf_context['memory_delta_mb'] = round(
                            end_memory['rss_mb'] - self.start_memory['rss_mb'], 2
                        )
                        perf_context['memory_end_mb'] = round(end_memory['rss_mb'], 2)
                except Exception:
                    pass

            # Determine log level based on execution time
            if execution_time > self.threshold_seconds * 5:
                log_level = 'warning'
                perf_context['slow_operation'] = True
            elif execution_time > self.threshold_seconds * 2:
                log_level = 'info'
                perf_context['moderate_operation'] = True
            else:
                log_level = self.level

            log_method = getattr(self.logger, log_level)
            log_method(
                f"Performance: {self.operation_name} completed in {execution_time:.3f}s",
                **perf_context
            )

        return False


# Convenience context manager functions
@contextmanager
def timed_operation(operation_name: str,
                    logger: Union[str, UnifiedLogger] = None,
                    level: str = 'info'):
    """
    Simple context manager for timing operations

    Args:
        operation_name: Name of the operation
        logger: Logger instance or name
        level: Log level

    Example:
        with timed_operation("database_query", logger):
            result = db.query("SELECT * FROM users")
    """
    with log_execution_context(
            logger=logger,
            message=operation_name,
            level=level,
            include_timing=True
    ) as ctx:
        yield ctx


@contextmanager
def error_handling(operation_name: str,
                   logger: Union[str, UnifiedLogger] = None,
                   reraise: bool = True,
                   default_return=None):
    """
    Context manager for error handling and logging

    Args:
        operation_name: Name of the operation
        logger: Logger instance or name
        reraise: Whether to reraise exceptions
        default_return: Value to return if exception occurs and reraise=False

    Example:
        with error_handling("api_call", logger, reraise=False) as handler:
            result = make_api_call()
            handler.set_result(result)
    """
    with log_execution_context(
            logger=logger,
            message=operation_name,
            level='info',
            log_errors=True
    ) as ctx:
        try:
            yield ctx
        except Exception as e:
            if not reraise:
                ctx.set_result(default_return)
                return default_return
            raise


# Export all context managers
__all__ = [
    'log_execution_context',
    'temporary_log_level',
    'temporary_logger_context',
    'log_performance',
    'timed_operation',
    'error_handling'
]