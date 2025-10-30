#!/usr/bin/env python3.11
"""Test script to verify the MCP server can be imported and initialized."""

import sys
import os
from pathlib import Path

# Add paths for dependencies
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "src"))
sys.path.insert(0, str(current_dir.parent / "pyMeticulous"))
sys.path.insert(0, str(current_dir.parent / "python-sdk" / "src"))

try:
    print("Testing imports...")
    from meticulous_mcp.server import mcp
    print("✓ Successfully imported meticulous_mcp.server")
    
    print(f"✓ Server name: {mcp.name}")
    print("\n✓ All imports successful!")
    print("\nTo run the server, use:")
    print("  python3.11 -m meticulous_mcp.server")
    print("\nOr if installed:")
    print("  meticulous-mcp")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("\nMake sure you have:")
    print("1. Python 3.11+ installed")
    print("2. Dependencies installed (pip install -r requirements.txt)")
    print("3. pyMeticulous and python-sdk repos cloned in parent directory")
    sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

