# logging_suite/__init__.py - Enhanced Orchestration Layer with Logger Configuration Management
"""
logging_suite - A unified logging package with pluggable backends
ENHANCED: Added comprehensive logger configuration management and inheritance
"""

# =============================================================================
# UTF-8 ENCODING FIX - Applied at module import
# =============================================================================

import sys
import codecs

# Force UTF-8 encoding for stdout to support emoji and special characters
if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    except (AttributeError, TypeError):
        # Fallback for environments where buffer isn't available
        pass

# =============================================================================
# VERSION AND METADATA
# =============================================================================

__version__ = "1.0.0"
__author__ = "logging_suite Team"
__license__ = "MIT"

# =============================================================================
# CORE IMPORTS - ALWAYS AVAILABLE
# =============================================================================

# Pure configuration (no circular imports)
from .config import (
    get_global_config,
    get_effective_config,
    get_sensitive_keys,
    configure_sensitive_keys,
    add_sensitive_keys,
    remove_sensitive_keys,
)

# Factory with dependency injection (no circular imports)
from .factory import LoggerFactory

# Orchestration layer (combines config + factory safely)
from .orchestration import (
    configure_global_logging,
    configure_json_logging,
    configure_development_logging,
    configure_production_logging,
    configure_exception_handling,
    enable_enhanced_exceptions,
    disable_enhanced_exceptions,
    configure_for_django,
    configure_for_fastapi,
    configure_for_flask,
    configure_for_cli,
    ensure_environment_overrides_applied,
    create_logger as _orchestration_create_logger,
    # ENHANCED: Logger configuration management functions
    set_logger_config,
    get_logger_config,
    clear_logger_config,
    get_all_logger_configs,
    clear_all_logger_configs,
    configure_logger_with_preset,
    get_logger_configuration_summary,
    create_logger_with_inherited_config,
    migrate_logger_configs_to_new_format,
    # ENHANCED: Stream configuration functions
    configure_streams,
    configure_console_stream_only,
    configure_file_stream_only,
    get_stream_configuration_summary,
)

# Core unified logger
from .unified_logger import UnifiedLogger


# =============================================================================
# BACKEND SYSTEM
# =============================================================================

def get_available_backends():
    """Get list of available logging backends"""
    from .backends import get_available_backends
    return get_available_backends()


# =============================================================================
# TRACING SYSTEM
# =============================================================================

try:
    from .tracing import (
        TraceManager,
        enable_development_tracing,
        enable_production_tracing,
        disable_all_tracing,
        configure_tracing_for_module,
        get_tracing_status,
        TemporaryTracing
    )

    HAS_TRACING = True
except ImportError:
    HAS_TRACING = False


    # No-op implementations
    class TraceManager:
        @staticmethod
        def configure(**kwargs): pass

        @staticmethod
        def should_trace_function(*args): return False

        @staticmethod
        def get_trace_config(): return {}

        @staticmethod
        def get_trace_level(): return 'info'

        @staticmethod
        def enter_trace(*args): pass

        @staticmethod
        def exit_trace(*args): pass


    def enable_development_tracing():
        pass


    def enable_production_tracing():
        pass


    def disable_all_tracing():
        pass


    def configure_tracing_for_module(*args, **kwargs):
        pass


    def get_tracing_status():
        return {'enabled': False}


    class TemporaryTracing:
        def __init__(self, *args, **kwargs): pass

        def __enter__(self): return self

        def __exit__(self, *args): pass

# =============================================================================
# ENHANCED DECORATORS
# =============================================================================

try:
    from .decorators import (
        catch,
        catch_and_log,
        log_execution_time,
        log_api_calls,
        log_database_operations,
        traced,
        FunctionTracing
    )

    HAS_DECORATORS = True
except ImportError:
    HAS_DECORATORS = False


    # No-op decorators
    def catch(*args, **kwargs):
        def decorator(func): return func

        return decorator


    catch_and_log = catch
    log_execution_time = catch
    log_api_calls = catch
    log_database_operations = catch
    traced = catch


    class FunctionTracing:
        def __init__(self, *args, **kwargs): pass

        def __enter__(self): return self

        def __exit__(self, *args): pass

# =============================================================================
# ENHANCED EXCEPTION HANDLING
# =============================================================================

try:
    from .exceptions import (
        get_unified_caller_context,
        get_exception_context,
        format_enhanced_traceback,
        format_exception_for_display,
        format_exception_for_json,
        create_exception_handler_for_backend
    )

    HAS_ENHANCED_EXCEPTIONS = True
except ImportError:
    HAS_ENHANCED_EXCEPTIONS = False


    # No-op exception functions
    def get_unified_caller_context(*args, **kwargs):
        return {}


    def get_exception_context(*args, **kwargs):
        return {}


    def format_enhanced_traceback(*args, **kwargs):
        return ""


    def format_exception_for_display(*args, **kwargs):
        return ""


    def format_exception_for_json(*args, **kwargs):
        return "{}"


    def create_exception_handler_for_backend(*args, **kwargs):
        return None

# =============================================================================
# GLOBAL EXCEPTION HOOK
# =============================================================================

try:
    from .global_exception_hook import (
        install_global_exception_hook,
        uninstall_global_exception_hook,
        is_global_exception_hook_installed
    )

    HAS_GLOBAL_EXCEPTION_HOOK = True
except ImportError:
    HAS_GLOBAL_EXCEPTION_HOOK = False


    # No-op global exception hook functions
    def install_global_exception_hook(*args, **kwargs):
        return False


    def uninstall_global_exception_hook(*args, **kwargs):
        return False


    def is_global_exception_hook_installed(*args, **kwargs):
        return False

# =============================================================================
# MIXINS
# =============================================================================

try:
    from .mixins import LoggingMixin, DjangoLoggingMixin

    HAS_MIXINS = True
except ImportError:
    HAS_MIXINS = False


    class LoggingMixin:
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.logger = None


    DjangoLoggingMixin = LoggingMixin

# =============================================================================
# BACKWARDS COMPATIBILITY
# =============================================================================

try:
    from .compatibility import (
        BackwardsCompatibleLogger,
        ConfigurationParser,
        MigrationHelper,
        migrate_from_django_logging,
        create_backwards_compatible_logger,
        test_compatibility
    )

    HAS_COMPATIBILITY = True
except ImportError:
    HAS_COMPATIBILITY = False


    # Basic compatibility implementations
    class BackwardsCompatibleLogger:
        def __init__(self, name, config=None):
            self.logger = get_logger(name)

        def __getattr__(self, name):
            return getattr(self.logger, name)


    def create_backwards_compatible_logger(name, **kwargs):
        return BackwardsCompatibleLogger(name)


    def test_compatibility():
        return {'success': True, 'details': []}


    def migrate_from_django_logging(*args):
        return {'error': 'Not available'}

# =============================================================================
# OPTIONAL FEATURES WITH GRACEFUL FALLBACK
# =============================================================================

# Context managers
try:
    from .context_managers import (
        log_execution_context,
        temporary_log_level
    )

    HAS_CONTEXT_MANAGERS = True
except ImportError:
    HAS_CONTEXT_MANAGERS = False


    class log_execution_context:
        def __init__(self, *args, **kwargs): pass

        def __enter__(self): return self

        def __exit__(self, *args): pass


    temporary_log_level = log_execution_context

# Styling and formatting
try:
    from .styling import (
        UnifiedConsoleFormatter,
        OutputStyle,
        LogLevel,
        PrettyJSONFormatter,
        CompactJSONFormatter,
        LogFileFormatter,
        create_formatter,
        create_pretty_json_formatter,
        get_formatter_for_handler
    )

    HAS_STYLING = True
except ImportError:
    HAS_STYLING = False

# Django utilities
try:
    from .django_utils import (
        get_current_request,
        set_current_request,
        clear_current_request
    )
    from .middleware import LoggingContextMiddleware

    HAS_DJANGO_UTILS = True
except ImportError:
    HAS_DJANGO_UTILS = False


    def get_current_request():
        return None


    def set_current_request(request):
        pass


    def clear_current_request():
        pass


    class LoggingContextMiddleware:
        def __init__(self, get_response=None):
            raise ImportError("Django is required for LoggingContextMiddleware")

# Analysis tools
try:
    from .analysis import LogAnalyzer, LogEntry

    HAS_ANALYSIS = True
except ImportError:
    HAS_ANALYSIS = False

# =============================================================================
# INTEGRATED TESTING SYSTEM
# =============================================================================

HAS_INTEGRATED_TESTS = False
_test_runner_class = None


def _get_test_runner_class():
    """Lazy import of test runner to avoid circular imports"""
    global _test_runner_class, HAS_INTEGRATED_TESTS

    if _test_runner_class is None:
        try:
            from .tests_integrated import LoggingSuiteTestRunner
            _test_runner_class = LoggingSuiteTestRunner
            HAS_INTEGRATED_TESTS = True
        except ImportError:
            HAS_INTEGRATED_TESTS = False
            _test_runner_class = False

    return _test_runner_class


def run_tests(quick: bool = False,
              verbose: bool = False,
              specific_test: str = None,
              benchmark: bool = False,
              coverage: bool = False) -> bool:
    """Run the integrated logging_suite test suite"""
    test_runner_class = _get_test_runner_class()

    if test_runner_class is False:
        print("⚠️  Integrated tests not available")
        return test_compatibility().get('success', False)

    runner = test_runner_class()
    return runner.run_tests(
        quick=quick,
        verbose=verbose,
        specific_test=specific_test,
        benchmark=benchmark,
        coverage=coverage
    )


def run_quick_tests() -> bool:
    """Run quick validation tests"""
    return run_tests(quick=True)


def get_available_tests() -> list:
    """Get list of available test classes"""
    test_runner_class = _get_test_runner_class()
    if test_runner_class is False:
        return ['test_compatibility']

    runner = test_runner_class()
    return runner.get_available_test_classes()


# =============================================================================
# MAIN API FUNCTIONS
# =============================================================================

def get_logger(name: str, **config) -> UnifiedLogger:
    """
    Get a logger with optional configuration
    ENHANCED: Now properly inherits global configuration and respects per-logger overrides
    """
    return _orchestration_create_logger(name, config=config)


# Convenience aliases
def getLogger(name: str, **config) -> UnifiedLogger:
    """Java-style convenience method"""
    return get_logger(name, **config)


def create_logger(name: str, **config) -> UnifiedLogger:
    """Factory-style convenience method"""
    return get_logger(name, **config)


def logger(name: str, **config) -> UnifiedLogger:
    """Minimal convenience method"""
    return get_logger(name, **config)


def quick_setup(level: str = 'INFO',
                format: str = 'json',
                console: bool = True,
                base_directory: str = 'logs',
                enable_tracing: bool = None,
                backend: str = 'standard',
                apply_env_overrides: bool = True,
                enhanced_exceptions: bool = None,
                global_exception_hook: bool = None) -> None:
    """Quick setup for logging_suite with sensible defaults"""

    # Auto-detect enhanced exceptions if not specified
    if enhanced_exceptions is None:
        import os
        env = os.getenv('ENVIRONMENT', os.getenv('DJANGO_ENVIRONMENT', 'development'))
        enhanced_exceptions = env.lower() in ('development', 'dev', 'local')

    # Auto-detect global exception hook if not specified
    if global_exception_hook is None:
        import os
        env = os.getenv('ENVIRONMENT', os.getenv('DJANGO_ENVIRONMENT', 'development'))
        global_exception_hook = env.lower() in ('development', 'dev', 'local')

    configure_global_logging(
        backend=backend,
        level=level,
        format=format,
        console=console,
        base_directory=base_directory,
        use_json_handlers=format == 'json',
        pretty_json=True,
        exception_diagnosis='auto' if enhanced_exceptions else False,
        exception_backtrace='auto' if enhanced_exceptions else True,
        exception_show_values=enhanced_exceptions,
        exception_colorize=enhanced_exceptions,
        global_exception_hook=global_exception_hook
    )

    # Auto-detect tracing if not specified
    if enable_tracing is None:
        import os
        env = os.getenv('ENVIRONMENT', os.getenv('DJANGO_ENVIRONMENT', 'development'))
        enable_tracing = env.lower() in ('development', 'dev', 'local')

    if enable_tracing and HAS_TRACING:
        enable_development_tracing()

    # Apply environment overrides if requested
    if apply_env_overrides:
        ensure_environment_overrides_applied()

    # Install global exception hook if enabled
    if global_exception_hook and HAS_GLOBAL_EXCEPTION_HOOK:
        install_global_exception_hook()


def get_package_info() -> dict:
    """Get information about logging_suite package"""
    return {
        'version': __version__,
        'author': __author__,
        'license': __license__,
        'available_backends': get_available_backends(),
        'features': {
            'context_managers': HAS_CONTEXT_MANAGERS,
            'styling': HAS_STYLING,
            'analysis': HAS_ANALYSIS,
            'django_utils': HAS_DJANGO_UTILS,
            'integrated_tests': HAS_INTEGRATED_TESTS,
            'enhanced_exceptions': HAS_ENHANCED_EXCEPTIONS,
            'tracing': HAS_TRACING,
            'decorators': HAS_DECORATORS,
            'mixins': HAS_MIXINS,
            'compatibility': HAS_COMPATIBILITY,
            'logger_config_management': True,  # ENHANCED: New feature
            'global_exception_hook': HAS_GLOBAL_EXCEPTION_HOOK,  # ENHANCED: New feature
        },
        'tracing_status': get_tracing_status() if HAS_TRACING else {'enabled': False},
        'package_location': __file__,
        'configuration_summary': get_logger_configuration_summary(),  # ENHANCED: New info
    }


# =============================================================================
# ENHANCED LOGGER CONFIGURATION API
# =============================================================================

def create_logger_with_config(name: str, config: dict, temporary: bool = False) -> UnifiedLogger:
    """
    Create a logger with specific configuration

    Args:
        name: Logger name
        config: Configuration dictionary
        temporary: If True, don't store the config permanently

    Returns:
        UnifiedLogger instance with specified configuration
    """
    return create_logger_with_inherited_config(name, config, temporary)


def configure_logger(name: str, **config) -> None:
    """
    Configure a specific logger

    Args:
        name: Logger name
        **config: Configuration options
    """
    set_logger_config(name, config, merge=True)


def reset_logger(name: str) -> bool:
    """
    Reset a logger to use global configuration

    Args:
        name: Logger name

    Returns:
        True if logger was reset, False if no override existed
    """
    return clear_logger_config(name)


def reset_all_loggers() -> None:
    """Reset all loggers to use global configuration"""
    clear_all_logger_configs()


def get_logger_status(name: str = None) -> dict:
    """
    Get status of logger(s)

    Args:
        name: Specific logger name, or None for all loggers

    Returns:
        Dictionary with logger status information
    """
    if name:
        # Status for specific logger
        config = get_logger_config(name)
        from .unified_logger import get_effective_logger_config
        return {
            'logger_name': name,
            'has_override': config is not None,
            'config_override': config,
            'effective_config': get_effective_logger_config(name)
        }
    else:
        # Status for all loggers
        return get_logger_configuration_summary()


def configure_multiple_loggers(configs: dict) -> None:
    """
    Configure multiple loggers at once

    Args:
        configs: Dictionary mapping logger names to their configurations
    """
    for logger_name, config in configs.items():
        set_logger_config(logger_name, config, merge=True)


def get_effective_logger_config(name: str) -> dict:
    """
    Get the effective configuration for a logger

    Args:
        name: Logger name

    Returns:
        Effective configuration dictionary
    """
    from .unified_logger import get_effective_logger_config as _get_effective
    return _get_effective(name)


def export_logger_configurations() -> dict:
    """
    Export all logger configurations for backup or migration

    Returns:
        Dictionary containing all configuration data
    """
    return LoggerFactory.export_logger_configurations()


def import_logger_configurations(config_data: dict, **options) -> dict:
    """
    Import logger configurations from exported data

    Args:
        config_data: Configuration data from export_logger_configurations
        **options: Import options (merge_global, clear_existing)

    Returns:
        Import results summary
    """
    return LoggerFactory.import_logger_configurations(config_data, **options)


def clone_logger_config(source_name: str, target_name: str) -> bool:
    """
    Clone configuration from one logger to another

    Args:
        source_name: Name of the source logger
        target_name: Name of the target logger

    Returns:
        True if configuration was cloned successfully
    """
    return LoggerFactory.clone_logger_config(source_name, target_name)


def validate_logger_config(name: str) -> dict:
    """
    Validate the configuration for a specific logger

    Args:
        name: Logger name

    Returns:
        Validation results
    """
    return LoggerFactory.validate_logger_configuration(name)


def create_multiple_loggers(logger_configs: dict) -> dict:
    """
    Create multiple loggers with their respective configurations

    Args:
        logger_configs: Dictionary mapping logger names to their configurations

    Returns:
        Dictionary mapping logger names to UnifiedLogger instances
    """
    return LoggerFactory.create_multiple_loggers(logger_configs)


# =============================================================================
# ADVANCED CONFIGURATION FEATURES
# =============================================================================

def configure_logger_hierarchy(hierarchy_config: dict) -> None:
    """
    Configure a hierarchy of loggers with inheritance

    Args:
        hierarchy_config: Nested dictionary defining logger hierarchy

    Example:
        configure_logger_hierarchy({
            'myapp': {
                'level': 'INFO',
                'format': 'json',
                'children': {
                    'database': {'level': 'DEBUG'},
                    'api': {'level': 'WARNING', 'file_path': 'api.log'}
                }
            }
        })
    """

    def _configure_hierarchy(config, parent_name=""):
        for logger_name, logger_config in config.items():
            # Build full logger name
            full_name = f"{parent_name}.{logger_name}" if parent_name else logger_name

            # Extract children config
            children = logger_config.pop('children', {})

            # Configure this logger
            if logger_config:
                set_logger_config(full_name, logger_config, merge=True)

            # Recursively configure children
            if children:
                _configure_hierarchy(children, full_name)

    _configure_hierarchy(hierarchy_config)


def setup_logging_profiles(profiles: dict) -> None:
    """
    Set up multiple logging profiles that can be easily switched between

    Args:
        profiles: Dictionary mapping profile names to configurations

    Example:
        setup_logging_profiles({
            'development': {'level': 'DEBUG', 'console': True},
            'production': {'level': 'WARNING', 'file_path': 'app.log'},
            'testing': {'level': 'ERROR', 'console': False}
        })
    """
    # Store profiles in a way that can be retrieved later
    global _logging_profiles
    _logging_profiles = profiles.copy()


def activate_logging_profile(profile_name: str) -> bool:
    """
    Activate a logging profile

    Args:
        profile_name: Name of the profile to activate

    Returns:
        True if profile was activated successfully
    """
    global _logging_profiles

    if not hasattr(activate_logging_profile, '_profiles_initialized'):
        _logging_profiles = {}

    if profile_name not in _logging_profiles:
        return False

    profile_config = _logging_profiles[profile_name]
    configure_global_logging(**profile_config)
    return True


def get_active_logging_profile() -> str:
    """
    Get the name of the currently active logging profile

    Returns:
        Profile name or 'custom' if no profile is active
    """
    # This would require tracking which profile is active
    # For now, return 'custom' as we don't track this yet
    return 'custom'


# =============================================================================
# USAGE EXAMPLES FOR ENHANCED FEATURES
# =============================================================================

def _example_usage_patterns():
    """
    Example usage patterns for enhanced logger configuration features
    (This function is not exported - it's just for documentation)
    """

    # Pattern 1: Global setup with per-logger overrides
    quick_setup(level='INFO', format='json', console=True)
    configure_logger('myapp.database', level='DEBUG', format='console')

    # Pattern 2: Runtime reconfiguration
    logger = get_logger('myapp.service')
    debug_logger = logger.set_config({'level': 'DEBUG', 'tracing_enabled': True})

    # Pattern 3: Temporary configurations
    temp_logger = create_logger_with_config('myapp.temp', {'level': 'ERROR'}, temporary=True)

    # Pattern 4: Bulk configuration
    configure_multiple_loggers({
        'myapp.user': {'level': 'INFO', 'file_path': 'users.log'},
        'myapp.payment': {'level': 'WARNING', 'file_path': 'payments.log'}
    })

    # Pattern 5: Configuration management
    status = get_logger_status('myapp.database')
    reset_logger('myapp.database')
    reset_all_loggers()

    # Pattern 6: Configuration backup/restore
    backup = export_logger_configurations()
    import_logger_configurations(backup, clear_existing=True)

    # Pattern 7: Hierarchical configuration
    configure_logger_hierarchy({
        'myapp': {
            'level': 'INFO',
            'children': {
                'database': {'level': 'DEBUG'},
                'api': {'level': 'WARNING'}
            }
        }
    })


# Initialize global variables
_logging_profiles = {}

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Version info
    '__version__',

    # Core components
    'LoggerFactory',
    'UnifiedLogger',

    # Configuration (orchestration layer)
    'configure_global_logging',
    'configure_json_logging',
    'configure_development_logging',
    'configure_production_logging',
    'get_global_config',
    'get_available_backends',
    'get_effective_config',
    'ensure_environment_overrides_applied',

    # ENHANCED: Stream configuration functions
    'configure_streams',
    'configure_console_stream_only',
    'configure_file_stream_only',
    'get_stream_configuration_summary',

    # ENHANCED: Logger configuration management
    'set_logger_config',
    'get_logger_config',
    'clear_logger_config',
    'get_all_logger_configs',
    'clear_all_logger_configs',
    'configure_logger_with_preset',
    'get_logger_configuration_summary',
    'create_logger_with_inherited_config',
    'migrate_logger_configs_to_new_format',
    'configure_logger',
    'reset_logger',
    'reset_all_loggers',
    'get_logger_status',
    'configure_multiple_loggers',
    'create_logger_with_config',
    'get_effective_logger_config',
    'export_logger_configurations',
    'import_logger_configurations',
    'clone_logger_config',
    'validate_logger_config',
    'create_multiple_loggers',
    'configure_logger_hierarchy',
    'setup_logging_profiles',
    'activate_logging_profile',
    'get_active_logging_profile',

    # Exception handling configuration
    'configure_exception_handling',
    'enable_enhanced_exceptions',
    'disable_enhanced_exceptions',

    # Exception handling functions
    'get_unified_caller_context',
    'get_exception_context',
    'format_enhanced_traceback',
    'format_exception_for_display',
    'format_exception_for_json',
    'create_exception_handler_for_backend',

    # Tracing
    'TraceManager',
    'enable_development_tracing',
    'enable_production_tracing',
    'disable_all_tracing',
    'configure_tracing_for_module',
    'get_tracing_status',
    'TemporaryTracing',
    'configure_for_django',
    'configure_for_fastapi',
    'configure_for_flask',
    'configure_for_cli',

    # Decorators
    'catch',
    'catch_and_log',
    'log_execution_time',
    'log_api_calls',
    'log_database_operations',
    'traced',
    'FunctionTracing',

    # Mixins
    'LoggingMixin',
    'DjangoLoggingMixin',

    # Backwards compatibility
    'BackwardsCompatibleLogger',
    'create_backwards_compatible_logger',
    'test_compatibility',
    'migrate_from_django_logging',

    # Django utilities
    'get_current_request',
    'set_current_request',
    'clear_current_request',
    'LoggingContextMiddleware',

    # Context managers
    'log_execution_context',
    'temporary_log_level',

    # Testing system
    'run_tests',
    'run_quick_tests',
    'get_available_tests',

    # Main API
    'get_logger',
    'getLogger',
    'create_logger',
    'logger',
    'quick_setup',
    'get_package_info',

    # Sensitive keys
    'get_sensitive_keys',
    'configure_sensitive_keys',
    'add_sensitive_keys',
    'remove_sensitive_keys',

    # Global exception hook
    'install_global_exception_hook',
    'uninstall_global_exception_hook',
    'is_global_exception_hook_installed',

    # Feature flags
    'HAS_CONTEXT_MANAGERS',
    'HAS_STYLING',
    'HAS_ANALYSIS',
    'HAS_DJANGO_UTILS',
    'HAS_INTEGRATED_TESTS',
    'HAS_ENHANCED_EXCEPTIONS',
    'HAS_GLOBAL_EXCEPTION_HOOK',
    'HAS_TRACING',
    'HAS_DECORATORS',
    'HAS_MIXINS',
    'HAS_COMPATIBILITY',
]

# Conditionally add optional features to __all__
if HAS_STYLING:
    __all__.extend([
        'UnifiedConsoleFormatter',
        'OutputStyle',
        'LogLevel',
        'PrettyJSONFormatter',
        'CompactJSONFormatter',
        'LogFileFormatter',
        'create_formatter',
        'create_pretty_json_formatter',
        'get_formatter_for_handler'
    ])

if HAS_ANALYSIS:
    __all__.extend(['LogAnalyzer', 'LogEntry'])

# Framework integration removed - using decorator-only approach for clean exception formatting