# logging_suite/decorators.py - Enhanced Exception Integration
"""
Enhanced decorators with proper chaining, execution time tracking, and global tracing control
ENHANCED: Integrated with new unified exception handling system
"""

import functools
import time
import sys
import traceback
import inspect
from typing import Callable, Any, Optional, Union

# Direct imports now that circular dependencies are resolved
from .factory import LoggerFactory
from .unified_logger import UnifiedLogger
from .tracing import TraceManager

# ENHANCED: Import exception handling
try:
    from .exceptions import (
        get_unified_caller_context,
        get_exception_context,
        create_exception_handler_for_backend
    )

    HAS_ENHANCED_EXCEPTIONS = True
except ImportError:
    HAS_ENHANCED_EXCEPTIONS = False

# Import unified exception formatter for beautiful/pprint output
try:
    from .unified_exception_formatter import UnifiedExceptionFormatter
    HAS_UNIFIED_FORMATTER = True
except ImportError:
    HAS_UNIFIED_FORMATTER = False
    UnifiedExceptionFormatter = None


def _sanitize_data(data):
    """Sanitize sensitive data from logs using configurable sensitive keys"""
    # Get sensitive keys from global configuration
    try:
        from . import get_sensitive_keys
        sensitive_keys = set(key.lower() for key in get_sensitive_keys())
    except ImportError:
        # Fallback to default keys if global config not available
        sensitive_keys = {'password', 'token', 'key', 'secret', 'auth', 'credential'}

    if isinstance(data, dict):
        sanitized = {}
        for key, value in data.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = '***REDACTED***'
            else:
                sanitized[key] = _sanitize_data(value) if isinstance(value, (dict, list, tuple)) else value
        return sanitized
    elif isinstance(data, (list, tuple)):
        return [_sanitize_data(item) for item in data]
    else:
        return data


def catch_and_log(
        logger: Union[str, UnifiedLogger, None] = None,
        level: str = 'error',
        reraise: bool = True,
        default_return: Any = None,
        message: Optional[str] = None,
        exclude: tuple = (),
        include_args: bool = False,
        include_kwargs: bool = False,
        sanitize_sensitive: bool = True,
        log_execution_time: bool = None,  # None = check TraceManager
        timing_level: str = None,
        enhanced_exceptions: bool = None  # ENHANCED: Control exception enhancement
):
    """
    Exception logging decorator with optional execution time tracking.
    ENHANCED: Uses new unified exception handling system
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Determine timing behavior - explicit setting overrides TraceManager
            if log_execution_time is not None:
                actual_log_execution_time = log_execution_time
            else:
                should_trace = TraceManager.should_trace_function(func.__name__, func.__module__)
                actual_log_execution_time = should_trace

            # Get timing level from TraceManager if not set
            actual_timing_level = timing_level or TraceManager.get_trace_level()

            # Get or create logger
            if isinstance(logger, UnifiedLogger):
                log_instance = logger
            elif isinstance(logger, str):
                log_instance = LoggerFactory.create_logger(logger)
            else:
                logger_name = f"{func.__module__}.{func.__name__}"
                log_instance = LoggerFactory.create_logger(logger_name)

            # ENHANCED: Setup exception handler if available
            exception_handler = None
            if HAS_ENHANCED_EXCEPTIONS and (enhanced_exceptions is not False):
                try:
                    from . import get_global_config
                    config = get_global_config()
                    backend_name = log_instance.backend_name
                    exception_handler = create_exception_handler_for_backend(backend_name, config)
                except ImportError:
                    pass

            # Mark function as being traced (for recursion prevention) - only if using TraceManager
            should_trace_for_manager = TraceManager.should_trace_function(func.__name__, func.__module__)
            if should_trace_for_manager:
                TraceManager.enter_trace(func.__name__, func.__module__)

            start_time = time.time()

            try:
                # Execute function
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Log successful completion if timing is enabled
                should_log_timing = actual_log_execution_time
                if log_execution_time is None:
                    # Using TraceManager, check threshold
                    should_log_timing = should_log_timing and TraceManager.should_log_execution_time(execution_time)
                elif log_execution_time is True:
                    # Explicitly enabled, always log
                    should_log_timing = True

                if should_log_timing:
                    # ENHANCED: Use unified caller context
                    caller_context = {}
                    if HAS_ENHANCED_EXCEPTIONS:
                        try:
                            caller_context = get_unified_caller_context(skip_frames=2)
                        except Exception:
                            pass

                    completion_context = {
                        'execution_time_seconds': round(execution_time, 4),
                        'execution_time_ms': round(execution_time * 1000, 2),
                        'operation_success': True,
                        'timing_source': 'explicit' if log_execution_time is True else 'tracemanager',
                        **caller_context
                    }

                    # Add performance warning if execution is slow
                    performance_level = actual_timing_level
                    try:
                        if TraceManager.is_performance_warning(execution_time):
                            completion_context['performance_warning'] = True
                            performance_level = 'warning'
                    except:
                        pass

                    # Include function arguments if requested and safe
                    if include_args and args:
                        completion_context['function_args'] = _sanitize_data(args) if sanitize_sensitive else args
                    if include_kwargs and kwargs:
                        completion_context['function_kwargs'] = _sanitize_data(kwargs) if sanitize_sensitive else kwargs

                    # Ensure we have a valid log level
                    if not hasattr(log_instance, performance_level):
                        performance_level = 'info'

                    timing_log_method = getattr(log_instance, performance_level)
                    timing_log_method(
                        f"Function completed: {func.__name__} [{execution_time:.3f}s]",
                        **completion_context
                    )

                return result

            except BaseException as e:
                execution_time = time.time() - start_time

                # Check if this exception type should be excluded
                if exclude and isinstance(e, exclude):
                    if reraise:
                        raise
                    return default_return

                # ENHANCED: Use new exception handling system
                exc_info = sys.exc_info()
                context = {
                    'execution_time_seconds': round(execution_time, 4),
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'operation_success': False,
                    'failed_after_seconds': round(execution_time, 4),
                }

                # Add function arguments if requested
                if include_args and args:
                    context['function_args'] = _sanitize_data(args) if sanitize_sensitive else args
                if include_kwargs and kwargs:
                    context['function_kwargs'] = _sanitize_data(kwargs) if sanitize_sensitive else kwargs

                # ENHANCED: Get unified exception and caller context
                if HAS_ENHANCED_EXCEPTIONS and exception_handler:
                    try:
                        # Get comprehensive exception context
                        exception_context = exception_handler.get_exception_context(exc_info)
                        caller_context = exception_handler.get_caller_context(skip_frames=2)

                        # Combine contexts
                        unified_context = exception_handler.create_unified_context(
                            caller_context=caller_context,
                            exception_context=exception_context,
                            logger_context=context
                        )
                        context.update(unified_context)

                        # Use enhanced exception formatting if available
                        if exception_handler.should_process_exception():
                            # ENHANCED: Choose output style - either beautiful/pprint OR existing JSON format
                            console_style = config.get('console_output_style', 'beautiful')
                            
                            if console_style == 'beautiful' and HAS_UNIFIED_FORMATTER:
                                # Use beautiful formatting instead of JSON logging
                                try:
                                    formatter = UnifiedExceptionFormatter(config)
                                    console_output = formatter.format_for_console(
                                        exc_info=exc_info,
                                        context=unified_context,
                                        system_info=None
                                    )
                                    print("\n" + "="*60, file=sys.stderr)
                                    print(f"🎭 Enhanced Exception Output ({func.__name__})", file=sys.stderr)
                                    print("="*60, file=sys.stderr)
                                    print(console_output, file=sys.stderr)
                                    print("="*60 + "\n", file=sys.stderr)
                                    sys.stderr.flush()
                                except Exception:
                                    # Fallback to JSON if beautiful formatting fails
                                    console_style = 'pprint'
                            
                            if console_style == 'pprint' or console_style != 'beautiful':
                                # Use existing JSON logging format
                                error_message = exception_handler.format_exception(
                                    exc_info=exc_info,
                                    message=message or f"Exception in {func.__name__} after {execution_time:.3f}s: {str(e)}",
                                    logger_context=context
                                )

                                if error_message:
                                    log_method = getattr(log_instance, level)
                                    log_method(error_message, **context)

                            if reraise:
                                raise
                            else:
                                return default_return

                    except Exception:
                        # Fall back to basic exception handling if enhanced fails
                        pass

                # Fallback to basic exception logging
                error_message = message or f"Exception in {func.__name__} after {execution_time:.3f}s: {str(e)}"

                # Add basic exception info
                context.update({
                    'exception_type_name': type(e).__name__,
                    'exception_message_text': str(e),
                    TraceManager.get_exception_key(): True
                })

                # Log the exception
                log_method = getattr(log_instance, level)
                log_method(error_message, **context)

                # Decide whether to reraise or return default
                if reraise:
                    raise
                else:
                    return default_return

            finally:
                # Mark function as no longer being traced - only if we marked it
                if should_trace_for_manager:
                    TraceManager.exit_trace(func.__name__, func.__module__)

        return wrapper

    return decorator


# Simplified convenience aliases
def catch(reraise: bool = True, level: str = 'error', log_execution_time: bool = None):
    """Simple loguru-style exception decorator with optional execution time logging"""
    return catch_and_log(
        reraise=reraise,
        level=level,
        log_execution_time=log_execution_time
    )


def log_execution_time(
        logger: Union[str, UnifiedLogger, None] = None,
        level: str = None,
        threshold_seconds: float = None,
        include_result: bool = False
):
    """
    Decorator to log execution time of functions.
    ENHANCED: Uses new unified exception handling system
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check if this function should be traced
            should_trace = TraceManager.should_trace_function(func.__name__, func.__module__)
            if not should_trace:
                # Fast path: no tracing overhead
                return func(*args, **kwargs)

            # Get configuration from TraceManager
            actual_level = level or TraceManager.get_trace_level()
            actual_threshold = threshold_seconds
            if actual_threshold is None:
                actual_threshold = TraceManager.get_trace_config()['min_execution_time']

            # Get or create logger
            if isinstance(logger, UnifiedLogger):
                log_instance = logger
            elif isinstance(logger, str):
                log_instance = LoggerFactory.create_logger(logger)
            else:
                logger_name = f"{func.__module__}.{func.__name__}"
                log_instance = LoggerFactory.create_logger(logger_name)

            start_time = time.time()

            # ENHANCED: Get unified caller context for start log
            start_context = {}
            if HAS_ENHANCED_EXCEPTIONS:
                try:
                    start_context = get_unified_caller_context(skip_frames=2)
                except Exception:
                    pass

            # Log function start
            timing_log_method = getattr(log_instance, actual_level)
            timing_log_method(
                f"Starting execution: {func.__name__}",
                action_type='start',
                **start_context
            )

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time

                # Only log if threshold is met
                if execution_time >= actual_threshold:
                    # ENHANCED: Get unified caller context for completion
                    completion_context = {}
                    if HAS_ENHANCED_EXCEPTIONS:
                        try:
                            completion_context = get_unified_caller_context(skip_frames=2)
                        except Exception:
                            pass

                    context = {
                        'action_type': 'complete',
                        'execution_time_seconds': round(execution_time, 4),
                        'execution_time_ms': round(execution_time * 1000, 2),
                        'operation_success': True,
                        **completion_context
                    }

                    # Check for performance warning
                    performance_level = actual_level
                    if TraceManager.is_performance_warning(execution_time):
                        context['performance_warning'] = True
                        performance_level = 'warning'

                    if include_result:
                        # Sanitize result if it contains sensitive data
                        context['result_value'] = _sanitize_data(result) if isinstance(result,
                                                                                       (dict, list, tuple)) else str(
                            result)[:100]

                    perf_log_method = getattr(log_instance, performance_level)
                    perf_log_method(
                        f"Completed execution: {func.__name__} in {execution_time:.3f}s",
                        **context
                    )

                return result

            except BaseException:
                # Don't handle exceptions here - let @catch_and_log handle them
                # Just log that timing was interrupted
                execution_time = time.time() - start_time

                # ENHANCED: Get unified caller context for interruption
                interruption_context = {}
                if HAS_ENHANCED_EXCEPTIONS:
                    try:
                        interruption_context = get_unified_caller_context(skip_frames=2)
                    except Exception:
                        pass

                timing_log_method(
                    f"Execution interrupted: {func.__name__} after {execution_time:.3f}s",
                    action_type='interrupted',
                    execution_time_seconds=round(execution_time, 4),
                    execution_time_ms=round(execution_time * 1000, 2),
                    operation_success=False,
                    **interruption_context
                )
                raise

        return wrapper

    return decorator


def traced(enabled: bool = True, level: str = None, min_execution_time: float = None):
    """
    Decorator to explicitly enable/disable tracing for a specific function
    ENHANCED: Uses unified caller context
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create temporary tracing context
            config = {}
            if level is not None:
                config['trace_level'] = level
            if min_execution_time is not None:
                config['min_execution_time'] = min_execution_time

            with FunctionTracing(func.__name__, func.__module__, enabled):
                if config:
                    original_config = TraceManager.get_trace_config()
                    TraceManager.configure(**config)
                    try:
                        return func(*args, **kwargs)
                    finally:
                        TraceManager.configure(**original_config)
                else:
                    return func(*args, **kwargs)

        return wrapper

    return decorator


def log_api_calls(
        logger: Union[str, UnifiedLogger, None] = None,
        allow_duplicate_logging: bool = False
):
    """
    API calls decorator with intelligent duplicate detection
    ENHANCED: Uses unified exception handling
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Detect instance for method calls
            instance = args[0] if args and hasattr(args[0], '__class__') else None

            # Check for existing logging mixin (unless duplicates are explicitly allowed)
            if not allow_duplicate_logging and instance:
                # Check if instance uses logging_suite mixins
                for cls in instance.__class__.__mro__:
                    class_name = cls.__name__
                    if any(mixin_name in class_name for mixin_name in [
                        'LoggingMixin', 'DjangoLoggingMixin'
                    ]):
                        # Check if mixin logging is active
                        if hasattr(instance, '_should_log_operation'):
                            if instance._should_log_operation('automatic'):
                                # Mixin will handle logging, skip decorator logging
                                if hasattr(instance, 'logger'):
                                    instance.logger.debug(
                                        f"Skipping API call logging for {func.__name__} - mixin handles logging",
                                        decorator_skipped=True,
                                        skip_reason="mixin_logging_active",
                                        hint="Set allow_duplicate_logging=True to override"
                                    )
                                return func(*args, **kwargs)

            # Proceed with decorator logging using catch_and_log
            return catch_and_log(
                logger=logger,
                level='error',
                reraise=True,
                message="API call {function} failed after {execution_time:.3f}s: {exception}",
                include_args=True,
                sanitize_sensitive=True,
                log_execution_time=None,  # Let TraceManager decide
                timing_level='info',
                enhanced_exceptions=True  # ENHANCED: Enable enhanced exceptions for API calls
            )(func)(*args, **kwargs)

        return wrapper

    return decorator


def log_database_operations(
        logger: Union[str, UnifiedLogger, None] = None,
        detect_db_operations: bool = True,
        log_no_operations: bool = True,
        no_op_level: str = 'debug',
        allow_duplicate_logging: bool = False
):
    """
    Database operations decorator with intelligent duplicate detection
    ENHANCED: Uses unified exception handling
    """

    def decorator(func: Callable) -> Callable:

        def _has_logging_mixin(instance):
            """Check if the instance uses logging_suite mixins that already handle logging"""
            if not instance:
                return False

            # Check if instance has LoggingSuite mixin classes
            for cls in instance.__class__.__mro__:
                class_name = cls.__name__
                # Check for logging_suite mixin classes
                if any(mixin_name in class_name for mixin_name in [
                    'LoggingMixin', 'DjangoLoggingMixin'
                ]):
                    return True

                # Check for mixin module path
                if hasattr(cls, '__module__') and cls.__module__:
                    if 'logging_suite.mixins' in cls.__module__:
                        return True

            return False

        def _should_log_db_operations(instance, method_name):
            """Determine if DB operations should be logged based on existing mixin configuration"""
            # If duplicate logging is explicitly allowed, always log
            if allow_duplicate_logging:
                return True

            # If no instance (static/class method), proceed with logging
            if not instance:
                return True

            # Check if instance has LoggingSuite mixins
            if not _has_logging_mixin(instance):
                return True

            # If it has mixins, check if logging is enabled for the specific operation
            if hasattr(instance, '_should_log_operation'):
                # Map method names to operation types
                operation_map = {
                    'save': 'save',
                    'delete': 'delete',
                    'refresh_from_db': 'refresh'
                }

                operation_type = operation_map.get(method_name, 'automatic')
                should_log = instance._should_log_operation(operation_type)

                if not should_log:
                    # Mixin logging is disabled, so we can log here
                    return True
                else:
                    # Mixin logging is enabled, avoid duplicate logging
                    return False

            # If we can't determine mixin settings, assume mixin will handle it
            return False

        @catch_and_log(
            logger=logger,
            level='error',
            reraise=True,
            message="Database operation {function} failed after {execution_time:.3f}s: {exception}",
            include_args=True,
            sanitize_sensitive=True,
            log_execution_time=None,  # Let TraceManager decide
            timing_level='debug',
            enhanced_exceptions=True  # ENHANCED: Enable enhanced exceptions for DB operations
        )
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Detect instance for method calls (first arg is usually 'self')
            instance = args[0] if args and hasattr(args[0], '__class__') else None
            method_name = func.__name__

            # Check if we should log based on existing mixin configuration
            should_log_here = _should_log_db_operations(instance, method_name)

            # Get or create logger
            if isinstance(logger, UnifiedLogger):
                log_instance = logger
            elif isinstance(logger, str):
                log_instance = LoggerFactory.create_logger(logger)
            else:
                log_instance = LoggerFactory.create_logger(f"{func.__module__}.{func.__name__}")

            # If mixin logging is active and duplicates not allowed, skip logging
            if not should_log_here:
                log_instance.debug(
                    f"Skipping DB operation logging for {func.__name__} - logging_suite mixin already handles logging",
                    instance_class_name=instance.__class__.__name__ if instance else None,
                    decorator_skipped=True,
                    skip_reason="mixin_logging_active",
                    hint="Set allow_duplicate_logging=True to override"
                )

                # Execute function without additional logging
                return func(*args, **kwargs)

            # Continue with normal DB operation detection and logging
            # Track database operations if detection is enabled
            db_operations_detected = False
            original_execute = None
            operation_count = 0

            if detect_db_operations:
                # Try to monkey-patch database operations to detect them
                try:
                    # Django ORM detection
                    from django.db import connection
                    original_execute = connection.cursor().execute

                    def counting_execute(*args, **kwargs):
                        nonlocal operation_count, db_operations_detected
                        operation_count += 1
                        db_operations_detected = True
                        return original_execute(*args, **kwargs)

                    connection.cursor().execute = counting_execute
                except ImportError:
                    # Not a Django environment, try other detection methods
                    pass
                except Exception:
                    # Detection failed, continue without it
                    pass

            try:
                # Execute the function
                result = func(*args, **kwargs)

                # Log database operation summary
                if detect_db_operations and should_log_here:
                    if db_operations_detected:
                        log_instance.info(
                            f"Database operations completed in {func.__name__}",
                            db_operations_count=operation_count,
                            operation_type='database_access',
                            instance_class_name=instance.__class__.__name__ if instance else None,
                            duplicate_detection_enabled=not allow_duplicate_logging
                        )
                    elif log_no_operations:
                        no_op_log_method = getattr(log_instance, no_op_level)
                        no_op_log_method(
                            f"No database operations detected in {func.__name__}",
                            operation_type='no_database_access',
                            note_text="Function marked as database operation but no DB calls detected",
                            instance_class_name=instance.__class__.__name__ if instance else None
                        )

                return result

            finally:
                # Restore original database execute if we patched it
                if original_execute and detect_db_operations:
                    try:
                        from django.db import connection
                        connection.cursor().execute = original_execute
                    except:
                        pass

        return wrapper

    return decorator


# Context manager for function-level tracing control
class FunctionTracing:
    """Context manager for controlling tracing on specific function calls"""

    def __init__(self, func_name: str, module_name: str = '__main__', enabled: bool = True):
        """
        Initialize function-specific tracing control

        Args:
            func_name: Name of function to control tracing for
            module_name: Module name (default: __main__)
            enabled: Whether to enable tracing for this function
        """
        self.func_name = func_name
        self.module_name = module_name
        self.enabled = enabled
        self.original_config = None

    def __enter__(self):
        """Enter context - modify tracing config for this function"""
        self.original_config = TraceManager.get_trace_config()

        if self.enabled:
            # Add this function to include list
            include_funcs = set(self.original_config.get('include_functions', set()))
            include_funcs.add(self.func_name)
            TraceManager.configure(
                global_enabled=True,
                include_functions=include_funcs
            )
        else:
            # Add this function to exclude list
            exclude_funcs = set(self.original_config.get('exclude_functions', set()))
            exclude_funcs.add(self.func_name)
            TraceManager.configure(exclude_functions=exclude_funcs)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore original configuration"""
        if self.original_config:
            TraceManager.configure(**self.original_config)


# Export all decorators - Clean API with smart defaults
__all__ = [
    'catch_and_log',
    'log_execution_time',
    'traced',
    'catch',
    'log_api_calls',  # Smart version with duplicate detection
    'log_database_operations',  # Smart version with duplicate detection
    'FunctionTracing'
]