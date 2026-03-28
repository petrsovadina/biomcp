---
color: purple
isContextNode: false
agent_name: Aki
status: claimed
---
# Arcade Deploy Layer

Paralelní deployment wrappery pro Arcade Cloud — 60 nástrojů delegujících na stejné privátní implementace jako FastMCP.

**Root path:** `src/czechmedmcp/arcade/`

**Key files:** entrypoint.py, poc_entrypoint.py, individual_tools.py, czech_tools.py, router_tools.py, thinking_tool.py

**Purpose:** Arcade-MCP-Server SDK wrappery. Klíčové rozdíly: @arcade_app.tool (bez závorek), Annotated[type, 'desc'] místo Field(), manuální clamping místo Pydantic constraints.

[[welcome_to_voicetree]]
