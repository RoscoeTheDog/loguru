# logging_suite/backends/registry.py
"""
Backend registry for managing available logging backends
ENHANCED: Better error handling, validation, and dynamic discovery
"""

import importlib
import sys
from typing import Dict, Type, List, Optional, Any
from .base import LoggingBackend


class BackendRegistry:
    """
    Enhanced registry for managing available logging backends
    Provides better error handling, validation, and dynamic discovery
    """

    def __init__(self):
        self._backends: Dict[str, Type[LoggingBackend]] = {}
        self._backend_info: Dict[str, Dict[str, Any]] = {}
        self._registration_errors: Dict[str, str] = {}
        self._validated_backends: Dict[str, bool] = {}

    def register(self, name: str, backend_class: Type[LoggingBackend],
                 validate: bool = True, force: bool = False):
        """
        Register a backend with enhanced validation and error handling

        Args:
            name: Backend name
            backend_class: Backend class
            validate: Whether to validate the backend on registration
            force: Whether to force registration even if validation fails
        """
        if not issubclass(backend_class, LoggingBackend):
            error_msg = f"Backend {name} must inherit from LoggingBackend"
            self._registration_errors[name] = error_msg
            if not force:
                raise ValueError(error_msg)

        # Store basic registration info
        self._backends[name] = backend_class
        self._backend_info[name] = {
            'class': backend_class,
            'module': backend_class.__module__,
            'available': False,  # Will be set during validation
            'error': None,
            'version': 'unknown'
        }

        # Validate backend if requested
        if validate:
            try:
                self._validate_backend(name)
            except Exception as e:
                error_msg = f"Backend {name} validation failed: {e}"
                self._registration_errors[name] = error_msg
                self._backend_info[name]['error'] = str(e)

                if not force:
                    # Remove from registry if validation fails and not forced
                    del self._backends[name]
                    del self._backend_info[name]
                    raise ValueError(error_msg)

    def _validate_backend(self, name: str) -> bool:
        """
        Validate that a backend can be instantiated and used

        Args:
            name: Backend name to validate

        Returns:
            True if backend is valid and available
        """
        if name not in self._backends:
            return False

        try:
            backend_class = self._backends[name]

            # Try to instantiate the backend
            backend_instance = backend_class()

            # Check if it implements required methods
            required_methods = ['create_logger', 'create_unified_logger',
                                'supports_context_binding', 'get_backend_name']

            for method in required_methods:
                if not hasattr(backend_instance, method):
                    raise AttributeError(f"Backend {name} missing required method: {method}")

                if not callable(getattr(backend_instance, method)):
                    raise AttributeError(f"Backend {name} method {method} is not callable")

            # Try to get backend info
            try:
                info = backend_instance.get_backend_info()
                if isinstance(info, dict):
                    self._backend_info[name].update(info)
            except Exception:
                pass  # Backend info is optional

            # Try to create a test logger
            try:
                test_logger = backend_instance.create_logger('test.validation', {})
                if test_logger is None:
                    raise ValueError(f"Backend {name} create_logger returned None")
            except Exception as e:
                raise ValueError(f"Backend {name} failed to create test logger: {e}")

            # Mark as validated and available
            self._validated_backends[name] = True
            self._backend_info[name]['available'] = True
            self._backend_info[name]['error'] = None

            return True

        except Exception as e:
            self._validated_backends[name] = False
            self._backend_info[name]['available'] = False
            self._backend_info[name]['error'] = str(e)
            raise

    def get_backend(self, name: str) -> Type[LoggingBackend]:
        """
        Get a backend by name with enhanced error reporting

        Args:
            name: Backend name

        Returns:
            Backend class

        Raises:
            ValueError: If backend is not available with detailed error info
        """
        if name not in self._backends:
            available = list(self._backends.keys())
            raise ValueError(
                f"Unknown backend: {name}. Available backends: {available}. "
                f"Registration errors: {self._registration_errors}"
            )

        # Check if backend was validated successfully
        if name in self._validated_backends and not self._validated_backends[name]:
            error_info = self._backend_info[name].get('error', 'Unknown validation error')
            raise ValueError(
                f"Backend {name} is not available due to validation failure: {error_info}"
            )

        return self._backends[name]

    def get_available_backends(self) -> List[str]:
        """
        Get list of successfully validated backend names

        Returns:
            List of available backend names
        """
        return [name for name, validated in self._validated_backends.items() if validated]

    def get_all_registered_backends(self) -> List[str]:
        """
        Get list of all registered backend names (including failed ones)

        Returns:
            List of all registered backend names
        """
        return list(self._backends.keys())

    def get_default_backend(self) -> str:
        """
        Get the default backend name with enhanced fallback logic

        Returns:
            Default backend name

        Raises:
            RuntimeError: If no backends are available
        """
        # Priority order: standard > structlog > loguru > any available
        preference_order = ['standard', 'structlog', 'loguru']

        # Check preferred backends first
        for backend in preference_order:
            if backend in self._validated_backends and self._validated_backends[backend]:
                return backend

        # Fall back to any available backend
        available = self.get_available_backends()
        if available:
            return available[0]

        # No backends available - this is a critical error
        error_details = []
        for name, error in self._registration_errors.items():
            error_details.append(f"  {name}: {error}")

        error_msg = "No backends available - this should not happen"
        if error_details:
            error_msg += f"\nRegistration errors:\n" + "\n".join(error_details)

        raise RuntimeError(error_msg)

    def is_backend_available(self, name: str) -> bool:
        """
        Check if a backend is available and validated

        Args:
            name: Backend name

        Returns:
            True if backend is available and validated
        """
        return (name in self._validated_backends and
                self._validated_backends[name])

    def list_backends_with_status(self) -> Dict[str, bool]:
        """
        List all potential backends with their availability status

        Returns:
            Dictionary mapping backend names to availability status
        """
        # Include both registered and known potential backends
        potential_backends = ['standard', 'structlog', 'loguru']

        status = {}
        for backend in potential_backends:
            status[backend] = self.is_backend_available(backend)

        # Add any other registered backends
        for backend in self._backends:
            if backend not in status:
                status[backend] = self.is_backend_available(backend)

        return status

    def get_backend_info(self, name: str) -> Dict[str, Any]:
        """
        Get detailed information about a backend

        Args:
            name: Backend name

        Returns:
            Dictionary with backend information
        """
        if name not in self._backend_info:
            return {
                'name': name,
                'available': False,
                'error': 'Backend not registered'
            }

        info = self._backend_info[name].copy()
        info['name'] = name
        return info

    def get_all_backend_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed information about all backends

        Returns:
            Dictionary mapping backend names to their info
        """
        return {name: self.get_backend_info(name) for name in self._backends}

    def revalidate_backend(self, name: str) -> bool:
        """
        Revalidate a specific backend (useful for runtime checks)

        Args:
            name: Backend name to revalidate

        Returns:
            True if backend is now valid
        """
        if name not in self._backends:
            return False

        try:
            return self._validate_backend(name)
        except Exception:
            return False

    def revalidate_all_backends(self) -> Dict[str, bool]:
        """
        Revalidate all registered backends

        Returns:
            Dictionary mapping backend names to validation results
        """
        results = {}
        for name in self._backends:
            results[name] = self.revalidate_backend(name)
        return results

    def discover_backends(self) -> List[str]:
        """
        Dynamically discover and register backends

        Returns:
            List of newly discovered backend names
        """
        discovered = []

        # Known backend modules to try discovering
        potential_backends = [
            ('standard', 'logging_suite.backends.standard', 'StandardLoggingBackend'),
            ('structlog', 'logging_suite.backends.structlog_backend', 'StructlogBackend'),
            ('loguru', 'logging_suite.backends.loguru_backend', 'LoguruBackend'),
        ]

        for name, module_name, class_name in potential_backends:
            if name not in self._backends:
                try:
                    module = importlib.import_module(module_name)
                    backend_class = getattr(module, class_name)
                    self.register(name, backend_class, validate=True, force=False)
                    discovered.append(name)
                except Exception as e:
                    self._registration_errors[name] = str(e)

        return discovered

    def get_registration_errors(self) -> Dict[str, str]:
        """Get all backend registration errors"""
        return self._registration_errors.copy()

    def clear_registration_errors(self):
        """Clear all registration errors"""
        self._registration_errors.clear()

    def unregister_backend(self, name: str) -> bool:
        """
        Unregister a backend

        Args:
            name: Backend name to unregister

        Returns:
            True if backend was unregistered
        """
        if name not in self._backends:
            return False

        # Don't allow unregistering the standard backend
        if name == 'standard':
            available = self.get_available_backends()
            if len(available) <= 1:
                raise ValueError("Cannot unregister standard backend when it's the only available backend")

        del self._backends[name]
        self._backend_info.pop(name, None)
        self._validated_backends.pop(name, None)
        self._registration_errors.pop(name, None)

        return True

    def reset_registry(self):
        """Reset the entire registry (useful for testing)"""
        self._backends.clear()
        self._backend_info.clear()
        self._validated_backends.clear()
        self._registration_errors.clear()