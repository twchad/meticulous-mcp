#!/usr/local/opt/python@3.11/bin/python3.11
"""Run script for the Meticulous MCP server.
    
This script can be called from any directory using an absolute path.
It automatically sets up the Python path for dependencies.

Usage:
    python3.11 "/absolute/path/to/run_server.py"
    or
    /usr/local/opt/python@3.11/bin/python3.11 "/absolute/path/to/run_server.py"
    or
    ./run_server.py
"""

import sys
import os
from pathlib import Path

# Get the directory where this script is located (works even if called with absolute path)
# Use resolve() to handle any symlinks and get the absolute path
script_dir = Path(__file__).resolve().parent
project_root = script_dir

# Add paths for dependencies
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root.parent / "pyMeticulous"))
sys.path.insert(0, str(project_root.parent / "python-sdk" / "src"))

# Now import and run
if __name__ == "__main__":
    from meticulous_mcp.server import main
    main()
