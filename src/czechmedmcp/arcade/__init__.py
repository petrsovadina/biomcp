"""Arcade Deploy integration for CzechMedMCP.

This package provides Arcade-compatible tool wrappers that delegate
to the same private implementation functions used by the FastMCP
server. The arcade_app singleton is the Arcade equivalent of
core.mcp_app.

Install with: uv sync --extra arcade
Deploy with:  arcade deploy -e src/czechmedmcp/arcade/entrypoint.py
"""

from arcade_mcp_server import MCPApp

arcade_app = MCPApp(
    name="czech_med_mcp",
    version="0.8.0",
)
