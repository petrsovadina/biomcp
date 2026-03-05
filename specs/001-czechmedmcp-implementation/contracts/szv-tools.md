# SZV Tool Contracts

## Existing Tools (rename only)

### czechmed_search_procedure (was: szv_procedure_searcher)

```python
@mcp_app.tool()
async def czechmed_search_procedure(
    query: Annotated[str, Field(description="Procedure code or name")],
    specialty: Annotated[str | None, Field(description="Filter by specialty code")] = None,
    max_results: Annotated[int, Field(description="Maximum results", ge=1, le=100)] = 10,
) -> str:
    """Search health procedures (SZV). Offline data, <100ms response. Supports Czech diacritics."""
```

### czechmed_get_procedure_detail (was: szv_procedure_getter)

```python
@mcp_app.tool()
async def czechmed_get_procedure_detail(
    code: Annotated[str, Field(description="5-digit procedure code", pattern=r"^\d{5}$")],
) -> str:
    """Get complete procedure details including billing conditions, combinations, and point history."""
```

## New Tools

### czechmed_calculate_reimbursement

```python
@mcp_app.tool()
async def czechmed_calculate_reimbursement(
    procedure_code: Annotated[str, Field(description="5-digit procedure code", pattern=r"^\d{5}$")],
    insurance_code: Annotated[str, Field(
        description="Insurance company code: 111 (VZP), 201 (VoZP), 205 (ČPZP), 207 (OZP), 209 (ZPŠ), 211 (ZPMV), 213 (RBP)",
        pattern=r"^\d{3}$",
    )] = "111",
    count: Annotated[int, Field(description="Number of procedures", ge=1)] = 1,
) -> str:
    """Calculate CZK reimbursement for a procedure by insurance company. Default: VZP (111)."""
```

**Response schema:**
```json
{
  "content": "## Kalkulace: 09543 — Vyšetření EKG\n\n**Body**: 350\n**Pojišťovna**: VZP (111)\n**Sazba**: 1.15 CZK/bod\n**Cena za výkon**: 402.50 CZK\n**Celkem (2×)**: 805.00 CZK\n",
  "structuredContent": {
    "procedure_code": "09543",
    "procedure_name": "Vyšetření EKG",
    "point_value": 350,
    "insurance_code": "111",
    "insurance_name": "VZP",
    "rate_per_point": 1.15,
    "count": 2,
    "unit_price_czk": 402.50,
    "total_czk": 805.00,
    "patient_copay_czk": 0.0
  }
}
```

**Rate table** (hardcoded, updated annually):

| Code | Name | Rate (CZK/bod) |
|------|------|----------------|
| 111 | VZP | 1.15 |
| 201 | VoZP | 1.10 |
| 205 | ČPZP | 1.12 |
| 207 | OZP | 1.11 |
| 209 | ZPŠ | 1.09 |
| 211 | ZPMV | 1.13 |
| 213 | RBP | 1.08 |
