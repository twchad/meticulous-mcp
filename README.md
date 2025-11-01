# Meticulous Espresso Profile MCP Server

An MCP (Model Context Protocol) server for managing espresso profiles on your Meticulous espresso machine. Use AI assistants like Claude Desktop or Cursor to create, validate, and manage espresso profiles without manual JSON editing.

## Quick Start

### Step 1: Install Python 3.11+

**Mac:**
```bash
# Check if you have Python 3.11+
python3.11 --version

# If not installed, install via Homebrew:
brew install python@3.11
```

**Windows:**
- Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"
- Verify installation: Open Command Prompt and run `python --version`

### Step 2: Install Dependencies

Navigate to the `meticulous-mcp` directory and install:

```bash
cd meticulous-mcp
pip install -r requirements.txt
```

**Note:** This project uses local dependencies (`pyMeticulous` and `python-sdk`). Make sure these directories are in the parent folder alongside `meticulous-mcp`.

## What is Meticulous MCP?

Meticulous MCP allows you to create and install Meticulous profiles on your machine via AI agents.

You can use natural language to describe the kind of profile you want, stages required, flow rate, temperature, etc., and an agent will build a profile for you -- no JSON or fiddling in the app required. The server helps agents understand espresso profiling and gives them tools to interact with your Meticulous via the API. The server is built off of Meticulous' Python API, the Meticulous espresso profile schema, and wisdom from Lance Hedrick, Aramse, and Home-Barista.com.

You must have access to an agent that can use desktop/local MCP via STDIO. Popular clients for this include Claude Desktop, Goose, LibreChat, Cherry Studio, and LM Studio. It's only been tested with Goose, Cursor, and Claude Desktop. ChatGPT can not currently call MCP tools on your desktop.

**⚠️ Important Disclaimer:** Please use Meticulous MCP at your own risk. There's no warranty of any kind, and if your AI builds a whacky profile that bricks your Meticulous, the creators are not responsible. The MCP server is only a communication layer that allows AI to talk to your Meticulous. While there is profile validation, and the Meticulous fails to load certain types of weird profiles, we can't guarantee everything. Please check your profiles in the app before running them.

Lastly, don't bother the Meticulous development team about Meticulous MCP. We did not submit it to Meticulous intentionally, because it does not meet Meticulous' standards for review.

Have fun profiling!

### Step 3: Configure Your MCP Client

Add the Meticulous MCP server to your MCP client configuration.

#### For Claude Desktop

**Mac:** Edit `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows:** Edit `%APPDATA%\Claude\claude_desktop_config.json`

Add this configuration:

```json
{
  "mcpServers": {
    "meticulous-mcp": {
      "command": "python3.11",
      "args": [
        "/absolute/path/to/Meticulous MCP/meticulous-mcp/run_server.py"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/Meticulous MCP/meticulous-mcp/src:/absolute/path/to/Meticulous MCP/pyMeticulous:/absolute/path/to/Meticulous MCP/python-sdk/src"
      }
    }
  }
}
```

**Replace `/absolute/path/to/Meticulous MCP` with your actual path.**

**Note:** The `PYTHONPATH` environment variable is optional when using `run_server.py` since it automatically sets up paths internally. However, including it serves as a safeguard and ensures compatibility across different execution contexts. If you encounter import errors, make sure PYTHONPATH is set correctly.

**Mac example:**
```json
{
  "mcpServers": {
    "meticulous-mcp": {
      "command": "python3.11",
      "args": [
        "/Users/yourname/Meticulous MCP/meticulous-mcp/run_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/yourname/Meticulous MCP/meticulous-mcp/src:/Users/yourname/Meticulous MCP/pyMeticulous:/Users/yourname/Meticulous MCP/python-sdk/src"
      }
    }
  }
}
```

**Windows example:**
```json
{
  "mcpServers": {
    "meticulous-mcp": {
      "command": "python",
      "args": [
        "C:\\Users\\YourName\\Meticulous MCP\\meticulous-mcp\\run_server.py"
      ],
      "env": {
        "PYTHONPATH": "C:\\Users\\YourName\\Meticulous MCP\\meticulous-mcp\\src;C:\\Users\\YourName\\Meticulous MCP\\pyMeticulous;C:\\Users\\YourName\\Meticulous MCP\\python-sdk\\src"
      }
    }
  }
}
```

**Note for Windows:** Use backslashes (`\\`) in paths and semicolons (`;`) in PYTHONPATH.

#### For Cursor

Edit `~/.cursor/mcp.json` (Mac) or `%APPDATA%\Cursor\mcp.json` (Windows) and add the same configuration as above.

### Step 4: Test Your Setup

**Mac:**
```bash
cd meticulous-mcp
python3.11 test_server.py
```

Or run from the parent directory (make sure to include the forward slash):
```bash
python3.11 meticulous-mcp/test_server.py
```

**Windows:**
```bash
cd meticulous-mcp
python test_server.py
```

Or run from the parent directory (make sure to include the backslash):
```bash
python meticulous-mcp\test_server.py
```

You should see:
```
Testing imports...
✓ Successfully imported meticulous_mcp.server
✓ Server name: Meticulous Espresso Profile Server

✓ All imports successful!
```

### Step 5: Restart Your MCP Client

- **Claude Desktop:** Quit and restart Claude Desktop
- **Cursor:** Restart Cursor

Your Meticulous MCP server should now be available!

## What You Can Do

Once connected, you can ask your AI assistant to:

- **Create espresso profiles** - "Create a new espresso profile with..."
- **List profiles** - "Show me all my espresso profiles"
- **Get profile details** - "Show me the details of profile X"
- **Update profiles** - "Modify profile X to..."
- **Duplicate profiles** - "Copy profile X and name it Y"
- **Validate profiles** - "Check if this profile JSON is valid"
- **Run profiles** - "Execute profile X on the machine"

## Features

- **Structured Profile Creation**: Create profiles using typed parameters instead of raw JSON
- **Profile Validation**: Validate profiles against JSON schema with helpful error messages
- **Profile Management**: List, get, update, duplicate, and delete profiles
- **Profile Execution**: Load and run profiles on the machine
- **MCP Resources**: Access espresso knowledge, schema reference, and profiles as resources
- **MCP Prompts**: Prompt templates for creating and modifying profiles

## Advanced Configuration

### Using a Different Host Name

If your Meticulous machine uses a different hostname (not the default `meticulousmodelalmondmilklatte.local`), you can configure it in two ways:

#### Option 1: Environment Variable (Recommended)

Add the `METICULOUS_API_URL` environment variable to your MCP client configuration:

**Mac example:**
```json
{
  "mcpServers": {
    "meticulous-mcp": {
      "command": "python3.11",
      "args": [
        "/Users/yourname/Meticulous MCP/meticulous-mcp/run_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/yourname/Meticulous MCP/meticulous-mcp/src:/Users/yourname/Meticulous MCP/pyMeticulous:/Users/yourname/Meticulous MCP/python-sdk/src",
        "METICULOUS_API_URL": "http://your-machine-name.local"
      }
    }
  }
}
```

**Windows example:**
```json
{
  "mcpServers": {
    "meticulous-mcp": {
      "command": "python",
      "args": [
        "C:\\Users\\YourName\\Meticulous MCP\\meticulous-mcp\\run_server.py"
      ],
      "env": {
        "PYTHONPATH": "C:\\Users\\YourName\\Meticulous MCP\\meticulous-mcp\\src;C:\\Users\\YourName\\Meticulous MCP\\pyMeticulous;C:\\Users\\YourName\\Meticulous MCP\\python-sdk\\src",
        "METICULOUS_API_URL": "http://your-machine-name.local"
      }
    }
  }
}
```

#### Option 2: System Environment Variable

**Mac (Terminal):**
```bash
export METICULOUS_API_URL=http://your-machine-name.local
```

**Mac (persistent - add to `~/.zshrc` or `~/.bash_profile`):**
```bash
echo 'export METICULOUS_API_URL=http://your-machine-name.local' >> ~/.zshrc
source ~/.zshrc
```

**Windows (Command Prompt):**
```cmd
set METICULOUS_API_URL=http://your-machine-name.local
```

**Windows (persistent - System Properties):**
1. Right-click "This PC" → Properties
2. Advanced system settings → Environment Variables
3. Add new System variable: `METICULOUS_API_URL` = `http://your-machine-name.local`

**Default:** If not set, defaults to `http://meticulousmodelalmondmilklatte.local`

### Alternative: Using Python Module Directly

If you prefer to use the Python module directly instead of the run script:

**Mac:**
```json
{
  "mcpServers": {
    "meticulous-mcp": {
      "command": "python3.11",
      "args": [
        "-m",
        "meticulous_mcp.server"
      ],
      "env": {
        "PYTHONPATH": "/Users/yourname/Meticulous MCP/meticulous-mcp/src:/Users/yourname/Meticulous MCP/pyMeticulous:/Users/yourname/Meticulous MCP/python-sdk/src"
      }
    }
  }
}
```

**Windows:** Same format, but use `python` instead of `python3.11`.

**Note:** When using the module approach (`-m meticulous_mcp.server`), the `PYTHONPATH` environment variable is **required** because the module needs to know where to find the dependencies.

## Troubleshooting

### Python Version Issues

**Problem:** Error about `match` statement or syntax errors

**Solution:** Ensure you're using Python 3.11 or higher:
- Mac: `python3.11 --version`
- Windows: `python --version`

### Import Errors

**Problem:** Module not found errors

**Solution:** 
- If using `run_server.py`: The script should handle paths automatically, but ensure PYTHONPATH is set in your MCP config as a safeguard
- If using the module approach (`-m meticulous_mcp.server`): PYTHONPATH is required
- Verify your PYTHONPATH includes all three directories:
  1. `meticulous-mcp/src`
  2. `pyMeticulous` (parent directory)
  3. `python-sdk/src` (parent directory)

### Path Issues on Windows

**Problem:** Paths with spaces not working

**Solution:** 
- Use double backslashes: `C:\\Users\\YourName\\Meticulous MCP\\...`
- Or use forward slashes: `C:/Users/YourName/Meticulous MCP/...`
- Windows Python accepts both formats

### Server Not Connecting

**Problem:** MCP client can't connect to server

**Solutions:**
1. Check that Python path is correct in your config
2. Verify the `run_server.py` path is absolute and correct
3. Test manually: `python3.11 /path/to/run_server.py` (should start without errors)
4. Check that all dependencies are installed: `pip install -r requirements.txt`

### Machine Not Found

**Problem:** Cannot connect to Meticulous machine

**Solutions:**
1. Verify your machine is powered on and on the same network
2. Check the hostname in your machine's settings
3. Set `METICULOUS_API_URL` environment variable (see Advanced Configuration)
4. Try accessing `http://your-machine-name.local` in a browser

## Tools Reference

### create_profile
Create a new espresso profile with structured parameters.

### list_profiles
List all available profiles.

### get_profile
Get full profile details by ID.

### update_profile
Update an existing profile.

### duplicate_profile
Duplicate a profile and optionally modify it.

### delete_profile
Delete a profile permanently.

### validate_profile
Validate a profile JSON against the schema.

### run_profile
Load and execute a profile (without saving).

## Resources

- `espresso://knowledge` - Espresso profiling knowledge
- `espresso://schema` - Profile schema reference
- `espresso://profile/{id}` - Individual profile as resource

## Prompts

- `create_espresso_profile` - Prompt template for creating profiles
- `modify_espresso_profile` - Prompt template for modifying profiles

## Development

Run tests:
```bash
pytest
```

## Dependencies

- pyMeticulous: Python API wrapper for Meticulous machine
- mcp: Model Context Protocol SDK
- jsonschema: JSON schema validation
- pydantic: Data validation

## License

This project is licensed under the GNU General Public License v3.0 or later (GPL-3.0-or-later).

### GPL 3 Compliance

This project uses code from `pyMeticulous`, which is licensed under GPL 3.0. As a result, this project must also be licensed under GPL 3.0 in accordance with the GPL copyleft requirements.

### Attribution

This project incorporates code from:
- **pyMeticulous**: Licensed under GPL 3.0 (see `../pyMeticulous/LICENSE`)
- **python-sdk (mcp)**: Licensed under MIT License (see `../python-sdk/LICENSE`)

For full license terms, see the [LICENSE](LICENSE) file in this directory.
