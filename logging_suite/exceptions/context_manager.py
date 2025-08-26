# logging_suite/exceptions/context_manager.py
"""
Unified exception context manager for logging_suite
FIXED: No config imports - accepts config as parameters
FIXED: Compatible type hints for Python 3.9
"""

import inspect
import sys
import traceback
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path

# Python 3.9 compatible type hint for frame
try:
    from types import FrameType
except ImportError:
    # Fallback for older Python versions
    FrameType = type(sys._getframe())


class ExceptionContextManager:
    """
    Centralized manager for exception context and caller detection
    FIXED: No global config access - configuration passed as parameters
    """

    def __init__(self,
                 capture_locals: bool = True,
                 max_locals_length: int = 100,
                 sensitive_keys: List[str] = None):
        """
        Initialize exception context manager

        Args:
            capture_locals: Whether to capture local variable values
            max_locals_length: Maximum length for variable values
            sensitive_keys: Keys to mask in variable capture
        """
        self.capture_locals = capture_locals
        self.max_locals_length = max_locals_length
        self.sensitive_keys = set(sensitive_keys or [
            'password', 'passwd', 'pwd', 'token', 'secret', 'key', 'auth',
            'credential', 'api_key', 'private_key', 'access_token',
            'refresh_token', 'session_key', 'ssn', 'social_security',
            'credit_card', 'ccn', 'cvv', 'pin', 'authorization'
        ])

    def get_unified_caller_context(self, skip_frames: int = 1) -> Dict[str, Any]:
        """
        Get unified caller context with consistent naming

        Args:
            skip_frames: Number of frames to skip (1 = immediate caller)

        Returns:
            Dictionary with standardized caller context
        """
        try:
            frame = inspect.currentframe()

            # Skip the specified number of frames plus this function
            for _ in range(skip_frames + 1):
                if frame is None:
                    break
                frame = frame.f_back

            if frame is None:
                return {}

            # Skip LoggingSuite internal frames to find the actual user code
            user_frame = self._find_user_frame(frame)

            if user_frame is None:
                return {}

            code = user_frame.f_code

            context = {
                'caller_function': code.co_name,
                'caller_module': user_frame.f_globals.get('__name__', 'unknown'),
                'caller_file': Path(code.co_filename).name if code.co_filename else 'unknown',
                'caller_file_path': code.co_filename,
                'caller_line': user_frame.f_lineno,
                'caller_location': f"{Path(code.co_filename).name}:{user_frame.f_lineno}" if code.co_filename else "unknown:0"
            }

            # Add local variables if enabled
            if self.capture_locals:
                try:
                    locals_dict = self._capture_frame_locals(user_frame)
                    if locals_dict:
                        context['caller_locals'] = locals_dict
                except Exception:
                    # Don't let variable capture break logging
                    pass

            return context

        except Exception:
            # Don't let context extraction break logging
            return {}

    def get_exception_context(self, exc_info: Optional[Tuple] = None) -> Dict[str, Any]:
        """
        Get comprehensive exception context with enhanced details

        Args:
            exc_info: Exception info tuple (type, value, traceback) or None for current

        Returns:
            Dictionary with complete exception context
        """
        if exc_info is None:
            exc_info = sys.exc_info()

        if exc_info == (None, None, None):
            return {}

        exc_type, exc_value, exc_traceback = exc_info

        context = {
            'exception_type': exc_type.__name__ if exc_type else 'Unknown',
            'exception_message': str(exc_value) if exc_value else 'Unknown error',
            'exception_module': exc_type.__module__ if exc_type else 'unknown',
        }

        if exc_traceback:
            # Get exception location (where the error actually occurred)
            exception_frame = exc_traceback.tb_frame
            exception_code = exception_frame.f_code

            context.update({
                'exception_function': exception_code.co_name,
                'exception_file': Path(exception_code.co_filename).name if exception_code.co_filename else 'unknown',
                'exception_file_path': exception_code.co_filename,
                'exception_line': exc_traceback.tb_lineno,
                'exception_location': f"{Path(exception_code.co_filename).name}:{exc_traceback.tb_lineno}" if exception_code.co_filename else "unknown:0"
            })

            # Add local variables at exception point if enabled
            if self.capture_locals:
                try:
                    exception_locals = self._capture_frame_locals(exception_frame)
                    if exception_locals:
                        context['exception_locals'] = exception_locals
                except Exception:
                    pass

            # Add stack trace summary
            try:
                stack_frames = self._extract_stack_frames(exc_traceback)
                context['stack_frames'] = stack_frames
                context['stack_summary'] = self._create_stack_summary(stack_frames)
            except Exception:
                pass

        return context

    def _find_user_frame(self, start_frame) -> Optional[FrameType]:
        """
        Find the first frame that represents actual user code (not LoggingSuite internals)

        Args:
            start_frame: Starting frame to search from

        Returns:
            First user code frame or None
        """
        frame = start_frame

        while frame is not None:
            code = frame.f_code
            filename = code.co_filename
            function_name = code.co_name

            # Skip LoggingSuite internal frames
            if self._is_loggingsuite_internal(filename, function_name):
                frame = frame.f_back
                continue

            # Skip standard logging internal frames
            if self._is_logging_internal(function_name):
                frame = frame.f_back
                continue

            # Skip decorator wrapper frames
            if self._is_decorator_wrapper(function_name):
                frame = frame.f_back
                continue

            # Found user code
            return frame

        return None

    def _is_loggingsuite_internal(self, filename: str, function_name: str) -> bool:
        """Check if this is a LoggingSuite internal frame"""
        if not filename:
            return False

        # Check filename
        if 'LoggingSuite' in filename or 'loggingsuite' in filename.lower():
            # Internal LoggingSuite functions to skip
            internal_functions = {
                '_log_with_backend', 'debug', 'info', 'warning', 'error', 'critical',
                'exception', 'bind', '__call__', '_process_log_data', 'format',
                '_format_message_with_context', '_get_actual_caller_context',
                'get_caller_context', '_sanitize_extra_for_logging', 'get_unified_caller_context',
                'get_exception_context', '_find_user_frame'
            }
            return function_name in internal_functions

        return False

    def _is_logging_internal(self, function_name: str) -> bool:
        """Check if this is a standard logging internal frame"""
        logging_internals = {
            '_log', 'log', 'handle', 'emit', 'format', 'formatTime',
            'formatException', 'formatMessage', 'getMessage'
        }
        return function_name in logging_internals

    def _is_decorator_wrapper(self, function_name: str) -> bool:
        """Check if this is a decorator wrapper frame"""
        wrapper_names = {
            'wrapper', 'inner', 'decorated_function', 'decorator_wrapper'
        }
        return function_name in wrapper_names

    def _capture_frame_locals(self, frame: FrameType) -> Dict[str, Any]:
        """
        Capture local variables from a frame with sanitization

        Args:
            frame: Frame to capture locals from

        Returns:
            Dictionary of sanitized local variables
        """
        if not frame:
            return {}

        try:
            locals_dict = {}
            frame_locals = frame.f_locals

            for name, value in frame_locals.items():
                # Skip private/internal variables
                if name.startswith('__') and name.endswith('__'):
                    continue

                # Skip large objects and functions
                if callable(value) or hasattr(value, '__dict__'):
                    locals_dict[name] = f"<{type(value).__name__}>"
                    continue

                # Sanitize sensitive values
                if any(sensitive in name.lower() for sensitive in self.sensitive_keys):
                    if isinstance(value, str) and len(value) > 4:
                        locals_dict[name] = f"{value[:2]}***{value[-2:]}"
                    else:
                        locals_dict[name] = "***"
                    continue

                # Truncate long values
                try:
                    str_value = str(value)
                    if len(str_value) > self.max_locals_length:
                        locals_dict[name] = f"{str_value[:self.max_locals_length]}...(truncated)"
                    else:
                        locals_dict[name] = value
                except Exception:
                    locals_dict[name] = f"<{type(value).__name__}>"

            return locals_dict

        except Exception:
            return {}

    def _extract_stack_frames(self, tb) -> List[Dict[str, Any]]:
        """
        Extract stack frame information from traceback

        Args:
            tb: Traceback object

        Returns:
            List of frame information dictionaries
        """
        frames = []

        while tb is not None:
            frame = tb.tb_frame
            code = frame.f_code

            frame_info = {
                'function': code.co_name,
                'file': Path(code.co_filename).name if code.co_filename else 'unknown',
                'file_path': code.co_filename,
                'line': tb.tb_lineno,
                'location': f"{Path(code.co_filename).name}:{tb.tb_lineno}" if code.co_filename else "unknown:0"
            }

            # Add locals if enabled
            if self.capture_locals:
                try:
                    frame_locals = self._capture_frame_locals(frame)
                    if frame_locals:
                        frame_info['locals'] = frame_locals
                except Exception:
                    pass

            frames.append(frame_info)
            tb = tb.tb_next

        return frames

    def _create_stack_summary(self, frames: List[Dict[str, Any]]) -> str:
        """
        Create a concise stack summary

        Args:
            frames: List of frame information

        Returns:
            Human-readable stack summary
        """
        if not frames:
            return "No stack information available"

        # Show the call chain in reverse order (most recent first)
        summary_parts = []
        for frame in reversed(frames[-3:]):  # Last 3 frames
            location = frame.get('location', 'unknown')
            function = frame.get('function', 'unknown')
            summary_parts.append(f"{location} in {function}()")

        return " → ".join(summary_parts)


# =============================================================================
# FACTORY FUNCTIONS WITH PARAMETER INJECTION
# =============================================================================

def create_context_manager_with_config(config: Dict[str, Any]) -> ExceptionContextManager:
    """
    Create an ExceptionContextManager with configuration
    FIXED: Config passed as parameter instead of imported
    """
    return ExceptionContextManager(
        capture_locals=config.get('exception_diagnosis', True),
        max_locals_length=config.get('exception_locals_max_length', 100),
        sensitive_keys=config.get('sensitive_keys', [])
    )


def get_unified_caller_context(skip_frames: int = 1,
                               capture_locals: bool = None,
                               sensitive_keys: List[str] = None,
                               config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to get unified caller context
    FIXED: Config passed as parameter instead of imported

    Args:
        skip_frames: Number of frames to skip
        capture_locals: Whether to capture local variables (None = use config)
        sensitive_keys: Keys to mask (None = use config)
        config: Configuration dictionary (if None, use defaults)

    Returns:
        Unified caller context
    """
    # Use provided config or defaults
    if config is None:
        config = {}

    if capture_locals is None:
        capture_locals = config.get('exception_diagnosis', True)
    if sensitive_keys is None:
        sensitive_keys = config.get('sensitive_keys', [])

    # Create context manager with configuration
    context_manager = ExceptionContextManager(
        capture_locals=capture_locals,
        sensitive_keys=sensitive_keys
    )

    return context_manager.get_unified_caller_context(skip_frames + 1)


def get_exception_context(exc_info: Optional[Tuple] = None,
                          capture_locals: bool = None,
                          sensitive_keys: List[str] = None,
                          config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to get exception context
    FIXED: Config passed as parameter instead of imported

    Args:
        exc_info: Exception info tuple or None for current
        capture_locals: Whether to capture local variables (None = use config)
        sensitive_keys: Keys to mask (None = use config)
        config: Configuration dictionary (if None, use defaults)

    Returns:
        Exception context
    """
    # Use provided config or defaults
    if config is None:
        config = {}

    if capture_locals is None:
        capture_locals = config.get('exception_diagnosis', True)
    if sensitive_keys is None:
        sensitive_keys = config.get('sensitive_keys', [])

    # Create context manager with configuration
    context_manager = ExceptionContextManager(
        capture_locals=capture_locals,
        sensitive_keys=sensitive_keys
    )

    return context_manager.get_exception_context(exc_info)