# logging_suite/backends/validator.py
"""
Comprehensive backend validation and testing system
Ensures all backends meet quality and functionality standards
"""

import time
import traceback
from typing import Dict, Any, List, Optional, Type
from .base import LoggingBackend, BackendTestSuite


class BackendValidator:
    """
    Comprehensive validator for logging_suite backends
    Provides thorough testing and validation capabilities
    """

    def __init__(self):
        self.validation_history = []

    def validate_backend_class(self, backend_class: Type[LoggingBackend],
                               backend_name: str) -> Dict[str, Any]:
        """
        Validate a backend class before registration

        Args:
            backend_class: Backend class to validate
            backend_name: Name to register backend as

        Returns:
            Validation results
        """
        validation = {
            'backend_name': backend_name,
            'backend_class': backend_class.__name__,
            'module': backend_class.__module__,
            'valid': True,
            'errors': [],
            'warnings': [],
            'test_results': {},
            'validation_time': time.time()
        }

        # Test 1: Check class inheritance
        try:
            if not issubclass(backend_class, LoggingBackend):
                validation['errors'].append("Backend class must inherit from LoggingBackend")
                validation['valid'] = False
        except Exception as e:
            validation['errors'].append(f"Error checking inheritance: {e}")
            validation['valid'] = False

        # Test 2: Try to instantiate the backend
        backend_instance = None
        try:
            backend_instance = backend_class()
            validation['test_results']['instantiation'] = 'SUCCESS'
        except Exception as e:
            validation['errors'].append(f"Failed to instantiate backend: {e}")
            validation['valid'] = False
            validation['test_results']['instantiation'] = f'FAILED: {e}'
            return validation  # Can't continue without instance

        # Test 3: Run comprehensive backend tests
        if backend_instance:
            try:
                test_suite = BackendTestSuite(backend_instance)
                comprehensive_results = test_suite.run_comprehensive_tests()
                validation['test_results']['comprehensive'] = comprehensive_results

                if not comprehensive_results['overall_success']:
                    validation['valid'] = False
                    validation['errors'].append("Backend failed comprehensive tests")

            except Exception as e:
                validation['errors'].append(f"Comprehensive testing failed: {e}")
                validation['valid'] = False
                validation['test_results']['comprehensive'] = f'FAILED: {e}'

        # Test 4: Validate backend name consistency
        if backend_instance:
            try:
                reported_name = backend_instance.get_backend_name()
                if reported_name != backend_name:
                    validation['warnings'].append(
                        f"Backend reports name '{reported_name}' but registering as '{backend_name}'"
                    )
            except Exception as e:
                validation['errors'].append(f"Failed to get backend name: {e}")
                validation['valid'] = False

        # Test 5: Configuration validation tests
        if backend_instance:
            try:
                test_configs = [
                    {'level': 'DEBUG', 'console': True},
                    {'level': 'INFO', 'format': 'json'},
                    {'level': 'ERROR', 'console': False, 'file_path': '/tmp/test.log'}
                ]

                config_test_results = []
                for i, config in enumerate(test_configs):
                    try:
                        config_validation = backend_instance.validate_config(config)
                        config_test_results.append({
                            'config': config,
                            'result': 'SUCCESS',
                            'validation': config_validation
                        })
                    except Exception as e:
                        config_test_results.append({
                            'config': config,
                            'result': f'FAILED: {e}',
                            'validation': None
                        })
                        validation['warnings'].append(f"Config validation {i + 1} failed: {e}")

                validation['test_results']['configuration'] = config_test_results

            except Exception as e:
                validation['errors'].append(f"Configuration testing failed: {e}")

        # Record validation
        self.validation_history.append(validation)

        return validation

    def validate_backend_instance(self, backend_instance: LoggingBackend) -> Dict[str, Any]:
        """
        Validate an already instantiated backend

        Args:
            backend_instance: Backend instance to validate

        Returns:
            Validation results
        """
        validation = {
            'backend_name': backend_instance.get_backend_name(),
            'backend_class': backend_instance.__class__.__name__,
            'valid': True,
            'errors': [],
            'warnings': [],
            'test_results': {},
            'validation_time': time.time()
        }

        # Test 1: Check availability
        try:
            if not backend_instance.is_available():
                validation['errors'].append("Backend reports as not available")
                validation['valid'] = False
            validation['test_results']['availability'] = 'SUCCESS'
        except Exception as e:
            validation['errors'].append(f"Availability check failed: {e}")
            validation['valid'] = False
            validation['test_results']['availability'] = f'FAILED: {e}'

        # Test 2: Check for initialization errors
        try:
            if backend_instance.has_initialization_errors():
                init_errors = backend_instance.get_initialization_errors()
                validation['warnings'].extend([f"Init error: {err}" for err in init_errors])
        except Exception as e:
            validation['warnings'].append(f"Could not check initialization errors: {e}")

        # Test 3: Test logger creation with various configs
        test_configs = [
            {},  # Empty config
            {'level': 'DEBUG'},  # Simple config
            {'level': 'INFO', 'console': True, 'format': 'json'},  # Complex config
        ]

        logger_creation_results = []
        for i, config in enumerate(test_configs):
            try:
                test_logger = backend_instance.create_logger(f'test.config.{i}', config)
                if test_logger is None:
                    logger_creation_results.append(f'Config {i}: FAILED - None returned')
                    validation['errors'].append(f"Logger creation with config {i} returned None")
                    validation['valid'] = False
                else:
                    logger_creation_results.append(f'Config {i}: SUCCESS')
            except Exception as e:
                logger_creation_results.append(f'Config {i}: FAILED - {e}')
                validation['errors'].append(f"Logger creation with config {i} failed: {e}")
                validation['valid'] = False

        validation['test_results']['logger_creation'] = logger_creation_results

        # Test 4: Test unified logger creation
        try:
            unified_logger = backend_instance.create_unified_logger('test.unified', {})
            if unified_logger is None:
                validation['errors'].append("Unified logger creation returned None")
                validation['valid'] = False
            else:
                validation['test_results']['unified_logger'] = 'SUCCESS'
        except Exception as e:
            validation['errors'].append(f"Unified logger creation failed: {e}")
            validation['valid'] = False
            validation['test_results']['unified_logger'] = f'FAILED: {e}'

        # Test 5: Test context binding if supported
        try:
            if backend_instance.supports_context_binding():
                unified_logger = backend_instance.create_unified_logger('test.context', {})
                bound_logger = unified_logger.bind(test_key='test_value')
                if bound_logger is None:
                    validation['errors'].append("Context binding returned None")
                    validation['valid'] = False
                else:
                    validation['test_results']['context_binding'] = 'SUCCESS'
            else:
                validation['test_results']['context_binding'] = 'NOT_SUPPORTED'
        except Exception as e:
            validation['errors'].append(f"Context binding test failed: {e}")
            validation['valid'] = False
            validation['test_results']['context_binding'] = f'FAILED: {e}'

        return validation

    def run_stress_test(self, backend_instance: LoggingBackend,
                        iterations: int = 100) -> Dict[str, Any]:
        """
        Run stress tests on a backend

        Args:
            backend_instance: Backend to stress test
            iterations: Number of test iterations

        Returns:
            Stress test results
        """
        stress_results = {
            'backend_name': backend_instance.get_backend_name(),
            'iterations': iterations,
            'start_time': time.time(),
            'end_time': None,
            'total_duration': None,
            'success_count': 0,
            'error_count': 0,
            'errors': [],
            'performance_metrics': {
                'avg_logger_creation_time': 0,
                'avg_unified_logger_creation_time': 0,
                'memory_stable': True
            }
        }

        logger_creation_times = []
        unified_creation_times = []

        for i in range(iterations):
            try:
                # Test logger creation performance
                start_time = time.time()
                logger = backend_instance.create_logger(f'stress.test.{i}', {'level': 'INFO'})
                logger_creation_time = time.time() - start_time
                logger_creation_times.append(logger_creation_time)

                if logger is None:
                    raise ValueError(f"Logger creation {i} returned None")

                # Test unified logger creation performance
                start_time = time.time()
                unified_logger = backend_instance.create_unified_logger(f'stress.unified.{i}', {})
                unified_creation_time = time.time() - start_time
                unified_creation_times.append(unified_creation_time)

                if unified_logger is None:
                    raise ValueError(f"Unified logger creation {i} returned None")

                # Test context binding if supported
                if backend_instance.supports_context_binding():
                    bound_logger = unified_logger.bind(iteration=i, test_key='stress_test')
                    if bound_logger is None:
                        raise ValueError(f"Context binding {i} returned None")

                stress_results['success_count'] += 1

            except Exception as e:
                stress_results['error_count'] += 1
                stress_results['errors'].append(f"Iteration {i}: {e}")

        stress_results['end_time'] = time.time()
        stress_results['total_duration'] = stress_results['end_time'] - stress_results['start_time']

        # Calculate performance metrics
        if logger_creation_times:
            stress_results['performance_metrics']['avg_logger_creation_time'] = (
                    sum(logger_creation_times) / len(logger_creation_times)
            )

        if unified_creation_times:
            stress_results['performance_metrics']['avg_unified_logger_creation_time'] = (
                    sum(unified_creation_times) / len(unified_creation_times)
            )

        return stress_results

    def validate_all_registered_backends(self, registry) -> Dict[str, Any]:
        """
        Validate all backends in a registry

        Args:
            registry: Backend registry to validate

        Returns:
            Comprehensive validation results
        """
        validation_results = {
            'validation_time': time.time(),
            'total_backends': len(registry.get_all_registered_backends()),
            'available_backends': len(registry.get_available_backends()),
            'validation_summary': {
                'all_valid': True,
                'total_errors': 0,
                'total_warnings': 0
            },
            'backend_results': {},
            'registry_health': {}
        }

        # Validate each registered backend
        for backend_name in registry.get_all_registered_backends():
            try:
                if registry.is_backend_available(backend_name):
                    backend_class = registry.get_backend(backend_name)
                    backend_instance = backend_class()
                    backend_validation = self.validate_backend_instance(backend_instance)
                else:
                    # Backend is registered but not available
                    backend_info = registry.get_backend_info(backend_name)
                    backend_validation = {
                        'backend_name': backend_name,
                        'valid': False,
                        'errors': [f"Backend not available: {backend_info.get('error', 'Unknown error')}"],
                        'warnings': [],
                        'test_results': {}
                    }

                validation_results['backend_results'][backend_name] = backend_validation

                if not backend_validation['valid']:
                    validation_results['validation_summary']['all_valid'] = False

                validation_results['validation_summary']['total_errors'] += len(backend_validation['errors'])
                validation_results['validation_summary']['total_warnings'] += len(backend_validation['warnings'])

            except Exception as e:
                validation_results['backend_results'][backend_name] = {
                    'backend_name': backend_name,
                    'valid': False,
                    'errors': [f"Validation exception: {e}"],
                    'warnings': [],
                    'test_results': {}
                }
                validation_results['validation_summary']['all_valid'] = False
                validation_results['validation_summary']['total_errors'] += 1

        # Evaluate registry health
        try:
            default_backend = registry.get_default_backend()
            validation_results['registry_health']['default_backend'] = default_backend
            validation_results['registry_health']['default_available'] = True
        except Exception as e:
            validation_results['registry_health']['default_backend'] = None
            validation_results['registry_health']['default_available'] = False
            validation_results['registry_health']['default_error'] = str(e)
            validation_results['validation_summary']['all_valid'] = False

        validation_results['registry_health']['registration_errors'] = registry.get_registration_errors()

        return validation_results

    def get_validation_history(self) -> List[Dict[str, Any]]:
        """Get history of all validations performed"""
        return self.validation_history.copy()

    def clear_validation_history(self):
        """Clear validation history"""
        self.validation_history.clear()

    def generate_validation_report(self, validation_results: Dict[str, Any]) -> str:
        """
        Generate a human-readable validation report

        Args:
            validation_results: Results from validate_all_registered_backends

        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("logging_suite Backend Validation Report")
        report.append("=" * 60)

        summary = validation_results['validation_summary']
        report.append(f"Overall Status: {'✅ PASS' if summary['all_valid'] else '❌ FAIL'}")
        report.append(f"Total Backends: {validation_results['total_backends']}")
        report.append(f"Available Backends: {validation_results['available_backends']}")
        report.append(f"Total Errors: {summary['total_errors']}")
        report.append(f"Total Warnings: {summary['total_warnings']}")

        # Registry health
        health = validation_results['registry_health']
        report.append(f"\nRegistry Health:")
        if health.get('default_available'):
            report.append(f"  ✅ Default Backend: {health['default_backend']}")
        else:
            report.append(f"  ❌ Default Backend: Not Available ({health.get('default_error', 'Unknown error')})")

        # Backend details
        report.append(f"\nBackend Details:")
        for backend_name, backend_result in validation_results['backend_results'].items():
            status = "✅" if backend_result['valid'] else "❌"
            report.append(f"  {status} {backend_name}")

            if backend_result['errors']:
                for error in backend_result['errors']:
                    report.append(f"    ❌ {error}")

            if backend_result['warnings']:
                for warning in backend_result['warnings']:
                    report.append(f"    ⚠️  {warning}")

        report.append("=" * 60)

        return "\n".join(report)