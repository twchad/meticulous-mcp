"""Entry point for running the MCP server."""

import sys
from pathlib import Path

# Add paths for dependencies if running as module
# When running as `python -m meticulous_mcp`, __file__ is this file
# We need to go up to project root: meticulous_mcp/__main__.py -> meticulous_mcp/ -> src/ -> project root
if __name__ == "__main__":
    # Get the project root (parent of src/)
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root / "src"))
    sys.path.insert(0, str(project_root.parent / "pyMeticulous"))
    sys.path.insert(0, str(project_root.parent / "python-sdk" / "src"))

from meticulous_mcp.server import mcp

if __name__ == "__main__":
    mcp.run("stdio")

