#!/usr/bin/env python3
"""
Simple test to isolate the exception hook issue.
"""

import sys
from loguru import logger
from loguru._exception_hook import GlobalExceptionHook

def main():
    """Test the exception hook directly."""
    print(">> TESTING EXCEPTION HOOK DIRECTLY")
    print("=" * 50)
    
    # Create exception hook
    hook = GlobalExceptionHook(logger, "hierarchical")
    hook.install()
    
    # Create a simple exception
    data = {}
    missing = data["test"]  # This should trigger the exception hook

if __name__ == "__main__":
    main()