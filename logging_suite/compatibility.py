# logging_suite/compatibility.py
"""
Backwards compatibility layer for existing logging setups
FIXED: Path handling and better error checking
"""

import logging
import os
from typing import Dict, Any, Optional, List
from .factory import LoggerFactory
from .unified_logger import UnifiedLogger


class BackwardsCompatibleLogger:
    """
    Logger that maintains API compatibility with existing logging setups
    while providing logging_suite enhancements
    """

    def __init__(self, name: str, existing_config: Dict[str, Any] = None):
        """
        Initialize backwards compatible logger

        Args:
            name: Logger name
            existing_config: Existing logging configuration to maintain compatibility
        """
        self.name = name
        self.existing_config = existing_config or {}

        # Parse the existing config and create logging_suite config
        suite_config = ConfigurationParser.parse_generic_config(existing_config)

        # Create the unified logger
        self._logger = LoggerFactory.create_logger(name, config=suite_config)

        # Store backend name for compatibility reporting
        self.backend_name = self._logger.backend_name

    # Maintain standard logging API
    def debug(self, msg, *args, **kwargs):
        """Debug level logging with standard API"""
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self._logger.debug(msg, **extra, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Info level logging with standard API"""
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self._logger.info(msg, **extra, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Warning level logging with standard API"""
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self._logger.warning(msg, **extra, **kwargs)

    def warn(self, msg, *args, **kwargs):
        """Alias for warning"""
        self.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Error level logging with standard API"""
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self._logger.error(msg, **extra, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Critical level logging with standard API"""
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self._logger.critical(msg, **extra, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """Exception logging with standard API"""
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self._logger.exception(msg, **extra, **kwargs)

    # Enhanced LoggingSuite methods (optional to use)
    def bind(self, **context):
        """Bind context (logging_suite enhancement)"""
        return self._logger.bind(**context)

    @property
    def raw_logger(self):
        """Access to underlying logger"""
        return self._logger.raw_logger

    def get_effective_level(self):
        """Get effective log level for compatibility"""
        return getattr(self._logger.raw_logger, 'level', logging.INFO)

    def setLevel(self, level):
        """Set log level for compatibility"""
        if hasattr(self._logger.raw_logger, 'setLevel'):
            self._logger.raw_logger.setLevel(level)

    def addHandler(self, handler):
        """Add handler for compatibility"""
        if hasattr(self._logger.raw_logger, 'addHandler'):
            self._logger.raw_logger.addHandler(handler)

    def removeHandler(self, handler):
        """Remove handler for compatibility"""
        if hasattr(self._logger.raw_logger, 'removeHandler'):
            self._logger.raw_logger.removeHandler(handler)

    # Properties for full standard logging compatibility
    @property
    def level(self):
        """Get current level"""
        return getattr(self._logger.raw_logger, 'level', logging.INFO)

    @level.setter
    def level(self, value):
        """Set current level"""
        if hasattr(self._logger.raw_logger, 'setLevel'):
            self._logger.raw_logger.setLevel(value)

    def getEffectiveLevel(self):
        """Get effective level"""
        return self.get_effective_level()

    def isEnabledFor(self, level):
        """Check if level is enabled"""
        return level >= self.get_effective_level()

    def getChild(self, suffix):
        """Get child logger for compatibility"""
        child_name = f"{self.name}.{suffix}"
        return BackwardsCompatibleLogger(child_name, self.existing_config)

    # Make it behave like the underlying logger for advanced use cases
    def __getattr__(self, name):
        """Delegate unknown attributes to underlying logger"""
        return getattr(self._logger, name)


class ConfigurationParser:
    """Parse existing logging configurations and convert to logging_suite format"""

    @staticmethod
    def parse_django_logging_config(django_config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Django LOGGING configuration"""
        suite_config = {
            'format': 'json',  # Default to JSON
            'console': True,
            'level': 'INFO'
        }

        # Extract handlers
        handlers = django_config.get('handlers', {})

        # Look for file handlers
        for handler_name, handler_config in handlers.items():
            handler_class = handler_config.get('class', '')

            if 'FileHandler' in handler_class:
                # FIXED: Better filename handling
                filename = handler_config.get('filename')
                if filename:
                    suite_config['file_path'] = os.path.expanduser(filename)
                suite_config['level'] = handler_config.get('level', 'INFO')

            elif 'StreamHandler' in handler_class or 'ConsoleHandler' in handler_class:
                suite_config['console'] = True
                suite_config['console_level'] = handler_config.get('level', 'DEBUG')

        # Extract formatters
        formatters = django_config.get('formatters', {})
        for formatter_name, formatter_config in formatters.items():
            if 'json' in formatter_name.lower():
                suite_config['format'] = 'json'
            elif formatter_config.get('class') and 'json' in formatter_config['class'].lower():
                suite_config['format'] = 'json'

        # Extract loggers
        loggers = django_config.get('loggers', {})
        if loggers:
            # Use the first logger's level as default
            first_logger = next(iter(loggers.values()))
            suite_config['level'] = first_logger.get('level', 'INFO')

        # Preserve custom handlers
        custom_handlers = []
        for handler_name, handler_config in handlers.items():
            if handler_config.get('class') not in [
                'logging.StreamHandler', 'logging.FileHandler',
                'logging.handlers.RotatingFileHandler'
            ]:
                custom_handlers.append(handler_config)

        if custom_handlers:
            suite_config['custom_handlers'] = custom_handlers

        return suite_config

    @staticmethod
    def parse_structlog_config(structlog_config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse structlog configuration"""
        suite_config = {
            'backend': 'structlog',
            'format': 'json',
            'console': True,
            'level': 'INFO'
        }

        # Extract processors
        processors = structlog_config.get('processors', [])
        suite_config['processors'] = processors

        # Check for console renderer
        for processor in processors:
            if isinstance(processor, str):
                if 'ConsoleRenderer' in processor:
                    suite_config['format'] = 'console'
                elif 'JSONRenderer' in processor:
                    suite_config['format'] = 'json'
            elif hasattr(processor, '__name__'):
                if 'ConsoleRenderer' in processor.__name__:
                    suite_config['format'] = 'console'
                elif 'JSONRenderer' in processor.__name__:
                    suite_config['format'] = 'json'

        # Extract other structlog settings
        if 'wrapper_class' in structlog_config:
            suite_config['wrapper_class'] = structlog_config['wrapper_class']

        if 'logger_factory' in structlog_config:
            suite_config['logger_factory'] = structlog_config['logger_factory']

        return suite_config

    @staticmethod
    def parse_loguru_config(loguru_config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse loguru configuration"""
        suite_config = {
            'backend': 'loguru',
            'format': 'json',
            'console': True,
            'level': 'INFO'
        }

        # Extract common loguru settings
        if 'level' in loguru_config:
            suite_config['level'] = loguru_config['level']

        if 'rotation' in loguru_config:
            suite_config['rotation'] = loguru_config['rotation']

        if 'retention' in loguru_config:
            suite_config['retention'] = loguru_config['retention']

        if 'serialize' in loguru_config:
            suite_config['format'] = 'json' if loguru_config['serialize'] else 'console'

        if 'sink' in loguru_config:
            sink = loguru_config['sink']
            if isinstance(sink, str):
                # FIXED: Better path handling
                suite_config['file_path'] = os.path.expanduser(sink)
            elif hasattr(sink, 'write'):  # File-like object
                suite_config['console'] = True

        return suite_config

    @staticmethod
    def parse_generic_config(config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse generic logging configuration"""
        if not config:
            return {'format': 'json', 'console': True, 'level': 'INFO'}

        # Try to detect configuration type
        if 'handlers' in config and 'formatters' in config:
            return ConfigurationParser.parse_django_logging_config(config)
        elif 'processors' in config:
            return ConfigurationParser.parse_structlog_config(config)
        elif any(key in config for key in ['rotation', 'retention', 'serialize']):
            return ConfigurationParser.parse_loguru_config(config)
        else:
            # Generic configuration - pass through with defaults
            result_config = {
                'format': config.get('format', 'json'),
                'console': config.get('console', True),
                'level': config.get('level', 'INFO'),
                'backend': config.get('backend'),
            }

            # FIXED: Better file path handling
            file_path = config.get('file_path')
            if file_path:
                result_config['file_path'] = os.path.expanduser(file_path)

            # Add other config items
            for k, v in config.items():
                if k not in ['format', 'console', 'level', 'file_path', 'backend']:
                    result_config[k] = v

            return result_config


class MigrationHelper:
    """Helper for migrating existing logging setups to logging_suite"""

    @staticmethod
    def analyze_existing_setup(config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze existing setup and provide migration recommendations"""
        analysis = {
            'detected_type': 'unknown',
            'recommendations': [],
            'compatibility_issues': [],
            'migration_steps': [],
            'complexity': 'simple'
        }

        # Detect configuration type
        if 'handlers' in config_dict and 'formatters' in config_dict:
            analysis['detected_type'] = 'django_logging'
            analysis['recommendations'].append("Use BackwardsCompatibleLogger for seamless migration")
            analysis['recommendations'].append("Consider switching to JSON formatting for better structure")

            # Check complexity
            handler_count = len(config_dict.get('handlers', {}))
            formatter_count = len(config_dict.get('formatters', {}))
            logger_count = len(config_dict.get('loggers', {}))

            if handler_count > 3 or formatter_count > 2 or logger_count > 5:
                analysis['complexity'] = 'complex'
                analysis['recommendations'].append("Consider gradual migration due to complex setup")

        elif 'processors' in config_dict:
            analysis['detected_type'] = 'structlog'
            analysis['recommendations'].append("logging_suite has native structlog support")
            analysis['recommendations'].append("Your existing processors will be preserved")

            processor_count = len(config_dict.get('processors', []))
            if processor_count > 5:
                analysis['complexity'] = 'moderate'

        elif any(key in config_dict for key in ['rotation', 'retention', 'serialize']):
            analysis['detected_type'] = 'loguru'
            analysis['recommendations'].append("logging_suite has native loguru support")
            analysis['recommendations'].append("Rotation and retention settings will be preserved")

        else:
            analysis['detected_type'] = 'custom_or_simple'
            analysis['recommendations'].append("Configuration can be easily adapted to logging_suite")

        # Common compatibility issues
        if analysis['detected_type'] == 'django_logging':
            # Check for custom handlers that might need special attention
            handlers = config_dict.get('handlers', {})
            for handler_name, handler_config in handlers.items():
                handler_class = handler_config.get('class', '')
                if 'EmailHandler' in handler_class:
                    analysis['compatibility_issues'].append(
                        f"Email handler '{handler_name}' needs manual configuration"
                    )
                elif 'SysLogHandler' in handler_class:
                    analysis['compatibility_issues'].append(
                        f"SysLog handler '{handler_name}' may need address configuration"
                    )

        # Migration steps based on complexity
        if analysis['complexity'] == 'simple':
            analysis['migration_steps'] = [
                "1. Import logging_suite: from logging_suite import configure_json_logging, LoggerFactory",
                "2. Configure globally: configure_json_logging(level='INFO', console=True)",
                "3. Replace logger creation: logger = LoggerFactory.create_logger(__name__)",
                "4. Update log calls to use structured data: logger.info('message', key=value)",
                "5. Add decorators for enhanced functionality: @catch_and_log, @log_execution_time"
            ]
        else:
            analysis['migration_steps'] = [
                "1. Start with backwards compatibility: BackwardsCompatibleLogger(name, existing_config)",
                "2. Test existing functionality works unchanged",
                "3. Gradually replace loggers one module at a time",
                "4. Migrate to structured logging patterns",
                "5. Add enhanced features (decorators, analysis tools)",
                "6. Remove backwards compatibility when migration complete"
            ]

        return analysis

    @staticmethod
    def generate_migration_code(existing_config: Dict[str, Any],
                                logger_names: List[str]) -> str:
        """Generate migration code for existing setup"""
        config_type = 'unknown'

        # Detect type
        if 'handlers' in existing_config and 'formatters' in existing_config:
            config_type = 'django'
        elif 'processors' in existing_config:
            config_type = 'structlog'
        elif any(key in existing_config for key in ['rotation', 'retention']):
            config_type = 'loguru'

        migration_code = f"""# logging_suite Migration Code
# Detected configuration type: {config_type}

from logging_suite import configure_json_logging, LoggerFactory
from logging_suite.compatibility import BackwardsCompatibleLogger

# Step 1: Configure logging_suite globally
configure_json_logging(
    level='INFO',
    console=True,
    base_directory='logs',
    format='json'
)

# Step 2: Create loggers (choose one approach)

# Option A: Backwards Compatible (maintains existing API)
# Use this approach for immediate compatibility with existing code
"""

        for logger_name in logger_names[:3]:  # Show first 3 examples
            safe_name = logger_name.replace('.', '_').replace('-', '_')
            migration_code += f"""
{safe_name}_logger = BackwardsCompatibleLogger('{logger_name}')
# Use exactly like before: {safe_name}_logger.info('message', extra={{'key': 'value'}})
# Enhanced usage available: {safe_name}_logger.bind(user_id=123).info('message')
"""

        migration_code += """
# Option B: Full logging_suite (enhanced features)
# Use this for new code or after testing backwards compatibility
"""

        for logger_name in logger_names[:3]:
            safe_name = logger_name.replace('.', '_').replace('-', '_')
            migration_code += f"""
{safe_name}_logger = LoggerFactory.create_logger('{logger_name}')
# Enhanced usage: {safe_name}_logger.info('message', key='value', user_id=123)
"""

        migration_code += """
# Step 3: Add enhanced decorators (optional)
from logging_suite.decorators import catch_and_log, log_execution_time

@catch_and_log(reraise=True, include_args=True)
@log_execution_time(level='info')
def your_function():
    # Your code here with automatic exception and timing logging
    pass

# Step 4: Use mixins for object-specific logging (optional)
from logging_suite import LoggingMixin

class YourClass(LoggingMixin):
    _logging_config = {
        'level': 'DEBUG',
        'format': 'json'
    }

    def __init__(self):
        super().__init__()
        self.bind_logger_context(component='your_component')

    def your_method(self):
        self.logger.info("Method called", action="your_method")
"""

        return migration_code

    @staticmethod
    def validate_migration(original_config: Dict[str, Any],
                           suite_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that migration preserves important settings"""
        validation = {
            'status': 'success',
            'warnings': [],
            'preserved_settings': [],
            'lost_settings': []
        }

        # Check preserved settings
        if 'level' in suite_config:
            validation['preserved_settings'].append(f"Log level: {suite_config['level']}")

        if 'file_path' in suite_config:
            validation['preserved_settings'].append(f"File logging: {suite_config['file_path']}")

        if 'console' in suite_config:
            validation['preserved_settings'].append(f"Console logging: {suite_config['console']}")

        # Check for potential issues
        if original_config.get('handlers', {}) and 'custom_handlers' not in suite_config:
            validation['warnings'].append("Custom handlers may need manual configuration")

        if original_config.get('filters'):
            validation['warnings'].append("Logging filters not automatically migrated")
            validation['lost_settings'].append("Custom filters")

        # Set status based on issues
        if validation['warnings']:
            validation['status'] = 'warning'

        if validation['lost_settings']:
            validation['status'] = 'partial'

        return validation


class LegacyLoggerAdapter:
    """Adapter to make logging_suite loggers work with legacy code expecting standard loggers"""

    def __init__(self, unified_logger: UnifiedLogger):
        self.unified_logger = unified_logger
        self._level = logging.INFO

    def debug(self, msg, *args, **kwargs):
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self.unified_logger.debug(msg, **extra)

    def info(self, msg, *args, **kwargs):
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self.unified_logger.info(msg, **extra)

    def warning(self, msg, *args, **kwargs):
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self.unified_logger.warning(msg, **extra)

    def error(self, msg, *args, **kwargs):
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self.unified_logger.error(msg, **extra)

    def critical(self, msg, *args, **kwargs):
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self.unified_logger.critical(msg, **extra)

    def exception(self, msg, *args, **kwargs):
        if args:
            msg = msg % args
        extra = kwargs.pop('extra', {})
        self.unified_logger.exception(msg, **extra)

    # Properties for compatibility
    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value

    def setLevel(self, level):
        self._level = level

    def getEffectiveLevel(self):
        return self._level

    def isEnabledFor(self, level):
        return level >= self._level

    def addHandler(self, handler):
        """Add handler (delegate to underlying logger if possible)"""
        if hasattr(self.unified_logger.raw_logger, 'addHandler'):
            self.unified_logger.raw_logger.addHandler(handler)

    def removeHandler(self, handler):
        """Remove handler (delegate to underlying logger if possible)"""
        if hasattr(self.unified_logger.raw_logger, 'removeHandler'):
            self.unified_logger.raw_logger.removeHandler(handler)


def migrate_from_django_logging(settings_module: str) -> Dict[str, Any]:
    """
    Migrate from Django LOGGING configuration
    FIXED: Better error handling and path validation

    Args:
        settings_module: Django settings module path (e.g., 'myproject.settings')

    Returns:
        Migration information and generated code
    """
    try:
        import importlib

        # FIXED: Handle None settings_module
        if not settings_module:
            return {
                'error': 'Settings module path is required',
                'recommendations': [
                    'Provide a valid Django settings module path',
                    'Example: migrate_from_django_logging("myproject.settings")'
                ]
            }

        settings = importlib.import_module(settings_module)

        if not hasattr(settings, 'LOGGING'):
            return {
                'error': 'No LOGGING configuration found in settings',
                'recommendations': [
                    'Configure logging_suite from scratch using configure_json_logging()',
                    'Add LoggingMixin to your Django models for enhanced logging'
                ]
            }

        django_config = settings.LOGGING

        # Analyze the configuration
        analysis = MigrationHelper.analyze_existing_setup(django_config)

        # Parse to logging_suite format
        suite_config = ConfigurationParser.parse_django_logging_config(django_config)

        # Extract logger names
        logger_names = list(django_config.get('loggers', {}).keys())
        if not logger_names:
            logger_names = ['django', 'myapp']  # Default examples

        # Generate migration code
        migration_code = MigrationHelper.generate_migration_code(django_config, logger_names)

        # Validate migration
        validation = MigrationHelper.validate_migration(django_config, suite_config)

        return {
            'success': True,
            'original_config': django_config,
            'suite_config': suite_config,
            'analysis': analysis,
            'migration_code': migration_code,
            'logger_names': logger_names,
            'validation': validation,
            'summary': f"Found {len(logger_names)} loggers in Django configuration. "
                       f"Migration complexity: {analysis['complexity']}. "
                       f"logging_suite can maintain compatibility while adding structured logging.",
            'next_steps': [
                "1. Copy the generated migration code to your project",
                "2. Test with BackwardsCompatibleLogger first",
                "3. Gradually migrate to full LoggingSuite features",
                "4. Add decorators and mixins for enhanced functionality"
            ]
        }

    except ImportError as e:
        return {
            'error': f'Could not import settings module: {e}',
            'recommendations': [
                'Check the settings module path',
                'Ensure Django is in your Python path',
                'Try relative import: "from . import settings"'
            ]
        }
    except Exception as e:
        return {
            'error': f'Error analyzing Django configuration: {e}',
            'recommendations': [
                'Check Django settings syntax',
                'Ensure LOGGING configuration is a dictionary',
                'Consider manual logging_suite configuration'
            ]
        }


def create_backwards_compatible_logger(name: str,
                                       level: str = 'INFO',
                                       existing_config: Dict[str, Any] = None) -> BackwardsCompatibleLogger:
    """
    Convenience function to create a backwards compatible logger

    Args:
        name: Logger name
        level: Log level
        existing_config: Optional existing configuration

    Returns:
        BackwardsCompatibleLogger instance
    """
    if existing_config is None:
        existing_config = {
            'level': level,
            'console': True,
            'format': 'json'
        }

    return BackwardsCompatibleLogger(name, existing_config)


def test_compatibility(logger_name: str = 'test.compatibility') -> Dict[str, Any]:
    """
    Test backwards compatibility functionality

    Args:
        logger_name: Name for test logger

    Returns:
        Test results
    """
    results = {
        'tests_passed': 0,
        'tests_failed': 0,
        'details': []
    }

    try:
        # Test 1: Basic logger creation
        logger = create_backwards_compatible_logger(logger_name)
        results['tests_passed'] += 1
        results['details'].append("✓ Logger creation successful")

        # Test 2: Standard logging methods
        logger.info("Test info message", extra={'test_key': 'test_value'})
        logger.debug("Test debug message")
        logger.warning("Test warning message")
        results['tests_passed'] += 1
        results['details'].append("✓ Standard logging methods work")

        # Test 3: Enhanced features
        bound_logger = logger.bind(test_context='enhanced')
        bound_logger.info("Test enhanced logging")
        results['tests_passed'] += 1
        results['details'].append("✓ Enhanced features available")

        # Test 4: Level management
        original_level = logger.getEffectiveLevel()
        logger.setLevel(logging.DEBUG)
        logger.setLevel(original_level)
        results['tests_passed'] += 1
        results['details'].append("✓ Level management works")

    except Exception as e:
        results['tests_failed'] += 1
        results['details'].append(f"✗ Test failed: {e}")

    results['success'] = results['tests_failed'] == 0
    results['summary'] = f"Passed: {results['tests_passed']}, Failed: {results['tests_failed']}"

    return results