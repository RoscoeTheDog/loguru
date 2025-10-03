#!/usr/bin/env python3
"""
Simple test of uncaught exception with hierarchical formatting.
"""

import sys
from loguru import logger
from loguru._template_formatters import create_hierarchical_format_function
from loguru._exception_hook import install_exception_hook

def setup_logging():
    """Setup hierarchical logging with exception hook."""
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
    """Test uncaught exception - no try/except to let hook handle it."""
    print(">> TESTING UNCAUGHT EXCEPTION HANDLING")
    print("=" * 50)
    
    hook = setup_logging()
    
    logger.info("Processing critical financial settlement",
               settlement_id="STL-001",
               amount_usd=50000.00,
               bank="example_bank")
    
    logger.info("Validating settlement parameters",
               validation_checks=["balance", "limits", "compliance"],
               all_checks_passed=True)
    
    # This will be an uncaught exception - NO try/except
    settlement_data = {
        "id": "STL-001",
        "amount": 50000.00,
        "bank": "example_bank"
        # Missing "reference" field
    }
    
    # This will trigger the exception hook
    reference = settlement_data["reference"]  # KeyError!
    logger.success(f"Settlement processed with reference: {reference}")

if __name__ == "__main__":
    main()