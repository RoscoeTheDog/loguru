# logging_suite/tests_integrated.py
"""
Integrated test suite for logging_suite package
Consolidates all testing functionality for easy access from main module
FIXED: Import issues and circular import resolution - uses orchestration layer
"""

import unittest
import tempfile
import shutil
import sys
import os
import time
import threading
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO
from contextlib import contextmanager
from typing import List, Dict, Any, Optional

# FIXED: Use orchestration layer instead of direct config imports to avoid circular imports
try:
    from .factory import LoggerFactory
    from .unified_logger import UnifiedLogger

    # FIXED: Import from orchestration layer instead of config directly
    from .orchestration import (
        configure_global_logging, create_logger,
        configure_development_logging, configure_production_logging,
        configure_for_cli, ensure_environment_overrides_applied,
        get_available_backends  # This is also in orchestration.py
    )

    # Import config functions that are actually in config.py
    from .config import get_global_config

    from .tracing import (
        TraceManager, enable_development_tracing, get_tracing_status
    )
    from .decorators import catch_and_log, log_execution_time, traced
    from .mixins import LoggingMixin
    from .compatibility import create_backwards_compatible_logger, test_compatibility

    # Ensure backends are properly initialized
    from .backends import ensure_backends_initialized

    # Global exception hook imports
    try:
        from .global_exception_hook import (
            install_global_exception_hook,
            uninstall_global_exception_hook,
            is_global_exception_hook_installed,
            DataFormatter,
            EnhancedConsoleFormatter
        )
        HAS_GLOBAL_EXCEPTION_HOOK = True
    except ImportError:
        HAS_GLOBAL_EXCEPTION_HOOK = False

    IMPORTS_SUCCESSFUL = True

except ImportError as e:
    print(f"Warning: Could not import logging_suite modules: {e}")
    IMPORTS_SUCCESSFUL = False


# Helper functions that we'll define locally to avoid circular imports
def _get_logger(name: str, **config):
    """Get logger without importing from __init__.py"""
    if not IMPORTS_SUCCESSFUL:
        raise ImportError("logging_suite modules not available")
    return LoggerFactory.create_logger(name, config=config)


def _quick_setup(**kwargs):
    """Quick setup using orchestration layer"""
    if not IMPORTS_SUCCESSFUL:
        raise ImportError("logging_suite modules not available")

    # Apply defaults
    config = {
        'level': 'INFO',
        'format': 'json',
        'console': True,
        'base_directory': 'logs',
        'enable_tracing': None,
        'backend': 'standard',
        'apply_env_overrides': True
    }
    config.update(kwargs)

    # Use orchestration layer for configuration
    configure_global_logging(
        backend=config['backend'],
        level=config['level'],
        format=config['format'],
        console=config['console'],
        base_directory=config['base_directory'],
        use_json_handlers=config['format'] == 'json',
        pretty_json=True
    )

    # Handle tracing
    if config['enable_tracing'] is None:
        env = os.getenv('ENVIRONMENT', os.getenv('DJANGO_ENVIRONMENT', 'development'))
        config['enable_tracing'] = env.lower() in ('development', 'dev', 'local')

    if config['enable_tracing']:
        enable_development_tracing()

    # Apply environment overrides if requested
    if config['apply_env_overrides']:
        ensure_environment_overrides_applied()


def _quick_api_setup(framework='fastapi'):
    """Quick API setup using orchestration layer"""
    if framework.lower() == 'fastapi':
        from .orchestration import configure_for_fastapi
        configure_for_fastapi()
    else:
        _quick_setup(level='INFO', console=True, enable_tracing=True)


def _get_package_info():
    """Get package info without importing from __init__.py"""
    if not IMPORTS_SUCCESSFUL:
        return {
            'version': '1.0.0',
            'author': 'logging_suite Team',
            'license': 'MIT',
            'available_backends': ['standard'],
            'features': {'integrated_tests': True},
            'package_location': __file__,
            'initialized': False,
        }

    return {
        'version': '1.0.0',
        'author': 'logging_suite Team',
        'license': 'MIT',
        'available_backends': get_available_backends(),
        'features': {
            'integrated_tests': True,
            'tracing': True,
        },
        'tracing_status': get_tracing_status(),
        'package_location': __file__,
        'initialized': True,
    }


# Try to import sensitive key functions if available
try:
    from .config import (
        configure_sensitive_keys, get_sensitive_keys,
        add_sensitive_keys, remove_sensitive_keys
    )

    HAS_SENSITIVE_KEY_CONFIG = True
except ImportError:
    HAS_SENSITIVE_KEY_CONFIG = False

# Ensure backends are initialized if possible
if IMPORTS_SUCCESSFUL:
    ensure_backends_initialized()


class TestEnvironment:
    """Test environment setup and teardown"""

    def __init__(self):
        self.temp_dir = None
        self.original_env = {}

    def __enter__(self):
        # Create temporary directory for test logs
        self.temp_dir = tempfile.mkdtemp(prefix='loggingsuite_test_')

        # Store original environment variables
        env_vars = [
            'LOGGINGSUITE_LEVEL', 'LOGGINGSUITE_TRACING', 'LOGGINGSUITE_BACKEND',
            'LOGGINGSUITE_AUTO_CONFIGURE', 'ENVIRONMENT', 'DEBUG'
        ]

        for var in env_vars:
            self.original_env[var] = os.getenv(var)
            if var in os.environ:
                del os.environ[var]

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original environment
        for var, value in self.original_env.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]

        # Force close any open file handlers that might be in use
        try:
            # Close standard logging handlers
            import logging
            logging.shutdown()

            # Try to explicitly close any handlers in our logger factory
            if IMPORTS_SUCCESSFUL:
                for name, logger in LoggerFactory._logger_instances.items() if hasattr(LoggerFactory, '_logger_instances') else {}:
                    if hasattr(logger, 'handlers'):
                        for handler in list(logger.handlers):
                            try:
                                handler.flush()
                                handler.close()
                            except Exception:
                                pass
        except Exception as e:
            print(f"Warning: Error while closing loggers: {e}")

        # Force Python's garbage collection to release any resources
        import gc
        gc.collect()

        # Wait a moment for file operations to complete
        import time
        time.sleep(0.1)

        # Clean up temporary directory with retry logic
        if self.temp_dir and os.path.exists(self.temp_dir):
            max_retries = 3
            retry_delay = 0.5

            for attempt in range(max_retries):
                try:
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
                    break
                except PermissionError as e:
                    if attempt < max_retries - 1:
                        print(f"Retry {attempt+1}/{max_retries}: Failed to clean up test directory: {e}")
                        time.sleep(retry_delay)
                    else:
                        print(f"Warning: Failed to clean up test directory after {max_retries} attempts: {e}")
                        print(f"Temporary files may remain in: {self.temp_dir}")


class TestBackendAvailability(unittest.TestCase):
    """Test backend availability and functionality"""

    def setUp(self):
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("logging_suite modules not available")

        self.test_env = TestEnvironment()
        self.test_env.__enter__()
        ensure_backends_initialized()

    def tearDown(self):
        if hasattr(self, 'test_env'):
            self.test_env.__exit__(None, None, None)

    def test_backend_detection(self):
        """Test automatic backend detection"""
        backends = get_available_backends()
        self.assertIsInstance(backends, list)
        self.assertIn('standard', backends)

    def test_backend_status(self):
        """Test backend status reporting"""
        status = LoggerFactory.get_backend_status()
        self.assertIsInstance(status, dict)
        self.assertTrue(status.get('standard', False))

    def test_standard_backend(self):
        """Test standard logging backend"""
        logger = LoggerFactory.create_logger('test_standard', backend='standard')
        self.assertIsNotNone(logger)

        logger.info("Test message", test_data="test_value")
        logger.warning("Test warning", component_name="test")
        logger.error("Test error", error_code=500)

    def test_backend_fallback(self):
        """Test backend fallback mechanism"""
        try:
            logger = LoggerFactory.create_logger('test_fallback', backend='nonexistent')
            self.assertIsNotNone(logger)
            self.assertEqual(logger.backend_name, 'standard')
        except Exception as e:
            self.assertIn("not available", str(e).lower())


class TestConvenienceMethods(unittest.TestCase):
    """Test convenience methods and aliases"""

    def setUp(self):
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("logging_suite modules not available")

        self.test_env = TestEnvironment()
        self.test_env.__enter__()
        _quick_setup(level='DEBUG', console=True)

    def tearDown(self):
        if IMPORTS_SUCCESSFUL:
            try:
                # Clean up loggers before removing temp directory
                LoggerFactory.cleanup_loggers()
            except Exception as e:
                print(f"Warning: Logger cleanup failed: {e}")

        if hasattr(self, 'test_env'):
            self.test_env.__exit__(None, None, None)

    def test_get_logger_variants(self):
        """Test logger creation methods"""
        # Test basic logger creation
        logger1 = _get_logger('test.get_logger')
        self.assertIsNotNone(logger1)
        self.assertTrue(hasattr(logger1, 'info'))
        self.assertTrue(hasattr(logger1, 'backend_name'))

        # Test they work for logging
        logger1.info("Test from get_logger")

    def test_logger_configuration(self):
        """Test logger creation with configuration"""
        test_logger = _get_logger('test.config', level='WARNING', format='json')
        self.assertIsNotNone(test_logger)
        test_logger.warning("Configuration test", config_type="custom")


class TestSensitiveKeyConfiguration(unittest.TestCase):
    """Test configurable sensitive key sanitization"""

    def setUp(self):
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("logging_suite modules not available")

        # Only run these tests if sensitive key config is available
        if not HAS_SENSITIVE_KEY_CONFIG:
            self.skipTest("Sensitive key configuration not available")

        self.test_env = TestEnvironment()
        self.test_env.__enter__()

        # Reset to defaults
        configure_sensitive_keys(reset_to_defaults=True)

    def tearDown(self):
        if hasattr(self, 'test_env'):
            self.test_env.__exit__(None, None, None)
        if HAS_SENSITIVE_KEY_CONFIG:
            # Reset to defaults
            configure_sensitive_keys(reset_to_defaults=True)

    def test_default_sensitive_keys(self):
        """Test default sensitive keys"""
        keys = get_sensitive_keys()
        self.assertIn('password', keys)
        self.assertIn('token', keys)
        self.assertIn('api_key', keys)

    def test_add_sensitive_keys(self):
        """Test adding custom sensitive keys"""
        original_count = len(get_sensitive_keys())

        # Add custom keys
        new_keys = add_sensitive_keys('custom_secret', 'internal_token')

        self.assertGreater(len(new_keys), original_count)
        self.assertIn('custom_secret', new_keys)
        self.assertIn('internal_token', new_keys)


class TestQuickSetupAndConfiguration(unittest.TestCase):
    """Test quick setup functions and configuration management"""

    def setUp(self):
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("logging_suite modules not available")

        self.test_env = TestEnvironment()
        self.test_env.__enter__()

    def tearDown(self):
        if hasattr(self, 'test_env'):
            self.test_env.__exit__(None, None, None)

    def test_quick_setup(self):
        """Test quick setup function"""
        _quick_setup(
            level='DEBUG',
            format='json',
            console=True,
            base_directory=self.test_env.temp_dir,
            enable_tracing=True
        )

        test_logger = _get_logger('test_quick_setup')
        test_logger.info("Quick setup test", feature_name="configuration")

    def test_framework_configurations(self):
        """Test framework-specific configurations"""
        configure_for_cli()
        cli_logger = _get_logger('test_cli')
        cli_logger.info("CLI configuration test")

        _quick_api_setup('fastapi')
        api_logger = _get_logger('test_api')
        api_logger.info("API configuration test", endpoint_path="/test")

    def test_environment_based_config(self):
        """Test environment-based configuration"""
        os.environ['LOGGINGSUITE_LEVEL'] = 'WARNING'
        os.environ['LOGGINGSUITE_TRACING'] = 'true'
        os.environ['LOGGINGSUITE_PRETTY_JSON'] = 'true'

        # Apply environment overrides
        ensure_environment_overrides_applied()

        current_config = get_global_config()
        self.assertEqual(current_config['level'], 'WARNING')
        self.assertTrue(current_config['tracing_enabled'])
        self.assertTrue(current_config['pretty_json'])


class TestDecorators(unittest.TestCase):
    """Test enhanced decorators functionality"""

    def setUp(self):
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("logging_suite modules not available")

        self.test_env = TestEnvironment()
        self.test_env.__enter__()
        _quick_setup(level='DEBUG', base_directory=self.test_env.temp_dir, enable_tracing=True)
        self.logger = _get_logger('test_decorators')

    def tearDown(self):
        if hasattr(self, 'test_env'):
            self.test_env.__exit__(None, None, None)

    def test_catch_and_log_decorator(self):
        """Test catch_and_log decorator"""

        @catch_and_log(logger=self.logger, include_args=True, sanitize_sensitive=True, reraise=False)
        def test_function(user_id: int, password: str = "secret123"):
            if user_id < 0:
                raise ValueError("Invalid user ID")
            return f"User {user_id} processed"

        result = test_function(123)
        self.assertEqual(result, "User 123 processed")

        result = test_function(-1)
        self.assertIsNone(result)

    def test_execution_time_decorator(self):
        """Test log_execution_time decorator"""

        @log_execution_time(logger=self.logger, threshold_seconds=0.01)
        def slow_function():
            time.sleep(0.02)
            return "completed"

        result = slow_function()
        self.assertEqual(result, "completed")

    def test_traced_decorator(self):
        """Test traced decorator"""

        @traced(enabled=True, level='info', min_execution_time=0.0)
        def always_traced():
            return "always traced"

        @traced(enabled=False)
        def never_traced():
            return "never traced"

        result1 = always_traced()
        result2 = never_traced()
        self.assertEqual(result1, "always traced")
        self.assertEqual(result2, "never traced")


class TestTracingSystem(unittest.TestCase):
    """Test global tracing system"""

    def setUp(self):
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("logging_suite modules not available")

        self.test_env = TestEnvironment()
        self.test_env.__enter__()
        _quick_setup(level='DEBUG', base_directory=self.test_env.temp_dir, enable_tracing=True)

    def tearDown(self):
        if hasattr(self, 'test_env'):
            self.test_env.__exit__(None, None, None)

    def test_tracing_configuration(self):
        """Test tracing configuration"""
        enable_development_tracing()
        status = get_tracing_status()
        self.assertTrue(status.get('enabled', False))

    def test_tracing_manager(self):
        """Test TraceManager functionality"""
        TraceManager.configure(
            global_enabled=True,
            include_modules={'test.*'},
            exclude_functions={'__str__', '__repr__'},
            min_execution_time=0.0,
            performance_threshold=0.1
        )

        should_trace = TraceManager.should_trace_function('test_func', 'test.module')
        self.assertTrue(should_trace)

        should_not_trace = TraceManager.should_trace_function('__str__', 'test.module')
        self.assertFalse(should_not_trace)


class TestMixinsAndDjangoIntegration(unittest.TestCase):
    """Test mixin functionality"""

    def setUp(self):
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("logging_suite modules not available")

        self.test_env = TestEnvironment()
        self.test_env.__enter__()
        _quick_setup(level='DEBUG', base_directory=self.test_env.temp_dir)

    def tearDown(self):
        if hasattr(self, 'test_env'):
            self.test_env.__exit__(None, None, None)

    def test_basic_logging_mixin(self):
        """Test basic LoggingMixin functionality"""

        class TestClass(LoggingMixin):
            def __init__(self, name):
                super().__init__()
                self.name = name
                self.id = 123

        obj = TestClass("test_object")
        self.assertIsNotNone(obj.logger)
        obj.logger.info("Test message from mixin", object_name=obj.name)
        obj.bind_logger_context(operation_type="test", status_flag="active")
        obj.logger.info("Message with bound context")


class TestCompatibilityAndMigration(unittest.TestCase):
    """Test backwards compatibility and migration features"""

    def setUp(self):
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("logging_suite modules not available")

        self.test_env = TestEnvironment()
        self.test_env.__enter__()
        _quick_setup(level='DEBUG', base_directory=self.test_env.temp_dir)

    def tearDown(self):
        if hasattr(self, 'test_env'):
            self.test_env.__exit__(None, None, None)

    def test_backwards_compatible_logger(self):
        """Test BackwardsCompatibleLogger functionality"""
        compat_logger = create_backwards_compatible_logger('test.compat')
        compat_logger.info("Standard info message", extra={'key_name': 'value'})
        compat_logger.warning("Warning with formatting: %s", "formatted_value")
        compat_logger.error("Error message")

        enhanced = compat_logger.bind(user_id=123, session_key="test_session")
        enhanced.info("Enhanced logging with context")

    def test_compatibility_testing(self):
        """Test built-in compatibility testing"""
        results = test_compatibility('test.compat.logger')
        self.assertIn('tests_passed', results)
        self.assertIn('tests_failed', results)
        self.assertIn('success', results)


class TestPerformanceAndBenchmarks(unittest.TestCase):
    """Test performance characteristics and benchmarks"""

    def setUp(self):
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("logging_suite modules not available")

        self.test_env = TestEnvironment()
        self.test_env.__enter__()
        _quick_setup(level='INFO', base_directory=self.test_env.temp_dir, enable_tracing=False)

    def tearDown(self):
        if hasattr(self, 'test_env'):
            self.test_env.__exit__(None, None, None)

    def test_logging_performance(self):
        """Test basic logging performance"""
        test_logger = _get_logger('performance_test')

        start_time = time.time()
        for i in range(1000):
            test_logger.info("Performance test message", iteration=i, test_data="sample")
        end_time = time.time()

        duration = end_time - start_time
        rate = 1000 / duration
        self.assertGreater(rate, 50)  # Should be reasonably fast

    def test_concurrent_logging(self):
        """Test concurrent logging from multiple threads"""
        results = []

        def worker_thread(thread_id):
            thread_logger = _get_logger(f'thread_{thread_id}')
            try:
                for i in range(5):
                    thread_logger.info(f"Thread {thread_id} message {i}",
                                       thread_id=thread_id, message_num=i)
                    time.sleep(0.001)
                results.append(f"thread_{thread_id}_success")
            except Exception as e:
                results.append(f"thread_{thread_id}_error: {e}")

        threads = []
        for i in range(5):
            t = threading.Thread(target=worker_thread, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        success_count = len([r for r in results if 'success' in r])
        self.assertEqual(success_count, 5)


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Test error handling and edge cases"""

    def setUp(self):
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("logging_suite modules not available")

        self.test_env = TestEnvironment()
        self.test_env.__enter__()

    def tearDown(self):
        if hasattr(self, 'test_env'):
            self.test_env.__exit__(None, None, None)

    def test_missing_dependencies_handling(self):
        """Test graceful handling of missing dependencies"""
        # Test that package works even with missing optional dependencies
        test_logger = _get_logger('test_missing_deps')
        test_logger.info("Testing with potentially missing dependencies")

        # Test feature flags
        info = _get_package_info()
        self.assertIn('features', info)

    def test_invalid_configuration(self):
        """Test handling of invalid configurations"""
        # Test invalid backend - should fall back gracefully
        try:
            logger_instance = LoggerFactory.create_logger('test', backend='nonexistent')
            self.assertIsNotNone(logger_instance)  # Should fall back to standard
        except Exception as e:
            # Exception is also acceptable if it's informative
            self.assertIn("backend", str(e).lower())


class TestGlobalExceptionHook(unittest.TestCase):
    """Test global exception hook functionality with section controls and pretty printing"""

    def setUp(self):
        if not IMPORTS_SUCCESSFUL:
            self.skipTest("logging_suite modules not available")
        
        if not HAS_GLOBAL_EXCEPTION_HOOK:
            self.skipTest("Global exception hook not available")

        self.test_env = TestEnvironment()
        self.test_env.__enter__()
        _quick_setup(level='DEBUG', base_directory=self.test_env.temp_dir)
        
        # Ensure hook is uninstalled at start
        if is_global_exception_hook_installed():
            uninstall_global_exception_hook()

    def tearDown(self):
        # Clean up hook if installed
        if HAS_GLOBAL_EXCEPTION_HOOK and is_global_exception_hook_installed():
            uninstall_global_exception_hook()
            
        if hasattr(self, 'test_env'):
            self.test_env.__exit__(None, None, None)

    def test_section_control_flags_in_config(self):
        """Test that section control flags are present in global configuration"""
        config = get_global_config()
        
        expected_flags = [
            'show_exception_details', 'show_system_state', 'show_stack_trace',
            'show_code_context', 'show_environment_vars', 'pretty_print_stack_data',
            'stack_data_max_length', 'stack_data_max_depth'
        ]
        
        for flag in expected_flags:
            self.assertIn(flag, config, f"Section control flag '{flag}' missing from config")

    def test_hook_installation_and_removal(self):
        """Test basic hook installation and removal"""
        self.assertFalse(is_global_exception_hook_installed())
        
        success = install_global_exception_hook()
        self.assertTrue(success)
        self.assertTrue(is_global_exception_hook_installed())
        
        success = uninstall_global_exception_hook()
        self.assertTrue(success)
        self.assertFalse(is_global_exception_hook_installed())

    def test_data_formatter_functionality(self):
        """Test DataFormatter with various data types"""
        formatter = DataFormatter(max_length=50, max_depth=2, pretty_print=True)
        
        test_cases = {
            'string': 'hello world',
            'number': 42,
            'boolean': True,
            'none': None,
            'list': [1, 2, 3, 4, 5],
            'dict': {'key': 'value'},
            'nested_dict': {'level1': {'level2': {'level3': 'deep'}}},
            'long_string': 'a' * 100  # Should be truncated
        }
        
        for name, value in test_cases.items():
            with self.subTest(data_type=name):
                formatted = formatter.format_value(value)
                self.assertIsInstance(formatted, str)
                self.assertLessEqual(len(formatted), formatter.max_length)

    def test_console_formatter_section_controls(self):
        """Test that console formatter respects section control flags"""
        # Test with all sections enabled
        config_all = {
            'show_exception_details': True,
            'show_system_state': True,
            'show_stack_trace': True,
            'show_code_context': True,
            'show_environment_vars': True,
            'use_colors': False
        }
        
        formatter_all = EnhancedConsoleFormatter(colorize=False, config=config_all)
        
        # Test with minimal sections
        config_minimal = {
            'show_exception_details': False,
            'show_system_state': False,
            'show_stack_trace': False,
            'show_code_context': False,
            'show_environment_vars': False,
            'use_colors': False
        }
        
        formatter_minimal = EnhancedConsoleFormatter(colorize=False, config=config_minimal)
        
        # Mock exception data
        exc_type = ValueError
        exc_value = ValueError("Test exception")
        exc_traceback = None
        system_info = {
            'process': {'pid': 1234, 'memory_rss': 1024000},
            'environment': {'environment_vars': {'TEST_VAR': 'test_value'}}
        }
        exception_context = {
            'exception_location': 'test.py:10',
            'exception_function': 'test_function',
            'exception_module': 'test_module'
        }
        
        output_all = formatter_all.format_comprehensive_output(
            exc_type, exc_value, exc_traceback, system_info, exception_context
        )
        
        output_minimal = formatter_minimal.format_comprehensive_output(
            exc_type, exc_value, exc_traceback, system_info, exception_context
        )
        
        # Minimal output should be significantly shorter
        self.assertLess(len(output_minimal), len(output_all))

    def test_environment_variables_for_section_controls(self):
        """Test environment variable support for section control flags"""
        from logging_suite.config import get_environment_overrides
        
        test_env_vars = {
            'LOGGINGSUITE_SHOW_EXCEPTION_DETAILS': 'false',
            'LOGGINGSUITE_SHOW_SYSTEM_STATE': 'true', 
            'LOGGINGSUITE_SHOW_STACK_TRACE': 'false',
            'LOGGINGSUITE_PRETTY_PRINT_STACK_DATA': 'false',
            'LOGGINGSUITE_STACK_DATA_MAX_LENGTH': '100',
            'LOGGINGSUITE_STACK_DATA_MAX_DEPTH': '2'
        }
        
        # Store original values
        original_values = {}
        for env_var in test_env_vars:
            original_values[env_var] = os.environ.get(env_var)
        
        try:
            # Set test values
            for env_var, value in test_env_vars.items():
                os.environ[env_var] = value
            
            overrides = get_environment_overrides()
            
            expected_overrides = {
                'show_exception_details': False,
                'show_system_state': True,
                'show_stack_trace': False,
                'pretty_print_stack_data': False,
                'stack_data_max_length': 100,
                'stack_data_max_depth': 2
            }
            
            for key, expected_value in expected_overrides.items():
                self.assertEqual(overrides.get(key), expected_value,
                               f"Environment override for '{key}' failed")
                
        finally:
            # Restore original values
            for env_var, original_value in original_values.items():
                if original_value is None:
                    os.environ.pop(env_var, None)
                else:
                    os.environ[env_var] = original_value

    def test_development_config_includes_section_flags(self):
        """Test that development configuration includes all section control flags"""
        configure_development_logging()
        config = get_global_config()
        
        expected_dev_flags = {
            'show_exception_details': True,
            'show_system_state': True,
            'show_stack_trace': True,
            'show_code_context': True,
            'show_environment_vars': True,
            'pretty_print_stack_data': True,
            'stack_data_max_length': 500,
            'stack_data_max_depth': 5
        }
        
        for flag, expected_value in expected_dev_flags.items():
            actual_value = config.get(flag)
            self.assertEqual(actual_value, expected_value,
                           f"Development config flag '{flag}' mismatch: got {actual_value}, expected {expected_value}")

    def test_hook_with_custom_config(self):
        """Test hook installation with custom configuration"""
        custom_config = {
            'show_exception_details': True,
            'show_system_state': False,
            'show_stack_trace': True,
            'show_code_context': False,
            'show_environment_vars': False,
            'pretty_print_stack_data': True,
            'stack_data_max_length': 100,
            'stack_data_max_depth': 2
        }
        
        success = install_global_exception_hook(custom_config)
        self.assertTrue(success)
        self.assertTrue(is_global_exception_hook_installed())


class LoggingSuiteTestRunner:
    """Enhanced test runner with comprehensive reporting and configuration"""

    def __init__(self):
        self.test_classes = [
            TestBackendAvailability,
            TestConvenienceMethods,
            TestQuickSetupAndConfiguration,
            TestDecorators,
            TestTracingSystem,
            TestMixinsAndDjangoIntegration,
            TestCompatibilityAndMigration,
            TestPerformanceAndBenchmarks,
            TestErrorHandlingAndEdgeCases
        ]

        # Only include sensitive key tests if available
        if HAS_SENSITIVE_KEY_CONFIG:
            self.test_classes.insert(2, TestSensitiveKeyConfiguration)
            
        # Only include global exception hook tests if available
        if HAS_GLOBAL_EXCEPTION_HOOK:
            self.test_classes.insert(-2, TestGlobalExceptionHook)  # Insert before performance tests

    def get_available_test_classes(self) -> List[str]:
        """Get list of available test class names"""
        return [cls.__name__ for cls in self.test_classes]

    def run_tests(self,
                  quick: bool = False,
                  verbose: bool = False,
                  specific_test: Optional[str] = None,
                  benchmark: bool = False,
                  coverage: bool = False) -> bool:
        """
        Run the test suite with various options

        Args:
            quick: Run only essential tests
            verbose: Verbose output
            specific_test: Run only specific test class
            benchmark: Include performance benchmarks
            coverage: Generate coverage report (if available)

        Returns:
            True if all tests passed
        """
        if not IMPORTS_SUCCESSFUL:
            print("❌ Cannot run tests: logging_suite modules not available")
            return False

        # Clean header
        print("\n" + "═" * 80)
        print("🧪 LOGGING SUITE TEST RUNNER")
        print("═" * 80)

        # Compact package info
        self._show_package_info()

        # Ensure backends are initialized
        ensure_backends_initialized()

        # Determine test scope
        if specific_test:
            test_classes = [cls for cls in self.test_classes if cls.__name__ == specific_test]
            if not test_classes:
                print(f"\n❌ Test class '{specific_test}' not found")
                print("💡 Available test classes:")
                for class_name in self.get_available_test_classes():
                    print(f"   • {class_name}")
                return False
            scope_info = f"🎯 Specific test: {specific_test}"
        elif quick:
            essential_tests = [
                TestBackendAvailability,
                TestConvenienceMethods,
                TestQuickSetupAndConfiguration,
                TestCompatibilityAndMigration
            ]
            test_classes = essential_tests
            scope_info = "⚡ Quick mode (essential tests)"
        else:
            test_classes = self.test_classes
            scope_info = "🔍 Full suite (all tests)"

        if not benchmark:
            test_classes = [cls for cls in test_classes if cls != TestPerformanceAndBenchmarks]
        else:
            scope_info += " + benchmarks"

        # Calculate total test count
        total_test_count = sum(
            unittest.TestLoader().loadTestsFromTestCase(cls).countTestCases()
            for cls in test_classes
        )

        print(f"\n{scope_info}")
        print(f"📊 {total_test_count} tests across {len(test_classes)} test suites")
        print("─" * 80)

        # Initialize counters
        overall_start_time = time.time()
        test_results = []
        total_passed = 0
        total_failed = 0
        total_errors = 0
        total_skipped = 0

        # Run test classes
        for i, test_class in enumerate(test_classes, 1):
            class_name = test_class.__name__.replace('Test', '').replace('And', ' & ')

            print(f"\n{i:2d}/{len(test_classes)} 📂 {class_name}")

            # Create and run test suite
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            stream = StringIO()
            runner = unittest.TextTestRunner(stream=stream, verbosity=1, buffer=True)

            class_start_time = time.time()
            result = runner.run(suite)
            class_duration = time.time() - class_start_time

            # Process results
            passed = result.testsRun - len(result.failures) - len(result.errors)
            failed = len(result.failures)
            errors = len(result.errors)
            skipped = len(getattr(result, 'skipped', []))

            total_passed += passed
            total_failed += failed
            total_errors += errors
            total_skipped += skipped

            # Status display
            if failed + errors == 0:
                status = "✅ PASS"
                detail = f"({passed} tests, {class_duration:.1f}s)"
            else:
                status = "❌ FAIL" if failed > 0 else "⚠️  ERROR"
                detail = f"({passed} pass, {failed} fail, {errors} err, {class_duration:.1f}s)"

            print(f"      {status} {detail}")

            # Store detailed results for later
            test_results.append({
                'class': test_class,
                'result': result,
                'duration': class_duration,
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'skipped': skipped
            })

            # Show individual test failures in compact format (non-verbose)
            if not verbose and (failed + errors > 0):
                all_failures = result.failures + result.errors
                for test, traceback in all_failures[:3]:  # Show first 3 failures
                    test_method = str(test).split('.')[-1].replace('test_', '')
                    first_error_line = traceback.split('\n')[-2].strip() if '\n' in traceback else traceback.strip()
                    print(f"        ❌ {test_method}: {first_error_line}")
                if len(all_failures) > 3:
                    print(f"        ... and {len(all_failures) - 3} more failures")

        # Calculate totals
        overall_duration = time.time() - overall_start_time
        total_tests = total_passed + total_failed + total_errors + total_skipped
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        # Final summary with clean formatting
        print("\n" + "═" * 80)
        print("📊 FINAL RESULTS")
        print("═" * 80)

        # Aligned summary table
        print(f"Total Tests:     {total_tests:>6}")
        print(f"✅ Passed:        {total_passed:>6} ({total_passed/total_tests*100:>5.1f}%)")

        if total_failed > 0:
            print(f"❌ Failed:        {total_failed:>6} ({total_failed/total_tests*100:>5.1f}%)")
        if total_errors > 0:
            print(f"⚠️  Errors:        {total_errors:>6} ({total_errors/total_tests*100:>5.1f}%)")
        if total_skipped > 0:
            print(f"⏭️  Skipped:       {total_skipped:>6} ({total_skipped/total_tests*100:>5.1f}%)")

        print(f"⏱️  Duration:      {overall_duration:>6.2f}s")

        # Show verbose details if requested
        if verbose and (total_failed + total_errors > 0):
            print("\n" + "─" * 80)
            print("🔍 DETAILED ERROR REPORT")
            print("─" * 80)
            for test_result in test_results:
                if test_result['failed'] + test_result['errors'] > 0:
                    class_name = test_result['class'].__name__
                    print(f"\n📂 {class_name}:")

                    # Show failures
                    for test, traceback in test_result['result'].failures:
                        test_name = str(test).split('.')[-1]
                        print(f"  ❌ {test_name}")
                        # Show last few lines of traceback
                        lines = traceback.strip().split('\n')
                        relevant_lines = [line for line in lines[-5:] if line.strip()]
                        for line in relevant_lines[-2:]:
                            print(f"     {line}")

                    # Show errors
                    for test, traceback in test_result['result'].errors:
                        test_name = str(test).split('.')[-1]
                        print(f"  ⚠️  {test_name}")
                        lines = traceback.strip().split('\n')
                        relevant_lines = [line for line in lines[-5:] if line.strip()]
                        for line in relevant_lines[-2:]:
                            print(f"     {line}")

        # Coverage report
        if coverage:
            print("\n" + "─" * 80)
            self._generate_coverage_report()

        # Final verdict
        print("\n" + "═" * 80)
        success = total_failed == 0 and total_errors == 0

        if success:
            print(f"🎉 SUCCESS! All {total_passed} tests passed in {overall_duration:.2f}s")
        else:
            failed_total = total_failed + total_errors
            print(f"💥 FAILURE! {failed_total} test(s) failed, {total_passed} passed")
            if not verbose:
                print("💡 Use --verbose for detailed error information")

        print("═" * 80)
        return success

    def _show_package_info(self):
        """Show essential package information in compact format"""
        try:
            info = _get_package_info()

            # One-line essential info
            version = info.get('version', 'dev')
            backend_count = len(info.get('available_backends', []))
            feature_count = len([f for f, available in info.get('features', {}).items() if available])

            print(f"📦 logging_suite v{version} • {backend_count} backends • {feature_count} features enabled")

            # Show any critical issues
            if not info.get('initialized', True):
                print("⚠️  Package not fully initialized")

            if HAS_SENSITIVE_KEY_CONFIG:
                try:
                    key_count = len(get_sensitive_keys())
                    print(f"🔐 {key_count} sensitive keys configured")
                except Exception:
                    pass

        except Exception as e:
            print(f"⚠️  Package info unavailable: {e}")

    def _generate_coverage_report(self):
        """Generate coverage report if coverage.py is available"""
        try:
            import coverage
            print("📊 COVERAGE ANALYSIS")
            print("─" * 40)
            print("🔧 Coverage integration in development")
            print("💡 To enable coverage tracking:")
            print("   1. pip install coverage")
            print("   2. coverage run -m logging_suite run-tests")
            print("   3. coverage report")
            print("   4. coverage html  # for HTML report")

        except ImportError:
            print("📊 COVERAGE UNAVAILABLE")
            print("─" * 40)
            print("❌ Coverage package not installed")
            print("💡 Install with: pip install coverage")


# Export the test runner for use by main module
__all__ = ['LoggingSuiteTestRunner']


def main():
    """Main entry point for running tests directly"""
    import argparse

    parser = argparse.ArgumentParser(description='logging_suite Integrated Test Suite')
    parser.add_argument('--quick', '-q', action='store_true', help='Run quick test suite only')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--test-class', help='Run specific test class')
    parser.add_argument('--benchmark', '-b', action='store_true', help='Include benchmarks')
    parser.add_argument('--coverage', '-c', action='store_true', help='Generate coverage report')
    parser.add_argument('--list-tests', action='store_true', help='List available test classes')

    args = parser.parse_args()

    runner = LoggingSuiteTestRunner()

    if args.list_tests:
        print("Available test classes:")
        for test_class in runner.get_available_test_classes():
            print(f"  • {test_class}")
        return

    # Run the test suite
    success = runner.run_tests(
        quick=args.quick,
        verbose=args.verbose,
        specific_test=args.test_class,
        benchmark=args.benchmark,
        coverage=args.coverage
    )

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()