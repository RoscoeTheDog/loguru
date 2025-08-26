#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Color Demo - Test actual color output
============================================

Tests if colors work in your terminal and shows template features.
"""

import sys
import os
import time
from loguru import logger
from loguru._templates import template_registry
from loguru._template_formatters import create_template_formatter
from loguru._context_styling import SmartContextEngine

# Force color support
os.environ['FORCE_COLOR'] = '1'


def test_basic_colors():
    """Test if terminal supports colors."""
    print("\n" + "="*50)
    print("BASIC COLOR TEST")
    print("="*50)
    
    print("If you see colors below, your terminal supports ANSI:")
    print(f"\033[91m● RED\033[0m")
    print(f"\033[92m● GREEN\033[0m") 
    print(f"\033[93m● YELLOW\033[0m")
    print(f"\033[94m● BLUE\033[0m")
    print(f"\033[95m● MAGENTA\033[0m")
    print(f"\033[96m● CYAN\033[0m")


def test_loguru_colors():
    """Test loguru's built-in colors.""" 
    print("\n" + "="*50)
    print("LOGURU COLOR TEST")
    print("="*50)
    
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>",
        colorize=True
    )
    
    print("Loguru with manual color tags:")
    logger.debug("Debug message")
    logger.info("Info message") 
    logger.success("Success message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")


def test_context_recognition():
    """Test context recognition without colors first."""
    print("\n" + "="*50)
    print("CONTEXT RECOGNITION TEST")
    print("="*50)
    
    engine = SmartContextEngine()
    
    messages = [
        "User alice@company.com logged in",
        "Payment $1,234.56 processed",
        "IP address: 192.168.1.100",
        "URL: https://api.example.com",
        "File: /var/log/app.log"
    ]
    
    for msg in messages:
        matches = engine.analyze_message(msg)
        types = [match['context_type'].value for match in matches]
        print(f"'{msg}' -> Found: {', '.join(types) if types else 'none'}")


def test_template_formatting():
    """Test template formatting."""
    print("\n" + "="*50)
    print("TEMPLATE FORMATTING TEST")
    print("="*50)
    
    # Test each template
    for template_name in ["beautiful", "minimal", "classic"]:
        print(f"\n{template_name.upper()} template:")
        
        logger.remove()
        
        # For beautiful template, show what the formatter would produce
        formatter = create_template_formatter(
            format_string="{time:HH:mm:ss} | {level} | {message}",
            template=template_name
        )
        
        # Test record
        test_record = {
            "time": "12:34:56",
            "level": {"name": "INFO"},
            "message": "User alice@example.com from 192.168.1.1",
            "extra": {}
        }
        
        formatted = formatter.format_map(test_record)
        print(f"Raw output: {repr(formatted)}")
        print(f"Display:    {formatted}")
        
        # Also test with loguru handler
        logger.add(sys.stderr, format=formatted, colorize=True)
        logger.info("Live test message")


def test_simple_template_demo():
    """Simple template demonstration."""
    print("\n" + "="*50) 
    print("LIVE TEMPLATE DEMO")
    print("="*50)
    
    # Test beautiful template specifically
    logger.remove()
    
    # Method 1: Use loguru's built-in color formatting
    logger.add(
        sys.stderr,
        format="<blue>{time:HH:mm:ss}</blue> | <level>{level: <8}</level> | {message}",
        colorize=True,
        level="DEBUG"
    )
    
    print("\nLoguru with colors enabled:")
    logger.info("Basic colored message")
    logger.bind(user="alice").info("Message with context")
    logger.warning("Warning message") 
    logger.error("Error message")
    
    # Method 2: Test our template formatter output
    print(f"\nOur template system output:")
    formatter = create_template_formatter(
        "{time:HH:mm:ss} | {level} | {message}",
        "beautiful"
    )
    
    test_record = {
        "time": "12:34:56",
        "level": {"name": "ERROR"},
        "message": "Template system working with alice@test.com",
        "extra": {}
    }
    
    result = formatter.format_map(test_record)
    print(f"Template result: {result}")


def main():
    """Run simple color tests."""
    print("""
LOGURU ENHANCED - COLOR TEST
============================

This tests if colors work in your terminal and 
demonstrates the template system features.
""")
    
    try:
        test_basic_colors()
        test_loguru_colors()
        test_context_recognition()
        test_template_formatting()
        test_simple_template_demo()
        
        print("\n" + "="*50)
        print("COLOR TEST COMPLETE")
        print("="*50)
        print("""
Results Summary:
- If you saw colored text above, colors are working!
- The template system is detecting context patterns
- Loguru's color formatting is functional
        
If no colors appeared:
- Try Windows Terminal instead of Command Prompt
- Try Git Bash or PowerShell
- Your terminal may not support ANSI colors
        """)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.remove()


if __name__ == "__main__":
    main()