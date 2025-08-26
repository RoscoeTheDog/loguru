# logging_suite/tracing.py
"""
Global tracing and execution control for logging_suite
ENHANCED: Better integration with improved caller context detection
"""

from typing import Dict, Any, Set, List, Optional
import fnmatch
import threading
import os


class TraceManager:
    """
    Global manager for function tracing and execution logging.
    ENHANCED: Now works better with improved caller context detection to show
    actual user functions in global tracing instead of LoggingSuite internals.

    Provides centralized control over:
    - Which functions should be traced
    - What level of detail to capture
    - Performance-conscious enable/disable controls
    """

    _instance = None
    _lock = threading.RLock()

    def __init__(self):
        """Initialize TraceManager with default configuration"""
        self._config = {
            # Master controls
            'global_enabled': False,
            'trace_level': 'debug',

            # Function filtering - enhanced to work better with caller context detection
            'include_modules': set(),
            'exclude_modules': {'logging.*', 'urllib3.*', 'requests.*', 'LoggingSuite.*'},
            'include_functions': set(),
            'exclude_functions': {'__init__', '__str__', '__repr__', '__unicode__', '__hash__',
                                  '_log_with_backend', '_get_actual_caller_context', 'get_caller_context'},

            # Performance controls
            'min_execution_time': 0.0,  # Only trace if execution > this (seconds)
            'max_trace_depth': 10,  # Prevent infinite recursion in traces
            'performance_threshold': 1.0,  # Log performance warnings above this

            # Exception handling
            'exception_key': 'exc_info',  # Standard structlog/stdlib key
            'capture_locals': False,  # Capture local variables in exceptions (dev only)

            # Environment-based defaults
            'auto_configure_by_environment': True,

            # Enhanced caller context integration
            'use_enhanced_caller_detection': True,  # Use improved caller context
            'skip_internal_frames': True,  # Skip LoggingSuite internal frames
        }

        # Runtime state
        self._trace_depth = 0
        self._traced_functions = set()  # Track what's being traced to prevent recursion

        # Auto-configure based on environment if enabled
        if self._config['auto_configure_by_environment']:
            self._configure_by_environment()

    @classmethod
    def get_instance(cls):
        """Get singleton instance of TraceManager"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    @classmethod
    def configure(cls, **config):
        """
        Configure global tracing settings

        Args:
            global_enabled (bool): Master switch for all tracing
            trace_level (str): Default log level for traces ('debug', 'info', etc.)
            include_modules (set/list): Module patterns to include (e.g., {'myapp.*'})
            exclude_modules (set/list): Module patterns to exclude
            include_functions (set/list): Specific function names to include
            exclude_functions (set/list): Specific function names to exclude
            min_execution_time (float): Only trace functions slower than this
            performance_threshold (float): Log performance warnings above this
            exception_key (str): Key to use for exception data in structured logs
            capture_locals (bool): Capture local variables in exceptions (security risk)
            use_enhanced_caller_detection (bool): Use improved caller context detection
            skip_internal_frames (bool): Skip LoggingSuite internal frames
        """
        instance = cls.get_instance()
        with cls._lock:
            # Convert lists to sets for faster lookup
            for key in ['include_modules', 'exclude_modules', 'include_functions', 'exclude_functions']:
                if key in config and isinstance(config[key], (list, tuple)):
                    config[key] = set(config[key])

            instance._config.update(config)

    @classmethod
    def enable_tracing(cls,
                       modules: Optional[List[str]] = None,
                       functions: Optional[List[str]] = None,
                       level: str = 'debug'):
        """
        Enable tracing for specific modules/functions

        Args:
            modules: List of module patterns to trace (e.g., ['myapp.*', 'services.payment'])
            functions: List of specific function names to trace
            level: Log level for traces
        """
        config = {'global_enabled': True, 'trace_level': level}

        if modules:
            config['include_modules'] = set(modules)

        if functions:
            config['include_functions'] = set(functions)

        cls.configure(**config)

    @classmethod
    def disable_tracing(cls):
        """Disable all tracing (fast path for performance)"""
        cls.configure(global_enabled=False)

    @classmethod
    def should_trace_function(cls, func_name: str, module_name: str) -> bool:
        """
        Determine if a function should be traced
        ENHANCED: Better filtering to work with improved caller context detection

        Args:
            func_name: Name of the function
            module_name: Module where function is defined

        Returns:
            bool: Whether function should be traced
        """
        instance = cls.get_instance()

        # Fast path: if tracing is globally disabled
        if not instance._config['global_enabled']:
            return False

        # Enhanced: Skip LoggingSuite internal functions automatically
        if instance._config['skip_internal_frames']:
            if (module_name and 'LoggingSuite' in module_name and
                    func_name in ['_log_with_backend', 'debug', 'info', 'warning', 'error', 'critical',
                                  'exception', 'bind', '__call__', '_process_log_data', 'format',
                                  '_format_message_with_context', '_get_actual_caller_context',
                                  'get_caller_context']):
                return False

        # Prevent recursion - don't trace if we're already tracing this function
        func_signature = f"{module_name}.{func_name}"
        if func_signature in instance._traced_functions:
            return False

        # Check trace depth limit
        if instance._trace_depth >= instance._config['max_trace_depth']:
            return False

        # Check explicit function inclusion
        include_functions = instance._config['include_functions']
        if include_functions and func_name not in include_functions:
            return False

        # Check explicit function exclusion
        exclude_functions = instance._config['exclude_functions']
        if func_name in exclude_functions:
            return False

        # Check module patterns
        include_modules = instance._config['include_modules']
        exclude_modules = instance._config['exclude_modules']

        # If include list exists, module must match one of the patterns
        if include_modules:
            if not any(fnmatch.fnmatch(module_name, pattern) for pattern in include_modules):
                return False

        # If exclude list exists, module must not match any pattern
        if exclude_modules:
            if any(fnmatch.fnmatch(module_name, pattern) for pattern in exclude_modules):
                return False

        return True

    @classmethod
    def should_log_execution_time(cls, execution_time: float) -> bool:
        """
        Determine if execution time should be logged based on threshold

        Args:
            execution_time: Function execution time in seconds

        Returns:
            bool: Whether execution time meets threshold for logging
        """
        instance = cls.get_instance()
        return execution_time >= instance._config['min_execution_time']

    @classmethod
    def is_performance_warning(cls, execution_time: float) -> bool:
        """
        Determine if execution time warrants a performance warning

        Args:
            execution_time: Function execution time in seconds

        Returns:
            bool: Whether execution time exceeds performance threshold
        """
        instance = cls.get_instance()
        return execution_time >= instance._config['performance_threshold']

    @classmethod
    def get_trace_config(cls) -> Dict[str, Any]:
        """Get current tracing configuration"""
        instance = cls.get_instance()
        return instance._config.copy()

    @classmethod
    def get_exception_key(cls) -> str:
        """Get the configured exception key for structured logging"""
        instance = cls.get_instance()
        return instance._config['exception_key']

    @classmethod
    def get_trace_level(cls) -> str:
        """Get the configured trace level"""
        instance = cls.get_instance()
        return instance._config['trace_level']

    @classmethod
    def enter_trace(cls, func_name: str, module_name: str):
        """Mark entry into a traced function (for recursion prevention)"""
        instance = cls.get_instance()
        func_signature = f"{module_name}.{func_name}"
        with cls._lock:
            instance._traced_functions.add(func_signature)
            instance._trace_depth += 1

    @classmethod
    def exit_trace(cls, func_name: str, module_name: str):
        """Mark exit from a traced function"""
        instance = cls.get_instance()
        func_signature = f"{module_name}.{func_name}"
        with cls._lock:
            instance._traced_functions.discard(func_signature)
            instance._trace_depth = max(0, instance._trace_depth - 1)

    def _configure_by_environment(self):
        """Auto-configure tracing based on environment variables and context"""
        # Check environment variables
        env_tracing = os.getenv('LOGGINGSUITE_TRACING', '').lower()
        if env_tracing in ('true', '1', 'on', 'enabled'):
            self._config['global_enabled'] = True
        elif env_tracing in ('false', '0', 'off', 'disabled'):
            self._config['global_enabled'] = False

        # Check for debug/development environment
        debug_env = os.getenv('DEBUG', '').lower()
        django_debug = os.getenv('DJANGO_DEBUG', '').lower()
        env_name = os.getenv('ENVIRONMENT', os.getenv('DJANGO_ENVIRONMENT', '')).lower()

        is_development = (
                debug_env in ('true', '1') or
                django_debug in ('true', '1') or
                env_name in ('development', 'dev', 'local')
        )

        is_production = env_name in ('production', 'prod')

        if is_development:
            # Development: Enable tracing with more detail
            self._config.update({
                'global_enabled': True,
                'trace_level': 'debug',
                'min_execution_time': 0.0,  # Trace everything
                'capture_locals': True,  # Safe in development
                'performance_threshold': 0.5,  # Lower threshold for dev
                'use_enhanced_caller_detection': True,  # Always use enhanced detection in dev
            })
        elif is_production:
            # Production: Minimal tracing for performance
            self._config.update({
                'global_enabled': False,  # Disabled by default in production
                'trace_level': 'warning',
                'min_execution_time': 1.0,  # Only slow functions
                'capture_locals': False,  # Security risk in production
                'performance_threshold': 2.0,  # Higher threshold for prod
                'use_enhanced_caller_detection': True,  # Still beneficial in production
            })


# Convenience functions for common use cases
def enable_development_tracing():
    """Enable tracing optimized for development with enhanced caller detection"""
    TraceManager.configure(
        global_enabled=True,
        trace_level='debug',
        min_execution_time=0.0,
        capture_locals=True,
        performance_threshold=0.5,
        include_modules={'__main__', 'MyApp.*'},  # Include main and app modules
        exclude_modules={'django.contrib.*', 'django.core.*', 'django.db.*', 'logging.*',
                         'urllib3.*', 'requests.*', 'LoggingSuite.*'},  # Enhanced exclusions
        use_enhanced_caller_detection=True,
        skip_internal_frames=True
    )


def enable_production_tracing(modules: Optional[List[str]] = None):
    """
    Enable minimal tracing for production with enhanced caller detection

    Args:
        modules: Specific modules to trace (default: none, manual enable required)
    """
    config = {
        'global_enabled': True,
        'trace_level': 'info',
        'min_execution_time': 1.0,  # Only slow functions
        'capture_locals': False,
        'performance_threshold': 3.0,
        'use_enhanced_caller_detection': True,
        'skip_internal_frames': True
    }

    if modules:
        config['include_modules'] = set(modules)

    TraceManager.configure(**config)


def disable_all_tracing():
    """Completely disable tracing for maximum performance"""
    TraceManager.disable_tracing()


def configure_tracing_for_module(module_pattern: str,
                                 level: str = 'debug',
                                 min_execution_time: float = 0.0):
    """
    Enable tracing for a specific module pattern with enhanced caller detection

    Args:
        module_pattern: Module pattern to trace (e.g., 'myapp.services.*')
        level: Log level for traces
        min_execution_time: Minimum execution time to log
    """
    TraceManager.configure(
        global_enabled=True,
        include_modules={module_pattern},
        trace_level=level,
        min_execution_time=min_execution_time,
        use_enhanced_caller_detection=True,
        skip_internal_frames=True
    )


def get_tracing_status() -> Dict[str, Any]:
    """
    Get current tracing status for debugging

    Returns:
        dict: Current tracing configuration and runtime state
    """
    config = TraceManager.get_trace_config()
    instance = TraceManager.get_instance()

    return {
        'enabled': config['global_enabled'],
        'trace_level': config['trace_level'],
        'current_depth': instance._trace_depth,
        'traced_functions_count': len(instance._traced_functions),
        'include_modules': list(config['include_modules']),
        'exclude_modules': list(config['exclude_modules']),
        'min_execution_time': config['min_execution_time'],
        'performance_threshold': config['performance_threshold'],
        'enhanced_caller_detection': config.get('use_enhanced_caller_detection', True),
        'skip_internal_frames': config.get('skip_internal_frames', True),
    }


# Context manager for temporary tracing
class TemporaryTracing:
    """Context manager for temporarily enabling/disabling tracing"""

    def __init__(self, enabled: bool = True, **config):
        """
        Initialize temporary tracing context

        Args:
            enabled: Whether to enable tracing in this context
            **config: Additional tracing configuration
        """
        self.enabled = enabled
        self.config = config
        self.original_config = None

    def __enter__(self):
        """Enter context - save current config and apply temporary config"""
        self.original_config = TraceManager.get_trace_config()

        if self.enabled:
            # Ensure enhanced caller detection is enabled by default
            config_with_defaults = {
                'use_enhanced_caller_detection': True,
                'skip_internal_frames': True,
                **self.config
            }
            TraceManager.configure(global_enabled=True, **config_with_defaults)
        else:
            TraceManager.configure(global_enabled=False)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore original configuration"""
        if self.original_config:
            TraceManager.configure(**self.original_config)


# Usage examples in docstring
__doc__ += """

Enhanced Usage Examples with Improved Caller Context:

# Global configuration with enhanced caller detection
from logging_suite.tracing import TraceManager, enable_development_tracing

# Enable enhanced tracing for development
enable_development_tracing()  # Now shows actual user functions, not LoggingSuite internals

# Manual configuration with enhanced caller detection
TraceManager.configure(
    global_enabled=True,
    include_modules={'myapp.*', 'services.*'},
    exclude_functions={'__init__', '__str__'},
    min_execution_time=0.1,  # Only functions slower than 100ms
    trace_level='info',
    use_enhanced_caller_detection=True,  # Show real caller functions
    skip_internal_frames=True           # Skip LoggingSuite internals
)

# Check if function should be traced (now respects enhanced caller detection)
should_trace = TraceManager.should_trace_function('process_payment', 'myapp.services')

# Temporary tracing context with enhanced detection
with TemporaryTracing(enabled=True, trace_level='debug', use_enhanced_caller_detection=True):
    # All functions traced at debug level with real caller context
    some_function()

# Check current status (includes enhanced caller detection status)
status = get_tracing_status()
print(f"Enhanced caller detection: {status['enhanced_caller_detection']}")
print(f"Skip internal frames: {status['skip_internal_frames']}")

# Environment variable control (enhanced detection enabled by default)
# LOGGINGSUITE_TRACING=true python myapp.py  # Enables enhanced tracing
# DEBUG=true python myapp.py                 # Auto-enables with enhanced detection

# Now when tracing is enabled, you'll see logs like:
# INFO - myapp.services - User payment processed [0.245s]
#   actual_function: process_payment
#   actual_module: myapp.services  
#   actual_file: payment_service.py
#   actual_line: 42
#
# Instead of:
# INFO - LoggingSuite.unified_logger - _log_with_backend completed [0.001s]
"""