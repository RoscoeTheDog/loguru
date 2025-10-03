#!/usr/bin/env python3
"""
Debug the exception hook to see what's causing the markup issue.
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
    
    # Install exception hook with debug
    hook = install_exception_hook(logger, "hierarchical")
    return hook

def debug_exception_formatting():
    """Debug what's happening in exception formatting."""
    import traceback
    from loguru._hierarchical_formatter import HierarchicalFormatter
    from loguru._templates import template_registry
    from datetime import datetime
    
    # Create a simple exception
    try:
        data = {}
        missing = data["test"]
    except KeyError as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        # Get the template
        template = template_registry.get("hierarchical")
        hierarchical_formatter = HierarchicalFormatter(template)
        
        # Debug the inputs
        timestamp = datetime.now().strftime("%H:%M:%S") 
        calling_module = "debug_exception_hook"  # Hardcode to avoid markup issues
        message = f"Unhandled {exc_type.__name__}: {str(exc_value)}"
        
        print(f"DEBUG - timestamp: {repr(timestamp)}")
        print(f"DEBUG - calling_module: {repr(calling_module)}")
        print(f"DEBUG - message: {repr(message)}")
        print(f"DEBUG - level: ERROR")
        
        # Try formatting without exception_info first
        try:
            formatted_output = hierarchical_formatter.format_record(
                level="ERROR",
                message=message,
                logger_name=calling_module,
                timestamp=timestamp,
                extra={},
                exception_info=None  # Try without exception info first
            )
            print("SUCCESS: Formatting worked without exception_info")
            print(formatted_output[:200] + "..." if len(formatted_output) > 200 else formatted_output)
        except Exception as format_error:
            print(f"ERROR in formatting without exception_info: {format_error}")
            
        # Now try with exception_info
        try:
            formatted_output = hierarchical_formatter.format_record(
                level="ERROR",
                message=message,
                logger_name=calling_module,
                timestamp=timestamp,
                extra={},
                exception_info=(exc_type, exc_value, exc_traceback)
            )
            print("SUCCESS: Formatting worked with exception_info")
        except Exception as format_error:
            print(f"ERROR in formatting with exception_info: {format_error}")

def main():
    """Debug exception hook formatting."""
    print(">> DEBUGGING EXCEPTION HOOK FORMATTING")
    print("=" * 50)
    
    debug_exception_formatting()

if __name__ == "__main__":
    main()