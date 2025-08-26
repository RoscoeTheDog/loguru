#!/usr/bin/env python3
"""
Debug the level markup issue.
"""

from loguru._hierarchical_formatter import HierarchicalFormatter
from loguru._templates import template_registry
from loguru._colorizer import Colorizer

# Get hierarchical template
template = template_registry.get("hierarchical")
formatter = HierarchicalFormatter(template)

# Test level markup
print("Testing level markup processing...")
print()

# Test the level styling directly
level_display = "INFO" 
if "INFO" in template.level_styles:
    style = template.level_styles["INFO"]
    level_display = f"<{style}>{level_display}</{style}>"
    print(f"Raw level markup: {repr(level_display)}")
    
    # Test colorization
    try:
        colorized = Colorizer.ansify(level_display)
        print(f"Colorized: {repr(colorized)}")
        print(f"Display: {colorized}")
    except Exception as e:
        print(f"Colorization error: {e}")

print()

# Test full formatting
result = formatter.format_record(
    level="INFO",
    message="Test message",
    logger_name="test",
    timestamp="12:34:56",
    extra={}
)

print("Full result first line:")
lines = result.split('\n')
print(repr(lines[0]))