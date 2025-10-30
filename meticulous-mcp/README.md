# Meticulous Espresso Profile MCP Server

MCP server for managing espresso profiles for the Meticulous espresso machine. Provides AI agents with structured tools to create, validate, and manage espresso profiles without JSON manipulation.

## Features

- **Structured Profile Creation**: Create profiles using typed parameters instead of raw JSON
- **Profile Validation**: Validate profiles against JSON schema with helpful error messages
- **Profile Management**: List, get, update, duplicate, and delete profiles
- **Profile Execution**: Load and run profiles on the machine
- **MCP Resources**: Access espresso knowledge, schema reference, and profiles as resources
- **MCP Prompts**: Prompt templates for creating and modifying profiles

## Installation

```bash
cd meticulous-mcp
pip install -e .
```

Note: You'll also need to install the dependencies for `pyMeticulous` and `mcp` SDK. These can be installed from their local repositories or via pip if published.

**Important**: This project requires Python 3.11 or higher. The `match` statement and other Python 3.10+ features are used.

## Configuration

Set the `METICULOUS_API_URL` environment variable to point to your Meticulous machine:

```bash
export METICULOUS_API_URL=http://meticulousmodelalmondmilklatte.local
```

If not set, defaults to `http://meticulousmodelalmondmilklatte.local`.

## Usage

Run the server with stdio transport using Python 3.11+:

```bash
python3.11 -m meticulous_mcp.server
```

Or using the MCP CLI:

```bash
mcp run meticulous_mcp.server stdio
```

If you have the package installed:

```bash
meticulous-mcp
```

To test if everything is set up correctly:

```bash
python3.11 test_server.py
```

## Tools

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
Delete a profile.

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

