#!/usr/bin/env python3
"""
Test script to verify the logging_suite architecture fixes work correctly
This tests the core imports and basic functionality
"""


def test_imports():
    """Test that all imports work without circular import errors"""
    print("Testing imports...")

    try:
        # Test core imports that previously had circular import issues
        from logging_suite.config import get_global_config, get_effective_config
        print("✅ Config imports successful")

        from logging_suite.factory import LoggerFactory
        print("✅ Factory imports successful")

        from logging_suite.unified_logger import UnifiedLogger
        print("✅ UnifiedLogger imports successful")

        from logging_suite.exceptions import get_unified_caller_context, get_exception_context
        print("✅ Exception handling imports successful")

        from logging_suite.orchestration import configure_global_logging, create_logger
        print("✅ Orchestration imports successful")

        # Test main package import
        import logging_suite
        print("✅ Main package imports successful")

        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_basic_functionality():
    """Test basic logging functionality"""
    print("\nTesting basic functionality...")

    try:
        import logging_suite

        # Test quick setup
        logging_suite.quick_setup(level='INFO', format='json', console=True)
        print("✅ Quick setup successful")

        # Test logger creation
        logger = logging_suite.get_logger('test.architecture')
        print("✅ Logger creation successful")

        # Test basic logging
        logger.info("Architecture test successful", test_type="basic_functionality")
        print("✅ Basic logging successful")

        # Test context binding
        bound_logger = logger.bind(component="test", test_id=123)
        bound_logger.info("Context binding test", status="success")
        print("✅ Context binding successful")

        # Test exception logging
        try:
            raise ValueError("Test exception for architecture validation")
        except Exception:
            logger.exception("Test exception handled successfully")
            print("✅ Exception logging successful")

        return True

    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backend_system():
    """Test backend system works"""
    print("\nTesting backend system...")

    try:
        from logging_suite.backends import get_available_backends, ensure_backends_initialized

        # Ensure backends are initialized
        ensure_backends_initialized()
        print("✅ Backend initialization successful")

        # Get available backends
        backends = get_available_backends()
        print(f"✅ Available backends: {backends}")

        # Test factory with dependency injection
        from logging_suite.factory import LoggerFactory
        from logging_suite.backends import registry

        logger = LoggerFactory.create_logger_with_registry(
            'test.backend',
            backend='standard',
            config={'level': 'DEBUG'},
            registry=registry
        )
        logger.info("Backend system test successful")
        print("✅ Backend dependency injection successful")

        return True

    except Exception as e:
        print(f"❌ Backend test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_exception_system():
    """Test enhanced exception system"""
    print("\nTesting exception system...")

    try:
        from logging_suite.exceptions import (
            get_unified_caller_context,
            get_exception_context,
            create_exception_handler_for_backend
        )

        # Test caller context
        context = get_unified_caller_context(skip_frames=1)
        print(f"✅ Caller context: {context.get('caller_function', 'unknown')}")

        # Test exception context
        try:
            raise RuntimeError("Test exception for context")
        except Exception:
            import sys
            exc_context = get_exception_context(sys.exc_info())
            print(f"✅ Exception context: {exc_context.get('exception_type', 'unknown')}")

        # Test backend-aware exception handler
        config = {'exception_diagnosis': True, 'exception_backtrace': True}
        handler = create_exception_handler_for_backend('standard', config)
        print("✅ Exception handler creation successful")

        return True

    except Exception as e:
        print(f"❌ Exception system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("🧪 Testing logging_suite Architecture Fixes")
    print("=" * 50)

    tests = [
        ("Core Imports", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Backend System", test_backend_system),
        ("Exception System", test_exception_system)
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} test...")
        try:
            if test_func():
                print(f"✅ {test_name} test PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} test FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name} test FAILED with exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All architecture tests PASSED! logging_suite is working correctly.")
        print("\n💡 You can now run the full test suite:")
        print("   python -m logging_suite run-tests --quick")
        return True
    else:
        print(f"⚠️ {failed} tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    import sys

    success = main()
    sys.exit(0 if success else 1)