# Quickstart: Arcade Deploy Integration

## Prerequisites

- Python 3.10+
- `uv` package manager
- Arcade account (https://arcade.dev — Hobby plan is free)

## Setup

```bash
# 1. Install with Arcade extra (SDK: arcade-mcp-server)
uv sync --extra arcade

# 2. Install Arcade CLI (global tool: arcade-mcp)
uv tool install arcade-mcp

# 3. Login to Arcade
arcade login
```

## PoC Deployment (5 tools)

```bash
# Deploy PoC entrypoint
arcade deploy -e src/czechmedmcp/arcade/poc_entrypoint.py
```

## Full Deployment (60 tools)

```bash
# Deploy full entrypoint
arcade deploy -e src/czechmedmcp/arcade/entrypoint.py
```

## Local Development

```bash
# Run Arcade server locally (stdio mode)
uv run python -m czechmedmcp.arcade.entrypoint stdio

# Run Arcade server locally (HTTP mode)
uv run python -m czechmedmcp.arcade.entrypoint http
```

## Verify Deployment

```bash
# Check that all 60 tools are registered
uv run python -c "
import asyncio
from czechmedmcp.arcade import arcade_app
# Import to trigger registrations
import czechmedmcp.arcade.individual_tools
import czechmedmcp.arcade.czech_tools
import czechmedmcp.arcade.router_tools
import czechmedmcp.arcade.thinking_tool
import czechmedmcp.arcade.metrics_tool
print(f'Arcade tools registered: {len(arcade_app._tools)}')
"
```

## Railway Deployment (unchanged)

```bash
# Standard FastMCP deployment — no changes
uv run czechmedmcp run --mode streamable_http --port 8000
```
