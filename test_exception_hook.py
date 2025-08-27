#!/usr/bin/env python3
"""
Test the exception hook to see if it's working correctly.
"""

import sys
from loguru import logger
from loguru._template_formatters import create_hierarchical_format_function
from loguru._exception_hook import install_exception_hook

def setup_logging():
    """Setup hierarchical logging."""
    logger.remove()
    
    format_func = create_hierarchical_format_function(
        format_string="{time:HH:mm:ss} | {level} | {name} | {message}",
        template="hierarchical"
    )
    
    logger.add(sys.stderr, format=format_func, colorize=True)
    
    # Install exception hook
    hook = install_exception_hook(logger, "hierarchical")
    return hook

def main():
    """Test uncaught exception handling."""
    print(">> TESTING EXCEPTION HOOK")
    print("=" * 50)
    
    hook = setup_logging()
    
    logger.info("About to trigger uncaught exception")
    
    # This should be caught by the exception hook
    data = {"key1": "value1"}
    missing_value = data["missing_key"]  # KeyError - should be caught!
    print(f"This should not print: {missing_value}")

if __name__ == "__main__":
    main()