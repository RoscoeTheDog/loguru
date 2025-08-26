# logging_suite/factory.py - Enhanced Factory with Configuration Inheritance
"""
Logger factory for creating unified loggers with different backends
ENHANCED: Now properly inherits global configuration and respects per-logger overrides
"""

from typing import Any, Dict, Optional, List, TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    from .unified_logger import UnifiedLogger
    from .backends.registry import BackendRegistry


class LoggerFactory:
    """
    Factory class for creating logger instances with different backends
    ENHANCED: Now properly inherits global configuration and respects per-logger overrides
    """
    _logger_instances = {}  # Track created logger instances for cleanup

    @classmethod
    def create_logger_with_registry(cls,
                                    name: str,
                                    backend: str = None,
                                    config: Dict[str, Any] = None,
                                    registry: 'BackendRegistry' = None) -> 'UnifiedLogger':
        """
        Create a unified logger with dependency injection and proper config inheritance

        Args:
            name: Logger name
            backend: Backend name (auto-detect if None)
            config: Configuration dictionary (merged with global config)
            registry: Backend registry (required for dependency injection)

        Returns:
            UnifiedLogger instance

        Raises:
            ValueError: If backend is not available
            ImportError: If backend dependencies are missing
        """
        if registry is None:
            raise ValueError("Backend registry is required for dependency injection")

        # Lazy import to avoid circular dependencies
        from .unified_logger import UnifiedLogger, get_effective_logger_config

        # Get effective configuration for this logger (global + per-logger overrides)
        effective_config = get_effective_logger_config(name)

        # Merge with provided config (provided config takes precedence)
        if config:
            effective_config.update(config)

        # Auto-detect backend if not specified
        if backend is None:
            backend = effective_config.get('backend') or registry.get_default_backend()

        try:
            backend_class = registry.get_backend(backend)
            backend_instance = backend_class()
            return backend_instance.create_unified_logger(name, effective_config)

        except (ValueError, ImportError) as e:
            # Fall back to standard logging if specified backend is unavailable
            if backend != 'standard':
                # Issue warning about fallback
                warning_msg = f"Warning: {backend} backend unavailable ({e}), falling back to standard logging"
                print(warning_msg)  # Print to stdout for immediate visibility
                warnings.warn(warning_msg, UserWarning, stacklevel=2)

                try:
                    standard_backend_class = registry.get_backend('standard')
                    standard_backend = standard_backend_class()
                    return standard_backend.create_unified_logger(name, effective_config)
                except Exception as fallback_error:
                    raise ImportError(
                        f"Failed to create logger with {backend} backend and standard fallback failed: {fallback_error}")
            else:
                # Standard backend itself failed - this is critical
                raise e

    @classmethod
    def create_logger(cls, name: str, backend: str = None, config: Dict[str, Any] = None) -> 'UnifiedLogger':
        """
        Create a unified logger (convenience method that gets registry)
        ENHANCED: Now properly inherits global configuration

        Args:
            name: Logger name
            backend: Backend name (auto-detect if None)
            config: Configuration dictionary (merged with global config)

        Returns:
            UnifiedLogger instance
        """
        # Get registry from backends module
        from .backends import registry
        logger = cls.create_logger_with_registry(name, backend, config, registry)

        # Store reference for cleanup purposes
        cls._logger_instances[name] = logger

        return logger

    @classmethod
    def create_raw_logger_with_registry(cls,
                                        name: str,
                                        backend: str = None,
                                        config: Dict[str, Any] = None,
                                        registry: 'BackendRegistry' = None) -> Any:
        """
        Create a raw logger (without UnifiedLogger wrapper) with dependency injection
        ENHANCED: Now properly inherits global configuration

        Args:
            name: Logger name
            backend: Backend name (auto-detect if None)
            config: Configuration dictionary (merged with global config)
            registry: Backend registry (required for dependency injection)

        Returns:
            Raw logger instance (backend-specific type)
        """
        if registry is None:
            raise ValueError("Backend registry is required for dependency injection")

        # Get effective configuration for this logger
        from .unified_logger import get_effective_logger_config
        effective_config = get_effective_logger_config(name)

        # Merge with provided config
        if config:
            effective_config.update(config)

        if backend is None:
            backend = effective_config.get('backend') or registry.get_default_backend()

        try:
            backend_class = registry.get_backend(backend)
            backend_instance = backend_class()
            return backend_instance.create_logger(name, effective_config)
        except (ValueError, ImportError) as e:
            # Fall back to standard logging if specified backend is unavailable
            if backend != 'standard':
                warning_msg = f"Warning: {backend} backend unavailable ({e}), falling back to standard logging"
                print(warning_msg)
                warnings.warn(warning_msg, UserWarning, stacklevel=2)

                try:
                    standard_backend_class = registry.get_backend('standard')
                    standard_backend = standard_backend_class()
                    return standard_backend.create_logger(name, effective_config)
                except Exception as fallback_error:
                    raise ImportError(
                        f"Failed to create raw logger with {backend} backend and standard fallback failed: {fallback_error}")
            else:
                raise e

    @classmethod
    def create_raw_logger(cls, name: str, backend: str = None, config: Dict[str, Any] = None) -> Any:
        """
        Create a raw logger (convenience method that gets registry)
        ENHANCED: Now properly inherits global configuration

        Args:
            name: Logger name
            backend: Backend name (auto-detect if None)
            config: Configuration dictionary (merged with global config)

        Returns:
            Raw logger instance (backend-specific type)
        """
        from .backends import registry
        return cls.create_raw_logger_with_registry(name, backend, config, registry)

    @classmethod
    def create_logger_with_fallback(cls, name: str,
                                    preferred_backends: List[str],
                                    config: Dict[str, Any] = None,
                                    registry: 'BackendRegistry' = None) -> 'UnifiedLogger':
        """
        Create a logger with a list of preferred backends, falling back through the list
        ENHANCED: Now properly inherits global configuration

        Args:
            name: Logger name
            preferred_backends: List of backend names in order of preference
            config: Configuration dictionary (merged with global config)
            registry: Backend registry (gets default if None)

        Returns:
            UnifiedLogger instance using the first available backend
        """
        if registry is None:
            from .backends import registry as default_registry
            registry = default_registry

        # Get effective configuration for this logger
        from .unified_logger import get_effective_logger_config
        effective_config = get_effective_logger_config(name)

        # Merge with provided config
        if config:
            effective_config.update(config)

        for backend in preferred_backends:
            try:
                return cls.create_logger_with_registry(name, backend, effective_config, registry)
            except (ValueError, ImportError):
                continue

        # If none of the preferred backends work, use default
        return cls.create_logger_with_registry(name, None, effective_config, registry)

    @classmethod
    def get_backend_status(cls, registry: 'BackendRegistry' = None) -> Dict[str, bool]:
        """
        Get status of all potential backends

        Args:
            registry: Backend registry (gets default if None)

        Returns:
            Dictionary mapping backend names to availability status
        """
        if registry is None:
            from .backends import registry as default_registry
            registry = default_registry

        return registry.list_backends_with_status()

    @classmethod
    def get_available_backends(cls, registry: 'BackendRegistry' = None) -> List[str]:
        """
        Get list of available logging backends

        Args:
            registry: Backend registry (gets default if None)

        Returns:
            List of available backend names
        """
        if registry is None:
            from .backends import registry as default_registry
            registry = default_registry

        return registry.get_available_backends()

    @classmethod
    def get_backend_info(cls, backend_name: str = None, registry: 'BackendRegistry' = None) -> Dict[str, Any]:
        """
        Get information about a specific backend

        Args:
            backend_name: Backend name (default backend if None)
            registry: Backend registry (gets default if None)

        Returns:
            Backend information dictionary
        """
        if registry is None:
            from .backends import registry as default_registry
            registry = default_registry

        if backend_name is None:
            backend_name = registry.get_default_backend()

        try:
            backend_class = registry.get_backend(backend_name)
            backend_instance = backend_class()
            return backend_instance.get_backend_info()
        except (ValueError, ImportError) as e:
            return {
                'name': backend_name,
                'available': False,
                'error': str(e)
            }

    @classmethod
    def validate_backend_config(cls, backend_name: str, config: Dict[str, Any],
                                registry: 'BackendRegistry' = None) -> Dict[str, Any]:
        """
        Validate configuration for a specific backend

        Args:
            backend_name: Backend name
            config: Configuration to validate
            registry: Backend registry (gets default if None)

        Returns:
            Validation results with any warnings or errors
        """
        if registry is None:
            from .backends import registry as default_registry
            registry = default_registry

        validation = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'backend': backend_name
        }

        try:
            backend_class = registry.get_backend(backend_name)

            # Basic validation - check for common config issues
            if backend_name == 'structlog' and 'processors' in config:
                if not isinstance(config['processors'], list):
                    validation['errors'].append("'processors' must be a list for structlog backend")
                    validation['valid'] = False

            if backend_name == 'loguru' and 'serialize' in config:
                if not isinstance(config['serialize'], bool):
                    validation['warnings'].append("'serialize' should be boolean for loguru backend")

            # Check for incompatible options
            if backend_name == 'standard' and config.get('context_binding'):
                validation['warnings'].append("Standard logging backend doesn't support native context binding")

        except (ValueError, ImportError) as e:
            validation['valid'] = False
            validation['errors'].append(f"Backend not available: {e}")

        return validation

    @classmethod
    def test_backend_functionality(cls, backend_name: str, registry: 'BackendRegistry' = None) -> Dict[str, Any]:
        """
        Test backend functionality

        Args:
            backend_name: Backend name to test
            registry: Backend registry (gets default if None)

        Returns:
            Test results dictionary
        """
        if registry is None:
            from .backends import registry as default_registry
            registry = default_registry

        test_results = {
            'backend': backend_name,
            'available': False,
            'logger_creation': False,
            'unified_logger_creation': False,
            'basic_logging': False,
            'errors': []
        }

        try:
            # Test 1: Backend availability
            backend_class = registry.get_backend(backend_name)
            backend_instance = backend_class()
            test_results['available'] = True

            # Test 2: Raw logger creation
            try:
                raw_logger = backend_instance.create_logger(f'test_{backend_name}', {})
                if raw_logger is not None:
                    test_results['logger_creation'] = True
            except Exception as e:
                test_results['errors'].append(f"Raw logger creation failed: {e}")

            # Test 3: Unified logger creation
            try:
                unified_logger = backend_instance.create_unified_logger(f'test_{backend_name}_unified', {})
                if unified_logger is not None:
                    test_results['unified_logger_creation'] = True

                    # Test 4: Basic logging
                    try:
                        unified_logger.info("Test message", test_key="test_value")
                        test_results['basic_logging'] = True
                    except Exception as e:
                        test_results['errors'].append(f"Basic logging failed: {e}")

            except Exception as e:
                test_results['errors'].append(f"Unified logger creation failed: {e}")

        except (ValueError, ImportError) as e:
            test_results['errors'].append(f"Backend not available: {e}")

        return test_results

    @classmethod
    def create_exception_handler(cls, backend_name: str, config: Dict[str, Any]) -> Any:
        """
        Create an exception handler for a specific backend with given config

        Args:
            backend_name: Name of the backend
            config: Configuration dictionary

        Returns:
            Backend-aware exception handler or None if not available
        """
        try:
            from .exceptions import create_exception_handler_for_backend
            return create_exception_handler_for_backend(backend_name, config)
        except ImportError:
            return None

    @classmethod
    def create_logger_with_config_override(cls, name: str,
                                           config_override: Dict[str, Any],
                                           backend: str = None) -> 'UnifiedLogger':
        """
        Create a logger with a temporary configuration override
        This is useful for creating loggers with specific settings without
        permanently changing the global or per-logger configuration

        Args:
            name: Logger name
            config_override: Temporary configuration override
            backend: Backend name (auto-detect if None)

        Returns:
            UnifiedLogger instance with temporary configuration
        """
        # Get effective configuration for this logger
        from .unified_logger import get_effective_logger_config
        effective_config = get_effective_logger_config(name)

        # Apply temporary override
        temp_config = {**effective_config, **config_override}

        # Create logger with temporary config (don't store the override)
        from .backends import registry
        return cls.create_logger_with_registry(name, backend, temp_config, registry)

    @classmethod
    def get_logger_configuration_status(cls) -> Dict[str, Any]:
        """
        Get comprehensive information about logger configuration state

        Returns:
            Dictionary with configuration status information
        """
        from .unified_logger import get_all_logger_configs
        from .config import get_global_config

        status = {
            'global_config': get_global_config(),
            'per_logger_configs': get_all_logger_configs(),
            'total_configured_loggers': len(get_all_logger_configs()),
            'available_backends': cls.get_available_backends(),
            'default_backend': None  # Will be set below
        }

        # Get default backend safely
        try:
            from .backends import registry
            status['default_backend'] = registry.get_default_backend()
        except Exception as e:
            status['default_backend'] = f"Error: {e}"

        return status

    @classmethod
    def clear_all_logger_configurations(cls) -> None:
        """
        Clear all per-logger configuration overrides
        This resets all loggers to use global configuration
        """
        from .unified_logger import clear_all_logger_configs
        clear_all_logger_configs()

    @classmethod
    def reset_logger_to_global_config(cls, logger_name: str) -> bool:
        """
        Reset a specific logger to use global configuration

        Args:
            logger_name: Name of the logger to reset

        Returns:
            True if logger config was cleared, False if no override existed
        """
        from .unified_logger import clear_logger_config
        return clear_logger_config(logger_name)

    @classmethod
    def get_logger_effective_config(cls, logger_name: str) -> Dict[str, Any]:
        """
        Get the effective configuration that would be used for a logger

        Args:
            logger_name: Name of the logger

        Returns:
            Effective configuration dictionary
        """
        from .unified_logger import get_effective_logger_config
        return get_effective_logger_config(logger_name)

    @classmethod
    def validate_logger_configuration(cls, logger_name: str) -> Dict[str, Any]:
        """
        Validate the configuration for a specific logger

        Args:
            logger_name: Name of the logger to validate

        Returns:
            Validation results
        """
        effective_config = cls.get_logger_effective_config(logger_name)
        backend_name = effective_config.get('backend', 'standard')

        return cls.validate_backend_config(backend_name, effective_config)

    @classmethod
    def create_multiple_loggers(cls, logger_configs: Dict[str, Dict[str, Any]]) -> Dict[str, 'UnifiedLogger']:
        """
        Create multiple loggers with their respective configurations

        Args:
            logger_configs: Dictionary mapping logger names to their configurations

        Returns:
            Dictionary mapping logger names to UnifiedLogger instances
        """
        loggers = {}

        for logger_name, config in logger_configs.items():
            try:
                loggers[logger_name] = cls.create_logger(logger_name, config=config)
            except Exception as e:
                # Log error but continue with other loggers
                print(f"Warning: Failed to create logger '{logger_name}': {e}")

        return loggers

    @classmethod
    def clone_logger_config(cls, source_logger_name: str, target_logger_name: str) -> bool:
        """
        Clone configuration from one logger to another

        Args:
            source_logger_name: Name of the source logger
            target_logger_name: Name of the target logger

        Returns:
            True if configuration was cloned successfully
        """
        from .unified_logger import get_logger_config, set_logger_config

        source_config = get_logger_config(source_logger_name)
        if source_config is None:
            return False

        set_logger_config(target_logger_name, source_config.copy(), merge=False)
        return True

    @classmethod
    def export_logger_configurations(cls) -> Dict[str, Any]:
        """
        Export all logger configurations for backup or migration

        Returns:
            Dictionary containing all configuration data
        """
        from .unified_logger import get_all_logger_configs
        from .config import get_global_config

        return {
            'format_version': '1.0',
            'global_config': get_global_config(),
            'per_logger_configs': get_all_logger_configs(),
            'backend_status': cls.get_backend_status(),
            'export_timestamp': None  # Could add timestamp if needed
        }

    @classmethod
    def cleanup_loggers(cls):
        """
        Close all logger handlers and clean up resources

        Call this method before application shutdown or before tests cleanup
        to ensure all file handlers are properly closed.
        """
        # Close all handlers for all tracked loggers
        for name, logger in cls._logger_instances.items():
            try:
                if hasattr(logger, 'raw_logger') and hasattr(logger.raw_logger, 'handlers'):
                    for handler in list(logger.raw_logger.handlers):
                        try:
                            handler.flush()
                            handler.close()
                        except Exception:
                            pass
            except Exception:
                pass

    @classmethod
    def import_logger_configurations(cls, config_data: Dict[str, Any],
                                     merge_global: bool = True,
                                     clear_existing: bool = False) -> Dict[str, Any]:
        """
        Import logger configurations from exported data

        Args:
            config_data: Configuration data from export_logger_configurations
            merge_global: Whether to merge with existing global config
            clear_existing: Whether to clear existing per-logger configs first

        Returns:
            Import results summary
        """
        from .unified_logger import set_logger_config, clear_all_logger_configs
        from .config import update_global_config

        results = {
            'success': True,
            'imported_loggers': 0,
            'errors': [],
            'warnings': []
        }

        try:
            # Clear existing configurations if requested
            if clear_existing:
                clear_all_logger_configs()
                results['warnings'].append("Cleared all existing per-logger configurations")

            # Import global configuration
            if 'global_config' in config_data:
                if merge_global:
                    update_global_config(**config_data['global_config'])
                    results['warnings'].append("Merged global configuration")
                else:
                    # Would need a reset function to replace entirely
                    results['warnings'].append("Global config merge mode only supported currently")

            # Import per-logger configurations
            if 'per_logger_configs' in config_data:
                for logger_name, config in config_data['per_logger_configs'].items():
                    try:
                        set_logger_config(logger_name, config, merge=False)
                        results['imported_loggers'] += 1
                    except Exception as e:
                        results['errors'].append(f"Failed to import config for '{logger_name}': {e}")
                        results['success'] = False

        except Exception as e:
            results['success'] = False
            results['errors'].append(f"Import failed: {e}")

        return results