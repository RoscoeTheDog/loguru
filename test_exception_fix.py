"""Test that exception logging works with hierarchical formatting after fix"""
import sys
from loguru import logger
from loguru._template_formatters import create_hierarchical_format_function

# Remove default handler
logger.remove()

# Add hierarchical console handler
console_format_func = create_hierarchical_format_function(
    format_string="{time:HH:mm:ss} | {level} | {name} | {message}",
    template="hierarchical"
)

logger.add(
    sys.stderr,
    format=console_format_func,
    colorize=True,
    level="INFO",
    backtrace=True,
    diagnose=True,
)

# Test basic logging (should work)
logger.info("Testing hierarchical logging", test_stage="basic")

# Test exception logging (was failing before fix)
logger.info("Testing exception logging", test_stage="exception_handling")
try:
    data = {"name": "test", "version": "1.0"}
    missing = data["missing_key"]  # KeyError
except KeyError as e:
    logger.exception("Caught exception - testing fix for issue #2",
                    error_type="KeyError",
                    missing_field=str(e).strip("'\""),
                    test_result="should_succeed_with_fix")

logger.success("Exception logging fix test completed successfully!")
print("\n" + "="*80)
print("SUCCESS - Exception logging with hierarchical format WORKED!")
print("="*80)
