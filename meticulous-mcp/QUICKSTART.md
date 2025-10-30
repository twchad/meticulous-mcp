# Meticulous MCP Server - Quick Start Guide

## Prerequisites

- Python 3.11 or higher (check with `python3.11 --version`)
- Dependencies installed (see Installation section)

## Quick Run

### Option 1: Using the run script (Recommended)

```bash
cd meticulous-mcp
python3.11 run_server.py
```

### Option 2: Using Python module

```bash
cd meticulous-mcp
PYTHONPATH="src:../pyMeticulous:../python-sdk/src" python3.11 -m meticulous_mcp
```

### Option 3: Direct Python execution

```bash
cd meticulous-mcp
PYTHONPATH="src:../pyMeticulous:../python-sdk/src" python3.11 -c "from meticulous_mcp.server import main; main()"
```

## Test Installation

Before running, test that everything is set up:

```bash
python3.11 test_server.py
```

You should see:
```
✓ Successfully imported meticulous_mcp.server
✓ Server name: Meticulous Espresso Profile Server
✓ All imports successful!
```

## Troubleshooting

### Python version too old
If you get errors about `match` statement or syntax errors, make sure you're using Python 3.11+:
```bash
python3.11 --version  # Should show 3.11.x or higher
```

### Import errors
Make sure the dependencies are in the correct locations:
- `../pyMeticulous` - pyMeticulous repository
- `../python-sdk` - MCP Python SDK repository

### Module not found
Add the paths explicitly:
```bash
export PYTHONPATH="src:../pyMeticulous:../python-sdk/src:$PYTHONPATH"
python3.11 run_server.py
```

