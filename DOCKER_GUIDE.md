# Meticulous MCP Server: Docker Guide

This guide explains how to build and run the Meticulous MCP server using Docker.

## Prerequisites

- [Docker](https://www.docker.com/get-started) and [Docker Compose](https://docs.docker.com/compose/install/) installed.
- A Meticulous Home Espresso machine on your local network.

## Quick Start (Build & Run)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/manonstreet/meticulous-mcp.git
   cd meticulous-mcp
   ```

2. **Configure your machine IP:**
   Open `docker-compose.yml` and replace the `METICULOUS_API_URL` with your machine's local IP address:
   ```yaml
   environment:
     # Examples: http://192.168.x.x, http://10.x.x.x, http://172.16.x.x
     - METICULOUS_API_URL=http://<YOUR_MACHINE_IP>
   ```

2. **Build the container:**
   ```bash
   docker compose build
   ```

3. **Start the server:**
   ```bash
   docker compose up -d
   ```

The server will now be running on port `8080`.

## Verifying the Server

You can check the logs to ensure it connected to your machine:
```bash
docker compose logs -f
```

## Integrating with Claude Desktop

To use this with Claude Desktop, add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "meticulous": {
      "command": "docker",
      "args": [
        "exec",
        "-i",
        "meticulous-mcp-server",
        "python",
        "run_http.py"
      ]
    }
  }
}
```

## Troubleshooting

- **Connection Refused:** Ensure your Meticulous machine is awake and on the same Wi-Fi network.
- **Port Conflict:** If port `8080` is already in use, change the mapping in `docker-compose.yml`.
