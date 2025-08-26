#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loguru Enhanced Demo Script
===========================

This script demonstrates all the powerful features of the enhanced loguru library,
including the new template-based styling system, smart context recognition, 
function tracing, and global exception handling.

Run this script to see beautiful, informative logging in action!
"""

import sys
import time
import threading
import tempfile
from pathlib import Path

# Import loguru and new template system features
from loguru import logger
from loguru._templates import template_registry, TemplateConfig, StyleMode
from loguru._tracing import FunctionTracer, PerformanceTracer, create_development_tracer
from loguru._exception_hook import install_exception_hook, ExceptionContext
from loguru._context_styling import SmartContextEngine, AdaptiveContextEngine


def demo_header(title: str):
    """Print a beautiful demo section header."""
    print(f"\n{'='*60}")
    print(f">> {title}")
    print(f"{'='*60}")


def demo_basic_loguru():
    """Demonstrate basic loguru functionality."""
    demo_header("Basic Loguru Functionality")
    
    # Configure with beautiful template
    logger.remove()  # Remove default handler
    logger.configure_style("beautiful")
    
    logger.debug("Debug message - detailed information for developers")
    logger.info("Application started successfully")
    logger.success("User authentication completed")
    logger.warning("Memory usage is getting high: 85%")
    logger.error("Failed to connect to database")
    logger.critical("System is running out of disk space!")
    
    print("\n>> Notice the beautiful colors and styling!")


def demo_smart_context_recognition():
    """Demonstrate smart context auto-styling."""
    demo_header("Smart Context Recognition & Auto-Styling")
    
    logger.info("Processing user john.doe@example.com from IP 192.168.1.100")
    logger.info("API call: GET /api/users/12345 returned status 200")
    logger.info("Payment processed: $1,234.56 for order #ORD-2023-001")
    logger.info("File uploaded: /home/user/documents/report.pdf (2.5MB)")
    logger.info("Database query executed in 45ms")
    logger.info("OAuth token: abc123def456ghi789 (expires: 2024-12-31T23:59:59Z)")
    logger.error("Connection failed to https://api.external-service.com/v1/data")
    
    # Demonstrate context binding with smart styling
    logger.bind(
        user_id="user_12345",
        session_id="sess_abc123",
        ip="10.0.1.50",
        action="purchase"
    ).info("Transaction completed successfully")
    
    print("\n✨ Notice how emails, IPs, URLs, currency, file paths are automatically styled!")


def demo_template_system():
    """Demonstrate different template styles."""
    demo_header("Template System - Different Styles")
    
    templates = ["beautiful", "minimal", "classic"]
    message = "Template styling demonstration with user alice@company.com"
    
    for template in templates:
        print(f"\n📄 Template: {template}")
        print("-" * 40)
        
        logger.remove()
        logger.configure_style(template)
        logger.info(message)
        logger.warning("This is a warning message")
        logger.error("This is an error message")


def demo_dual_stream_logging():
    """Demonstrate console vs file logging with different templates."""
    demo_header("Dual Stream Logging - Console vs File")
    
    # Create temporary file for demo
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
    temp_file.close()
    
    try:
        logger.remove()
        
        # Configure different templates for console and file
        handler_ids = logger.configure_streams(
            console=dict(
                sink=sys.stderr,
                template="beautiful", 
                level="INFO",
                format="{time:HH:mm:ss} | {level} | {message}"
            ),
            file=dict(
                sink=temp_file.name,
                template="minimal",
                level="DEBUG", 
                format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
            )
        )
        
        logger.debug("Debug message - only in file")
        logger.info("Info message - in both console and file") 
        logger.warning("Warning message with context", extra={"component": "auth", "user": "alice"})
        logger.error("Error message with user bob@test.com and IP 172.16.0.1")
        
        # Show file contents
        print(f"\n📁 File log contents ({temp_file.name}):")
        print("-" * 40)
        with open(temp_file.name, 'r') as f:
            print(f.read())
            
    finally:
        # Cleanup
        Path(temp_file.name).unlink(missing_ok=True)
        for handler_id in handler_ids.values():
            try:
                logger.remove(handler_id)
            except:
                pass


# Demo functions for tracing
def simulate_user_login(username: str, password: str) -> bool:
    """Simulate user authentication process."""
    time.sleep(0.1)  # Simulate processing time
    
    if username == "admin" and password == "secret":
        return True
    elif username == "error":
        raise ValueError("Invalid credentials provided")
    else:
        return False


def simulate_database_query(table: str, filters: dict) -> list:
    """Simulate database query with variable performance."""
    query_time = 0.05 if table == "users" else 0.3  # Simulate different query times
    time.sleep(query_time)
    
    return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]


def demo_function_tracing():
    """Demonstrate advanced function tracing."""
    demo_header("Advanced Function Tracing & Performance Monitoring")
    
    logger.remove()
    logger.configure_style("beautiful")
    
    # Create development tracer with rules
    tracer = create_development_tracer(logger)
    
    # Add specific rule for simulation functions
    tracer.add_rule(
        pattern=r"simulate_.*",
        log_args=True,
        log_result=True,
        log_duration=True,
        level="INFO"
    )
    
    # Apply tracing to our demo functions
    traced_login = tracer.trace(simulate_user_login)
    traced_query = tracer.trace(simulate_database_query)
    
    print("🔍 Function tracing with entry/exit logging:")
    
    # Demonstrate successful calls
    result = traced_login("alice", "password123")
    data = traced_query("users", {"active": True})
    
    # Demonstrate error handling
    try:
        traced_login("error", "invalid")
    except ValueError as e:
        logger.info(f"Caught expected error: {e}")
    
    print("\n✨ Notice the automatic entry/exit logging with arguments and timing!")


def demo_performance_monitoring():
    """Demonstrate performance monitoring with thresholds."""
    demo_header("Performance Monitoring with Thresholds")
    
    # Create performance tracer
    perf_tracer = PerformanceTracer(logger, "beautiful")
    
    @perf_tracer.trace_performance(threshold_ms=100, track_stats=True)
    def fast_operation():
        """A fast operation that should not trigger alerts."""
        time.sleep(0.05)
        return "completed quickly"
    
    @perf_tracer.trace_performance(threshold_ms=100, track_stats=True)  
    def slow_operation():
        """A slow operation that should trigger performance alerts."""
        time.sleep(0.15)
        return "completed slowly"
    
    print("⚡ Performance monitoring with automatic alerts:")
    
    # Run operations
    fast_operation()
    slow_operation()
    
    # Show performance statistics
    fast_stats = perf_tracer.get_performance_stats("fast_operation")
    slow_stats = perf_tracer.get_performance_stats("slow_operation")
    
    if fast_stats:
        logger.info(f"Fast operation stats: avg={fast_stats['avg_ms']:.1f}ms")
    if slow_stats:
        logger.info(f"Slow operation stats: avg={slow_stats['avg_ms']:.1f}ms") 
    
    print("\n✨ Notice the automatic performance threshold alerts!")


def demo_exception_handling():
    """Demonstrate global exception handling."""
    demo_header("Global Exception Hook Integration")
    
    logger.remove()
    logger.configure_style("beautiful")
    
    print("🛡️ Installing global exception hook for beautiful error reporting...")
    
    # Install global exception hook
    hook = install_exception_hook(logger, "beautiful")
    
    try:
        print("\n1. Exception in main thread:")
        
        def risky_calculation(x, y, z):
            user_data = {"name": "Alice", "age": 30}
            calculation_result = x * y
            return calculation_result / z  # This will fail when z=0
        
        try:
            risky_calculation(10, 5, 0)
        except ZeroDivisionError:
            logger.exception("Caught division by zero error")
        
        print("\n2. Exception context manager:")
        
        with ExceptionContext(logger, "beautiful"):
            try:
                # This would be caught by the context exception hook
                invalid_operation = {"key": "value"}[10]  
            except (KeyError, TypeError):
                logger.exception("Caught key error in context")
        
        print("\n3. Thread exception handling:")
        
        def background_task():
            try:
                problematic_data = [1, 2, 3]
                return problematic_data[10]  # Index error
            except IndexError:
                logger.exception("Exception in background thread")
        
        thread = threading.Thread(target=background_task)
        thread.start()
        thread.join()
        
    finally:
        # Clean up exception hook
        hook.uninstall()
    
    print("\n✨ Notice the beautiful exception formatting with context information!")


def demo_structured_logging():
    """Demonstrate structured logging features."""
    demo_header("Structured Logging & JSON Output")
    
    # Create temporary JSON log file
    temp_json = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
    temp_json.close()
    
    try:
        logger.remove()
        
        # Configure structured logging
        logger.configure_streams(
            console=dict(
                sink=sys.stderr,
                template="beautiful",
                format="{time:HH:mm:ss} | {level} | {message} | {extra}"
            ),
            json=dict(
                sink=temp_json.name,
                serialize=True,
                level="INFO"
            )
        )
        
        # Log structured data
        logger.bind(
            user_id="12345",
            session="sess_abc123", 
            action="login",
            ip="192.168.1.100",
            user_agent="Mozilla/5.0"
        ).info("User login successful")
        
        logger.bind(
            transaction_id="tx_789",
            amount=99.99,
            currency="USD",
            merchant="Online Store"
        ).info("Payment processed")
        
        logger.bind(
            error_code="DB_001",
            table="users",
            query_time_ms=1250
        ).error("Database query timeout")
        
        # Show JSON output
        print(f"\n📊 Structured JSON log contents:")
        print("-" * 40)
        with open(temp_json.name, 'r') as f:
            print(f.read())
            
    finally:
        Path(temp_json.name).unlink(missing_ok=True)
    
    print("✨ Perfect for log aggregation systems like ELK, Splunk, or Datadog!")


def demo_adaptive_context_learning():
    """Demonstrate adaptive context learning."""
    demo_header("Adaptive Context Learning Engine")
    
    logger.remove()
    logger.configure_style("beautiful")
    
    # Create adaptive engine
    engine = AdaptiveContextEngine()
    
    print("🧠 Demonstrating adaptive learning from usage patterns:")
    
    # Sample application-specific messages
    messages = [
        "Processing webhook webhook_12345 for event user.created",
        "Kafka message consumed from topic user-events partition 3",
        "Redis cache miss for key user:profile:12345",
        "Elasticsearch query executed on index app-logs-2024.01",
        "Docker container app-server-001 restarted successfully"
    ]
    
    for i, message in enumerate(messages, 1):
        print(f"\n{i}. Analyzing: {message}")
        matches = engine.analyze_message(message)
        
        # Record usage to improve learning
        for match in matches:
            engine.record_usage(match['pattern_name'])
        
        # Show what was detected
        if matches:
            detected = [f"{match['context_type'].value}" for match in matches]
            print(f"   Detected: {', '.join(detected)}")
        else:
            print("   No patterns detected yet")
        
        # Log with smart styling
        logger.info(message)
    
    print("\n✨ The engine learns your application's specific patterns over time!")


def demo_custom_template():
    """Demonstrate creating and using custom templates."""
    demo_header("Custom Template Creation")
    
    # Create a custom template
    custom_template = TemplateConfig(
        name="demo_custom",
        description="Custom template for demo application",
        level_styles={
            "DEBUG": "dim white",
            "INFO": "bold cyan", 
            "SUCCESS": "bold green",
            "WARNING": "bold yellow",
            "ERROR": "bold red",
            "CRITICAL": "bold white on red"
        },
        context_styles={
            "user_id": "bold cyan",
            "transaction_id": "bold green", 
            "error_code": "bold red",
            "ip": "magenta",
            "email": "blue"
        },
        mode=StyleMode.HYBRID,
        preserve_markup=True,
        context_detection=True
    )
    
    # Register the custom template
    template_registry.register(custom_template)
    
    logger.remove()
    logger.configure_style("demo_custom")
    
    print("🎨 Using custom template with specialized styling:")
    
    logger.info("Custom template demonstration")
    logger.bind(
        user_id="USR_12345",
        transaction_id="TXN_ABC789"
    ).info("Transaction processed for alice@company.com")
    
    logger.bind(error_code="AUTH_001").error("Authentication failed for IP 10.0.0.1")
    logger.success("Custom template working perfectly!")
    
    print("\n✨ Custom templates let you match your application's specific needs!")


def main():
    """Run the complete loguru enhanced demo."""
    print("""
🎨 Welcome to the Enhanced Loguru Demo!
=====================================

This demonstration showcases the powerful new features added to loguru:
• Beautiful template-based styling system
• Smart context auto-styling and recognition  
• Advanced function tracing and performance monitoring
• Global exception hook integration
• Structured logging enhancements
• Adaptive learning capabilities

Let's see them all in action!
""")
    
    try:
        # Core functionality demos
        demo_basic_loguru()
        demo_smart_context_recognition()
        demo_template_system()
        demo_dual_stream_logging()
        
        # Advanced feature demos
        demo_function_tracing()
        demo_performance_monitoring()
        demo_exception_handling()
        demo_structured_logging()
        demo_adaptive_context_learning()
        demo_custom_template()
        
        # Final message
        print(f"\n{'='*60}")
        print("🎉 Demo Complete!")
        print("="*60)
        print("""
✅ You've seen all the major features of enhanced loguru:

📋 Template System:
   • Zero-config beautiful output
   • Multiple built-in templates (beautiful, minimal, classic)
   • Custom template creation
   • Runtime template switching

🧠 Smart Features:
   • Automatic context recognition (15+ types)
   • Adaptive learning engine
   • Pattern-based styling rules

🔍 Development Tools:
   • Function tracing with pattern matching
   • Performance monitoring with thresholds
   • Global exception hooks with context extraction

🏗️ Production Ready:
   • Dual-stream logging (console + file)
   • Structured JSON output
   • Performance optimizations
   • 100% backward compatibility

Ready to make your logging beautiful and informative!
        """)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup - remove all handlers
        logger.remove()
        print("\n🧹 Cleanup completed")


if __name__ == "__main__":
    main()