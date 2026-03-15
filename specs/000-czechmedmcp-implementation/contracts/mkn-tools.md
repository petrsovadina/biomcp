# MKN-10 Tool Contracts

## Existing Tools (rename only)

### czechmed_search_diagnosis (was: mkn_diagnosis_searcher)

```python
@mcp_app.tool()
async def czechmed_search_diagnosis(
    query: Annotated[str, Field(description="Symptom description or MKN-10 code in Czech")],
    max_results: Annotated[int, Field(description="Maximum results", ge=1, le=50)] = 10,
) -> str:
    """Search MKN-10 diagnosis classification. Supports Czech diacritics and trigram matching."""
```

### czechmed_get_diagnosis_detail (was: mkn_diagnosis_getter)

```python
@mcp_app.tool()
async def czechmed_get_diagnosis_detail(
    code: Annotated[str, Field(description="MKN-10 code (e.g., J06, J06.9)", pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$")],
) -> str:
    """Get complete diagnosis details including hierarchy, inclusions, and exclusions."""
```

### czechmed_browse_diagnosis (was: mkn_category_browser → czechmed_browse_classification → v2.1 rename)

```python
@mcp_app.tool()
async def czechmed_browse_diagnosis(
    code: Annotated[str | None, Field(description="Parent code or None for root chapters")] = None,
) -> str:
    """Browse MKN-10 classification hierarchy. Returns children of given code or root chapters."""
```

## New Tools

### czechmed_get_diagnosis_stats

```python
@mcp_app.tool()
async def czechmed_get_diagnosis_stats(
    code: Annotated[str, Field(description="MKN-10 code", pattern=r"^[A-Z]\d{2}(\.\d{1,2})?$")],
    year: Annotated[int | None, Field(description="Year (2015-2025)", ge=2015, le=2025)] = None,
) -> str:
    """Get epidemiological statistics for a diagnosis from NZIP open data — case counts, gender, age, region distribution."""
```

**Response schema:**
```json
{
  "content": "## Statistika: J06 — Akutní infekce horních cest dýchacích\n\n**Rok**: 2024\n**Celkem případů**: 234,567\n...",
  "structuredContent": {
    "code": "J06",
    "name_cs": "Akutní infekce horních cest dýchacích, mnohočetná a NS",
    "year": 2024,
    "total_cases": 234567,
    "male_count": 112345,
    "female_count": 122222,
    "age_distribution": [
      {"age_group": "0-14", "count": 89000},
      {"age_group": "15-24", "count": 45000}
    ],
    "region_distribution": [
      {"region": "Praha", "count": 45000},
      {"region": "Brno", "count": 23000}
    ]
  }
}
```

**Data source**: NZIP Open Data CSV (`nzip.cz`)
**Cache TTL**: 7 days (CACHE_TTL_MONTH / 4)
