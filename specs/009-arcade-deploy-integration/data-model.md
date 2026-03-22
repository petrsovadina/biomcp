# Data Model: Arcade Deploy Integration

**Branch**: `009-arcade-deploy-integration` | **Date**: 2026-03-21

## Overview

This feature introduces no new data entities or persistence. It creates a parallel tool registration layer (Arcade) that delegates to existing private implementation functions.

## Key Entities

### Arcade MCPApp (Runtime)

The Arcade application singleton, analogous to the existing `mcp_app` FastMCP singleton.

| Attribute | Type | Source |
|-----------|------|--------|
| `name` | `str` | Hardcoded: `"CzechMedMCP"` |
| `version` | `str` | From `czechmedmcp.__version__` |

**Lifecycle**: Created at module import time in `arcade/__init__.py`. No persistent state.

### Tool Wrapper (Code Pattern)

Each Arcade tool wrapper is a thin async function that:

1. Accepts parameters with `Annotated[type, "description"]`
2. Validates constraints manually (ge/le from Pydantic Field)
3. Calls the existing private implementation function
4. Returns `str`

**Mapping (60 wrappers total)**:

| Source Module | Wrapper Module | Count |
|---------------|----------------|-------|
| `individual_tools.py` | `arcade/individual_tools.py` | 33 |
| `czech/czech_tools.py` | `arcade/czech_tools.py` | 23 |
| `router.py` | `arcade/router_tools.py` | 2 |
| `thinking_tool.py` | `arcade/thinking_tool.py` | 1 |
| `metrics_handler.py` | `arcade/metrics_tool.py` | 1 |

### Dependency Graph (No Changes)

```
Arcade wrapper → private impl function → http_client / domain module → external API
                                        ↘ diskcache (shared)
```

The Arcade wrappers share the same runtime cache, HTTP client, and data infrastructure as FastMCP tools. No duplication of data or state.
