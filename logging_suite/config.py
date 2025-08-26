# logging_suite/config.py - Pure Configuration Layer
"""
Pure configuration storage and retrieval for logging_suite
FIXED: No factory imports, no circular dependencies
"""

import os
from typing import Dict, Any, List, Optional

# Global configuration storage - pure data, no imports
_global_config: Dict[str, Any] = {
    # Backend configuration
    'backend': 'standard',
    'level': 'INFO',
    'console': True,
    'base_directory': 'logs',
    'filename_template': '{class_name}_{instance_id}_{timestamp}.log',

    # Format configuration
    'format': 'json',
    'use_json_handlers': True,
    'pretty_json': True,
    'json_indent': 2,
    'json_separators': (', ', ': '),

    # File handling
    'rotation': '10 MB',
    'retention': '1 week',

    # Tracing configuration
    'tracing_enabled': False,
    'tracing_include_modules': [],
    'tracing_exclude_modules': ['django.*', 'logging.*', 'urllib3.*', 'requests.*'],
    'tracing_exclude_functions': ['__init__', '__str__', '__repr__', '__unicode__', '__hash__'],
    'exception_key': 'exc_info',
    'min_execution_time': 0.0,
    'performance_threshold': 1.0,

    # Exception handling configuration
    'exception_diagnosis': 'auto',
    'exception_backtrace': 'auto',
    'exception_depth': 10,
    'exception_locals_max_length': 100,
    'exception_show_values': True,
    'exception_colorize': True,

    # Backend-specific exception settings
    'loguru_diagnose': True,
    'loguru_backtrace': True,
    'enhance_loguru_exceptions': False,

    # Styling configuration
    'use_colors': True,
    'use_symbols': True,
    'compact_format': False,
    'show_module': True,
    'show_function': False,
    'show_context': True,
    'highlight_keywords': ['ERROR', 'SUCCESS', 'FAILED', 'WARNING', 'COMPLETED', 'STARTED'],

    # Sensitive key sanitization
    'sensitive_keys': [
        'password', 'passwd', 'pwd', 'token', 'secret', 'key', 'auth',
        'credential', 'api_key', 'private_key', 'access_token',
        'refresh_token', 'session_key', 'ssn', 'social_security',
        'credit_card', 'ccn', 'cvv', 'pin', 'authorization'
    ],

    # Global exception hook configuration
    'global_exception_hook': False,
    'include_system_info': True,
    'exception_hook_level': 'error',
    
    # Console output section controls
    'show_exception_details': True,
    'show_system_state': True,
    'show_stack_trace': True,
    'show_code_context': True,
    'show_environment_vars': True,
    
    # Pretty printing options for stack trace data
    'pretty_print_stack_data': True,
    'stack_data_max_length': 200,
    'stack_data_max_depth': 3,
    
    # Output styling options (beautiful is the default, pprint for legacy JSON support)
    'exception_output_style': 'beautiful',  # 'beautiful' or 'pprint' 
    'console_output_style': 'beautiful',    # 'beautiful' or 'pprint'
    
    # Console log styling (for regular log messages, not exceptions)
    'console_log_style': 'hierarchical',    # 'hierarchical', 'plain', 'compact', 'card', 'minimal'
}


# =============================================================================
# PURE CONFIGURATION FUNCTIONS - NO IMPORTS
# =============================================================================

def get_global_config() -> Dict[str, Any]:
    """Get current global configuration (pure data access)"""
    return _global_config.copy()


def update_global_config(**config) -> None:
    """Update global configuration (pure data storage)"""
    global _global_config
    _global_config.update(config)


def reset_global_config() -> None:
    """Reset configuration to defaults"""
    global _global_config
    # Reset to default values (defined above)
    default_config = {
        'backend': 'standard',
        'level': 'INFO',
        'console': True,
        'base_directory': 'logs',
        'filename_template': '{class_name}_{instance_id}_{timestamp}.log',
        'format': 'json',
        'use_json_handlers': True,
        'pretty_json': True,
        'json_indent': 2,
        'json_separators': (', ', ': '),
        'rotation': '10 MB',
        'retention': '1 week',
        'tracing_enabled': False,
        'tracing_include_modules': [],
        'tracing_exclude_modules': ['django.*', 'logging.*', 'urllib3.*', 'requests.*'],
        'tracing_exclude_functions': ['__init__', '__str__', '__repr__', '__unicode__', '__hash__'],
        'exception_key': 'exc_info',
        'min_execution_time': 0.0,
        'performance_threshold': 1.0,
        'exception_diagnosis': 'auto',
        'exception_backtrace': 'auto',
        'exception_depth': 10,
        'exception_locals_max_length': 100,
        'exception_show_values': True,
        'exception_colorize': True,
        'loguru_diagnose': True,
        'loguru_backtrace': True,
        'enhance_loguru_exceptions': False,
        'use_colors': True,
        'use_symbols': True,
        'compact_format': False,
        'show_module': True,
        'show_function': False,
        'show_context': True,
        'highlight_keywords': ['ERROR', 'SUCCESS', 'FAILED', 'WARNING', 'COMPLETED', 'STARTED'],
        'sensitive_keys': [
            'password', 'passwd', 'pwd', 'token', 'secret', 'key', 'auth',
            'credential', 'api_key', 'private_key', 'access_token',
            'refresh_token', 'session_key', 'ssn', 'social_security',
            'credit_card', 'ccn', 'cvv', 'pin', 'authorization'
        ],
        'global_exception_hook': False,
        'include_system_info': True,
        'exception_hook_level': 'error',
        'show_exception_details': True,
        'show_system_state': True,
        'show_stack_trace': True,
        'show_code_context': True,
        'show_environment_vars': True,
        'pretty_print_stack_data': True,
        'stack_data_max_length': 200,
        'stack_data_max_depth': 3,
        'exception_output_style': 'beautiful',
        'console_output_style': 'beautiful',
        'console_log_style': 'hierarchical'
    }
    _global_config = default_config


def get_environment_overrides() -> Dict[str, Any]:
    """Get configuration overrides from environment variables"""
    env_overrides = {}

    # Basic logging settings
    if os.getenv('LOGGINGSUITE_LEVEL'):
        env_overrides['level'] = os.getenv('LOGGINGSUITE_LEVEL').upper()

    if os.getenv('LOGGINGSUITE_FORMAT'):
        env_overrides['format'] = os.getenv('LOGGINGSUITE_FORMAT').lower()

    if os.getenv('LOGGINGSUITE_BACKEND'):
        env_overrides['backend'] = os.getenv('LOGGINGSUITE_BACKEND').lower()

    # Console/pretty settings
    console_env = os.getenv('LOGGINGSUITE_CONSOLE', '').lower()
    if console_env in ('true', '1', 'on', 'enabled'):
        env_overrides['console'] = True
    elif console_env in ('false', '0', 'off', 'disabled'):
        env_overrides['console'] = False

    pretty_env = os.getenv('LOGGINGSUITE_PRETTY_JSON', '').lower()
    if pretty_env in ('true', '1', 'on', 'enabled'):
        env_overrides['pretty_json'] = True
    elif pretty_env in ('false', '0', 'off', 'disabled'):
        env_overrides['pretty_json'] = False

    # Tracing control
    tracing_env = os.getenv('LOGGINGSUITE_TRACING', '').lower()
    if tracing_env in ('true', '1', 'on', 'enabled'):
        env_overrides['tracing_enabled'] = True
    elif tracing_env in ('false', '0', 'off', 'disabled'):
        env_overrides['tracing_enabled'] = False

    if os.getenv('LOGGINGSUITE_TRACE_MODULES'):
        modules = os.getenv('LOGGINGSUITE_TRACE_MODULES').split(',')
        env_overrides['tracing_include_modules'] = [m.strip() for m in modules]

    # Performance settings
    if os.getenv('LOGGINGSUITE_PERF_THRESHOLD'):
        try:
            env_overrides['performance_threshold'] = float(os.getenv('LOGGINGSUITE_PERF_THRESHOLD'))
        except ValueError:
            pass

    # Exception handling settings
    exception_diagnosis_env = os.getenv('LOGGINGSUITE_EXCEPTION_DIAGNOSIS', '').lower()
    if exception_diagnosis_env in ('true', '1', 'on', 'enabled'):
        env_overrides['exception_diagnosis'] = True
    elif exception_diagnosis_env in ('false', '0', 'off', 'disabled'):
        env_overrides['exception_diagnosis'] = False
    elif exception_diagnosis_env == 'auto':
        env_overrides['exception_diagnosis'] = 'auto'

    exception_backtrace_env = os.getenv('LOGGINGSUITE_EXCEPTION_BACKTRACE', '').lower()
    if exception_backtrace_env in ('true', '1', 'on', 'enabled'):
        env_overrides['exception_backtrace'] = True
    elif exception_backtrace_env in ('false', '0', 'off', 'disabled'):
        env_overrides['exception_backtrace'] = False
    elif exception_backtrace_env == 'auto':
        env_overrides['exception_backtrace'] = 'auto'

    if os.getenv('LOGGINGSUITE_EXCEPTION_DEPTH'):
        try:
            env_overrides['exception_depth'] = int(os.getenv('LOGGINGSUITE_EXCEPTION_DEPTH'))
        except ValueError:
            pass

    # Loguru-specific settings
    loguru_diagnose_env = os.getenv('LOGGINGSUITE_LOGURU_DIAGNOSE', '').lower()
    if loguru_diagnose_env in ('true', '1', 'on', 'enabled'):
        env_overrides['loguru_diagnose'] = True
    elif loguru_diagnose_env in ('false', '0', 'off', 'disabled'):
        env_overrides['loguru_diagnose'] = False

    # Sensitive keys
    if os.getenv('LOGGINGSUITE_SENSITIVE_KEYS'):
        keys = os.getenv('LOGGINGSUITE_SENSITIVE_KEYS').split(',')
        env_overrides['sensitive_keys'] = [k.strip() for k in keys]

    # Global exception hook settings
    global_hook_env = os.getenv('LOGGINGSUITE_GLOBAL_EXCEPTION_HOOK', '').lower()
    if global_hook_env in ('true', '1', 'on', 'enabled'):
        env_overrides['global_exception_hook'] = True
    elif global_hook_env in ('false', '0', 'off', 'disabled'):
        env_overrides['global_exception_hook'] = False

    system_info_env = os.getenv('LOGGINGSUITE_INCLUDE_SYSTEM_INFO', '').lower()
    if system_info_env in ('true', '1', 'on', 'enabled'):
        env_overrides['include_system_info'] = True
    elif system_info_env in ('false', '0', 'off', 'disabled'):
        env_overrides['include_system_info'] = False

    if os.getenv('LOGGINGSUITE_EXCEPTION_HOOK_LEVEL'):
        level = os.getenv('LOGGINGSUITE_EXCEPTION_HOOK_LEVEL').upper()
        if level in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
            env_overrides['exception_hook_level'] = level.lower()

    # Console output section controls
    section_controls = {
        'LOGGINGSUITE_SHOW_EXCEPTION_DETAILS': 'show_exception_details',
        'LOGGINGSUITE_SHOW_SYSTEM_STATE': 'show_system_state',
        'LOGGINGSUITE_SHOW_STACK_TRACE': 'show_stack_trace',
        'LOGGINGSUITE_SHOW_CODE_CONTEXT': 'show_code_context',
        'LOGGINGSUITE_SHOW_ENVIRONMENT_VARS': 'show_environment_vars',
        'LOGGINGSUITE_PRETTY_PRINT_STACK_DATA': 'pretty_print_stack_data'
    }

    for env_var, config_key in section_controls.items():
        env_value = os.getenv(env_var, '').lower()
        if env_value in ('true', '1', 'on', 'enabled'):
            env_overrides[config_key] = True
        elif env_value in ('false', '0', 'off', 'disabled'):
            env_overrides[config_key] = False

    # Stack data formatting options
    if os.getenv('LOGGINGSUITE_STACK_DATA_MAX_LENGTH'):
        try:
            env_overrides['stack_data_max_length'] = int(os.getenv('LOGGINGSUITE_STACK_DATA_MAX_LENGTH'))
        except ValueError:
            pass

    if os.getenv('LOGGINGSUITE_STACK_DATA_MAX_DEPTH'):
        try:
            env_overrides['stack_data_max_depth'] = int(os.getenv('LOGGINGSUITE_STACK_DATA_MAX_DEPTH'))
        except ValueError:
            pass

    # Output styling options
    if os.getenv('LOGGINGSUITE_EXCEPTION_OUTPUT_STYLE'):
        style = os.getenv('LOGGINGSUITE_EXCEPTION_OUTPUT_STYLE').lower()
        if style in ('beautiful', 'pprint'):
            env_overrides['exception_output_style'] = style
            
    if os.getenv('LOGGINGSUITE_CONSOLE_OUTPUT_STYLE'):
        style = os.getenv('LOGGINGSUITE_CONSOLE_OUTPUT_STYLE').lower()
        if style in ('beautiful', 'pprint'):
            env_overrides['console_output_style'] = style
    
    if os.getenv('LOGGINGSUITE_CONSOLE_LOG_STYLE'):
        style = os.getenv('LOGGINGSUITE_CONSOLE_LOG_STYLE').lower()
        if style in ('hierarchical', 'standard', 'compact', 'card', 'minimal'):
            env_overrides['console_log_style'] = style

    return env_overrides


def get_environment_based_config() -> Dict[str, Any]:
    """Get configuration based on environment (development/production/etc)"""
    env = os.getenv('DJANGO_ENVIRONMENT', os.getenv('ENVIRONMENT', 'development'))

    env_configs = {
        'production': {
            'level': 'WARNING',
            'console': False,
            'format': 'json',
            'use_json_handlers': True,
            'pretty_json': False,
            'rotation': '50 MB',
            'retention': '30 days',
            'tracing_enabled': False,
            'min_execution_time': 2.0,
            'performance_threshold': 5.0,
            'exception_key': 'exc_info',
            'use_colors': False,
            'use_symbols': False,
            'compact_format': True,
            'exception_diagnosis': False,
            'exception_backtrace': True,
            'exception_show_values': False,
            'exception_colorize': False,
        },
        'staging': {
            'level': 'INFO',
            'console': True,
            'format': 'json',
            'use_json_handlers': True,
            'pretty_json': False,
            'rotation': '20 MB',
            'retention': '7 days',
            'tracing_enabled': True,
            'min_execution_time': 0.5,
            'performance_threshold': 2.0,
            'tracing_include_modules': ['myapp.*'],
            'exception_key': 'exc_info',
            'use_colors': True,
            'use_symbols': False,
            'compact_format': True,
            'exception_diagnosis': False,
            'exception_backtrace': True,
            'exception_show_values': False,
            'exception_colorize': True,
        },
        'testing': {
            'level': 'ERROR',
            'console': False,
            'use_file': False,
            'format': 'json',
            'use_json_handlers': True,
            'pretty_json': False,
            'tracing_enabled': False,
            'min_execution_time': 10.0,
            'exception_key': 'exc_info',
            'use_colors': False,
            'use_symbols': False,
            'compact_format': True,
            'exception_diagnosis': False,
            'exception_backtrace': False,
            'exception_show_values': False,
            'exception_colorize': False,
        },
        'development': {
            'level': 'DEBUG',
            'console': True,
            'format': 'console',
            'use_json_handlers': True,
            'pretty_json': True,
            'json_indent': 2,
            'json_separators': (', ', ': '),
            'tracing_enabled': True,
            'min_execution_time': 0.0,
            'performance_threshold': 0.5,
            'tracing_exclude_modules': ['django.*', 'logging.*'],
            'exception_key': 'exc_info',
            'use_colors': True,
            'use_symbols': True,
            'compact_format': False,
            'show_module': True,
            'show_function': True,
            'show_context': True,
            'exception_diagnosis': True,
            'exception_backtrace': True,
            'exception_show_values': True,
            'exception_colorize': True,
            'global_exception_hook': True,
            'include_system_info': True,
            'exception_hook_level': 'error',
            'show_exception_details': True,
            'show_system_state': True,
            'show_stack_trace': True,
            'show_code_context': True,
            'show_environment_vars': True,
            'pretty_print_stack_data': True,
            'stack_data_max_length': 500,  # More verbose in development
            'stack_data_max_depth': 5,
            'exception_output_style': 'beautiful',  # Use beautiful formatting in development
            'console_output_style': 'beautiful',
        }
    }

    return env_configs.get(env, env_configs['development'])


def resolve_exception_config_for_backend(backend: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Resolve 'auto' exception configuration settings based on backend capabilities
    Pure function - no imports
    """
    if config is None:
        config = get_global_config()

    resolved_config = config.copy()
    backend_lower = backend.lower()

    # Resolve 'auto' settings based on backend
    if resolved_config.get('exception_diagnosis') == 'auto':
        if backend_lower == 'loguru':
            resolved_config['exception_diagnosis'] = False  # Let loguru handle it
        else:
            resolved_config['exception_diagnosis'] = True

    if resolved_config.get('exception_backtrace') == 'auto':
        if backend_lower == 'loguru':
            resolved_config['exception_backtrace'] = False  # Let loguru handle it
        else:
            resolved_config['exception_backtrace'] = True

    return resolved_config


def merge_configs(*configs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple configuration dictionaries (later configs override earlier ones)"""
    merged = {}
    for config in configs:
        if config:
            merged.update(config)
    return merged


def get_effective_config(custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get the effective configuration by merging global, environment, and custom configs"""
    # Start with global config
    effective_config = get_global_config()

    # Apply environment-based config
    env_based_config = get_environment_based_config()
    effective_config.update(env_based_config)

    # Apply environment variable overrides
    env_overrides = get_environment_overrides()
    effective_config.update(env_overrides)

    # Apply custom config
    if custom_config:
        effective_config.update(custom_config)

    return effective_config


# =============================================================================
# CONFIGURATION PRESET BUILDERS - PURE DATA FUNCTIONS
# =============================================================================

def build_development_config(**overrides) -> Dict[str, Any]:
    """Build development configuration preset with proper stream separation"""
    config = {
        'backend': 'standard',
        'level': 'DEBUG',
        
        # Console stream configuration - Beautiful hierarchical output for developers
        'console_stream': {
            'enabled': True,
            'format': 'beautiful',     # Hierarchical Unicode rendering
            'use_colors': True,        # Color-coded log levels
            'use_symbols': True,       # Unicode symbols and box drawing
            'show_module': True,       # Show module names
            'show_function': True,     # Show function names
            'show_context': True,      # Show structured context
            'compact_format': False,   # Full detailed format
            'highlight_keywords': ['ERROR', 'SUCCESS', 'FAILED', 'WARNING', 'COMPLETED', 'STARTED'],
        },
        
        # File stream configuration - Structured JSON for processing
        'file_stream': {
            'enabled': True,
            'format': 'json',          # Structured JSON format
            'base_directory': 'logs',
            'pretty_json': True,       # Indented JSON for readability
            'json_indent': 2,
            'json_separators': (', ', ': '),
            'use_json_handlers': True,
            'rotation': '10 MB',       # File rotation
            'retention': '30 days',    # File retention
        },
        
        # Legacy compatibility (deprecated, but maintained for backward compatibility)
        'console': True,
        'format': 'beautiful',         # Default to beautiful for development
        'file_logging': True,
        'base_directory': 'logs',
        'use_colors': True,
        'use_symbols': True,
        'show_module': True,
        'show_function': True,
        'show_context': True,
        'compact_format': False,
        'pretty_json': True,
        'json_indent': 2,
        'json_separators': (', ', ': '),
        'tracing_enabled': True,
        'min_execution_time': 0.0,
        'performance_threshold': 0.5,
        'tracing_exclude_modules': ['django.*', 'logging.*', 'urllib3.*', 'requests.*'],
        'exception_diagnosis': True,
        'exception_backtrace': True,
        'exception_show_values': True,
        'exception_colorize': True,
        'exception_depth': 15,
        'processor_type': 'development',
        'global_exception_hook': True,
        'include_system_info': True,
        'exception_hook_level': 'error',
        'show_exception_details': True,
        'show_system_state': True,
        'show_stack_trace': True,
        'show_code_context': True,
        'show_environment_vars': True,
        'pretty_print_stack_data': True,
        'stack_data_max_length': 500,
        'stack_data_max_depth': 5,
        'exception_output_style': 'beautiful',
        'console_output_style': 'beautiful',
    }
    config.update(overrides)
    return config


def build_production_config(base_directory: str = '/var/log/app',
                            level: str = 'WARNING',
                            rotation: str = '100 MB',
                            retention: str = '30 days',
                            enable_performance_tracing: bool = False,
                            **overrides) -> Dict[str, Any]:
    """Build production configuration preset with proper stream separation"""
    config = {
        'backend': 'standard',
        'level': level,
        
        # Console stream configuration - Minimal or disabled in production
        'console_stream': {
            'enabled': False,          # Typically disabled in production
            'format': 'compact',       # If enabled, use compact format
            'use_colors': False,       # No colors in production console
            'use_symbols': False,      # No Unicode symbols in production
            'compact_format': True,    # Compact format for production
        },
        
        # File stream configuration - Optimized JSON for log aggregation
        'file_stream': {
            'enabled': True,
            'format': 'json',          # Structured JSON format
            'base_directory': base_directory,
            'rotation': rotation,
            'retention': retention,
            'pretty_json': False,      # Compact JSON for production efficiency
            'json_indent': None,       # No indentation
            'json_separators': (',', ':'),  # Minimal separators
            'use_json_handlers': True,
            'compression': True,       # Compress rotated logs
            'buffer_size': 1000,       # Larger buffer for performance
            'flush_interval': 5.0,     # Less frequent flushes
        },
        
        # Legacy compatibility (deprecated, but maintained for backward compatibility)
        'console': False,
        'format': 'json',
        'use_json_handlers': True,
        'pretty_json': False,
        'json_indent': None,
        'json_separators': (',', ':'),
        'base_directory': base_directory,
        'rotation': rotation,
        'retention': retention,
        'use_colors': False,
        'use_symbols': False,
        'compact_format': True,
        'exception_diagnosis': False,
        'exception_backtrace': True,
        'exception_show_values': False,
        'exception_colorize': False,
        'exception_depth': 5,
        'tracing_enabled': enable_performance_tracing,
    }

    if enable_performance_tracing:
        config.update({
            'min_execution_time': 2.0,
            'performance_threshold': 5.0,
            'tracing_exclude_modules': ['django.*', 'logging.*', 'urllib3.*', 'requests.*']
        })

    config.update(overrides)
    return config


def build_json_config(backend: str = 'standard',
                      level: str = 'INFO',
                      base_directory: str = 'logs',
                      console: bool = True,
                      rotation: str = '10 MB',
                      retention: str = '1 week',
                      enable_tracing: bool = None,
                      trace_modules: List[str] = None,
                      pretty_json: bool = True,
                      enhanced_exceptions: bool = None,
                      **overrides) -> Dict[str, Any]:
    """Build JSON logging configuration preset"""
    config = {
        'backend': backend,
        'level': level,
        'console': console,
        'base_directory': base_directory,
        'format': 'json',
        'use_json_handlers': True,
        'rotation': rotation,
        'retention': retention,
        'pretty_json': pretty_json
    }

    if pretty_json:
        config.update({
            'json_indent': 2,
            'json_separators': (', ', ': ')
        })
    else:
        config.update({
            'json_indent': None,
            'json_separators': (',', ':')
        })

    # Auto-configure tracing if not specified
    if enable_tracing is None:
        env = os.getenv('ENVIRONMENT', os.getenv('DJANGO_ENVIRONMENT', 'development'))
        enable_tracing = env.lower() in ('development', 'dev', 'local')

    if enable_tracing:
        config.update({
            'tracing_enabled': True,
            'min_execution_time': 0.1,
            'performance_threshold': 1.0,
        })
        if trace_modules:
            config['tracing_include_modules'] = trace_modules

    # Auto-configure exceptions if not specified
    if enhanced_exceptions is None:
        env = os.getenv('ENVIRONMENT', os.getenv('DJANGO_ENVIRONMENT', 'development'))
        enhanced_exceptions = env.lower() in ('development', 'dev', 'local')

    if enhanced_exceptions:
        config.update({
            'exception_diagnosis': 'auto',
            'exception_backtrace': 'auto',
            'exception_show_values': True,
            'exception_colorize': True
        })
    else:
        config.update({
            'exception_diagnosis': False,
            'exception_backtrace': True,
            'exception_show_values': False,
            'exception_colorize': False
        })

    config.update(overrides)
    return config


def build_cli_config(**overrides) -> Dict[str, Any]:
    """Build CLI application configuration preset"""
    config = {
        'level': 'INFO',
        'console': True,
        'format': 'console',
        'use_json_handlers': False,
        'pretty_json': False,
        'tracing_enabled': False,
        'base_directory': 'logs',
        'use_colors': True,
        'use_symbols': False,  # Symbols might not work in all terminals
        'compact_format': True,
        'show_module': False,
        'show_function': False,
        'exception_diagnosis': False,
        'exception_backtrace': True,
        'exception_show_values': False,
        'exception_colorize': True
    }
    config.update(overrides)
    return config


def build_django_config(debug_mode: bool = None, **overrides) -> Dict[str, Any]:
    """Build Django-specific configuration preset"""
    if debug_mode is None:
        # Try to detect Django debug mode from environment
        env = os.getenv('DJANGO_DEBUG', os.getenv('DEBUG', 'false')).lower()
        debug_mode = env in ('true', '1', 'on')

    if debug_mode:
        return build_development_config(**overrides)
    else:
        return build_production_config(enable_performance_tracing=True, **overrides)


def build_fastapi_config(**overrides) -> Dict[str, Any]:
    """Build FastAPI-specific configuration preset"""
    config = {
        'level': 'INFO',
        'console': True,
        'enable_tracing': True,
        'trace_modules': ['app.*', 'routers.*', 'services.*'],
        'enhanced_exceptions': True
    }
    config.update(overrides)
    return build_json_config(**config)


def build_flask_config(**overrides) -> Dict[str, Any]:
    """Build Flask-specific configuration preset"""
    config = {
        'level': 'INFO',
        'console': True,
        'enable_tracing': True,
        'trace_modules': ['app.*', 'views.*', 'services.*'],
        'enhanced_exceptions': True
    }
    config.update(overrides)
    return build_json_config(**config)


# =============================================================================
# SENSITIVE KEYS MANAGEMENT - PURE DATA FUNCTIONS
# =============================================================================

def configure_sensitive_keys(keys: List[str] = None,
                             reset_to_defaults: bool = False,
                             append: bool = True) -> List[str]:
    """Configure sensitive keys for sanitization"""
    global _global_config

    if reset_to_defaults:
        _global_config['sensitive_keys'] = [
            'password', 'passwd', 'pwd', 'token', 'secret', 'key', 'auth',
            'credential', 'api_key', 'private_key', 'access_token',
            'refresh_token', 'session_key', 'ssn', 'social_security',
            'credit_card', 'ccn', 'cvv', 'pin', 'authorization'
        ]

    if keys:
        if append:
            existing_keys = set(_global_config.get('sensitive_keys', []))
            existing_keys.update(keys)
            _global_config['sensitive_keys'] = list(existing_keys)
        else:
            _global_config['sensitive_keys'] = keys[:]

    return _global_config.get('sensitive_keys', [])


def get_sensitive_keys() -> List[str]:
    """Get current sensitive keys list"""
    return _global_config.get('sensitive_keys', [])


def add_sensitive_keys(*keys: str) -> List[str]:
    """Add sensitive keys to the current list"""
    return configure_sensitive_keys(list(keys), append=True)


def remove_sensitive_keys(*keys: str) -> List[str]:
    """Remove sensitive keys from the current list"""
    current_keys = set(_global_config.get('sensitive_keys', []))
    current_keys.difference_update(keys)
    _global_config['sensitive_keys'] = list(current_keys)
    return _global_config['sensitive_keys']