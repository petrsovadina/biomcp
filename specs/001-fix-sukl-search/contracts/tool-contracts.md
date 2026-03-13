# Tool Contracts: SUKL Search Fix

## czechmed_search_medicine (modified)

**Input** (unchanged):
```json
{
  "query": "string (drug name, substance, or ATC code)",
  "page": "int (default 1)",
  "page_size": "int (default 10, max 100)"
}
```

**Output** (unchanged):
```json
{
  "total": 42,
  "page": 1,
  "page_size": 10,
  "results": [
    {
      "sukl_code": "0029216",
      "name": "CELSENTRI",
      "strength": "150MG",
      "atc_code": "J05AX09",
      "pharmaceutical_form": "TBL FLM"
    }
  ]
}
```

**Performance contract**: Response within 10 seconds (cold start may take up to 60 seconds for first-ever query while index builds).

**Error contract**:
```json
{
  "total": 0,
  "page": 1,
  "page_size": 10,
  "results": [],
  "error": "SUKL API unavailable: <message>"
}
```

## czechmed_compare_alternatives (modified behavior)

**Input** (unchanged):
```json
{
  "sukl_code": "string (7-digit SUKL code)"
}
```

**Performance contract**: Response within 15 seconds.

## czechmed_drug_profile (modified behavior)

**Input** (unchanged):
```json
{
  "query": "string (drug name or SUKL code)"
}
```

**Performance contract**: Response within 20 seconds.

## czechmed_find_pharmacies (updated error handling)

**Input** (unchanged):
```json
{
  "city": "string (optional)",
  "postal_code": "string (optional)",
  "nonstop_only": "bool (default false)",
  "page": "int (default 1)",
  "page_size": "int (default 10)"
}
```

**New error response** (if API non-functional):
```json
{
  "content": "## Lékárny\n\n*SUKL API pro lékárny je momentálně nedostupné.*",
  "structured": {
    "error": "SUKL pharmacy API is currently unavailable (504)",
    "note": "This endpoint has been non-functional since 2026-03."
  }
}
```

## Internal: DrugIndex API (new)

```python
# src/biomcp/czech/sukl/drug_index.py

async def get_drug_index() -> DrugIndex:
    """Get or build the drug index singleton."""

def search_index(
    index: DrugIndex,
    query: str,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[DrugIndexEntry], int]:
    """Search index, return (page_results, total_matches)."""
```
