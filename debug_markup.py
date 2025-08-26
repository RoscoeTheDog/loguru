#!/usr/bin/env python3
"""
Debug the markup generation to see what's happening.
"""

from loguru._hierarchical_formatter import HierarchicalFormatter
from loguru._templates import template_registry

# Get hierarchical template
template = template_registry.get("hierarchical")
formatter = HierarchicalFormatter(template)

# Test message with email
message = "User alice@company.com logged in"
context = {"user_id": "alice123"}

# Apply context styling only
styled_message = formatter._apply_context_styling(message, context)
print("After context styling:")
print(repr(styled_message))
print()

# Full format test
result = formatter.format_record(
    level="INFO",
    message=message,
    logger_name="test_module",
    timestamp="12:34:56",
    extra=context
)

print("Full formatted result:")
print(repr(result))
print()
print("Actual output:")
print(result)