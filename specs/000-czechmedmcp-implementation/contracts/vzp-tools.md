# VZP Tool Contracts

## Repurposed Tools

### czechmed_get_drug_reimbursement (was: vzp_codebook_searcher → czechmed_get_vzp_reimbursement → v2.1 rename)

```python
@mcp_app.tool()
async def czechmed_get_drug_reimbursement(
    sukl_code: Annotated[str, Field(description="7-digit SUKL code", pattern=r"^\d{7}$")],
) -> str:
    """Get VZP drug reimbursement details — group, max price, coverage, copay, prescription conditions."""
```

**Response schema:**
```json
{
  "content": "## VZP Úhrada: Ibuprofen 400mg\n\n**Úhradová skupina**: P/72/1\n**Max. cena**: 89.50 CZK\n**Úhrada**: 67.00 CZK\n**Doplatek**: 22.50 CZK\n**Podmínky**: Bez omezení\n",
  "structuredContent": {
    "sukl_code": "0012345",
    "name": "Ibuprofen 400mg",
    "reimbursement_group": "P/72/1",
    "max_price": 89.50,
    "reimbursement_amount": 67.00,
    "patient_copay": 22.50,
    "prescription_conditions": "Bez omezení",
    "valid_from": "2026-01-01"
  }
}
```

**Data source**: VZP drug price lists (web scraping `vzp.cz/poskytovatele`)
**Cache TTL**: 24 hours
**Risk**: HTML structure changes → ParseError with URL for manual access

### czechmed_compare_alternatives (was: vzp_codebook_getter — repurposed)

```python
@mcp_app.tool()
async def czechmed_compare_alternatives(
    sukl_code: Annotated[str, Field(description="7-digit SUKL code of reference drug", pattern=r"^\d{7}$")],
) -> str:
    """Compare drug price alternatives in same ATC group sorted by patient copay. Cross-module: SUKL + VZP data."""
```

**Response schema:**
```json
{
  "content": "## Cenové alternativy: Ibuprofen 400mg\n\n**ATC skupina**: M01AE01\n**Referenční doplatek**: 22.50 CZK\n\n| Přípravek | Doplatek | Úspora | Generikum | Dostupnost |\n|-----------|----------|--------|-----------|------------|\n| Ibalgin 400 | 15.00 CZK | 7.50 CZK | Ano | available |\n...",
  "structuredContent": {
    "reference_sukl_code": "0012345",
    "reference_name": "Ibuprofen 400mg",
    "reference_copay": 22.50,
    "atc_code": "M01AE01",
    "alternatives": [
      {
        "sukl_code": "0012346",
        "name": "Ibalgin 400",
        "patient_copay": 15.00,
        "savings_vs_reference": 7.50,
        "is_generic": true,
        "availability_status": "available"
      }
    ],
    "total_alternatives": 5
  }
}
```

**Implementation**:
1. Get reference drug detail from SÚKL → extract ATC code
2. Search SÚKL by ATC code → get all drugs in group
3. For each drug, get VZP reimbursement → extract copay
4. Sort by copay ascending, calculate savings vs reference
5. Optionally check availability for each alternative
