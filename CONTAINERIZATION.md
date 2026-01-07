# Architecture & Containerization

**Objective:** Package the Meticulous MCP server and its dependencies as a portable Docker container that allows any user to run it against their machine.

## 1. Monorepo Structure
Unlike the upstream repository which relies on external dependencies or manual setup, this repository acts as a **self-contained Monorepo**. It includes:

*   `meticulous-mcp/`: The core MCP server logic.
*   `pyMeticulous/`: The Python SDK for the machine.
*   `espresso-profile-schema/`: The JSON schema definitions.
*   `python-sdk/`: The core MCP protocol SDK.

This ensures that `docker compose build` works immediately for any user without needing to clone multiple repositories or manage git submodules.

## 2. Container Strategy
We treat the application as a portable appliance.

*   **Dockerfile:** Builds a lightweight Python environment. It installs the local "vendored" packages (`pyMeticulous`, etc.) directly into the container image.
*   **Docker Compose:** Standardizes the runtime arguments (ports, environment variables) so users only need to configure their machine IP.
*   **Entry Point (`run_http.py`):** A custom wrapper script is used instead of running `mcp` directly. This allows us to explicitly bind to `0.0.0.0` (accessible outside the container) and manage transport security settings.

## 3. Code Adaptations

To support running in Docker, we modified the original source code to be "Environment Aware":

### A. Network Binding (`run_http.py`)
*   **Problem:** FastMCP defaults to `127.0.0.1` (localhost only), which makes the server unreachable from the host machine when running in Docker.
*   **Fix:** We force `host="0.0.0.0"` to listen on all interfaces.

### B. Schema Discovery (`server.py`)
*   **Problem:** The server originally looked for relative paths (e.g., `../espresso-profile-schema`), which breaks in different deployment structures.
*   **Fix:** We implemented a **Priority Search Path** strategy:
    1.  `METICULOUS_SCHEMA_PATH` (Environment Variable - highest priority)
    2.  `/app/espresso-profile-schema/schema.json` (Standard Docker path)
    3.  `../../espresso-profile-schema` (Local Dev fallback)