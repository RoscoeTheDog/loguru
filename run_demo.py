#!/usr/bin/env python3
"""
🚀 Quick Demo Launcher
======================

Run this to see the enhanced loguru features in action!
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Launch the demo with proper setup."""
    demo_path = Path(__file__).parent / "demo.py"
    
    if not demo_path.exists():
        print("❌ Demo script not found!")
        return 1
    
    print("🚀 Launching Enhanced Loguru Demo...")
    print("=" * 50)
    
    try:
        # Run the demo script
        result = subprocess.run([sys.executable, str(demo_path)], check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Demo failed with exit code: {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted")
        return 0

if __name__ == "__main__":
    sys.exit(main())