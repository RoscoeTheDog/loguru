# logging_suite/mixins.py
"""
Enhanced mixins for adding logging capabilities to classes with flexible control
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .factory import LoggerFactory
from .config import get_effective_config


# Global configuration for logging control
_GLOBAL_LOGGING_CONFIG = {
    'enable_automatic_logging': True,  # Global toggle for automatic logging
    'enable_save_logging': True,       # Global toggle for save() logging
    'enable_delete_logging': True,     # Global toggle for delete() logging
    'enable_refresh_logging': True,    # Global toggle for refresh_from_db() logging
    'log_level': 'info',              # Default log level for automatic operations
    'log_method_calls': True,         # Whether to log method entry/exit
    'log_performance': True,          # Whether to log execution times
}


def configure_mixin_logging(**config):
    """
    Configure global logging behavior for all mixins

    Args:
        enable_automatic_logging (bool): Master switch for all automatic logging
        enable_save_logging (bool): Enable logging for save() operations
        enable_delete_logging (bool): Enable logging for delete() operations
        enable_refresh_logging (bool): Enable logging for refresh_from_db() operations
        log_level (str): Default log level ('debug', 'info', 'warning', 'error')
        log_method_calls (bool): Log method entry/exit
        log_performance (bool): Log execution times
    """
    global _GLOBAL_LOGGING_CONFIG
    _GLOBAL_LOGGING_CONFIG.update(config)


def get_mixin_logging_config() -> Dict[str, Any]:
    """Get current global mixin logging configuration"""
    return _GLOBAL_LOGGING_CONFIG.copy()


def disable_automatic_logging():
    """Convenience function to disable all automatic logging globally"""
    configure_mixin_logging(enable_automatic_logging=False)


def enable_automatic_logging():
    """Convenience function to enable all automatic logging globally"""
    configure_mixin_logging(enable_automatic_logging=True)


class LoggingMixin:
    """Enhanced mixin to add logging capabilities to any class with flexible control"""

    # Class-level logging configuration (per-class control)
    _logging_config: Dict[str, Any] = {}
    _disable_automatic_logging: bool = False  # Class-level disable switch
    _disable_save_logging: bool = False       # Class-level save logging control
    _disable_delete_logging: bool = False     # Class-level delete logging control
    _disable_refresh_logging: bool = False    # Class-level refresh logging control

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = None
        self._logger_context = {}

        # Instance-level logging control (highest priority)
        self._instance_disable_automatic_logging: bool = False
        self._instance_disable_save_logging: bool = False
        self._instance_disable_delete_logging: bool = False
        self._instance_disable_refresh_logging: bool = False

    # ===================
    # LOGGING CONTROL METHODS
    # ===================

    def disable_logging(self,
                       save: bool = True,
                       delete: bool = True,
                       refresh: bool = True,
                       all_automatic: bool = False):
        """
        Disable logging for specific operations on this instance

        Args:
            save (bool): Disable save() logging
            delete (bool): Disable delete() logging
            refresh (bool): Disable refresh_from_db() logging
            all_automatic (bool): Disable all automatic logging
        """
        if all_automatic:
            self._instance_disable_automatic_logging = True
        else:
            self._instance_disable_save_logging = save
            self._instance_disable_delete_logging = delete
            self._instance_disable_refresh_logging = refresh

    def enable_logging(self,
                      save: bool = True,
                      delete: bool = True,
                      refresh: bool = True,
                      all_automatic: bool = False):
        """
        Enable logging for specific operations on this instance

        Args:
            save (bool): Enable save() logging
            delete (bool): Enable delete() logging
            refresh (bool): Enable refresh_from_db() logging
            all_automatic (bool): Enable all automatic logging
        """
        if all_automatic:
            self._instance_disable_automatic_logging = False
        else:
            self._instance_disable_save_logging = not save
            self._instance_disable_delete_logging = not delete
            self._instance_disable_refresh_logging = not refresh

    def _should_log_operation(self, operation: str) -> bool:
        """
        Determine if logging should occur for a specific operation

        Priority order:
        1. Instance-level settings (highest priority)
        2. Class-level settings
        3. Global settings (lowest priority)

        Args:
            operation (str): 'save', 'delete', 'refresh', or 'automatic'

        Returns:
            bool: Whether logging should occur
        """
        # Check global master switch first
        if not _GLOBAL_LOGGING_CONFIG.get('enable_automatic_logging', True):
            return False

        # Check instance-level master switch
        if self._instance_disable_automatic_logging:
            return False

        # Check class-level master switch
        if getattr(self.__class__, '_disable_automatic_logging', False):
            return False

        # Check operation-specific settings
        if operation == 'save':
            # Instance level
            if self._instance_disable_save_logging:
                return False
            # Class level
            if getattr(self.__class__, '_disable_save_logging', False):
                return False
            # Global level
            return _GLOBAL_LOGGING_CONFIG.get('enable_save_logging', True)

        elif operation == 'delete':
            # Instance level
            if self._instance_disable_delete_logging:
                return False
            # Class level
            if getattr(self.__class__, '_disable_delete_logging', False):
                return False
            # Global level
            return _GLOBAL_LOGGING_CONFIG.get('enable_delete_logging', True)

        elif operation == 'refresh':
            # Instance level
            if self._instance_disable_refresh_logging:
                return False
            # Class level
            if getattr(self.__class__, '_disable_refresh_logging', False):
                return False
            # Global level
            return _GLOBAL_LOGGING_CONFIG.get('enable_refresh_logging', True)

        # Default for other operations
        return True

    @property
    def logger(self):
        """Get or create logger for this instance"""
        if self._logger is None:
            self._logger = self._create_logger()
        return self._logger

    def _create_logger(self):
        """Create a logger instance for this object"""
        # Get the class name and module
        class_name = self.__class__.__name__
        module_name = self.__class__.__module__

        # Create logger name
        if hasattr(self, 'id') and self.id:
            logger_name = f"{module_name}.{class_name}.{self.id}"
        else:
            logger_name = f"{module_name}.{class_name}"

        # Get effective configuration
        config = get_effective_config(self._logging_config)

        # Set up file path if needed
        if config.get('base_directory'):
            filename_template = config.get('filename_template', '{class_name}_{instance_id}_{timestamp}.log')

            # Generate filename from template
            instance_id = getattr(self, 'id', 'default')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            filename = filename_template.format(
                class_name=class_name.lower(),
                instance_id=instance_id,
                timestamp=timestamp,
                module=module_name.split('.')[-1] if '.' in module_name else module_name
            )

            # Ensure directory exists
            log_dir = Path(config['base_directory'])
            log_dir.mkdir(parents=True, exist_ok=True)

            config['file_path'] = str(log_dir / filename)

        # Create the logger
        logger = LoggerFactory.create_logger(logger_name, config=config)

        # Bind initial context
        context = {
            'class': class_name,
            'module': module_name,
            'logging_enabled': self._should_log_operation('automatic'),
            **self._logger_context
        }

        if hasattr(self, 'id') and self.id:
            context['instance_id'] = str(self.id)

        return logger.bind(**context)

    def bind_logger_context(self, **context):
        """Bind additional context to the logger"""
        self._logger_context.update(context)
        # Force logger recreation with new context
        self._logger = None

    def reset_logger(self):
        """Reset the logger (forces recreation on next access)"""
        self._logger = None

    # ===================
    # ENHANCED DJANGO MODEL METHODS (if Django is available)
    # ===================

    def save(self, *args, **kwargs):
        """
        Enhanced save method with optional logging control

        Args:
            *args: Standard Django save() arguments
            **kwargs: Standard Django save() arguments plus:
                - disable_logging (bool): Disable logging for this specific save call
                - log_level (str): Override log level for this save
                - additional logging context can be passed as kwargs
        """
        # Extract logging control parameters
        disable_logging = kwargs.pop('disable_logging', False)
        log_level = kwargs.pop('log_level', _GLOBAL_LOGGING_CONFIG.get('log_level', 'info'))

        # Determine if we should log this operation
        should_log = not disable_logging and self._should_log_operation('save')

        # Extract any additional context for logging
        log_context = {}
        for key in list(kwargs.keys()):
            if key.startswith('log_'):
                log_context[key[4:]] = kwargs.pop(key)  # Remove 'log_' prefix

        is_creation = getattr(self, 'pk', None) is None

        if should_log:
            # Log operation start
            log_method = getattr(self.logger, log_level)
            log_method(
                f"Starting {'creation' if is_creation else 'update'} of {self.__class__.__name__}",
                action='save_start',
                operation='create' if is_creation else 'update',
                **log_context
            )

        try:
            # Call the parent save method
            result = super().save(*args, **kwargs)

            if should_log:
                # Log successful completion
                log_method = getattr(self.logger, log_level)
                log_method(
                    f"Successfully {'created' if is_creation else 'updated'} {self.__class__.__name__}",
                    action='save_complete',
                    operation='create' if is_creation else 'update',
                    success=True,
                    instance_id=getattr(self, 'pk', None),
                    **log_context
                )

            return result

        except Exception as e:
            if should_log:
                # Log failure
                self.logger.error(
                    f"Failed to {'create' if is_creation else 'update'} {self.__class__.__name__}",
                    action='save_failed',
                    operation='create' if is_creation else 'update',
                    success=False,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    **log_context
                )
            raise

    def delete(self, *args, **kwargs):
        """
        Enhanced delete method with optional logging control

        Args:
            *args: Standard Django delete() arguments
            **kwargs: Standard Django delete() arguments plus:
                - disable_logging (bool): Disable logging for this specific delete call
                - log_level (str): Override log level for this delete
        """
        # Extract logging control parameters
        disable_logging = kwargs.pop('disable_logging', False)
        log_level = kwargs.pop('log_level', _GLOBAL_LOGGING_CONFIG.get('log_level', 'info'))

        # Determine if we should log this operation
        should_log = not disable_logging and self._should_log_operation('delete')

        # Extract any additional context for logging
        log_context = {}
        for key in list(kwargs.keys()):
            if key.startswith('log_'):
                log_context[key[4:]] = kwargs.pop(key)

        # Store instance info before deletion
        instance_id = getattr(self, 'pk', None)
        instance_str = str(self) if hasattr(self, '__str__') else f"{self.__class__.__name__}({instance_id})"

        if should_log:
            # Log operation start
            log_method = getattr(self.logger, log_level)
            log_method(
                f"Starting deletion of {self.__class__.__name__}",
                action='delete_start',
                operation='delete',
                instance_id=instance_id,
                instance_str=instance_str,
                **log_context
            )

        try:
            # Call the parent delete method
            result = super().delete(*args, **kwargs)

            if should_log:
                # Log successful completion
                log_method = getattr(self.logger, log_level)
                log_method(
                    f"Successfully deleted {self.__class__.__name__}",
                    action='delete_complete',
                    operation='delete',
                    success=True,
                    deleted_instance_id=instance_id,
                    deleted_instance_str=instance_str,
                    **log_context
                )

            return result

        except Exception as e:
            if should_log:
                # Log failure
                self.logger.error(
                    f"Failed to delete {self.__class__.__name__}",
                    action='delete_failed',
                    operation='delete',
                    success=False,
                    instance_id=instance_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    **log_context
                )
            raise

    def refresh_from_db(self, *args, **kwargs):
        """
        Enhanced refresh_from_db method with optional logging control

        Args:
            *args: Standard Django refresh_from_db() arguments
            **kwargs: Standard Django refresh_from_db() arguments plus:
                - disable_logging (bool): Disable logging for this specific refresh call
                - log_level (str): Override log level for this refresh
        """
        # Extract logging control parameters
        disable_logging = kwargs.pop('disable_logging', False)
        log_level = kwargs.pop('log_level', _GLOBAL_LOGGING_CONFIG.get('log_level', 'debug'))  # Default to debug for refresh

        # Determine if we should log this operation
        should_log = not disable_logging and self._should_log_operation('refresh')

        # Extract any additional context for logging
        log_context = {}
        for key in list(kwargs.keys()):
            if key.startswith('log_'):
                log_context[key[4:]] = kwargs.pop(key)

        instance_id = getattr(self, 'pk', None)
        fields_to_refresh = kwargs.get('fields', 'all')

        if should_log:
            # Log operation start
            log_method = getattr(self.logger, log_level)
            log_method(
                f"Starting refresh of {self.__class__.__name__}",
                action='refresh_start',
                operation='refresh',
                instance_id=instance_id,
                fields=fields_to_refresh,
                **log_context
            )

        try:
            # Call the parent refresh_from_db method
            result = super().refresh_from_db(*args, **kwargs)

            if should_log:
                # Log successful completion
                log_method = getattr(self.logger, log_level)
                log_method(
                    f"Successfully refreshed {self.__class__.__name__}",
                    action='refresh_complete',
                    operation='refresh',
                    success=True,
                    instance_id=instance_id,
                    fields=fields_to_refresh,
                    **log_context
                )

            return result

        except Exception as e:
            if should_log:
                # Log failure
                self.logger.error(
                    f"Failed to refresh {self.__class__.__name__}",
                    action='refresh_failed',
                    operation='refresh',
                    success=False,
                    instance_id=instance_id,
                    error_type=type(e).__name__,
                    error_message=str(e),
                    **log_context
                )
            raise


class DjangoLoggingMixin(LoggingMixin):
    """Enhanced mixin specifically for Django models with intelligent conflict detection"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._detect_existing_logging_extensions()

    def _detect_existing_logging_extensions(self):
        """
        Detect if this model already has extended save/delete/refresh methods
        and automatically disable logging to prevent conflicts
        """
        # Check if the model already has custom save/delete/refresh implementations
        # by examining the method resolution order

        # Get the MRO (Method Resolution Order)
        mro = self.__class__.__mro__

        # Check for common extended model patterns
        has_custom_save = False
        has_custom_delete = False
        has_custom_refresh = False

        for cls in mro:
            cls_name = cls.__name__

            # Detect common extended model patterns
            if any(pattern in cls_name.lower() for pattern in [
                'coremodel', 'extended', 'enhanced', 'audit', 'tracking',
                'basemodel', 'abstractmodel', 'timestamped'
            ]):
                # Check if this class defines its own save/delete/refresh methods
                if 'save' in cls.__dict__:
                    has_custom_save = True
                if 'delete' in cls.__dict__:
                    has_custom_delete = True
                if 'refresh_from_db' in cls.__dict__:
                    has_custom_refresh = True

        # Auto-disable logging for methods that are already extended
        if has_custom_save:
            self._instance_disable_save_logging = True
            if hasattr(self.logger, 'debug'):
                self.logger.debug(
                    "Auto-disabled save logging due to detected custom save implementation",
                    model=self.__class__.__name__,
                    detected_custom_save=True
                )

        if has_custom_delete:
            self._instance_disable_delete_logging = True
            if hasattr(self.logger, 'debug'):
                self.logger.debug(
                    "Auto-disabled delete logging due to detected custom delete implementation",
                    model=self.__class__.__name__,
                    detected_custom_delete=True
                )

        if has_custom_refresh:
            self._instance_disable_refresh_logging = True
            if hasattr(self.logger, 'debug'):
                self.logger.debug(
                    "Auto-disabled refresh logging due to detected custom refresh implementation",
                    model=self.__class__.__name__,
                    detected_custom_refresh=True
                )

    def _create_logger(self):
        """Create a Django-specific logger"""
        # Check if this is a Django model
        if hasattr(self, '_meta'):
            app_label = self._meta.app_label
            model_name = self._meta.model_name
            class_name = self.__class__.__name__

            # Create logger name with Django app structure
            if hasattr(self, 'pk') and self.pk:
                logger_name = f"{app_label}.{model_name}.{self.pk}"
            else:
                logger_name = f"{app_label}.{model_name}"
        else:
            # Fallback to regular mixin behavior
            return super()._create_logger()

        # Get effective configuration
        config = get_effective_config(self._logging_config)

        # Set up Django-specific file path
        if config.get('base_directory'):
            filename_template = config.get('filename_template', '{app_label}_{model_name}_{instance_id}_{timestamp}.log')

            # Generate filename from template
            instance_id = getattr(self, 'pk', 'new')
            timestamp = datetime.now().strftime('%Y%m%d')

            filename = filename_template.format(
                app_label=app_label,
                model_name=model_name,
                class_name=class_name.lower(),
                instance_id=instance_id,
                timestamp=timestamp
            )

            # Create app-specific directory
            log_dir = Path(config['base_directory']) / app_label
            log_dir.mkdir(parents=True, exist_ok=True)

            config['file_path'] = str(log_dir / filename)

        # Create the logger
        logger = LoggerFactory.create_logger(logger_name, config=config)

        # Bind Django-specific context
        context = {
            'app_label': app_label,
            'model_name': model_name,
            'class': class_name,
            'logging_enabled': self._should_log_operation('automatic'),
            **self._logger_context
        }

        if hasattr(self, 'pk') and self.pk:
            context['instance_id'] = str(self.pk)

        return logger.bind(**context)


# ===================
# COMPATIBILITY DECORATORS AND HELPERS
# ===================

def with_logging_control(disable_save=False, disable_delete=False, disable_refresh=False):
    """
    Class decorator to set logging control at the class level

    Usage:
        @with_logging_control(disable_save=True)
        class MyModel(models.Model, DjangoLoggingMixin):
            pass
    """
    def decorator(cls):
        cls._disable_save_logging = disable_save
        cls._disable_delete_logging = disable_delete
        cls._disable_refresh_logging = disable_refresh
        return cls
    return decorator


def disable_mixin_logging_for_class(cls, save=True, delete=True, refresh=True):
    """
    Utility function to disable logging for a specific class

    Usage:
        disable_mixin_logging_for_class(MyModel, save=True, delete=True)
    """
    if save:
        cls._disable_save_logging = True
    if delete:
        cls._disable_delete_logging = True
    if refresh:
        cls._disable_refresh_logging = True


# ===================
# INTEGRATION HELPERS
# ===================

def check_logging_conflicts(model_class):
    """
    Check if a Django model class has potential logging conflicts

    Args:
        model_class: Django model class to check

    Returns:
        dict: Analysis of potential conflicts and recommendations
    """
    analysis = {
        'has_custom_save': False,
        'has_custom_delete': False,
        'has_custom_refresh': False,
        'recommendations': [],
        'detected_extensions': []
    }

    # Check MRO for custom implementations
    for cls in model_class.__mro__:
        cls_name = cls.__name__

        # Skip Django's base classes
        if cls_name in ['Model', 'object']:
            continue

        # Check for custom method implementations
        if 'save' in cls.__dict__:
            analysis['has_custom_save'] = True
            analysis['detected_extensions'].append(f"{cls_name}.save()")

        if 'delete' in cls.__dict__:
            analysis['has_custom_delete'] = True
            analysis['detected_extensions'].append(f"{cls_name}.delete()")

        if 'refresh_from_db' in cls.__dict__:
            analysis['has_custom_refresh'] = True
            analysis['detected_extensions'].append(f"{cls_name}.refresh_from_db()")

    # Generate recommendations
    if analysis['has_custom_save']:
        analysis['recommendations'].append("Disable save logging: instance.disable_logging(save=True)")

    if analysis['has_custom_delete']:
        analysis['recommendations'].append("Disable delete logging: instance.disable_logging(delete=True)")

    if analysis['has_custom_refresh']:
        analysis['recommendations'].append("Disable refresh logging: instance.disable_logging(refresh=True)")

    if not any([analysis['has_custom_save'], analysis['has_custom_delete'], analysis['has_custom_refresh']]):
        analysis['recommendations'].append("No conflicts detected - safe to use all logging features")

    return analysis


# ===================
# USAGE EXAMPLES IN DOCSTRINGS
# ===================

class ExampleUsage:
    """
    Example usage patterns for the enhanced logging mixins

    # Global Configuration
    from logging_suite.mixins import configure_mixin_logging, disable_automatic_logging

    # Disable all automatic logging globally
    disable_automatic_logging()

    # Configure specific aspects globally
    configure_mixin_logging(
        enable_save_logging=False,  # Disable save logging globally
        log_level='debug',          # Default to debug level
        log_performance=True        # Enable performance logging
    )

    # Class-Level Control
    @with_logging_control(disable_save=True, disable_delete=True)
    class MyExtendedModel(models.Model, DjangoLoggingMixin):
        # This class will not log save() or delete() operations
        pass

    # Or set directly on class
    class MyModel(models.Model, DjangoLoggingMixin):
        _disable_save_logging = True  # Disable save logging for this class
        pass

    # Instance-Level Control
    model = MyModel()
    model.disable_logging(save=True, delete=True)  # Disable for this instance
    model.save()  # Will not be logged

    # Method-Level Control
    model.save(disable_logging=True)  # Disable logging for this specific call
    model.delete(disable_logging=True, log_level='error')  # Custom log level
    model.refresh_from_db(disable_logging=True)

    # Check for conflicts before enabling logging
    from logging_suite.mixins import check_logging_conflicts

    conflicts = check_logging_conflicts(MyExtendedModel)
    print(conflicts['recommendations'])

    # Integration with existing extended models
    class MyExistingExtendedModel(CoreModelExtended, DjangoLoggingMixin):
        pass  # DjangoLoggingMixin will auto-detect CoreModelExtended and disable conflicting logging
    """
    pass