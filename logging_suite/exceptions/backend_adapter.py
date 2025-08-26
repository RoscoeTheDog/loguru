# logging_suite/exceptions/backend_adapter.py
"""
Backend-aware exception handler that adapts to different logging backends
FIXED: No config imports - accepts config as parameters
"""

from typing import Dict, Any, Optional, Tuple
from .context_manager import create_context_manager_with_config
from .renderer import UnifiedExceptionRenderer


class BackendAwareExceptionHandler:
    """
    Exception handler that adapts its behavior based on the logging backend
    FIXED: Configuration passed as parameters instead of imported
    """

    def __init__(self, backend_name: str, config: Dict[str, Any]):
        """
        Initialize backend-aware exception handler

        Args:
            backend_name: Name of the logging backend ('standard', 'loguru', 'structlog')
            config: Configuration dictionary
        """
        self.backend_name = backend_name.lower()
        self.config = config

        # Determine capabilities based on backend
        self._setup_backend_capabilities()

        # Initialize components based on capabilities
        self._setup_components()

    def _setup_backend_capabilities(self):
        """Setup capabilities based on backend type"""
        if self.backend_name == 'loguru':
            # Loguru has native enhanced exception handling
            self.use_native_features = True
            self.enhance_exceptions = self.config.get('enhance_loguru_exceptions', False)
            self.capture_locals = False  # Let loguru handle this
            self.show_enhanced_traceback = False  # Let loguru handle this

            # Check if loguru's native features are enabled
            self.loguru_diagnose = self.config.get('loguru_diagnose', True)
            self.loguru_backtrace = self.config.get('loguru_backtrace', True)

        elif self.backend_name == 'structlog':
            # Structlog has some enhanced features but not as comprehensive as loguru
            self.use_native_features = False
            self.enhance_exceptions = self.config.get('exception_diagnosis', True)
            self.capture_locals = self.config.get('exception_diagnosis', True)
            self.show_enhanced_traceback = self.config.get('exception_backtrace', True)

        else:  # standard logging
            # Standard logging needs all our enhancements
            self.use_native_features = False
            self.enhance_exceptions = self.config.get('exception_diagnosis', True)
            self.capture_locals = self.config.get('exception_diagnosis', True)
            self.show_enhanced_traceback = self.config.get('exception_backtrace', True)

    def _setup_components(self):
        """Initialize components based on capabilities"""
        # Context manager for caller detection and exception context
        if self.enhance_exceptions and not self.use_native_features:
            self.context_manager = create_context_manager_with_config(self.config)
        else:
            self.context_manager = None

        # Exception renderer
        if self.enhance_exceptions:
            output_format = self.config.get('format', 'console')
            if output_format == 'json' or self.config.get('use_json_handlers', False):
                output_format = 'json'

            self.renderer = UnifiedExceptionRenderer(
                output_format=output_format,
                show_enhanced_traceback=self.show_enhanced_traceback and not self.use_native_features,
                show_caller_context=not self.use_native_features,
                show_exception_locals=self.capture_locals,
                colorize=self.config.get('use_colors', True),
                compact_mode=self.config.get('compact_format', False)
            )
        else:
            self.renderer = None

    def should_process_exception(self) -> bool:
        """
        Determine if we should process the exception or let the backend handle it

        Returns:
            True if we should process the exception
        """
        if self.backend_name == 'loguru':
            # Only process if loguru's native features are disabled AND we're asked to enhance
            return (not self.loguru_diagnose and not self.loguru_backtrace and
                    self.enhance_exceptions)

        # For other backends, process if enhancement is enabled
        return self.enhance_exceptions

    def get_caller_context(self, skip_frames: int = 1) -> Dict[str, Any]:
        """
        Get caller context, adapting based on backend capabilities

        Args:
            skip_frames: Number of frames to skip

        Returns:
            Caller context dictionary
        """
        if not self.should_process_exception() or not self.context_manager:
            return {}

        try:
            return self.context_manager.get_unified_caller_context(skip_frames + 1)
        except Exception:
            return {}

    def get_exception_context(self, exc_info: Optional[Tuple] = None) -> Dict[str, Any]:
        """
        Get exception context, adapting based on backend capabilities

        Args:
            exc_info: Exception info tuple or None for current

        Returns:
            Exception context dictionary
        """
        if not self.should_process_exception() or not self.context_manager:
            return {}

        try:
            return self.context_manager.get_exception_context(exc_info)
        except Exception:
            return {}

    def format_exception(self,
                         exc_info: Optional[Tuple] = None,
                         message: str = "",
                         logger_context: Dict[str, Any] = None) -> str:
        """
        Format exception for logging, adapting based on backend

        Args:
            exc_info: Exception info tuple or None for current
            message: Associated log message
            logger_context: Additional context from logger

        Returns:
            Formatted exception string or empty string if backend should handle it
        """
        if not self.should_process_exception() or not self.renderer:
            return ""  # Let the backend handle formatting

        try:
            return self.renderer.render_exception(exc_info, message, logger_context)
        except Exception:
            # Fallback to basic formatting if our renderer fails
            import traceback
            import sys

            if exc_info is None:
                exc_info = sys.exc_info()

            if exc_info == (None, None, None):
                return message

            exc_type, exc_value, exc_traceback = exc_info
            basic_tb = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

            if message:
                return f"{message}\n{basic_tb}"
            else:
                return basic_tb

    def get_backend_specific_config(self) -> Dict[str, Any]:
        """
        Get configuration to pass to the backend for its native exception handling

        Returns:
            Configuration dictionary for the backend
        """
        if self.backend_name == 'loguru':
            return {
                'diagnose': self.loguru_diagnose,
                'backtrace': self.loguru_backtrace,
                'colorize': self.config.get('use_colors', True)
            }
        elif self.backend_name == 'structlog':
            return {
                'include_traceback': self.config.get('exception_backtrace', True)
            }
        else:  # standard
            return {}

    def create_unified_context(self,
                               caller_context: Dict[str, Any] = None,
                               exception_context: Dict[str, Any] = None,
                               logger_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create unified context from various sources, handling backend differences

        Args:
            caller_context: Context from caller detection
            exception_context: Context from exception analysis
            logger_context: Context from logger

        Returns:
            Unified context dictionary with consistent naming
        """
        unified_context = {}

        # Add caller context with consistent naming
        if caller_context:
            unified_context.update(caller_context)

        # Add exception context
        if exception_context:
            unified_context.update(exception_context)

        # Add logger context
        if logger_context:
            # Filter out internal LoggingSuite context
            filtered_context = {k: v for k, v in logger_context.items()
                                if not k.startswith('_') and k not in ['exc_info', 'stack_info']}
            unified_context.update(filtered_context)

        # Clean up any duplicate or conflicting keys
        if self.backend_name == 'loguru':
            # Loguru might have its own context keys, normalize them
            if 'function' in unified_context and 'caller_function' not in unified_context:
                unified_context['caller_function'] = unified_context['function']
            if 'module' in unified_context and 'caller_module' not in unified_context:
                unified_context['caller_module'] = unified_context['module']

        return unified_context

    def is_exception_enhanced_by_backend(self) -> bool:
        """
        Check if the backend provides its own exception enhancement

        Returns:
            True if backend provides enhanced exception handling
        """
        if self.backend_name == 'loguru':
            return self.loguru_diagnose or self.loguru_backtrace

        return False


def create_exception_handler_for_backend(backend_name: str,
                                         config: Dict[str, Any]) -> BackendAwareExceptionHandler:
    """
    Factory function to create an appropriate exception handler for a backend
    FIXED: Pure function with no imports

    Args:
        backend_name: Name of the logging backend
        config: Configuration dictionary

    Returns:
        Configured BackendAwareExceptionHandler
    """
    # Apply backend-specific defaults to config copy
    config_copy = config.copy()

    if backend_name.lower() == 'loguru':
        # Default loguru configuration
        config_copy.setdefault('loguru_diagnose', True)
        config_copy.setdefault('loguru_backtrace', True)
        config_copy.setdefault('enhance_loguru_exceptions', False)  # Use native by default

    elif backend_name.lower() == 'structlog':
        # Default structlog configuration
        config_copy.setdefault('exception_diagnosis', True)
        config_copy.setdefault('exception_backtrace', True)

    else:  # standard logging
        # Default standard logging configuration
        config_copy.setdefault('exception_diagnosis', True)
        config_copy.setdefault('exception_backtrace', True)

    return BackendAwareExceptionHandler(backend_name, config_copy)