#!/usr/bin/env python3
"""
Test module-level exception to see if function name is <module>.
"""

import sys
from loguru._hierarchical_formatter import HierarchicalFormatter
from loguru._templates import template_registry

# Create module-level exception
try:
    data = {}
    missing = data["test"]  # This should create a <module> function name in traceback
except KeyError:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    
    # Get hierarchical formatter
    template = template_registry.get("hierarchical")
    formatter = HierarchicalFormatter(template)
    
    # Extract call stack
    call_stack = formatter._extract_call_stack(exc_traceback)
    print("Module-Level Exception Call Stack:")
    for i, (filename, lineno, function, code) in enumerate(call_stack):
        print(f"  Frame {i}:")
        print(f"    function: {repr(function)}")  # Should be '<module>'
        
        # Test file link creation
        file_link = f'File "{filename}", line {lineno}, in {function}'
        print(f"    file_link: {repr(file_link)}")
        
        if function == '<module>':
            print(f"    ✓ Found <module> function name!")
            print(f"    This will create markup: {file_link}")
    
    print("\nTesting what happens when we format this:")
    try:
        formatted = formatter.format_record(
            level="ERROR",
            message="Test message",
            logger_name="test",
            timestamp="00:00:00",
            extra={},
            exception_info=(exc_type, exc_value, exc_traceback)
        )
        print("SUCCESS: Formatting worked")
    except Exception as e:
        print(f"ERROR: {e}")
        print("This confirms the <module> issue!")