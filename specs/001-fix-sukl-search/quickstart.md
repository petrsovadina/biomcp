# Quickstart: Fix SUKL Drug Search

## Problem

`czechmed_search_medicine` fetches all 68,082 drug details from SUKL API on every search. This takes 5+ minutes and makes 3 tools unusable.

## Solution

Build a lazy-loaded in-memory drug index (~14 MB) from cached drug details, refreshed daily.

## Files to Modify

1. **New**: `src/biomcp/czech/sukl/drug_index.py` — DrugIndex singleton with lazy init + search
2. **Modify**: `src/biomcp/czech/sukl/search.py` — Replace `_sukl_drug_search()` to use index
3. **Modify**: `src/biomcp/czech/sukl/search.py` — Update `_find_pharmacies()` error handling
4. **New**: `tests/tdd/czech/test_drug_index.py` — Unit tests for index build + search
5. **Modify**: `tests/czech/test_sukl_search.py` — Update mocks for new search flow

## Implementation Steps

1. Create `drug_index.py` with `DrugIndex` class and `get_drug_index()` singleton
2. Implement index builder: fetch codes → fetch cached details → build searchable list
3. Implement `search_index()`: normalize query → substring match on name/ATC/supplement
4. Replace `_sukl_drug_search()` to use `get_drug_index()` + `search_index()`
5. Update `_find_pharmacies()` to handle 504 gracefully
6. Update unit tests
7. Run live validation

## Verification

```bash
# Unit tests
uv run python -m pytest tests/tdd/ tests/czech/ -x -q

# Live test
uv run python -c "
import asyncio
from biomcp.core import mcp_app
async def test():
    r = await mcp_app.call_tool('czechmed_search_medicine', {'query': 'ibuprofen'})
    print(str(r)[:500])
asyncio.run(test())
"
```
