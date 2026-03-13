# Quickstart: CzechMedMCP Implementation

**Branch**: `001-czechmedmcp-implementation` | **Date**: 2026-03-02

## Prerequisites

```bash
# Klonování a přepnutí na branch
git checkout 001-czechmedmcp-implementation

# Instalace dependencies
uv sync --all-extras && uv run pre-commit install

# Ověření aktuálního stavu (51 nástrojů)
uv run python -m pytest tests/tdd/test_mcp_integration.py -v
```

## Implementation Order

### 1. Foundation (Phase 1)

**Start here**: Přejmenování nástrojů a dual output utility.

```bash
# Soubory k editaci:
# src/biomcp/czech/czech_tools.py     — rename all 14 tools
# src/biomcp/czech/response.py        — NEW: format_czech_response()
# tests/czech/test_tool_registration.py — update expected names
# tests/tdd/test_mcp_integration.py    — update tool names in assertions

# Spuštění testů po renamu:
uv run python -m pytest tests/czech/ tests/tdd/test_mcp_integration.py -v
```

### 2. SÚKL Extensions (Phase 2)

```bash
# Nové soubory:
# src/biomcp/czech/sukl/reimbursement.py  — _get_reimbursement()
# Rozšířené soubory:
# src/biomcp/czech/sukl/search.py         — + _batch_availability()
# src/biomcp/czech/sukl/search.py         — + _find_pharmacies()
# src/biomcp/czech/sukl/getter.py         — enhance PIL/SPC
# src/biomcp/czech/sukl/models.py         — + new models
# src/biomcp/czech/czech_tools.py         — + 3 tool registrations

# Testy:
uv run python -m pytest tests/czech/test_sukl_batch.py tests/czech/test_sukl_reimbursement.py tests/czech/test_sukl_pharmacies.py -v
```

### 3. MKN + NRPZS + SZV (Phase 3)

```bash
# Nové soubory:
# src/biomcp/czech/mkn/stats.py           — _get_diagnosis_stats()
# src/biomcp/czech/szv/reimbursement.py   — _calculate_reimbursement()
# Rozšířené soubory:
# src/biomcp/czech/nrpzs/search.py        — + _get_codebooks()
# src/biomcp/czech/czech_tools.py         — + 3 tool registrations

# Testy:
uv run python -m pytest tests/czech/test_mkn_stats.py tests/czech/test_nrpzs_codebooks.py tests/czech/test_szv_reimbursement.py -v
```

### 4. VZP Drug Tools (Phase 4)

```bash
# Rozšířené soubory:
# src/biomcp/czech/vzp/search.py          — repurpose for drug reimbursement
# src/biomcp/czech/vzp/models.py          — + DrugReimbursement, DrugAlternative
# src/biomcp/czech/czech_tools.py         — update 2 tool registrations

# Testy:
uv run python -m pytest tests/czech/test_vzp_drug_reimb.py -v
```

### 5. Workflows (Phase 5)

```bash
# Nové soubory:
# src/biomcp/czech/workflows/__init__.py
# src/biomcp/czech/workflows/drug_profile.py
# src/biomcp/czech/workflows/diagnosis_assistant.py
# src/biomcp/czech/workflows/referral_assistant.py
# src/biomcp/czech/czech_tools.py         — + 3 workflow registrations

# Testy:
uv run python -m pytest tests/czech/test_workflow_drug.py tests/czech/test_workflow_diagnosis.py tests/czech/test_workflow_referral.py -v
```

### 6. Final Validation (Phase 6)

```bash
# Kompletní test suite
uv run python -m pytest -x --ff -n auto --dist loadscope

# Ověření 60 nástrojů (37 BioMCP + 23 Czech)
uv run python -m pytest tests/tdd/test_mcp_integration.py -v

# Ověření 23 českých nástrojů
uv run python -m pytest tests/czech/test_tool_registration.py -v

# Lint + types
uv run ruff check src tests
uv run mypy

# MCP Inspector — manuální test
make inspector
```

## Key Patterns to Follow

### Tool Registration

```python
# In czech_tools.py
from biomcp.core import mcp_app
from biomcp.metrics import track_performance

@mcp_app.tool()
@track_performance("czechmedmcp.tool_name")
async def czechmed_tool_name(
    param: Annotated[str, Field(description="...")],
) -> str:
    """Tool description."""
    return await _private_impl(param)
```

### Dual Output

```python
# In response.py
from biomcp.czech.response import format_czech_response

result = format_czech_response(
    data=model.model_dump(),
    tool_name="search_drug",
    markdown_template="## Výsledky vyhledávání\n..."
)
return result  # JSON string with content + structuredContent
```

### Cache Pattern

```python
from biomcp.http_client import (
    generate_cache_key, cache_response, get_cached_response
)
from biomcp.constants import CACHE_TTL_DAY, CZECH_HTTP_TIMEOUT

cache_key = generate_cache_key("GET", url, params)
cached = get_cached_response(cache_key)
if cached:
    return cached

async with httpx.AsyncClient(timeout=CZECH_HTTP_TIMEOUT) as client:
    resp = await client.get(url, params=params)
# ...
cache_response(cache_key, result, CACHE_TTL_DAY)
```

### Workflow Orchestration

```python
import asyncio

results = await asyncio.gather(
    _get_detail(code),
    _check_availability(code),
    _get_reimbursement(code),
    return_exceptions=True,
)

sections = []
for name, result in zip(["detail", "availability", "reimbursement"], results):
    if isinstance(result, Exception):
        sections.append({"section": name, "status": "error", "error": str(result)})
    else:
        sections.append({"section": name, "status": "ok", "data": result})
```

## Environment

```bash
# Žádné env variables povinné — všechny české API jsou veřejné
# Volitelné:
export BIOMCP_METRICS_ENABLED=true  # Performance tracking
export BIOMCP_OFFLINE=true          # Offline mode (cache only)
```
