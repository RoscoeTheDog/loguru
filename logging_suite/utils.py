# logging_suite/utils.py
"""
Utility functions for logging_suite
ENHANCED: Improved caller context inspection for better tracing accuracy
"""

import inspect
import sys
import traceback
import json
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
from datetime import datetime


def get_caller_context(skip_frames: int = 1, skip_loggingsuite_frames: bool = True) -> Dict[str, Any]:
    """
    Get context information about the caller
    ENHANCED: Now properly skips LoggingSuite internal frames for accurate tracing

    Args:
        skip_frames: Number of frames to skip (1 = immediate caller)
        skip_loggingsuite_frames: Whether to skip LoggingSuite internal frames

    Returns:
        Dictionary with caller context information
    """
    try:
        frame = inspect.currentframe()

        # Skip the specified number of frames
        for _ in range(skip_frames + 1):  # +1 to skip this function
            if frame is None:
                break
            frame = frame.f_back

        if frame is None:
            return {}

        # Skip LoggingSuite internal frames to find the actual caller
        if skip_loggingsuite_frames:
            while frame is not None:
                code = frame.f_code
                filename = code.co_filename
                function_name = code.co_name

                # Skip LoggingSuite internal methods (enhanced list)
                if (filename and ('LoggingSuite' in filename or 'loggingsuite' in filename.lower()) and
                        function_name in ['_log_with_backend', 'debug', 'info', 'warning', 'error', 'critical',
                                          'exception', 'bind', '__call__', '_process_log_data', 'format',
                                          '_format_message_with_context', '_get_actual_caller_context',
                                          'get_caller_context']):
                    frame = frame.f_back
                    continue

                # Also skip standard logging internal methods
                if function_name in ['_log', 'log', 'handle', 'emit', 'format', 'formatTime', 'formatException']:
                    frame = frame.f_back
                    continue

                # Skip decorator wrapper frames
                if function_name in ['wrapper', 'inner', 'decorated_function']:
                    frame = frame.f_back
                    continue

                # Skip common internal Python methods
                if function_name.startswith('__') and function_name.endswith('__'):
                    if function_name in ['__call__', '__getattr__', '__setattr__', '__enter__', '__exit__']:
                        frame = frame.f_back
                        continue

                # Found the actual caller
                break

        if frame is None:
            return {}

        code = frame.f_code

        return {
            'function': code.co_name,
            'filename': code.co_filename,
            'line_number': frame.f_lineno,
            'module': frame.f_globals.get('__name__', 'unknown'),
            'file_path': str(Path(code.co_filename).name) if code.co_filename else 'unknown'
        }
    except Exception:
        return {}


def create_child_logger(parent_logger, child_name: str, **additional_config):
    """
    Create a child logger with additional configuration

    Args:
        parent_logger: Parent UnifiedLogger instance
        child_name: Name for the child logger
        **additional_config: Additional configuration for the child

    Returns:
        New UnifiedLogger instance
    """
    from .factory import LoggerFactory

    # Combine parent logger name with child name
    if hasattr(parent_logger, '_raw_logger'):
        parent_name = getattr(parent_logger._raw_logger, 'name', 'unknown')
    else:
        parent_name = 'unknown'

    full_child_name = f"{parent_name}.{child_name}"

    # Create child logger with additional config
    return LoggerFactory.create_logger(full_child_name, config=additional_config)


def sanitize_log_data(data: Any,
                      sensitive_keys: List[str] = None,
                      max_string_length: int = 1000,
                      max_depth: int = 10) -> Any:
    """
    Sanitize data for logging by removing sensitive information and truncating large data

    Args:
        data: Data to sanitize
        sensitive_keys: List of keys to consider sensitive
        max_string_length: Maximum length for string values
        max_depth: Maximum recursion depth

    Returns:
        Sanitized data safe for logging
    """
    if sensitive_keys is None:
        sensitive_keys = [
            'password', 'passwd', 'pwd', 'token', 'secret', 'key', 'auth',
            'credential', 'api_key', 'private_key', 'access_token',
            'refresh_token', 'session_key', 'ssn', 'social_security',
            'credit_card', 'ccn', 'cvv', 'pin'
        ]

    def _sanitize_recursive(obj, depth=0):
        if depth > max_depth:
            return f"<MAX_DEPTH_EXCEEDED: {type(obj).__name__}>"

        if obj is None:
            return None
        elif isinstance(obj, (bool, int, float)):
            return obj
        elif isinstance(obj, str):
            # Check if string contains sensitive patterns
            obj_lower = obj.lower()
            if any(sensitive_key in obj_lower for sensitive_key in sensitive_keys):
                if len(obj) > 4:
                    return f"{obj[:2]}...{obj[-2:]}"
                else:
                    return "***"

            # Truncate long strings
            if len(obj) > max_string_length:
                return f"{obj[:max_string_length]}... (truncated)"
            return obj
        elif isinstance(obj, dict):
            sanitized = {}
            for key, value in obj.items():
                key_lower = str(key).lower()

                # Check if key is sensitive
                if any(sensitive_key in key_lower for sensitive_key in sensitive_keys):
                    if isinstance(value, str) and len(value) > 4:
                        sanitized[key] = f"{value[:2]}...{value[-2:]}"
                    else:
                        sanitized[key] = "***"
                else:
                    sanitized[key] = _sanitize_recursive(value, depth + 1)
            return sanitized
        elif isinstance(obj, (list, tuple)):
            sanitized = [_sanitize_recursive(item, depth + 1) for item in obj]
            return type(obj)(sanitized) if isinstance(obj, tuple) else sanitized
        else:
            # For other types, convert to string and truncate
            try:
                str_repr = str(obj)
                if len(str_repr) > max_string_length:
                    return f"{str_repr[:max_string_length]}... (truncated {type(obj).__name__})"
                return str_repr
            except Exception:
                return f"<UNSERIALIZABLE: {type(obj).__name__}>"

    return _sanitize_recursive(data)


def format_exception_for_logging(exc_info: Union[Exception, tuple, None] = None) -> Dict[str, Any]:
    """
    Format exception information for structured logging

    Args:
        exc_info: Exception info (Exception instance, sys.exc_info() tuple, or None for current)

    Returns:
        Dictionary with formatted exception information
    """
    if exc_info is None:
        exc_info = sys.exc_info()
    elif isinstance(exc_info, Exception):
        exc_info = (type(exc_info), exc_info, exc_info.__traceback__)

    if exc_info == (None, None, None):
        return {}

    exc_type, exc_value, exc_traceback = exc_info

    formatted = {
        'exception_type': exc_type.__name__ if exc_type else 'Unknown',
        'exception_message': str(exc_value) if exc_value else 'Unknown error',
        'exception_module': exc_type.__module__ if exc_type else 'unknown',
    }

    if exc_traceback:
        # Extract traceback information
        tb_lines = traceback.format_tb(exc_traceback)
        formatted.update({
            'traceback_lines': tb_lines,
            'traceback_summary': ''.join(tb_lines[-3:]) if len(tb_lines) > 3 else ''.join(tb_lines),
            'file': exc_traceback.tb_frame.f_code.co_filename,
            'line_number': exc_traceback.tb_lineno,
            'function': exc_traceback.tb_frame.f_code.co_name,
        })

        # Extract local variables if available (be careful with sensitive data)
        try:
            local_vars = exc_traceback.tb_frame.f_locals
            # Only include simple types and sanitize
            safe_locals = {}
            for key, value in local_vars.items():
                if isinstance(value, (str, int, float, bool, type(None))):
                    safe_locals[key] = sanitize_log_data(value)
                elif isinstance(value, (list, dict, tuple)) and len(str(value)) < 200:
                    safe_locals[key] = sanitize_log_data(value)
                else:
                    safe_locals[key] = f"<{type(value).__name__}>"

            if safe_locals:
                formatted['local_variables'] = safe_locals
        except Exception:
            pass  # Don't let local variable extraction break exception logging

    return formatted


def format_bytes(bytes_value: Union[int, float]) -> str:
    """
    Format byte count as human-readable string

    Args:
        bytes_value: Number of bytes

    Returns:
        Formatted string (e.g., "1.2 MB")
    """
    if bytes_value == 0:
        return "0 B"

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    unit_index = 0
    value = float(bytes_value)

    while value >= 1024 and unit_index < len(units) - 1:
        value /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(value)} {units[unit_index]}"
    else:
        return f"{value:.1f} {units[unit_index]}"


def format_duration(seconds: float) -> str:
    """
    Format duration in seconds as human-readable string

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "1.2s", "45ms", "2m 30s")
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.0f}μs"
    elif seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.0f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        return f"{hours}h {remaining_minutes}m"


def sanitize_for_logging(obj: Any) -> Any:
    """
    Sanitize any object for safe logging (alias for sanitize_log_data)

    Args:
        obj: Object to sanitize

    Returns:
        Sanitized object
    """
    return sanitize_log_data(obj)


def is_json_serializable(obj: Any) -> bool:
    """
    Check if an object is JSON serializable

    Args:
        obj: Object to check

    Returns:
        True if object can be serialized to JSON
    """
    try:
        json.dumps(obj, default=str)
        return True
    except (TypeError, ValueError):
        return False


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two dictionaries

    Args:
        dict1: First dictionary
        dict2: Second dictionary (takes precedence)

    Returns:
        Merged dictionary
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def create_log_context(**kwargs) -> Dict[str, Any]:
    """
    Create a standardized log context dictionary with caller information
    ENHANCED: Now uses improved caller context detection

    Args:
        **kwargs: Additional context fields

    Returns:
        Context dictionary with caller info and provided fields
    """
    context = get_caller_context(skip_frames=1)
    context.update(kwargs)
    context['timestamp'] = datetime.now().isoformat()
    return context


def ensure_serializable(obj: Any) -> Any:
    """
    Ensure an object is JSON serializable by converting problematic types

    Args:
        obj: Object to make serializable

    Returns:
        JSON-serializable version of the object
    """

    def _convert(item):
        if isinstance(item, datetime):
            return item.isoformat()
        elif isinstance(item, Path):
            return str(item)
        elif isinstance(item, bytes):
            try:
                return item.decode('utf-8')
            except UnicodeDecodeError:
                return item.hex()
        elif isinstance(item, Exception):
            return {
                'type': type(item).__name__,
                'message': str(item),
                'args': item.args
            }
        elif hasattr(item, '__dict__'):
            # For custom objects, return their dict representation
            try:
                return {k: _convert(v) for k, v in item.__dict__.items()}
            except Exception:
                return str(item)
        elif isinstance(item, (list, tuple)):
            return [_convert(x) for x in item]
        elif isinstance(item, dict):
            return {k: _convert(v) for k, v in item.items()}
        else:
            return item

    try:
        # First try to serialize as-is
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        # If that fails, try to convert
        return _convert(obj)


def truncate_string(s: str, max_length: int = 1000, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def extract_error_details(exception: Exception) -> Dict[str, Any]:
    """
    Extract detailed information from an exception

    Args:
        exception: Exception instance

    Returns:
        Dictionary with error details
    """
    details = {
        'type': type(exception).__name__,
        'message': str(exception),
        'module': type(exception).__module__,
    }

    # Add specific details for common exception types
    if hasattr(exception, 'errno'):
        details['errno'] = exception.errno

    if hasattr(exception, 'strerror'):
        details['strerror'] = exception.strerror

    if hasattr(exception, 'filename'):
        details['filename'] = exception.filename

    # For HTTP-related exceptions
    if hasattr(exception, 'status_code'):
        details['status_code'] = exception.status_code

    if hasattr(exception, 'response'):
        try:
            details['response_text'] = str(exception.response)[:500]  # Truncate
        except Exception:
            pass

    # Add args if they provide additional context
    if exception.args and len(exception.args) > 1:
        details['args'] = exception.args

    return details


def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage information

    Returns:
        Dictionary with memory usage in MB
    """
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': process.memory_percent()
        }
    except ImportError:
        # psutil not available, try alternative methods
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            return {
                'max_rss_mb': usage.ru_maxrss / 1024 / 1024 if sys.platform != 'darwin' else usage.ru_maxrss / 1024,
                'method': 'resource'
            }
        except Exception:
            return {'error': 'Memory usage unavailable'}


def validate_log_level(level: str) -> str:
    """
    Validate and normalize a log level string

    Args:
        level: Log level string

    Returns:
        Normalized log level

    Raises:
        ValueError: If level is invalid
    """
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    level_upper = level.upper()

    if level_upper not in valid_levels:
        raise ValueError(f"Invalid log level: {level}. Valid levels: {valid_levels}")

    return level_upper


def create_unique_logger_name(base_name: str, instance_id: Any = None) -> str:
    """
    Create a unique logger name with optional instance identifier

    Args:
        base_name: Base name for the logger
        instance_id: Optional instance identifier

    Returns:
        Unique logger name
    """
    if instance_id is not None:
        return f"{base_name}.{instance_id}"
    else:
        # Use timestamp for uniqueness
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return f"{base_name}.{timestamp}"