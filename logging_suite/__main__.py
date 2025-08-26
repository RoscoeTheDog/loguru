# logging_suite/__main__.py
"""
Command-line interface for logging_suite

Usage:
    python -m logging_suite <command> [options]

Commands:
    info        - Show package information
    backends    - Show available backends
    trace       - Show tracing status
    analyze     - Run log analysis (if available)
    test        - Run basic compatibility tests
    run-tests   - Run integrated test suite (NEW)
    migrate     - Migrate from existing logging setup
    demo        - Run demonstration
    version     - Show version information
"""

import sys
import argparse
from typing import List, Dict, Any


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser"""
    parser = argparse.ArgumentParser(
        prog='logging_suite',
        description='logging_suite command-line interface',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python -m logging_suite info
    python -m logging_suite backends
    python -m logging_suite trace --enable
    python -m logging_suite analyze --log-dir ./logs --level ERROR
    python -m logging_suite test --backend structlog
    python -m logging_suite run-tests --quick --verbose
    python -m logging_suite migrate --from django
    python -m logging_suite demo --format json
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Info command
    info_parser = subparsers.add_parser('info', help='Show package information')
    info_parser.add_argument('--verbose', '-v', action='store_true',
                             help='Show verbose information')

    # Backends command
    backends_parser = subparsers.add_parser('backends', help='Show available backends')
    backends_parser.add_argument('--test', '-t', action='store_true',
                                 help='Test backend availability')

    # Trace command
    trace_parser = subparsers.add_parser('trace', help='Show or configure tracing')
    trace_parser.add_argument('--enable', action='store_true', help='Enable tracing')
    trace_parser.add_argument('--disable', action='store_true', help='Disable tracing')
    trace_parser.add_argument('--modules', nargs='+', help='Module patterns to trace')
    trace_parser.add_argument('--level', default='debug', help='Trace level')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Run log analysis')
    analyze_parser.add_argument('--log-dir', default='logs', help='Log directory')
    analyze_parser.add_argument('--pattern', default='*.log', help='File pattern')
    analyze_parser.add_argument('--level', help='Filter by log level')
    analyze_parser.add_argument('--last-hours', type=int, help='Last N hours')
    analyze_parser.add_argument('--output', choices=['errors', 'performance', 'summary'],
                                help='Analysis type')
    analyze_parser.add_argument('--export', help='Export results to file')

    # Test command (basic compatibility) - FIXED: No --quick argument here
    test_parser = subparsers.add_parser('test', help='Run basic compatibility tests')
    test_parser.add_argument('--backend', help='Test specific backend')
    test_parser.add_argument('--config', help='Test with configuration file')
    test_parser.add_argument('--verbose', '-v', action='store_true')

    # NEW: Run-tests command (integrated test suite)
    run_tests_parser = subparsers.add_parser('run-tests', help='Run integrated test suite')
    run_tests_parser.add_argument('--quick', '-q', action='store_true',
                                  help='Run only essential tests for quick validation')
    run_tests_parser.add_argument('--verbose', '-v', action='store_true',
                                  help='Show verbose test output')
    run_tests_parser.add_argument('--test-class', '--class', dest='test_class',
                                  help='Run only specific test class')
    run_tests_parser.add_argument('--benchmark', '-b', action='store_true',
                                  help='Include performance benchmarks')
    run_tests_parser.add_argument('--coverage', '-c', action='store_true',
                                  help='Generate coverage report (if available)')
    run_tests_parser.add_argument('--list-tests', action='store_true',
                                  help='List available test classes')

    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate from existing setup')
    migrate_parser.add_argument('--from', dest='from_type', required=True,
                                choices=['django', 'structlog', 'loguru', 'standard'],
                                help='Source logging system')
    migrate_parser.add_argument('--settings', help='Django settings module')
    migrate_parser.add_argument('--config', help='Configuration file')
    migrate_parser.add_argument('--output', help='Output migration code to file')
    migrate_parser.add_argument('--dry-run', action='store_true', help='Show migration without applying')

    # Demo command
    demo_parser = subparsers.add_parser('demo', help='Run demonstration')
    demo_parser.add_argument('--format', choices=['json', 'console'], default='console',
                             help='Output format')
    demo_parser.add_argument('--backend', help='Specific backend to demo')
    demo_parser.add_argument('--tracing', action='store_true', help='Enable tracing in demo')
    demo_parser.add_argument('--duration', type=int, default=30, help='Demo duration in seconds')

    # Version command
    version_parser = subparsers.add_parser('version', help='Show version information')

    return parser


def cmd_info(args) -> None:
    """Show package information"""
    from . import get_package_info, __version__, __author__, __license__

    print(f"logging_suite v{__version__}")
    print(f"Author: {__author__}")
    print(f"License: {__license__}")
    print()

    if args.verbose:
        info = get_package_info()
        print("Package Information:")
        print(f"  Location: {info['package_location']}")
        print(f"  Available backends: {', '.join(info['available_backends'])}")
        print()

        print("Features:")
        for feature, available in info['features'].items():
            status = "✓" if available else "✗"
            print(f"  {status} {feature}")
        print()

        if info.get('tracing_status'):
            print("Tracing Status:")
            for key, value in info['tracing_status'].items():
                print(f"  {key}: {value}")


def cmd_backends(args) -> None:
    """Show available backends"""
    from .factory import LoggerFactory

    print("Available Logging Backends:")

    backend_status = LoggerFactory.get_backend_status()
    for backend, available in backend_status.items():
        status = "✓" if available else "✗"
        print(f"  {status} {backend}")

        if args.test and available:
            # Test the backend
            try:
                logger = LoggerFactory.create_logger(f'test_{backend}', backend=backend)
                logger.info("Backend test successful")
                print(f"    Test: ✓ Working")
            except Exception as e:
                print(f"    Test: ✗ Failed - {e}")

    print()
    default_backend = None
    try:
        from .backends import registry
        default_backend = registry.get_default_backend()
        print(f"Default backend: {default_backend}")
    except Exception:
        print("Default backend: unknown")


def cmd_trace(args) -> None:
    """Show or configure tracing"""
    from .tracing import get_tracing_status, TraceManager

    if args.enable:
        if args.modules:
            TraceManager.enable_tracing(args.modules, level=args.level)
            print(f"✓ Enabled tracing for modules: {', '.join(args.modules)}")
        else:
            from .tracing import enable_development_tracing
            enable_development_tracing()
            print("✓ Enabled development tracing")

    elif args.disable:
        from .tracing import disable_all_tracing
        disable_all_tracing()
        print("✓ Disabled all tracing")

    # Show current status
    status = get_tracing_status()
    print("\nTracing Status:")
    for key, value in status.items():
        print(f"  {key}: {value}")


def cmd_analyze(args) -> None:
    """Run log analysis"""
    try:
        from .analysis import LogAnalyzer
    except ImportError:
        print("✗ Log analysis not available - install with analysis dependencies")
        return

    print(f"Analyzing logs in: {args.log_dir}")

    analyzer = LogAnalyzer(args.log_dir)
    count = analyzer.load_logs(pattern=args.pattern)

    if count == 0:
        print("No log entries found!")
        return

    # Apply filters
    if args.level:
        analyzer = analyzer.filter_by_level(args.level)
        print(f"Filtered by level: {args.level}")

    if args.last_hours:
        analyzer = analyzer.filter_by_time_range(last_hours=args.last_hours)
        print(f"Filtered to last {args.last_hours} hours")

    # Show analysis
    if args.output == 'errors':
        analysis = analyzer.get_error_analysis()
        print("\n=== ERROR ANALYSIS ===")
        print(f"Total errors: {analysis.get('total_errors', 0)}")
        if analysis.get('top_error_types'):
            print("\nTop error types:")
            for error_type, count in analysis['top_error_types'][:5]:
                print(f"  {error_type}: {count}")

    elif args.output == 'performance':
        analysis = analyzer.get_performance_analysis()
        print("\n=== PERFORMANCE ANALYSIS ===")
        print(f"Timed operations: {analysis.get('total_timed_operations', 0)}")
        if analysis.get('slowest_operations'):
            print("\nSlowest operations:")
            for op in analysis['slowest_operations'][:5]:
                print(f"  {op['function']}: {op['execution_time']:.3f}s")

    elif args.output == 'summary':
        analysis = analyzer.get_activity_summary()
        print("\n=== ACTIVITY SUMMARY ===")
        print(f"Total entries: {analysis.get('total_entries', 0)}")
        if analysis.get('levels'):
            print("\nLog levels:")
            for level, count in analysis['levels'].items():
                print(f"  {level}: {count}")

    else:
        # Show recent entries
        print(f"\nShowing recent entries from {count} total:")
        analyzer.print_entries(limit=20, format_style='compact')

    # Export if requested
    if args.export:
        analyzer.export_to_file(args.export)
        print(f"\n✓ Results exported to: {args.export}")


def cmd_test(args) -> None:
    """Run basic compatibility tests (FIXED: No --quick argument accepted)"""
    from .compatibility import test_compatibility
    from .factory import LoggerFactory

    print("Running logging_suite basic compatibility tests...")

    if args.backend:
        # Test specific backend
        print(f"\nTesting {args.backend} backend:")
        try:
            logger = LoggerFactory.create_logger('test', backend=args.backend)
            logger.info("Test message", test_key="test_value")
            logger.warning("Test warning")
            logger.error("Test error")
            print(f"✓ {args.backend} backend working")
        except Exception as e:
            print(f"✗ {args.backend} backend failed: {e}")
    else:
        # Test all backends
        backend_status = LoggerFactory.get_backend_status()
        for backend, available in backend_status.items():
            if available:
                try:
                    logger = LoggerFactory.create_logger(f'test_{backend}', backend=backend)
                    logger.info("Test message")
                    print(f"✓ {backend} backend working")
                except Exception as e:
                    print(f"✗ {backend} backend failed: {e}")

    # Test general compatibility
    print("\nTesting general compatibility:")
    results = test_compatibility()

    for detail in results['details']:
        print(f"  {detail}")

    print(f"\nTest summary: {results['summary']}")
    if results['success']:
        print("✓ All compatibility tests passed")
        print("\n💡 For comprehensive testing, use: python -m logging_suite run-tests")
    else:
        print("✗ Some compatibility tests failed")


def cmd_run_tests(args) -> bool:
    """Run integrated test suite (NEW)"""
    try:
        # FIXED: Import the test runner properly, avoiding circular imports
        from .tests_integrated import LoggingSuiteTestRunner
    except ImportError as e:
        print("✗ Integrated test suite not available")
        print(f"   Import error: {e}")
        print("   This may be due to missing test dependencies or circular imports")
        print("   Falling back to basic compatibility tests...")

        # Create a mock args object for the fallback
        class MockArgs:
            def __init__(self):
                self.backend = None
                self.config = None
                self.verbose = getattr(args, 'verbose', False)

        mock_args = MockArgs()
        cmd_test(mock_args)
        return False

    if args.list_tests:
        runner = LoggingSuiteTestRunner()
        test_classes = runner.get_available_test_classes()
        print("Available test classes:")
        for test_class in test_classes:
            print(f"  • {test_class}")
        return True

    print("Running logging_suite integrated test suite...")

    runner = LoggingSuiteTestRunner()

    try:
        success = runner.run_tests(
            quick=args.quick,
            verbose=args.verbose,
            specific_test=args.test_class,
            benchmark=args.benchmark,
            coverage=args.coverage
        )

        return success

    except Exception as e:
        print(f"✗ Test execution failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return False


def cmd_migrate(args) -> None:
    """Migrate from existing logging setup"""
    print(f"Migrating from {args.from_type} logging setup...")

    if args.from_type == 'django':
        from .compatibility import migrate_from_django_logging

        settings_module = args.settings or 'settings'
        result = migrate_from_django_logging(settings_module)

        if 'error' in result:
            print(f"✗ Migration failed: {result['error']}")
            if 'recommendations' in result:
                print("\nRecommendations:")
                for rec in result['recommendations']:
                    print(f"  • {rec}")
            return

        print(f"✓ {result['summary']}")

        if args.dry_run:
            print("\n=== MIGRATION CODE (DRY RUN) ===")
            print(result['migration_code'])
        elif args.output:
            with open(args.output, 'w') as f:
                f.write(result['migration_code'])
            print(f"✓ Migration code written to: {args.output}")
        else:
            print("\n=== MIGRATION CODE ===")
            print(result['migration_code'])

        print("\nNext steps:")
        for step in result.get('next_steps', []):
            print(f"  {step}")

    else:
        print(f"Migration from {args.from_type} not yet implemented")
        print("Available migrations: django")


def cmd_demo(args) -> None:
    """Run demonstration"""
    import time
    import threading

    # FIXED: Import from submodules to avoid circular imports
    from .config import configure_global_logging
    from .factory import LoggerFactory
    from .tracing import enable_development_tracing
    from .decorators import catch_and_log, log_execution_time

    print(f"Running logging_suite demonstration...")
    print(f"Format: {args.format}, Duration: {args.duration}s")

    # Configure logging
    configure_global_logging(
        level='DEBUG',
        format=args.format,
        console=True,
        enable_tracing=args.tracing
    )

    if args.tracing:
        enable_development_tracing()
        print("✓ Tracing enabled")

    # Create demo logger
    logger = LoggerFactory.create_logger('demo')

    print("\n=== DEMONSTRATION OUTPUT ===")

    # Basic logging
    logger.info("Demo started", demo_id="demo_001", format=args.format)
    logger.debug("Debug message with context", step=1, action="demo")
    logger.warning("Warning message", level="warning", component="demo")

    # Structured logging with context
    user_logger = logger.bind(user_id=123, session="demo_session")
    user_logger.info("User action logged", action="login", ip="127.0.0.1")

    # Demonstrate decorators
    @catch_and_log(logger=logger)
    @log_execution_time(logger=logger)
    def demo_function(duration: float):
        """Demo function with decorators"""
        time.sleep(duration)
        logger.info("Function completed", duration=duration)
        return f"Result after {duration}s"

    # Run demo function
    result = demo_function(0.1)
    logger.info("Got result", result=result)

    # Demonstrate error handling
    @catch_and_log(logger=logger, reraise=False, default_return="error_handled")
    def error_function():
        """Function that raises an error"""
        raise ValueError("Demo error for testing")

    error_result = error_function()
    logger.info("Error handled gracefully", result=error_result)

    # Performance demo
    try:
        from .context_managers import log_performance

        with log_performance(logger, "performance_test", threshold_seconds=0.05):
            time.sleep(0.1)  # Simulate work
    except ImportError:
        logger.info("Context managers not available, skipping performance demo")

    # Concurrent logging demo
    def worker_thread(worker_id: int):
        worker_logger = logger.bind(worker_id=worker_id, thread="worker")
        for i in range(3):
            worker_logger.info(f"Worker {worker_id} step {i + 1}", step=i + 1)
            time.sleep(0.1)

    # Start worker threads
    threads = []
    for i in range(3):
        t = threading.Thread(target=worker_thread, args=(i,))
        threads.append(t)
        t.start()

    # Wait for threads
    for t in threads:
        t.join()

    logger.info("Demo completed", duration=args.duration, threads_created=3)

    print("\n=== DEMONSTRATION COMPLETE ===")
    print("Key features demonstrated:")
    print("  ✓ Basic structured logging")
    print("  ✓ Context binding")
    print("  ✓ Decorator integration")
    print("  ✓ Error handling")
    print("  ✓ Performance monitoring")
    print("  ✓ Concurrent logging")
    if args.tracing:
        print("  ✓ Function tracing")


def cmd_version(args) -> None:
    """Show version information"""
    from . import __version__, __author__, __license__

    print(f"logging_suite {__version__}")
    print(f"Copyright (c) 2024 {__author__}")
    print(f"License: {__license__}")

    # Show Python version
    print(f"Python: {sys.version.split()[0]}")

    # Show backend versions if available
    try:
        import structlog
        print(f"structlog: {structlog.__version__}")
    except ImportError:
        pass

    try:
        import loguru
        print(f"loguru: {loguru.__version__}")
    except ImportError:
        pass


def main():
    """Main CLI entry point"""
    parser = create_parser()

    if len(sys.argv) == 1:
        # No arguments provided, show help
        print("logging_suite - Unified Logging Framework")
        print()
        parser.print_help()
        return

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    try:
        if args.command == 'info':
            cmd_info(args)
        elif args.command == 'backends':
            cmd_backends(args)
        elif args.command == 'trace':
            cmd_trace(args)
        elif args.command == 'analyze':
            cmd_analyze(args)
        elif args.command == 'test':
            cmd_test(args)
        elif args.command == 'run-tests':  # NEW: Integrated test suite
            success = cmd_run_tests(args)
            sys.exit(0 if success else 1)
        elif args.command == 'migrate':
            cmd_migrate(args)
        elif args.command == 'demo':
            cmd_demo(args)
        elif args.command == 'version':
            cmd_version(args)
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()