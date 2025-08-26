#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Loguru Enhanced Demo Script
===========================

This script demonstrates the powerful new features of the enhanced loguru library.
"""

import sys
import time
import tempfile
from pathlib import Path

# Import loguru and new template system features
from loguru import logger
from loguru._tracing import FunctionTracer
from loguru._exception_hook import install_exception_hook


def print_header(title):
    """Print a section header."""
    print(f"\n{'='*50}")
    print(f"  {title}")
    print(f"{'='*50}")


def demo_basic_features():
    """Demonstrate basic enhanced features."""
    print_header("Basic Enhanced Loguru Features")
    
    # Configure with beautiful template
    logger.remove()
    logger.configure_style("beautiful")
    
    print("\n1. Basic logging with beautiful template:")
    logger.info("Application started successfully")
    logger.warning("Memory usage is getting high: 85%")
    logger.error("Failed to connect to database")
    
    print("\n2. Smart context recognition:")
    logger.info("User john.doe@example.com logged in from 192.168.1.100")
    logger.info("API call: GET /api/users/123 returned status 200")
    logger.info("Payment processed: $1,234.56 for order #12345")
    
    print("\n3. Context binding with styling:")
    logger.bind(
        user="alice",
        session="sess_123",
        ip="10.0.1.50"
    ).info("Transaction completed")


def demo_templates():
    """Demonstrate different templates."""
    print_header("Template System Comparison")
    
    templates = ["beautiful", "minimal", "classic"]
    message = "Template demo with user alice@company.com and IP 192.168.1.1"
    
    for template in templates:
        print(f"\n{template.upper()} template:")
        logger.remove()
        logger.configure_style(template)
        logger.info(message)
        logger.warning("This is a warning")
        logger.error("This is an error")


def demo_dual_streams():
    """Demonstrate console vs file logging."""
    print_header("Dual Stream Logging")
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False)
    temp_file.close()
    
    try:
        logger.remove()
        logger.configure_streams(
            console=dict(template="beautiful", level="INFO"),
            file=dict(sink=temp_file.name, template="minimal", level="DEBUG")
        )
        
        print("\nLogging to both console (beautiful) and file (minimal):")
        logger.debug("Debug message - only in file")
        logger.info("Info message - in both console and file")
        logger.error("Error with context: user bob@test.com")
        
        print(f"\nFile contents ({Path(temp_file.name).name}):")
        print("-" * 30)
        with open(temp_file.name, 'r') as f:
            print(f.read())
            
    finally:
        Path(temp_file.name).unlink(missing_ok=True)


def simulate_login(username: str) -> bool:
    """Demo function for tracing."""
    time.sleep(0.05)  # Simulate processing
    return username != "invalid"


def demo_function_tracing():
    """Demonstrate function tracing."""
    print_header("Function Tracing")
    
    logger.remove()
    logger.configure_style("beautiful")
    
    # Create tracer
    tracer = FunctionTracer(logger)
    traced_login = tracer.trace(simulate_login)
    
    print("\nFunction tracing with entry/exit logging:")
    result1 = traced_login("alice")
    result2 = traced_login("invalid")
    
    print(f"Results: alice={result1}, invalid={result2}")


def demo_exception_handling():
    """Demonstrate exception handling."""
    print_header("Exception Hook Integration")
    
    logger.remove()
    logger.configure_style("beautiful")
    
    print("Installing global exception hook...")
    hook = install_exception_hook(logger, "beautiful")
    
    try:
        print("\nDemonstrating exception capture:")
        
        def risky_function(x, y):
            return x / y
        
        try:
            risky_function(10, 0)
        except ZeroDivisionError:
            logger.exception("Caught division by zero")
            
    finally:
        hook.uninstall()


def demo_structured_logging():
    """Demonstrate structured logging."""
    print_header("Structured Logging")
    
    temp_json = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False)
    temp_json.close()
    
    try:
        logger.remove()
        logger.configure_streams(
            console=dict(template="beautiful"),
            json=dict(sink=temp_json.name, serialize=True)
        )
        
        print("\nStructured logging with JSON output:")
        logger.bind(
            user_id="12345",
            action="login",
            ip="192.168.1.100"
        ).info("User authentication successful")
        
        logger.bind(
            transaction_id="tx_789",
            amount=99.99,
            currency="USD"
        ).info("Payment processed")
        
        print(f"\nJSON log contents:")
        print("-" * 30)
        with open(temp_json.name, 'r') as f:
            content = f.read().strip()
            if content:
                # Pretty print first few chars
                lines = content.split('\n')
                for line in lines[:2]:
                    if len(line) > 100:
                        print(line[:100] + "...")
                    else:
                        print(line)
            
    finally:
        Path(temp_json.name).unlink(missing_ok=True)


def main():
    """Run the demo."""
    print("""
Enhanced Loguru Demo
====================

Showcasing the new template system features:
* Beautiful template-based styling
* Smart context auto-styling
* Function tracing and performance monitoring  
* Global exception handling
* Structured logging enhancements

Let's see them in action!
""")
    
    try:
        demo_basic_features()
        demo_templates()
        demo_dual_streams()
        demo_function_tracing()
        demo_exception_handling()
        demo_structured_logging()
        
        print(f"\n{'='*50}")
        print("  Demo Complete!")
        print(f"{'='*50}")
        print("""
Features demonstrated:
* Template system with beautiful, minimal, classic styles
* Smart context recognition (emails, IPs, URLs, etc.)
* Dual-stream logging (console + file with different templates)
* Function tracing with automatic entry/exit logging
* Global exception hooks with beautiful formatting
* Structured JSON logging for log aggregation systems

The enhanced loguru is ready for production use!
        """)
        
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.remove()


if __name__ == "__main__":
    main()