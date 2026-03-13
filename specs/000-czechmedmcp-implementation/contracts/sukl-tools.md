# SÚKL Tool Contracts

## Existing Tools (rename only)

### czechmed_search_drug (was: sukl_drug_searcher)

```python
@mcp_app.tool()
async def czechmed_search_drug(
    query: Annotated[str, Field(description="Drug name, active substance, SUKL code, or ATC code")],
    page: Annotated[int, Field(description="Page number (1-based)", ge=1)] = 1,
    page_size: Annotated[int, Field(description="Results per page", ge=1, le=100)] = 10,
) -> str:
    """Search Czech drug registry (SUKL). Supports diacritics-insensitive search."""
```

### czechmed_get_drug_detail (was: sukl_drug_getter)

```python
@mcp_app.tool()
async def czechmed_get_drug_detail(
    sukl_code: Annotated[str, Field(description="7-digit SUKL code", pattern=r"^\d{7}$")],
) -> str:
    """Get complete drug details from SUKL registry by SUKL code."""
```

### czechmed_check_availability (was: sukl_availability_checker)

```python
@mcp_app.tool()
async def czechmed_check_availability(
    sukl_code: Annotated[str, Field(description="7-digit SUKL code", pattern=r"^\d{7}$")],
) -> str:
    """Check real-time market availability of a drug from SUKL distribution data."""
```

### czechmed_get_pil (was: sukl_pil_getter) — ENHANCED

```python
@mcp_app.tool()
async def czechmed_get_pil(
    sukl_code: Annotated[str, Field(description="7-digit SUKL code", pattern=r"^\d{7}$")],
    section: Annotated[str | None, Field(
        description="Optional section: dosage, contraindications, side_effects, interactions, pregnancy, storage"
    )] = None,
) -> str:
    """Get Patient Information Leaflet (PIL) content. Optionally filter by section."""
```

### czechmed_get_spc (was: sukl_spc_getter) — ENHANCED

```python
@mcp_app.tool()
async def czechmed_get_spc(
    sukl_code: Annotated[str, Field(description="7-digit SUKL code", pattern=r"^\d{7}$")],
    section: Annotated[str | None, Field(
        description="Optional SPC section number (e.g., 4.1-4.9, 5.1-5.3, 6.1-6.6)"
    )] = None,
) -> str:
    """Get Summary of Product Characteristics (SPC) content. Optionally filter by section."""
```

## New Tools

### czechmed_batch_check_availability

```python
@mcp_app.tool()
async def czechmed_batch_check_availability(
    sukl_codes: Annotated[list[str], Field(
        description="List of 7-digit SUKL codes (1-50)",
        min_length=1,
        max_length=50,
    )],
) -> str:
    """Batch check market availability for multiple drugs in parallel."""
```

**Response schema:**
```json
{
  "content": "## Batch Availability Check\n...",
  "structuredContent": {
    "total_checked": 5,
    "available_count": 3,
    "shortage_count": 1,
    "error_count": 1,
    "items": [
      {"sukl_code": "0012345", "name": "...", "status": "available"},
      {"sukl_code": "0012346", "status": "shortage", "last_delivery": "2026-01-15"}
    ],
    "checked_at": "2026-03-02T10:30:00Z"
  }
}
```

### czechmed_get_reimbursement

```python
@mcp_app.tool()
async def czechmed_get_reimbursement(
    sukl_code: Annotated[str, Field(description="7-digit SUKL code", pattern=r"^\d{7}$")],
) -> str:
    """Get reimbursement details for a drug — manufacturer price, retail price, insurance coverage, patient copay."""
```

**Response schema:**
```json
{
  "content": "## Úhrada: Ibuprofen 400mg\n\n**Cena výrobce**: 45.20 CZK\n...",
  "structuredContent": {
    "sukl_code": "0012345",
    "name": "Ibuprofen 400mg",
    "manufacturer_price": 45.20,
    "max_retail_price": 89.50,
    "reimbursement_amount": 67.00,
    "patient_copay": 22.50,
    "reimbursement_group": "P/72/1"
  }
}
```

### czechmed_find_pharmacies

```python
@mcp_app.tool()
async def czechmed_find_pharmacies(
    city: Annotated[str | None, Field(description="City name")] = None,
    postal_code: Annotated[str | None, Field(description="5-digit postal code", pattern=r"^\d{5}$")] = None,
    nonstop_only: Annotated[bool, Field(description="Filter 24/7 pharmacies only")] = False,
    page: Annotated[int, Field(description="Page number", ge=1)] = 1,
    page_size: Annotated[int, Field(description="Results per page", ge=1, le=100)] = 10,
) -> str:
    """Find pharmacies by city, postal code, or 24/7 filter. At least city or postal_code required."""
```
