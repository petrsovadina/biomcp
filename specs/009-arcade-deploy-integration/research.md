# Research: Arcade Deploy Integration

**Branch**: `009-arcade-deploy-integration` | **Date**: 2026-03-21

## R1: Arcade MCP Server SDK API

**Decision**: Use `arcade_mcp_server.MCPApp` with `@app.tool` decorator pattern.

**Rationale**: There are **two separate packages**:
- **`arcade-mcp`** (CLI) — provides `arcade` CLI command (`arcade deploy`, `arcade login`, etc.). Install globally: `uv tool install arcade-mcp`
- **`arcade-mcp-server`** (SDK) — provides `MCPApp`, `Context`, auth providers. This is what you import in code. Installing `arcade-mcp` pulls this in as a dependency.

Import from `arcade_mcp_server`, NOT `arcade_mcp`.

**MCPApp name restriction**: Must be alphanumeric + underscores only. Use `czech_med_mcp` not `CzechMedMCP`.

**Key API surface**:
```python
from arcade_mcp_server import MCPApp
from typing import Annotated

app = MCPApp(name="czech_med_mcp", version="0.8.0")

@app.tool
async def my_tool(param: Annotated[str, "Description"]) -> str:
    """Tool docstring."""
    return await _private_impl(param)

if __name__ == "__main__":
    app.run()
```

**Additional registration methods**:
- `app.add_tool(my_function)` — register a single tool programmatically
- `app.add_tools_from_module(module)` — register all `@tool`-decorated functions from a module

**Alternatives considered**:
- Direct MCP SDK (too low-level, no Arcade Deploy support)
- Arcade Engine (overkill, designed for Arcade's full auth platform)

## R2: Parameter Annotation Differences

**Decision**: Arcade wrappers use `Annotated[type, "description"]` instead of `Annotated[type, Field(description="...")]`.

**Rationale**: Arcade SDK uses plain string annotations, not Pydantic Field. Pydantic constraints (`ge`, `le`, `min_length`, `max_length`) are not natively supported by Arcade annotations and must be enforced via validation inside wrapper functions.

**Impact on wrappers**:
- `Field(description="...")` → plain `"description"` string
- `Field(ge=1, le=100)` → manual `if page < 1: page = 1` in wrapper
- `list[str] | str | None` → may need simplification to `str | None` with manual parsing
- Default values work identically

## R3: Arcade Deploy CLI

**Decision**: Use `arcade deploy -e <entrypoint>` from project root.

**Rationale**: Arcade Deploy reads `pyproject.toml` for dependencies and deploys the MCP server to Arcade Cloud. The entrypoint file must have `if __name__ == "__main__": app.run()`.

**Commands**:
```bash
# Install CLI
uv tool install arcade-mcp

# Deploy
arcade deploy -e src/czechmedmcp/arcade_entrypoint.py

# Local dev (stdio)
python src/czechmedmcp/arcade_entrypoint.py stdio

# Local dev (HTTP)
python src/czechmedmcp/arcade_entrypoint.py http
```

## R4: Async Tool Support

**Decision**: Async tools are fully supported by Arcade SDK.

**Rationale**: Arcade examples show both sync and async tools. Since all CzechMedMCP private implementation functions are async, the Arcade wrappers will also be async. No adaptation needed.

## R5: Return Type Handling

**Decision**: All Arcade wrappers return `str`. The `think` tool wrapper serializes `dict` to JSON string.

**Rationale**: FastMCP tools mostly return `str` already (markdown via `render.to_markdown()` or `json.dumps()`). The `think` tool is the exception — it returns `dict`. Arcade supports `dict` returns, but per FR-007 we standardize on `str` for consistency and to avoid potential MCP protocol issues.

## R6: Optional Dependency Strategy

**Decision**: Add `arcade` optional extra in `pyproject.toml` with `arcade-mcp` dependency.

**Rationale**:
- `uv sync` (no extras) → FastMCP server works, no Arcade imports
- `uv sync --extra arcade` → Arcade entrypoint available
- Import guard: `try: from arcade_mcp_server import MCPApp except ImportError` not needed in entrypoint (only run when Arcade is installed)
- No conditional imports in existing code — Arcade code lives in separate modules

**pyproject.toml addition**:
```toml
[project.optional-dependencies]
arcade = ["arcade-mcp-server>=1.17.0"]
```

**Note**: The SDK package is `arcade-mcp-server`, not `arcade-mcp`. The CLI (`arcade-mcp`) is installed separately as a global tool.

## R10: Arcade Deploy Validation Process

**Decision**: `arcade deploy` starts server locally before uploading to validate health and extract tool metadata.

**Rationale**: This means the entrypoint must be runnable locally with all dependencies available. The deploy process:
1. Validates authentication (`arcade login`)
2. Checks `pyproject.toml` exists in working directory
3. Loads `.env` for environment variables
4. **Starts server locally** to validate health and discover tools
5. Uploads secrets to Arcade infrastructure
6. Creates and deploys package to Arcade Cloud

**Gotchas**:
- HTTP transport does NOT support auth/secrets locally — use stdio for local testing
- `arcade deploy` default entrypoint is `server.py` — must use `-e` for custom path
- Environment variables: `ARCADE_SERVER_TRANSPORT`, `ARCADE_SERVER_HOST`, `ARCADE_SERVER_PORT` override constructor params

## R7: Project Structure for Arcade Modules

**Decision**: Create `src/czechmedmcp/arcade/` package with entrypoint and per-module wrapper files.

**Rationale**: Mirrors the existing modular structure. The `arcade/` directory parallels how `czech/` is organized — separate namespace, own tool registrations.

**Alternatives considered**:
- Single entrypoint file with all 60 wrappers (900+ lines, unmaintainable)
- Code generation from FastMCP registrations (adds complexity, harder to debug)
- Shared decorator/adapter layer (over-engineering for thin wrappers)

## R8: Union Type Handling (list[str] | str | None)

**Decision**: Arcade wrappers accept `str | None` for parameters that FastMCP accepts as `list[str] | str | None`, using `ensure_list()` internally.

**Rationale**: Arcade's annotation system may not handle complex union types. Since MCP clients typically send strings (comma-separated for lists), accepting `str | None` and calling `ensure_list(value, split_strings=True)` is the safest approach.

## R9: PoC Tool Selection

**Decision**: PoC deploys 5 tools: `article_searcher`, `article_getter`, `czechmed_search_medicine`, `think`, `get_performance_metrics`.

**Rationale**:
- `article_searcher` — complex params (lists, booleans, pagination), tests PubMed API
- `article_getter` — simple fetch, validates basic connectivity
- `czechmed_search_medicine` — Czech tool, tests diskcache behavior on Arcade Cloud
- `think` — dict→str serialization edge case
- `get_performance_metrics` — minimal params, health-check tool
