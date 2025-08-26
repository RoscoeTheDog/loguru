# logging_suite/backends/base.py
"""
Abstract base class for logging backends
ENHANCED: Better validation, error handling, and introspection capabilities
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..unified_logger import UnifiedLogger


class LoggingBackend(ABC):
    """
    Enhanced abstract base class for logging backends
    Provides better validation, error handling, and introspection
    """

    def __init__(self):
        """Initialize the backend with validation"""
        self._backend_name = None
        self._backend_version = None
        self._initialization_errors = []
        self._is_validated = False

        # Perform initialization validation
        try:
            self._initialize()
            self._validate_backend()
            self._is_validated = True
        except Exception as e:
            self._initialization_errors.append(str(e))
            raise

    def _initialize(self):
        """
        Backend-specific initialization (override in subclasses)
        This is called during __init__ and can be used to set up
        backend-specific state or validate dependencies
        """
        pass

    def _validate_backend(self):
        """
        Validate that the backend is properly configured
        This checks that all required methods are implemented correctly
        """
        # Check that required abstract methods are implemented
        required_methods = ['create_logger', 'create_unified_logger',
                            'supports_context_binding', 'get_backend_name']

        for method_name in required_methods:
            if not hasattr(self, method_name):
                raise NotImplementedError(f"Backend must implement {method_name}")

            method = getattr(self, method_name)
            if not callable(method):
                raise TypeError(f"Backend {method_name} must be callable")

        # Try to get backend name
        try:
            name = self.get_backend_name()
            if not isinstance(name, str) or not name:
                raise ValueError("get_backend_name() must return a non-empty string")
            self._backend_name = name
        except Exception as e:
            raise ValueError(f"get_backend_name() failed: {e}")

        # Test basic functionality with a simple logger creation
        try:
            test_logger = self.create_logger('test.validation', {})
            if test_logger is None:
                raise ValueError("create_logger() returned None")
        except Exception as e:
            raise ValueError(f"create_logger() test failed: {e}")

    @abstractmethod
    def create_logger(self, name: str, config: Dict[str, Any]) -> Any:
        """
        Create and configure a raw logger instance

        Args:
            name: Logger name
            config: Configuration dictionary

        Returns:
            Raw logger instance (backend-specific type)
        """
        pass

    @abstractmethod
    def create_unified_logger(self, name: str, config: Dict[str, Any]) -> 'UnifiedLogger':
        """
        Create a unified logger wrapper

        Args:
            name: Logger name
            config: Configuration dictionary

        Returns:
            UnifiedLogger instance wrapping the raw logger
        """
        pass

    @abstractmethod
    def supports_context_binding(self) -> bool:
        """
        Check if this backend supports context binding

        Returns:
            True if backend supports binding context to logger instances
        """
        pass

    @abstractmethod
    def get_backend_name(self) -> str:
        """
        Get the name of this backend

        Returns:
            Backend name (e.g., 'structlog', 'loguru', 'standard')
        """
        pass

    def get_backend_version(self) -> str:
        """
        Get the version of the underlying logging library

        Returns:
            Version string or 'unknown'
        """
        if self._backend_version:
            return self._backend_version

        try:
            # Try to get version from the underlying library
            backend_name = self.get_backend_name()

            if backend_name == 'structlog':
                try:
                    import structlog
                    return getattr(structlog, '__version__', 'unknown')
                except ImportError:
                    return 'not_installed'

            elif backend_name == 'loguru':
                try:
                    import loguru
                    return getattr(loguru, '__version__', 'unknown')
                except ImportError:
                    return 'not_installed'

            elif backend_name == 'standard':
                import sys
                return f"python-{sys.version.split()[0]}"

            else:
                return 'unknown'

        except Exception:
            return 'unknown'

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Get comprehensive information about this backend

        Returns:
            Dictionary with backend information
        """
        info = {
            'name': self.get_backend_name(),
            'version': self.get_backend_version(),
            'supports_context_binding': self.supports_context_binding(),
            'class': self.__class__.__name__,
            'module': self.__class__.__module__,
            'validated': self._is_validated,
            'initialization_errors': self._initialization_errors.copy()
        }

        # Add backend-specific capabilities
        capabilities = self.get_capabilities()
        if capabilities:
            info['capabilities'] = capabilities

        # Add supported configuration options
        supported_config = self.get_supported_config_options()
        if supported_config:
            info['supported_config'] = supported_config

        return info

    def get_capabilities(self) -> Dict[str, bool]:
        """
        Get backend-specific capabilities
        Override in subclasses to provide detailed capability information

        Returns:
            Dictionary of capability names to boolean values
        """
        return {
            'context_binding': self.supports_context_binding(),
            'structured_logging': True,  # Assume all backends support this
            'file_logging': True,  # Assume all backends support this
            'console_logging': True,  # Assume all backends support this
        }

    def get_supported_config_options(self) -> List[str]:
        """
        Get list of supported configuration options
        Override in subclasses to provide specific configuration options

        Returns:
            List of supported configuration option names
        """
        return [
            'level',
            'console',
            'file_path',
            'format'
        ]

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration for this backend
        Override in subclasses for backend-specific validation

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validation results with warnings and errors
        """
        validation = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'backend': self.get_backend_name()
        }

        # Basic validation - check for invalid options
        supported_options = self.get_supported_config_options()

        for key in config.keys():
            if key not in supported_options:
                validation['warnings'].append(
                    f"Configuration option '{key}' is not officially supported by {self.get_backend_name()} backend"
                )

        # Validate specific options
        if 'level' in config:
            level = config['level']
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if isinstance(level, str):
                if level.upper() not in valid_levels:
                    validation['errors'].append(f"Invalid log level: {level}")
                    validation['valid'] = False
            else:
                validation['errors'].append("Log level must be a string")
                validation['valid'] = False

        if 'console' in config:
            if not isinstance(config['console'], bool):
                validation['warnings'].append("'console' should be a boolean value")

        return validation

    def test_backend_functionality(self) -> Dict[str, Any]:
        """
        Test backend functionality with various scenarios

        Returns:
            Dictionary with test results
        """
        test_results = {
            'overall_success': True,
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': []
        }

        def run_test(test_name: str, test_func):
            """Helper to run individual tests"""
            try:
                test_func()
                test_results['tests_passed'] += 1
                test_results['test_details'].append({
                    'name': test_name,
                    'status': 'PASS',
                    'error': None
                })
                return True
            except Exception as e:
                test_results['tests_failed'] += 1
                test_results['overall_success'] = False
                test_results['test_details'].append({
                    'name': test_name,
                    'status': 'FAIL',
                    'error': str(e)
                })
                return False

        # Test 1: Basic logger creation
        def test_basic_logger_creation():
            logger = self.create_logger('test.basic', {})
            if logger is None:
                raise ValueError("create_logger returned None")

        run_test("Basic Logger Creation", test_basic_logger_creation)

        # Test 2: Unified logger creation
        def test_unified_logger_creation():
            unified_logger = self.create_unified_logger('test.unified', {})
            if unified_logger is None:
                raise ValueError("create_unified_logger returned None")

        run_test("Unified Logger Creation", test_unified_logger_creation)

        # Test 3: Context binding capability
        def test_context_binding():
            if self.supports_context_binding():
                unified_logger = self.create_unified_logger('test.context', {})
                bound_logger = unified_logger.bind(test_key='test_value')
                if bound_logger is None:
                    raise ValueError("Context binding returned None")

        run_test("Context Binding", test_context_binding)

        # Test 4: Configuration validation
        def test_config_validation():
            test_config = {'level': 'DEBUG', 'console': True}
            validation = self.validate_config(test_config)
            if not isinstance(validation, dict) or 'valid' not in validation:
                raise ValueError("validate_config returned invalid format")

        run_test("Configuration Validation", test_config_validation)

        # Test 5: Backend info retrieval
        def test_backend_info():
            info = self.get_backend_info()
            required_keys = ['name', 'version', 'supports_context_binding']
            for key in required_keys:
                if key not in info:
                    raise ValueError(f"Backend info missing required key: {key}")

        run_test("Backend Info Retrieval", test_backend_info)

        return test_results

    def is_available(self) -> bool:
        """
        Check if this backend is available and functional

        Returns:
            True if backend is available
        """
        try:
            # Check if backend is validated
            if not self._is_validated:
                return False

            # Quick functionality test
            test_logger = self.create_logger('test.availability', {})
            return test_logger is not None

        except Exception:
            return False

    def get_initialization_errors(self) -> List[str]:
        """
        Get any errors that occurred during initialization

        Returns:
            List of error messages
        """
        return self._initialization_errors.copy()

    def has_initialization_errors(self) -> bool:
        """
        Check if there were any initialization errors

        Returns:
            True if there were initialization errors
        """
        return bool(self._initialization_errors)

    def create_test_logger_config(self) -> Dict[str, Any]:
        """
        Create a test configuration for this backend
        Override in subclasses for backend-specific test configs

        Returns:
            Test configuration dictionary
        """
        return {
            'level': 'DEBUG',
            'console': True,
            'format': 'json'
        }

    def supports_feature(self, feature_name: str) -> bool:
        """
        Check if backend supports a specific feature

        Args:
            feature_name: Name of the feature to check

        Returns:
            True if feature is supported
        """
        capabilities = self.get_capabilities()
        return capabilities.get(feature_name, False)

    def get_recommended_config(self, use_case: str = 'general') -> Dict[str, Any]:
        """
        Get recommended configuration for different use cases
        Override in subclasses for backend-specific recommendations

        Args:
            use_case: Use case ('development', 'production', 'testing', 'general')

        Returns:
            Recommended configuration dictionary
        """
        base_configs = {
            'development': {
                'level': 'DEBUG',
                'console': True,
                'format': 'console',
                'pretty_json': True
            },
            'production': {
                'level': 'WARNING',
                'console': False,
                'format': 'json',
                'pretty_json': False
            },
            'testing': {
                'level': 'ERROR',
                'console': False,
                'format': 'json'
            },
            'general': {
                'level': 'INFO',
                'console': True,
                'format': 'json'
            }
        }

        return base_configs.get(use_case, base_configs['general'])

    def __str__(self) -> str:
        """String representation of the backend"""
        return f"{self.__class__.__name__}(name='{self.get_backend_name()}', version='{self.get_backend_version()}')"

    def __repr__(self) -> str:
        """Detailed string representation of the backend"""
        return (f"{self.__class__.__name__}("
                f"name='{self.get_backend_name()}', "
                f"version='{self.get_backend_version()}', "
                f"validated={self._is_validated}, "
                f"errors={len(self._initialization_errors)})")


class BackendTestSuite:
    """
    Test suite for validating backend implementations
    Can be used to test custom backends or validate existing ones
    """

    def __init__(self, backend: LoggingBackend):
        """
        Initialize test suite for a backend

        Args:
            backend: Backend instance to test
        """
        self.backend = backend

    def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive tests on the backend

        Returns:
            Detailed test results
        """
        results = {
            'backend_name': self.backend.get_backend_name(),
            'overall_success': True,
            'test_suites': {},
            'summary': {
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0
            }
        }

        # Run backend's own functionality tests
        functionality_results = self.backend.test_backend_functionality()
        results['test_suites']['functionality'] = functionality_results
        results['summary']['total_tests'] += (functionality_results['tests_passed'] +
                                              functionality_results['tests_failed'])
        results['summary']['passed_tests'] += functionality_results['tests_passed']
        results['summary']['failed_tests'] += functionality_results['tests_failed']

        if not functionality_results['overall_success']:
            results['overall_success'] = False

        # Run validation tests
        validation_results = self._run_validation_tests()
        results['test_suites']['validation'] = validation_results
        results['summary']['total_tests'] += (validation_results['tests_passed'] +
                                              validation_results['tests_failed'])
        results['summary']['passed_tests'] += validation_results['tests_passed']
        results['summary']['failed_tests'] += validation_results['tests_failed']

        if not validation_results['overall_success']:
            results['overall_success'] = False

        return results

    def _run_validation_tests(self) -> Dict[str, Any]:
        """Run validation-specific tests"""
        validation_results = {
            'overall_success': True,
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': []
        }

        def run_test(test_name: str, test_func):
            try:
                test_func()
                validation_results['tests_passed'] += 1
                validation_results['test_details'].append({
                    'name': test_name,
                    'status': 'PASS',
                    'error': None
                })
                return True
            except Exception as e:
                validation_results['tests_failed'] += 1
                validation_results['overall_success'] = False
                validation_results['test_details'].append({
                    'name': test_name,
                    'status': 'FAIL',
                    'error': str(e)
                })
                return False

        # Test inheritance
        def test_inheritance():
            if not isinstance(self.backend, LoggingBackend):
                raise ValueError("Backend does not inherit from LoggingBackend")

        run_test("Proper Inheritance", test_inheritance)

        # Test required methods exist
        def test_required_methods():
            required_methods = ['create_logger', 'create_unified_logger',
                                'supports_context_binding', 'get_backend_name']
            for method in required_methods:
                if not hasattr(self.backend, method):
                    raise ValueError(f"Missing required method: {method}")
                if not callable(getattr(self.backend, method)):
                    raise ValueError(f"Method {method} is not callable")

        run_test("Required Methods Present", test_required_methods)

        return validation_results