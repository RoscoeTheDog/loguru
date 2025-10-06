"""Debug test to see if wrapper is being used"""
import sys
from loguru import logger
from loguru._template_formatters import create_hierarchical_format_function

# Remove default
logger.remove()

# Create format function
fmt_func = create_hierarchical_format_function()

# Add with debug
def debug_wrapper(record):
    print(f"\n>>> FORMAT FUNCTION CALLED with record keys: {list(record.keys())[:5]}...")
    result = fmt_func(record)
    print(f">>> FORMAT FUNCTION RETURNED: {len(result)} chars")
    return result

logger.add(sys.stderr, format=debug_wrapper, colorize=True, backtrace=True)

try:
    raise ValueError("test")
except:
    logger.exception("Test exception")
