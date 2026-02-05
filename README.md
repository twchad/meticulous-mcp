# Meticulous Espresso Profile MCP Server

An MCP (Model Context Protocol) server for managing espresso profiles on your Meticulous espresso machine. Use AI assistants like Claude Desktop or Goose to create, validate, and manage espresso profiles without diving deep in application or manual JSON editing.

## What is Meticulous MCP?

Meticulous MCP allows you to create and install Meticulous profiles on your machine via AI agents.

You can use natural language to describe the kind of profile you want, stages required, flow rate, temperature, etc., and an agent will build a profile for you -- no JSON or fiddling in the app required. The server helps agents understand espresso profiling and gives them tools to interact with your Meticulous via the API. The server is built off of Meticulous' Python API, the Meticulous espresso profile schema, and wisdom from Lance Hedrick, Aramse, and Home-Barista.com. The knowledge base for Agents needs work, and will evolve over time. It's not perfect and you may not like its suggestions, but you can be specific with your guidance to get around that.

You must have access to an agent that can use desktop/local MCP via STDIO. Popular clients for this include Claude Desktop, Goose, LibreChat, Cherry Studio, and LM Studio. It's only been tested with Goose, Cursor, and Claude Desktop. ChatGPT can not currently call MCP tools on your desktop.

## Disclaimer
**⚠️ Important Disclaimer:** Please use Meticulous MCP at your own risk. There's no warranty of any kind, and if your AI builds a whacky profile that bricks your Meticulous, the creators are not responsible. The MCP server is only a communication layer that allows AI to talk to your Meticulous. While there is profile validation, and the Meticulous fails to load certain types of weird profiles, we can't guarantee everything. The only safety limit is 15 bars pressure, which appears to be the limit in the app. **Please check your profiles in the app before running them.** In particular, the less smart the model, the more mistakes it might make, including getting the JSON submission right. The server gives the model feedback on its submission mistakes so that it can try again, but some models aren't good enough to fix themselves. If you model can't get the submission right over many tries, try a smarter model.

Lastly, **Meticulous MCP is not a product of Meticulous Home**. Please don't bother the Meticulous development team about Meticulous MCP. We did not submit it to Meticulous intentionally, because it does not meet Meticulous' standards for review. The server is a fun tool to build profiles, not part of the product.

Have fun profiling!

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

### Step 2: Download the Repository

Download or clone the Meticulous MCP repository from GitHub:

**Option 1: Clone with Git**
```bash
git clone https://github.com/twchad/meticulous-mcp.git
cd meticulous-mcp
```

**Option 2: Download ZIP**
- Visit [https://github.com/twchad/meticulous-mcp](https://github.com/twchad/meticulous-mcp)
- Click the green "Code" button
- Select "Download ZIP"
- Extract the downloaded file to your preferred location

### Step 3: Install Dependencies

Navigate to the `meticulous-mcp` directory and install:

```bash
cd meticulous-mcp
pip install -r requirements.txt
```

**Note:** This project uses local dependencies (`pyMeticulous` and `python-sdk`). Make sure these directories are in the parent folder alongside `meticulous-mcp`.

### Step 4: Configure Your MCP Client

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

### Step 5: Test Your Setup (Optional)

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

### Step 6: Restart Your MCP Client

- **Claude Desktop:** Quit and restart Claude Desktop
- **Cursor:** Restart Cursor

Your Meticulous MCP server should now be available!

## What You Can Do

Once connected, you can ask your AI assistant to:

- **Monitor machine status** - "Check current temperature and state"
- **Manage settings** - "Enable auto-preheat" or "Change the sound theme"
- **Access shot history** - "Get the log file for my last shot"
- **Create espresso profiles** - "Create a new espresso profile with..."
- **List profiles** - "Show me all my espresso profiles"
- **Get profile details** - "Show me the details of profile X or explain this profile to me.."
- **Update profiles** - "Modify profile X to..."
- **Duplicate profiles** - "Copy profile X and name it Y"
- **Validate profiles** - "Check if this profile JSON is valid"
- **Run profiles** - "Execute profile X on the machine"

## Example Agent Conversation

Here's a realistic example of how an AI agent would interact with your Meticulous machine to create a new espresso profile:

**User:** "I'd like to create a turbo shot profile for my light roast Ethiopian coffee. I want a bright, clear shot with good acidity."

**Agent:** "I'll create a turbo shot profile optimized for light roast coffee. This profile will use higher temperature and a 1:3 ratio for brightness and clarity."

**Agent calls:** `create_profile` with the following data:

```json
{
  "name": "Turbo Light Roast v1",
  "author": "AI Assistant",
  "temperature": 94.0,
  "final_weight": 54.0,
  "stages": [
    {
      "name": "Preinfusion",
      "key": "preinfusion",
      "type": "flow",
      "dynamics_points": [[0, 6]],
      "dynamics_over": "time",
      "dynamics_interpolation": "linear",
      "exit_triggers": [
        {"type": "pressure", "value": 1.5, "comparison": ">="},
        {"type": "time", "value": 20, "comparison": ">="}
      ]
    },
    {
      "name": "Infusion",
      "key": "infusion",
      "type": "pressure",
      "dynamics_points": [[0, 6.0], [3, 6.0]],
      "dynamics_over": "time",
      "dynamics_interpolation": "linear",
      "exit_triggers": [
        {"type": "time", "value": 15, "comparison": ">="},
        {"type": "weight", "value": 35, "comparison": ">="}
      ],
      "limits": [{"type": "flow", "value": 8}]
    },
    {
      "name": "Decline",
      "key": "decline",
      "type": "pressure",
      "dynamics_points": [[0, 6.0], [10, 3.0]],
      "dynamics_over": "time",
      "dynamics_interpolation": "linear",
      "exit_triggers": [
        {"type": "weight", "value": 54, "comparison": ">="},
        {"type": "time", "value": 30, "comparison": ">="}
      ]
    }
  ]
}
```

**Response from Meticulous Machine:**

```json
{
  "profile_id": "d188ba5f-4939-489a-9c0e-38fb879c9fdd",
  "profile_name": "Turbo Light Roast v1",
  "message": "Profile 'Turbo Light Roast v1' created successfully"
}
```

**Final Profile JSON Sent to Meticulous Machine:**

```json
{
  "name": "Turbo Light Roast v1",
  "id": "d188ba5f-4939-489a-9c0e-38fb879c9fdd",
  "author": "AI Assistant",
  "author_id": "f2d7b244-b2cd-4f9d-ae27-baee5f9ebaa8",
  "display": {
    "image": "/api/v1/profile/image/f9e16abcc19c1a34deaa9c2ac3bc7653.png",
    "accentColor": "#5098C8"
  },
  "temperature": 94.0,
  "final_weight": 54.0,
  "stages": [
    {
      "name": "Preinfusion",
      "key": "preinfusion",
      "type": "flow",
      "dynamics": {
        "points": [[0.0, 6.0]],
        "over": "time",
        "interpolation": "linear"
      },
      "exit_triggers": [
        {"type": "pressure", "value": 1.5, "relative": false, "comparison": ">="},
        {"type": "time", "value": 20.0, "relative": false, "comparison": ">="}
      ],
      "limits": []
    },
    {
      "name": "Infusion",
      "key": "infusion",
      "type": "pressure",
      "dynamics": {
        "points": [[0.0, 6.0], [3.0, 6.0]],
        "over": "time",
        "interpolation": "linear"
      },
      "exit_triggers": [
        {"type": "time", "value": 15.0, "relative": false, "comparison": ">="},
        {"type": "weight", "value": 35.0, "relative": false, "comparison": ">="}
      ],
      "limits": [{"type": "flow", "value": 8.0}]
    },
    {
      "name": "Decline",
      "key": "decline",
      "type": "pressure",
      "dynamics": {
        "points": [[0.0, 6.0], [10.0, 3.0]],
        "over": "time",
        "interpolation": "linear"
      },
      "exit_triggers": [
        {"type": "weight", "value": 54.0, "relative": false, "comparison": ">="},
        {"type": "time", "value": 30.0, "relative": false, "comparison": ">="}
      ],
      "limits": []
    }
  ]
}
```

**Agent:** "I've created a turbo shot profile called 'Turbo Light Roast v1' for your Ethiopian coffee. Here's what it does:

- **Temperature:** 94°C (ideal for light roasts to extract sweetness)
- **Pre-infusion:** Fast flow at 6 ml/s until pressure reaches 1.5 bar
- **Infusion:** Holds 6 bar pressure for quick extraction (exits at 35g or 15 seconds)
- **Decline:** Gradually reduces pressure from 6 to 3 bar for a smooth finish
- **Final yield:** 54g (1:3 ratio for bright, tea-like clarity)

The profile is now saved on your Meticulous machine and ready to use!"

### What This Example Shows

1. **Natural Language Input:** The user describes what they want in plain English
2. **Agent Intelligence:** The AI understands the request and applies espresso profiling knowledge
3. **Structured API Calls:** The agent constructs proper JSON with all required fields
4. **Automatic Normalization:** Missing fields like `relative` and `limits` are automatically added
5. **Machine-Ready Output:** The final JSON is fully compliant with the Meticulous schema
6. **User-Friendly Response:** The agent explains what the profile does in understandable terms

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

### Profile Creation Errors

**Problem:** Agent gets errors when trying to create profiles

**Solutions:**
1. Make sure your MCP server is up to date (restart your MCP client after updating)
2. Check that the agent has access to the espresso profiling knowledge resources
3. Try asking the agent to rephrase your request more simply
4. If errors persist, check the error message and try creating a simpler profile first

### Machine Not Found

**Problem:** Cannot connect to Meticulous machine

**Solutions:**
1. Verify your machine is powered on and on the same network
2. Check the hostname in your machine's settings
3. Set `METICULOUS_API_URL` environment variable (see Advanced Configuration)
4. Try accessing `http://your-machine-name.local` in a browser

## Tools Reference

### get_machine_status
Get the current status of the Meticulous machine (temperature, state, current shot data).

### get_settings / update_setting
Read and modify machine settings like `auto_preheat`, `enable_sounds`, etc.

### list_shot_history / get_shot_url
Browse history by date and retrieve direct download links for shot logs.

### create_profile
Create a new espresso profile with structured parameters.

**Required fields:**
- `name`: Profile name
- `author`: Author name  
- `temperature`: Brew temperature in Celsius (typically 82-96°C)
- `final_weight`: Target output weight in grams
- `stages`: Array of stage objects (see example conversation above)

**Optional fields:**
- `variables`: Custom variables for dynamic values
- `accent_color`: Hex color code (e.g., "#FF5733")

### list_profiles
List all available profiles.

### get_profile
Get full profile details by ID.

### update_profile
Update an existing profile.

**Required fields:**
- `profile_id`: ID of the profile to update

**Optional fields:**
- `name`: New profile name
- `temperature`: New temperature in Celsius
- `final_weight`: New target weight in grams
- `stages_json`: JSON string containing updated stages array

**Example:**
```json
{
  "profile_id": "profile-uuid-here",
  "name": "Updated Name",
  "temperature": 92.0
}
```

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

### Running Tests

To run the test suite locally:

```bash
cd meticulous-mcp
PYTHONPATH=/path/to/meticulous-mcp/src pytest tests/ -v
```

Or use the convenience script from the root directory:

```bash
./run_all_tests.sh
```

### CI/CD Pipeline

This repository uses GitHub Actions for continuous integration and continuous deployment. The CI/CD pipeline automatically:

- **Triggers on**: Push to `main` or `develop` branches, and pull requests targeting these branches
- **Build steps**:
  1. Sets up Python 3.11 environment
  2. Installs all dependencies from `requirements.txt`
  3. Runs the full test suite with pytest
  4. Reports test results and coverage

**Workflow file**: `.github/workflows/ci.yml`

The workflow ensures that all code changes are automatically tested before being merged, helping maintain code quality and catch issues early in the development process.

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
