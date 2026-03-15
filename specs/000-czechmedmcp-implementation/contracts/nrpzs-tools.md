# NRPZS Tool Contracts

## Existing Tools (rename only)

### czechmed_search_providers (was: nrpzs_provider_searcher → v2.1 plural rename)

```python
@mcp_app.tool()
async def czechmed_search_providers(
    query: Annotated[str | None, Field(description="Provider or facility name")] = None,
    city: Annotated[str | None, Field(description="City name")] = None,
    specialty: Annotated[str | None, Field(description="Medical specialty")] = None,
    care_form: Annotated[str | None, Field(description="Form of care")] = None,
    care_type: Annotated[str | None, Field(description="Type of care")] = None,
    page: Annotated[int, Field(description="Page number", ge=1)] = 1,
    page_size: Annotated[int, Field(description="Results per page", ge=1, le=100)] = 10,
) -> str:
    """Search Czech healthcare providers (NRPZS). Filter by city, specialty, care form/type."""
```

### czechmed_get_provider_detail (was: nrpzs_provider_getter)

```python
@mcp_app.tool()
async def czechmed_get_provider_detail(
    ico: Annotated[str, Field(description="8-digit provider ICO", pattern=r"^\d{8}$")],
) -> str:
    """Get complete provider profile including all workplaces and departments."""
```

## New Tools

### czechmed_get_nrpzs_codebooks (was: czechmed_get_codebooks → v2.1 rename)

```python
@mcp_app.tool()
async def czechmed_get_nrpzs_codebooks(
    codebook_type: Annotated[str, Field(
        description="Codebook type: specialties, care_forms, or care_types"
    )],
) -> str:
    """Get NRPZS reference codebook — list of specialties, care forms, or care types with codes and names."""
```

**Response schema:**
```json
{
  "content": "## Číselník: Odbornosti\n\n| Kód | Název |\n|-----|-------|\n| 001 | Vnitřní lékařství |\n...",
  "structuredContent": {
    "codebook_type": "specialties",
    "items": [
      {"code": "001", "name": "Vnitřní lékařství"},
      {"code": "002", "name": "Kardiologie"}
    ],
    "total": 95
  }
}
```

**Implementation**: Extract unique values from NRPZS CSV columns `ZZ_obor_pece`, `ZZ_forma_pece`, `ZZ_druh_pece`.
