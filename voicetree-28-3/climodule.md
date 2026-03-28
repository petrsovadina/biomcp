---
color: gold
isContextNode: false
agent_name: Aki
status: claimed
---
# CLI & Server Modes

Typer CLI app se třemi serverovými režimy (stdio, streamable_http, worker) a doménovými sub-příkazy.

**Root path:** `src/czechmedmcp/cli/`

**Key files:** server.py, __init__.py + per-domain CLI subcommands

**Purpose:** Entry point přes __main__.py → Typer app. Tři režimy: STDIO (Claude Desktop), HTTP endpoint (Railway), Legacy SSE worker.

[[welcome_to_voicetree]]
