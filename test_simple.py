#!/usr/bin/env python3
"""
Simple test to debug markup issues.
"""

import sys
from loguru import logger
from loguru._template_formatters import create_template_formatter

# Remove default handler
logger.remove()

# Add hierarchical template formatter
formatter = create_template_formatter(
    format_string="{time:HH:mm:ss} | {level} | {message}",
    template="hierarchical"
)

logger.add(sys.stderr, format=formatter.format_map, colorize=True, level="INFO")

print("Simple test for markup debugging")
print("=" * 40)

# Simple test without URLs
logger.info("Simple message without special content")

print()

# Test with email only
logger.info("User alice@company.com logged in", user_id="alice123")

print()

# Test with IP only
logger.info("Request from 192.168.1.100", status=200)

print("Simple tests complete!")