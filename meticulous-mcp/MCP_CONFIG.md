# MCP Client Configuration

The path to `run_server.py` contains spaces, so it needs to be properly configured in your MCP client.

## For MCP Clients (like Claude Desktop)

Use this configuration format:

```json
{
  "meticulous-mcp": {
    "command": "python3.11",
    "args": [
      "/Users/chadwathington/Meticulous MCP/meticulous-mcp/run_server.py"
    ]
  }
}
```

**Important**: Do NOT put quotes around the path in the JSON array. The JSON format handles the spaces automatically.

## Troubleshooting

If you're still getting path errors, try:

### Option 1: Use a symlink without spaces (Recommended)

```bash
ln -s "/Users/chadwathington/Meticulous MCP" ~/meticulous-mcp-parent
```

Then use:
```json
{
  "meticulous-mcp": {
    "command": "python3.11",
    "args": [
      "/Users/chadwathington/meticulous-mcp-parent/meticulous-mcp/run_server.py"
    ]
  }
}
```

### Option 2: Check Python path

Make sure `python3.11` is in your PATH:
```bash
which python3.11
```

If it's not, use the full path:
```json
{
  "meticulous-mcp": {
    "command": "/usr/local/bin/python3.11",
    "args": [
      "/Users/chadwathington/Meticulous MCP/meticulous-mcp/run_server.py"
    ]
  }
}
```

### Option 3: Use the module approach

If the script path continues to cause issues, you can use the module approach with PYTHONPATH:

```json
{
  "meticulous-mcp": {
    "command": "python3.11",
    "args": [
      "-m",
      "meticulous_mcp.server"
    ],
    "env": {
      "PYTHONPATH": "/Users/chadwathington/Meticulous MCP/meticulous-mcp/src:/Users/chadwathington/Meticulous MCP/pyMeticulous:/Users/chadwathington/Meticulous MCP/python-sdk/src"
    }
  }
}
```

