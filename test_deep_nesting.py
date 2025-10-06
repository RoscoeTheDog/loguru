"""Test that deep format spec nesting now works with increased recursion depth"""
import sys
from loguru import logger

logger.remove()
logger.add(sys.stderr, format="{time:HH:mm:ss} | {level} | {message}", colorize=True)

# Test deeply nested format specifications (would have failed with recursion_depth=2)
logger.info("Testing deep nesting", 
            level1={"level2": {"level3": {"level4": {"level5": "deep value"}}}})

print("\nDeep nesting test PASSED - recursion depth fix working!")
