#!/usr/bin/env python3
"""
Test just the uncaught exception part of the demo.
"""

import sys
import time
from loguru import logger
from loguru._template_formatters import create_hierarchical_format_function
from loguru._exception_hook import install_exception_hook

def setup_hierarchical_logging():
    """Setup hierarchical logging with exception hook."""
    logger.remove()
    
    format_func = create_hierarchical_format_function(
        format_string="{time:HH:mm:ss} | {level} | {name} | {message}",
        template="hierarchical"
    )
    
    logger.add(sys.stderr, format=format_func, colorize=True, level="DEBUG")
    
    # Install hierarchical exception hook for uncaught exceptions
    hook = install_exception_hook(logger, "hierarchical")
    return hook

def trigger_uncaught_exception():
    """Trigger an uncaught exception to test the hook."""
    print(">> TESTING UNCAUGHT EXCEPTION")
    print("=" * 50)
    
    logger.info("About to trigger uncaught exception for testing")
    
    # This will be an uncaught exception
    settlement_response = {
        "batch_id": "STL-001",
        "amount": 50000.0,
    }
    
    # Missing "settlement_reference" field - this should trigger hierarchical formatting!
    settlement_ref = settlement_response["settlement_reference"]  # KeyError!
    print(f"This should not print: {settlement_ref}")

def main():
    """Test uncaught exception handling without cleanup interference."""
    hook = setup_hierarchical_logging()
    
    # No try/except block - let the exception be truly uncaught
    trigger_uncaught_exception()
    
    # This should not be reached
    print("This should not print!")

if __name__ == "__main__":
    main()