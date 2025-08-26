#!/usr/bin/env python3
"""
Test what valid loguru markup looks like.
"""

from loguru._colorizer import Colorizer

# Test various markup formats
test_markups = [
    "<bold blue>INFO</bold blue>",
    "<blue>INFO</blue>", 
    "<bold>INFO</bold>",
    "<cyan>INFO</cyan>",
    "<red>INFO</red>",
    "<yellow>INFO</yellow>",
    "<green>INFO</green>",
    "<magenta>INFO</magenta>",
    "<white>INFO</white>",
    "<dim>INFO</dim>"
]

print("Testing loguru markup formats:")
print("=" * 40)

for markup in test_markups:
    try:
        result = Colorizer.ansify(markup)
        print(f"{markup:25} -> WORKS: {repr(result)}")
    except Exception as e:
        print(f"{markup:25} -> ERROR: {e}")