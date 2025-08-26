#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Color-Forced Loguru Demo - Shows actual colors in console
=========================================================

This demo forces color output to work in any terminal environment.
"""

import sys
import os
import time
from loguru import logger
from loguru._templates import template_registry, TemplateConfig, StyleMode
from loguru._template_formatters import TemplateFormatter, create_template_formatter
from loguru._tracing import FunctionTracer
from loguru._exception_hook import install_exception_hook
from loguru._context_styling import SmartContextEngine

# Force color output by setting environment
os.environ['FORCE_COLOR'] = '1'
os.environ['TERM'] = 'xterm-256color'

def demo_colors_working():
    """Test if colors work at all."""
    print("\n" + "="*60)
    print(">> TESTING COLOR SUPPORT")
    print("="*60)
    
    # Test basic ANSI colors first
    print("Basic ANSI color test:")
    print("\033[31mThis should be RED\033[0m")
    print("\033[32mThis should be GREEN\033[0m") 
    print("\033[33mThis should be YELLOW\033[0m")
    print("\033[34mThis should be BLUE\033[0m")
    print("\033[35mThis should be MAGENTA\033[0m")
    print("\033[36mThis should be CYAN\033[0m")
    
    # Test loguru's colorizer directly
    from loguru._colorizer import Colorizer
    colorizer = Colorizer()
    
    print("\nLoguru colorizer test:")
    print(colorizer.colorize("<red>This should be RED</red>"))
    print(colorizer.colorize("<green>This should be GREEN</green>"))
    print(colorizer.colorize("<yellow>This should be YELLOW</yellow>"))
    print(colorizer.colorize("<blue>This should be BLUE</blue>"))


def demo_template_output_direct():
    """Show template output directly without loguru handler."""
    print("\n" + "="*60)
    print(">> DIRECT TEMPLATE OUTPUT TEST")
    print("="*60)
    
    formatter = create_template_formatter(
        format_string="{time:HH:mm:ss} | {level} | {message}",
        template="beautiful"
    )
    
    # Create fake log records to test formatting
    test_records = [
        {
            "time": "12:34:56",
            "level": {"name": "INFO"},
            "message": "User alice@company.com logged in from 192.168.1.100",
            "extra": {"user": "alice", "ip": "192.168.1.100"}
        },
        {
            "time": "12:34:57", 
            "level": {"name": "WARNING"},
            "message": "Payment of $1,234.56 is pending",
            "extra": {}
        },
        {
            "time": "12:34:58",
            "level": {"name": "ERROR"}, 
            "message": "Connection failed to https://api.service.com",
            "extra": {}
        }
    ]
    
    print("Direct template formatting results:")
    for record in test_records:
        formatted = formatter.format_map(record)
        print(f"Formatted: {formatted}")
        
        # Also print the raw template output
        from loguru._colorizer import Colorizer
        colorizer = Colorizer()
        colored = colorizer.colorize(formatted)
        print(f"Colorized: {colored}")
        print()


def demo_loguru_with_forced_colors():
    """Demo loguru with forced color settings."""
    print("\n" + "="*60)
    print(">> LOGURU WITH FORCED COLORS")
    print("="*60)
    
    # Remove all handlers
    logger.remove()
    
    # Add handler with explicit colorize=True and format
    logger.add(
        sys.stderr, 
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True,
        level="DEBUG"
    )
    
    print("Standard loguru with manual colors:")
    logger.debug("Debug message")
    logger.info("Info message with user@example.com")
    logger.success("Success message") 
    logger.warning("Warning message with IP 192.168.1.1")
    logger.error("Error message with $99.99")
    logger.critical("Critical message")


def demo_template_with_context():
    """Demo template formatting with context."""
    print("\n" + "="*60)
    print(">> TEMPLATE WITH CONTEXT RECOGNITION") 
    print("="*60)
    
    logger.remove()
    
    # Create a formatter that should apply template styling
    formatter = create_template_formatter(
        format_string="<cyan>{time:HH:mm:ss}</cyan> | <level>{level: <8}</level> | {message}",
        template="beautiful"
    )
    
    # Custom format function that ensures colorization
    def color_format(record):
        formatted = formatter.format_map(record)
        from loguru._colorizer import Colorizer
        colorizer = Colorizer()
        return colorizer.colorize(formatted)
    
    logger.add(sys.stderr, format=color_format, colorize=False)  # We handle color ourselves
    
    print("Template formatting with context recognition:")
    logger.info("User registration: alice@company.com from 10.0.1.50")
    logger.info("Payment processed: $1,234.56 via card ****1234")
    logger.info("API request: GET /api/users/123 -> 200 OK")
    logger.warning("High memory usage: 85% on server01.prod.com")
    logger.error("Database timeout: query took 5000ms on table users")


def demo_context_engine_standalone():
    """Test context engine separately."""
    print("\n" + "="*60)
    print(">> CONTEXT ENGINE STANDALONE TEST")
    print("="*60)
    
    engine = SmartContextEngine()
    
    messages = [
        "User alice@company.com logged in from 192.168.1.100",
        "Payment $1,234.56 processed successfully", 
        "GET /api/users/123 returned 404",
        "File: /var/log/app.log (size: 2.5MB)",
        "URL: https://api.example.com/v1/users failed"
    ]
    
    print("Context analysis results:")
    for msg in messages:
        matches = engine.analyze_message(msg)
        print(f"\nMessage: {msg}")
        print(f"Matches: {len(matches)}")
        for match in matches:
            print(f"  - Type: {match['context_type'].value}")
            print(f"    Text: '{msg[match['start']:match['end']]}'")
            print(f"    Position: {match['start']}-{match['end']}")


def demo_simple_tracing():
    """Simple tracing demo without complex context."""
    print("\n" + "="*60)
    print(">> SIMPLE FUNCTION TRACING")
    print("="*60)
    
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        colorize=True
    )
    
    tracer = FunctionTracer(logger, "beautiful")
    
    @tracer.trace
    def simple_function(name: str) -> str:
        time.sleep(0.01)
        return f"Hello, {name}!"
    
    print("Function tracing test:")
    result = simple_function("Alice")
    print(f"Function returned: {result}")


def main():
    """Run color-focused demo."""
    print("""
ENHANCED LOGURU COLOR DEMO
==========================

This demo focuses on testing color output and template formatting
to ensure everything displays correctly in your console.
""")
    
    try:
        demo_colors_working()
        demo_template_output_direct()
        demo_loguru_with_forced_colors()
        demo_template_with_context()
        demo_context_engine_standalone() 
        demo_simple_tracing()
        
        print("\n" + "="*60)
        print(">> COLOR DEMO COMPLETE")
        print("="*60)
        print("""
If you saw colors above, the template system is working!

Key indicators:
- ANSI color codes should show actual colors
- Loguru messages should have colored timestamps and levels
- Template formatting should apply context-based styling
- Function tracing should show entry/exit with timing

If colors aren't showing:
1. Your terminal may not support ANSI colors
2. Try running in a different terminal (Windows Terminal, Git Bash, etc.)  
3. Check if COLORTERM or TERM environment variables are set
""")
        
    except Exception as e:
        print(f"\n>> Error in demo: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.remove()
        print("\n>> Demo cleanup completed")


if __name__ == "__main__":
    main()