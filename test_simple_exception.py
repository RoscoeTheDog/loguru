"""Test exception logging with simple format"""
import sys
from loguru import logger

# Remove default handler
logger.remove()

# Add simple console handler (non-hierarchical)
logger.add(
    sys.stderr,
    format="{time:HH:mm:ss} | {level} | {message}",
    colorize=True,
    level="INFO",
    backtrace=True,
    diagnose=True,
)

# Test exception logging
try:
    data = {"name": "test"}
    missing = data["missing_key"]
except KeyError as e:
    logger.exception("Exception test with simple format", error=str(e))

print("Simple format exception test completed")
