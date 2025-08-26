# logging_suite/backends/__init__.py
"""
Backend registry and initialization for logging_suite
FIXED: Complete backend registration with proper error handling
"""

import warnings
from typing import Dict, Any, List

# Import the registry first
from .registry import BackendRegistry
from .base import LoggingBackend

# Create global registry instance
registry = BackendRegistry()

# Track initialization status
_initialization_status = {
    'completed': False,
    'errors': [],
    'warnings': [],
    'successful_backends': [],
    'failed_backends': []
}


def _register_backend_safely(name: str, module_path: str, class_name: str) -> bool:
    """
    Safely register a backend with proper error handling

    Args:
        name: Backend name
        module_path: Module path
        class_name: Class name

    Returns:
        True if registration successful
    """
    try:
        # Import the module
        import importlib
        module = importlib.import_module(module_path)
        backend_class = getattr(module, class_name)

        # Register with validation
        registry.register(name, backend_class, validate=True, force=False)
        _initialization_status['successful_backends'].append(name)
        return True

    except ImportError as e:
        # Missing dependency - this is expected for optional backends
        error_msg = f"{name} backend unavailable: {e}"
        _initialization_status['failed_backends'].append(name)

        if name == 'standard':
            # Standard backend failure is critical
            _initialization_status['errors'].append(error_msg)
            raise RuntimeError(f"CRITICAL: {error_msg}")
        else:
            # Optional backend failure is just a warning
            _initialization_status['warnings'].append(error_msg)
            warnings.warn(f"Optional backend {name} not available: {e}", ImportWarning, stacklevel=2)
        return False

    except Exception as e:
        # Other errors are more serious
        error_msg = f"{name} backend registration failed: {e}"
        _initialization_status['errors'].append(error_msg)
        _initialization_status['failed_backends'].append(name)

        if name == 'standard':
            raise RuntimeError(f"CRITICAL: {error_msg}")
        else:
            warnings.warn(error_msg, UserWarning, stacklevel=2)
        return False


def _initialize_backends() -> None:
    """Initialize all available backends"""
    if _initialization_status['completed']:
        return  # Already initialized

    # Register backends in priority order (standard first)
    backends_to_register = [
        ('standard', 'logging_suite.backends.standard', 'StandardLoggingBackend'),
        ('structlog', 'logging_suite.backends.structlog_backend', 'StructlogBackend'),
        ('loguru', 'logging_suite.backends.loguru_backend', 'LoguruBackend'),
    ]

    for name, module_path, class_name in backends_to_register:
        _register_backend_safely(name, module_path, class_name)

    # Verify at least one backend is available
    if not registry.get_available_backends():
        raise RuntimeError("No backends available - logging_suite cannot function")

    # Ensure default backend is set
    try:
        default = registry.get_default_backend()
    except RuntimeError as e:
        raise RuntimeError(f"No default backend available: {e}")

    _initialization_status['completed'] = True


def get_initialization_status() -> Dict[str, Any]:
    """Get initialization status"""
    return _initialization_status.copy()


def ensure_backends_initialized() -> None:
    """Ensure backends are initialized (can be called multiple times safely)"""
    if not _initialization_status['completed']:
        _initialize_backends()


def get_available_backends() -> List[str]:
    """Get available backend names"""
    ensure_backends_initialized()
    return registry.get_available_backends()


def get_default_backend() -> str:
    """Get default backend name"""
    ensure_backends_initialized()
    return registry.get_default_backend()


# Initialize backends on import, but with proper error handling
try:
    _initialize_backends()
except Exception as e:
    # Store error but don't prevent import
    _initialization_status['errors'].append(f"Import-time initialization failed: {e}")
    # The ensure_backends_initialized() function can be called later to retry

# Export public interface
__all__ = [
    'registry',
    'LoggingBackend',
    'BackendRegistry',
    'get_initialization_status',
    'ensure_backends_initialized',
    'get_available_backends',
    'get_default_backend',
]