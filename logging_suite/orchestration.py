# logging_suite/orchestration.py - Enhanced Configuration Orchestration Layer
"""
Orchestration layer that combines pure configuration with factory calls
ENHANCED: Added logger configuration management and inheritance capabilities
FIXED: Console format configuration in configure_development_logging
"""

from typing import Dict, Any, Optional, TYPE_CHECKING

from .config import (
    get_global_config, update_global_config, get_effective_config,
    build_development_config, build_production_config, build_json_config,
    build_cli_config, build_django_config, build_fastapi_config, build_flask_config,
    get_environment_overrides, resolve_exception_config_for_backend
)

if TYPE_CHECKING:
    from .unified_logger import UnifiedLogger


def configure_global_logging(**config) -> None:
    """
    Configure global logging settings and apply them
    ENHANCED: Now properly handles logger configuration inheritance
    """
    # Update the global configuration
    update_global_config(**config)

    # Get the effective configuration
    effective_config = get_effective_config()

    # Resolve auto exception settings if backend is specified
    if 'backend' in config:
        resolved_config = resolve_exception_config_for_backend(config['backend'], effective_config)
        update_global_config(**resolved_config)

    # Configure tracing if settings are provided
    _configure_tracing_from_config(effective_config)


def configure_development_logging() -> None:
    """Configure logging optimized for development with proper stream separation"""
    dev_config = build_development_config()
    configure_global_logging(**dev_config)

    # Force enable tracing after configuration
    _enable_development_tracing()

    print("🚀 Development logging configured with enhanced features:")
    print("   ✓ Standard logging backend (maximum compatibility)")
    print("   ✓ Console stream: Beautiful hierarchical output with colors and symbols")
    print("   ✓ File stream: Structured JSON for processing and analysis")
    print("   ✓ Enhanced styling with Unicode box drawing")
    print("   ✓ Unified processors for data enhancement")
    print("   ✓ Full tracing enabled")
    print("   ✓ Enhanced exception handling with local variables")


def configure_production_logging(base_directory: str = '/var/log/app',
                                 level: str = 'WARNING',
                                 rotation: str = '100 MB',
                                 retention: str = '30 days',
                                 enable_performance_tracing: bool = False) -> None:
    """Configure logging optimized for production"""
    prod_config = build_production_config(
        base_directory=base_directory,
        level=level,
        rotation=rotation,
        retention=retention,
        enable_performance_tracing=enable_performance_tracing
    )
    configure_global_logging(**prod_config)


def configure_json_logging(backend: str = 'standard',
                           level: str = 'INFO',
                           base_directory: str = 'logs',
                           console: bool = True,
                           rotation: str = '10 MB',
                           retention: str = '1 week',
                           enable_tracing: bool = None,
                           trace_modules: list = None,
                           pretty_json: bool = True,
                           enhanced_exceptions: bool = None) -> None:
    """Configure JSON logging with sensible defaults"""
    json_config = build_json_config(
        backend=backend,
        level=level,
        base_directory=base_directory,
        console=console,
        rotation=rotation,
        retention=retention,
        enable_tracing=enable_tracing,
        trace_modules=trace_modules,
        pretty_json=pretty_json,
        enhanced_exceptions=enhanced_exceptions
    )
    configure_global_logging(**json_config)


def configure_for_django() -> None:
    """Configure logging_suite for Django projects"""
    django_config = build_django_config()
    configure_global_logging(**django_config)

    # Configure tracing for Django app modules
    _configure_django_tracing()


def configure_for_fastapi() -> None:
    """Configure logging_suite for FastAPI projects"""
    fastapi_config = build_fastapi_config()
    configure_global_logging(**fastapi_config)


def configure_for_flask() -> None:
    """Configure logging_suite for Flask projects"""
    flask_config = build_flask_config()
    configure_global_logging(**flask_config)


def configure_for_cli() -> None:
    """Configure logging_suite for CLI applications"""
    cli_config = build_cli_config()
    configure_global_logging(**cli_config)


def configure_exception_handling(diagnosis: Optional[str] = None,
                                 backtrace: Optional[str] = None,
                                 depth: Optional[int] = None,
                                 locals_max_length: Optional[int] = None,
                                 show_values: Optional[bool] = None,
                                 colorize: Optional[bool] = None,
                                 backend_specific: Dict[str, Any] = None) -> Dict[str, Any]:
    """Configure exception handling behavior"""
    config_updates = {}

    if diagnosis is not None:
        config_updates['exception_diagnosis'] = diagnosis
    if backtrace is not None:
        config_updates['exception_backtrace'] = backtrace
    if depth is not None:
        config_updates['exception_depth'] = depth
    if locals_max_length is not None:
        config_updates['exception_locals_max_length'] = locals_max_length
    if show_values is not None:
        config_updates['exception_show_values'] = show_values
    if colorize is not None:
        config_updates['exception_colorize'] = colorize
    if backend_specific:
        config_updates.update(backend_specific)

    # Apply updates
    update_global_config(**config_updates)

    # Return current exception configuration
    current_config = get_global_config()
    return {k: v for k, v in current_config.items()
            if k.startswith('exception_') or k.startswith('loguru_')}


def enable_enhanced_exceptions(for_all_backends: bool = False,
                               loguru_native: bool = True,
                               show_locals: bool = True,
                               show_tracebacks: bool = True) -> None:
    """Enable enhanced exception handling with sensible defaults"""
    if for_all_backends:
        configure_exception_handling(
            diagnosis=True,
            backtrace=True,
            backend_specific={
                'enhance_loguru_exceptions': True,
                'loguru_diagnose': not loguru_native,
                'loguru_backtrace': not loguru_native
            }
        )
    else:
        configure_exception_handling(
            diagnosis='auto',
            backtrace='auto',
            backend_specific={
                'enhance_loguru_exceptions': False,
                'loguru_diagnose': loguru_native,
                'loguru_backtrace': loguru_native
            }
        )


def disable_enhanced_exceptions() -> None:
    """Disable all enhanced exception handling"""
    configure_exception_handling(
        diagnosis=False,
        backtrace=False,
        backend_specific={
            'enhance_loguru_exceptions': False,
            'loguru_diagnose': False,
            'loguru_backtrace': False
        }
    )


def get_available_backends() -> list:
    """Get list of available backends"""
    from .backends import get_available_backends
    return get_available_backends()


def ensure_environment_overrides_applied():
    """Apply environment variable overrides to current configuration"""
    env_overrides = get_environment_overrides()
    if env_overrides:
        update_global_config(**env_overrides)


def create_logger(name: str, backend: str = None, config: Dict[str, Any] = None) -> 'UnifiedLogger':
    """
    Create a logger using current configuration
    ENHANCED: Now properly inherits global configuration and respects per-logger overrides
    """
    from .factory import LoggerFactory
    from .backends import registry

    # Get effective configuration (this now includes per-logger overrides)
    if config is None:
        config = {}

    # Use provided backend or get from effective config
    if backend is None:
        from .unified_logger import get_effective_logger_config
        effective_config = get_effective_logger_config(name)
        backend = effective_config.get('backend', registry.get_default_backend())

    # Create logger with dependency injection
    return LoggerFactory.create_logger_with_registry(
        name=name,
        backend=backend,
        config=config,
        registry=registry
    )


# =============================================================================
# ENHANCED LOGGER CONFIGURATION MANAGEMENT
# =============================================================================

def set_logger_config(logger_name: str, config: Dict[str, Any], merge: bool = True) -> None:
    """
    Set configuration for a specific logger by name

    Args:
        logger_name: Name of the logger to configure
        config: Configuration dictionary
        merge: Whether to merge with existing config (True) or replace entirely (False)
    """
    from .unified_logger import set_logger_config as _set_logger_config
    _set_logger_config(logger_name, config, merge)


    # Install global exception hook based on environment or explicit flag
    should_install_hook = config.get('global_exception_hook')
    if should_install_hook is None:
        # Auto-detect based on environment
        import os
        env = os.getenv('ENVIRONMENT', '').lower()
        should_install_hook = env in ['development', 'dev', 'debug']

    if should_install_hook:
        try:
            from .global_exception_hook import install_global_exception_hook
            install_global_exception_hook(config)
        except ImportError:
            pass  # Module not available, skip installation

    # Install global exception hook if enabled
    if config.get('global_exception_hook', False):
        try:
            from .global_exception_hook import install_global_exception_hook
            install_global_exception_hook(config)
        except ImportError:
            pass  # Module not available, skip installation

    # Auto-install global exception hook in development
    if config.get('global_exception_hook', True):
        try:
            from .global_exception_hook import install_global_exception_hook
            install_global_exception_hook(config)
        except ImportError:
            pass  # Module not available, skip installation

def get_logger_config(logger_name: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific logger by name

    Args:
        logger_name: Name of the logger

    Returns:
        Configuration dictionary or None if no override exists
    """
    from .unified_logger import get_logger_config as _get_logger_config
    return _get_logger_config(logger_name)


def clear_logger_config(logger_name: str) -> bool:
    """
    Clear configuration override for a specific logger

    Args:
        logger_name: Name of the logger

    Returns:
        True if config was cleared, False if no config existed
    """
    from .unified_logger import clear_logger_config as _clear_logger_config
    return _clear_logger_config(logger_name)


def get_all_logger_configs() -> Dict[str, Dict[str, Any]]:
    """
    Get all per-logger configuration overrides

    Returns:
        Dictionary mapping logger names to their configurations
    """
    from .unified_logger import get_all_logger_configs as _get_all_logger_configs
    return _get_all_logger_configs()


def clear_all_logger_configs() -> None:
    """Clear all per-logger configuration overrides"""
    from .unified_logger import clear_all_logger_configs as _clear_all_logger_configs
    _clear_all_logger_configs()


def configure_logger_with_preset(logger_name: str, preset: str, **overrides) -> None:
    """
    Configure a logger with a predefined preset

    Args:
        logger_name: Name of the logger to configure
        preset: Preset name ('development', 'production', 'json', 'cli', 'django', 'fastapi', 'flask')
        **overrides: Additional configuration overrides
    """
    preset_configs = {
        'development': build_development_config(**overrides),
        'production': build_production_config(**overrides),
        'json': build_json_config(**overrides),
        'cli': build_cli_config(**overrides),
        'django': build_django_config(**overrides),
        'fastapi': build_fastapi_config(**overrides),
        'flask': build_flask_config(**overrides)
    }

    if preset not in preset_configs:
        raise ValueError(f"Unknown preset: {preset}. Available: {list(preset_configs.keys())}")

    config = preset_configs[preset]
    set_logger_config(logger_name, config, merge=False)


def get_logger_configuration_summary() -> Dict[str, Any]:
    """
    Get a summary of current logger configuration state

    Returns:
        Dictionary with comprehensive configuration summary
    """
    from .factory import LoggerFactory

    summary = {
        'global_config': get_global_config(),
        'per_logger_configs': get_all_logger_configs(),
        'total_configured_loggers': len(get_all_logger_configs()),
        'available_backends': get_available_backends(),
        'backend_status': LoggerFactory.get_backend_status(),
        'configuration_inheritance': {
            'global_config_active': True,
            'per_logger_overrides_count': len(get_all_logger_configs()),
            'environment_overrides': get_environment_overrides()
        }
    }

    # Add default backend info
    try:
        from .backends import registry
        summary['default_backend'] = registry.get_default_backend()
    except Exception as e:
        summary['default_backend'] = f"Error: {e}"

    return summary


def create_logger_with_inherited_config(name: str,
                                        config_overrides: Dict[str, Any] = None,
                                        temporary: bool = False) -> 'UnifiedLogger':
    """
    Create a logger that inherits global config with optional overrides

    Args:
        name: Logger name
        config_overrides: Configuration overrides to apply
        temporary: If True, don't store the config override permanently

    Returns:
        UnifiedLogger instance with proper configuration inheritance
    """
    if config_overrides and not temporary:
        # Store the override permanently
        set_logger_config(name, config_overrides, merge=True)

    # Create logger (it will automatically inherit the proper config)
    return create_logger(name, config=config_overrides if temporary else None)


def migrate_logger_configs_to_new_format() -> Dict[str, Any]:
    """
    Migrate any old logger configurations to the new format
    This is a utility function for upgrading existing installations

    Returns:
        Migration summary
    """
    migration_summary = {
        'migrated_configs': 0,
        'errors': [],
        'warnings': [],
        'success': True
    }

    # This would implement migration logic if needed
    # For now, it's a placeholder that ensures the new system is working

    try:
        # Validate that the configuration system is working
        test_config = {'level': 'DEBUG', 'console': True}
        set_logger_config('migration_test', test_config)

        retrieved_config = get_logger_config('migration_test')
        if retrieved_config != test_config:
            migration_summary['errors'].append("Configuration storage/retrieval test failed")
            migration_summary['success'] = False
        else:
            migration_summary['warnings'].append("Configuration system validation passed")

        # Clean up test config
        clear_logger_config('migration_test')

    except Exception as e:
        migration_summary['errors'].append(f"Migration validation failed: {e}")
        migration_summary['success'] = False

    return migration_summary


# =============================================================================
# PRIVATE HELPER FUNCTIONS
# =============================================================================

def _configure_tracing_from_config(config: Dict[str, Any]) -> None:
    """Configure tracing based on configuration"""
    if not config.get('tracing_enabled', False):
        return

    try:
        from .tracing import TraceManager

        tracing_config = {}

        # Extract tracing-specific settings
        tracing_keys = [
            'tracing_enabled', 'tracing_include_modules', 'tracing_exclude_modules',
            'tracing_exclude_functions', 'exception_key', 'min_execution_time',
            'performance_threshold'
        ]

        for key in tracing_keys:
            if key in config:
                # Convert to TraceManager key format
                trace_key = key.replace('tracing_', '') if key.startswith('tracing_') else key
                if trace_key == 'enabled':
                    trace_key = 'global_enabled'
                tracing_config[trace_key] = config[key]

        # Convert lists to sets for TraceManager
        for key in ['include_modules', 'exclude_modules', 'exclude_functions']:
            if key in tracing_config and isinstance(tracing_config[key], list):
                tracing_config[key] = set(tracing_config[key])

        TraceManager.configure(**tracing_config)

    except ImportError:
        # Tracing module not available
        pass


def _enable_development_tracing() -> None:
    """Enable development-optimized tracing"""
    try:
        from .tracing import enable_development_tracing
        enable_development_tracing()
    except ImportError:
        pass


def _configure_django_tracing() -> None:
    """Configure Django-specific tracing"""
    try:
        # Try to detect Django settings
        import os
        django_debug = os.getenv('DJANGO_DEBUG', 'false').lower() == 'true'

        if django_debug:
            try:
                from django.conf import settings
                if hasattr(settings, 'INSTALLED_APPS'):
                    # Get Django app modules for tracing
                    django_apps = [app for app in settings.INSTALLED_APPS
                                   if not app.startswith('django.') and '.' not in app]
                    if django_apps:
                        app_patterns = [f"{app}.*" for app in django_apps]
                        _configure_tracing_for_modules(app_patterns)
            except ImportError:
                pass

    except Exception:
        # Django not available or not configured
        pass


def _configure_tracing_for_modules(module_patterns: list) -> None:
    """Configure tracing for specific module patterns"""
    try:
        from .tracing import TraceManager
        TraceManager.configure(
            global_enabled=True,
            include_modules=set(module_patterns),
            exclude_modules={'django.*', 'logging.*'}
        )
    except ImportError:
        pass


# =============================================================================
# STREAM CONFIGURATION FUNCTIONS
# =============================================================================

def configure_streams(console_config: Dict[str, Any] = None, 
                     file_config: Dict[str, Any] = None) -> None:
    """
    Configure console and file streams with specific settings
    
    Args:
        console_config: Console stream configuration
        file_config: File stream configuration
    """
    stream_config = {}
    
    if console_config:
        stream_config['console_stream'] = console_config
    
    if file_config:
        stream_config['file_stream'] = file_config
    
    configure_global_logging(**stream_config)


def configure_console_stream_only(format_type: str = 'beautiful',
                                  use_colors: bool = True,
                                  use_symbols: bool = True,
                                  compact: bool = False) -> None:
    """
    Configure console stream only (no file output)
    
    Args:
        format_type: Format type ('beautiful', 'simple', 'detailed')
        use_colors: Enable colored output
        use_symbols: Enable Unicode symbols
        compact: Use compact formatting
    """
    console_config = {
        'enabled': True,
        'format': format_type,
        'use_colors': use_colors,
        'use_symbols': use_symbols,
        'compact_format': compact,
        'show_module': True,
        'show_function': True,
        'show_context': True
    }
    
    file_config = {
        'enabled': False
    }
    
    configure_streams(console_config=console_config, file_config=file_config)


def configure_file_stream_only(base_directory: str = 'logs',
                              format_type: str = 'json',
                              pretty_json: bool = True,
                              rotation: str = '10 MB',
                              retention: str = '7 days') -> None:
    """
    Configure file stream only (no console output)
    
    Args:
        base_directory: Directory for log files
        format_type: Format type ('json', 'structured', 'plain')
        pretty_json: Enable indented JSON
        rotation: File rotation size
        retention: File retention period
    """
    console_config = {
        'enabled': False
    }
    
    file_config = {
        'enabled': True,
        'format': format_type,
        'base_directory': base_directory,
        'pretty_json': pretty_json,
        'rotation': rotation,
        'retention': retention,
        'use_json_handlers': True
    }
    
    configure_streams(console_config=console_config, file_config=file_config)


def get_stream_configuration_summary() -> Dict[str, Any]:
    """
    Get summary of current stream configurations
    
    Returns:
        Dictionary with console and file stream status
    """
    current_config = get_global_config()
    
    return {
        'console_stream': {
            'enabled': current_config.get('console_stream', {}).get('enabled', True),
            'format': current_config.get('console_stream', {}).get('format', 'simple'),
            'colors': current_config.get('console_stream', {}).get('use_colors', False),
            'symbols': current_config.get('console_stream', {}).get('use_symbols', False)
        },
        'file_stream': {
            'enabled': current_config.get('file_stream', {}).get('enabled', False),
            'format': current_config.get('file_stream', {}).get('format', 'json'),
            'directory': current_config.get('file_stream', {}).get('base_directory', 'logs'),
            'rotation': current_config.get('file_stream', {}).get('rotation', '10 MB'),
            'retention': current_config.get('file_stream', {}).get('retention', '7 days')
        },
        'legacy_config_active': 'console' in current_config or 'file_logging' in current_config
    }