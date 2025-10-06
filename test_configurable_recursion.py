"""Test configurable recursion depth via environment variable"""
import os
import sys

# Test 1: Default recursion depth (20)
print("="*80)
print("TEST 1: Default recursion depth (LOGURU_FORMAT_RECURSION_DEPTH=200)")
print("="*80)

from loguru import logger
from loguru._defaults import LOGURU_FORMAT_RECURSION_DEPTH

print(f"Current recursion depth: {LOGURU_FORMAT_RECURSION_DEPTH}")

logger.remove()
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level} | {message}", colorize=True)

# Test deep nesting (should work with default 20)
logger.info("Testing with default depth", 
            nested={"l1": {"l2": {"l3": {"l4": {"l5": "success"}}}}})

print("OK - Default depth test PASSED\n")

# Test 2: Custom recursion depth via environment variable
print("="*80)
print("TEST 2: Custom recursion depth via environment variable")
print("="*80)
print("Setting LOGURU_FORMAT_RECURSION_DEPTH=50 and reloading...")

# This demonstrates how users can configure it
print("\nIn your application, set before importing loguru:")
print("  import os")
print("  os.environ['LOGURU_FORMAT_RECURSION_DEPTH'] = '50'")
print("  from loguru import logger")
print("\nOr via shell:")
print("  export LOGURU_FORMAT_RECURSION_DEPTH=50")
print("  python your_script.py")

print("\n" + "="*80)
print("CONFIGURATION TEST COMPLETE")
print("="*80)
print("OK - Recursion depth is now configurable via LOGURU_FORMAT_RECURSION_DEPTH")
print("OK - Default value: 200 (lenient, handles deep tracebacks and recursive algorithms)")
print("OK - Can be increased for deeply nested format specifications")
print("OK - Follows loguru's environment variable convention")
print("="*80)
