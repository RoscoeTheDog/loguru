#!/usr/bin/env python3
"""
Debug the style rules to see what's creating the <module> tag.
"""

from loguru._hierarchical_formatter import HierarchicalFormatter
from loguru._templates import template_registry

def test_context_styling():
    """Test what happens when we apply context styling to the exception message."""
    
    # Get hierarchical template
    template = template_registry.get("hierarchical")
    formatter = HierarchicalFormatter(template)
    
    # Test message that's causing issues
    message = "Unhandled KeyError: 'test'"
    context = {}  # No context
    
    print(f"Original message: {repr(message)}")
    print(f"Template style rules: {len(template.style_rules)}")
    
    for i, rule in enumerate(template.style_rules):
        print(f"Rule {i}: pattern={rule.pattern.pattern}, style={rule.style}")
        matches = list(rule.pattern.finditer(message))
        if matches:
            print(f"  Matches found: {[m.group() for m in matches]}")
    
    # Test the actual styling
    try:
        styled_message = formatter._apply_context_styling(message, context)
        print(f"Styled message: {repr(styled_message)}")
        
        # Test colorization
        from loguru._colorizer import Colorizer
        colorized = Colorizer.ansify(styled_message)
        print(f"Colorized successfully: {len(colorized)} chars")
        
    except Exception as e:
        print(f"ERROR in styling: {e}")

if __name__ == "__main__":
    test_context_styling()