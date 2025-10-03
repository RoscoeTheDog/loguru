#!/usr/bin/env python3
"""
Debug the call stack to see if it contains <module> function names.
"""

import sys
from loguru._hierarchical_formatter import HierarchicalFormatter
from loguru._templates import template_registry

def test_call_stack():
    """Create an exception and examine the call stack."""
    
    try:
        data = {}
        missing = data["test"]
    except KeyError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        
        # Get hierarchical formatter
        template = template_registry.get("hierarchical")
        formatter = HierarchicalFormatter(template)
        
        # Extract call stack
        call_stack = formatter._extract_call_stack(exc_traceback)
        print("Call Stack Details:")
        for i, (filename, lineno, function, code) in enumerate(call_stack):
            print(f"  Frame {i}:")
            print(f"    filename: {repr(filename)}")
            print(f"    lineno: {repr(lineno)}")
            print(f"    function: {repr(function)}")  # This might be '<module>'!
            print(f"    code: {repr(code.strip() if code else '')}")
            
            # Test what the file link would look like
            file_link = f'File "{filename}", line {lineno}, in {function}'
            print(f"    file_link: {repr(file_link)}")
            
            # Test if this would cause markup issues
            if '<' in file_link and '>' in file_link:
                print(f"    ⚠️ Contains angle brackets: {file_link}")

if __name__ == "__main__":
    test_call_stack()