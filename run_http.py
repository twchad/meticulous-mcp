import sys
import os
from pathlib import Path

if __name__ == "__main__":
    from meticulous_mcp.server import mcp
    
    # FastMCP's constructor has default arguments that override environment variables.
    # We must explicitly overwrite the settings on the object to force 0.0.0.0.
    mcp.settings.host = os.environ.get("FASTMCP_HOST", "0.0.0.0")
    mcp.settings.port = int(os.environ.get("FASTMCP_PORT", "8080"))
    mcp.settings.log_level = os.environ.get("FASTMCP_LOG_LEVEL", "INFO")

    # DISABLING SECURITY CHECK:
    # Because the server was initialized with default host="127.0.0.1", it automatically 
    # enabled "DNS Rebinding Protection" which restricts the Host header to localhost.
    # Since we are changing the host to 0.0.0.0 to accept external traffic (e.g. from "studio"),
    # we must disable this protection to avoid "Invalid Host header" errors.
    mcp.settings.transport_security = None
        
    print(f"Starting Meticulous MCP server on {mcp.settings.host}:{mcp.settings.port} via Streamable HTTP", flush=True)
    mcp.run("streamable-http")