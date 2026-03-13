# Research: CzechMedMCP Implementation

**Branch**: `001-czechmedmcp-implementation` | **Date**: 2026-03-02 | **Spec**: [spec.md](spec.md)

## R1: Current Tool Inventory (14/23)

**Decision**: 14 Czech tools already implemented, 9 new needed + renaming all to `czechmed_` prefix.

**Rationale**: Existing tools cover basic search/getter for all 5 modules but lack batch operations, reimbursement calculations, pharmacy search, epidemiological stats, codebooks, and all 3 workflow orchestrations.

**Current → Target Name Mapping:**

| # | Current Name | Target Name | Status |
|---|-------------|-------------|--------|
| 1 | `sukl_drug_searcher` | `czechmed_search_drug` | RENAME |
| 2 | `sukl_drug_getter` | `czechmed_get_drug_detail` | RENAME |
| 3 | `sukl_spc_getter` | `czechmed_get_spc` | RENAME + ENHANCE |
| 4 | `sukl_pil_getter` | `czechmed_get_pil` | RENAME + ENHANCE |
| 5 | `sukl_availability_checker` | `czechmed_check_availability` | RENAME |
| 6 | `mkn_diagnosis_searcher` | `czechmed_search_diagnosis` | RENAME |
| 7 | `mkn_diagnosis_getter` | `czechmed_get_diagnosis_detail` | RENAME |
| 8 | `mkn_category_browser` | `czechmed_browse_classification` | RENAME |
| 9 | `nrpzs_provider_searcher` | `czechmed_search_provider` | RENAME |
| 10 | `nrpzs_provider_getter` | `czechmed_get_provider_detail` | RENAME |
| 11 | `szv_procedure_searcher` | `czechmed_search_procedure` | RENAME |
| 12 | `szv_procedure_getter` | `czechmed_get_procedure_detail` | RENAME |
| 13 | `vzp_codebook_searcher` | `czechmed_get_vzp_reimbursement` | RENAME + REPURPOSE |
| 14 | `vzp_codebook_getter` | `czechmed_compare_alternatives` | RENAME + REPURPOSE |
| 15 | — | `czechmed_batch_check_availability` | NEW |
| 16 | — | `czechmed_get_reimbursement` | NEW |
| 17 | — | `czechmed_find_pharmacies` | NEW |
| 18 | — | `czechmed_get_diagnosis_stats` | NEW |
| 19 | — | `czechmed_get_codebooks` | NEW |
| 20 | — | `czechmed_calculate_reimbursement` | NEW |
| 21 | — | `czechmed_drug_profile` | NEW (workflow) |
| 22 | — | `czechmed_diagnosis_assistant` | NEW (workflow) |
| 23 | — | `czechmed_referral_assistant` | NEW (workflow) |

**Alternatives considered**: Keep existing names and add new ones with `czechmed_` prefix only → rejected because spec FR-024 mandates unified prefix for all Czech tools.

## R2: HTTP Client Pattern

**Decision**: New Czech tools use `httpx.AsyncClient` directly (same as existing Czech modules), not `request_api()`.

**Rationale**: All 14 existing Czech tools bypass the global `request_api()` pipeline and use `httpx.AsyncClient` directly. They share cache functions (`generate_cache_key`, `cache_response`, `get_cached_response`) from `http_client.py`. Changing this pattern would require rewriting all existing Czech modules.

**Pattern to follow:**
```python
async with httpx.AsyncClient(timeout=CZECH_HTTP_TIMEOUT) as client:
    resp = await client.get(url, params=params)
    resp.raise_for_status()
```

**Alternatives considered**: Migrate to `request_api()` for full resilience stack → rejected because it would change all existing modules and the Czech APIs have different retry/rate-limit needs.

## R3: Dual Output Strategy

**Decision**: Implement `format_czech_response(data, tool_name)` utility returning JSON with both `content` (Markdown) and `structuredContent` (JSON dict).

**Rationale**: Spec FR-025 requires all tools return dual output. Current tools return only JSON string. Need a thin wrapper without changing return type (still `str`).

**Output format:**
```json
{
  "content": "## Lék: Ibuprofen 400mg\n\n**SÚKL kód**: 0012345\n...",
  "structuredContent": {
    "type": "drug_detail",
    "sukl_code": "0012345",
    "name": "Ibuprofen 400mg",
    ...
  }
}
```

**Alternatives considered**: Return raw Pydantic `.model_dump()` → rejected because MCP spec expects `content` field for human-readable text.

## R4: Workflow Orchestration Pattern

**Decision**: Workflow tools use `asyncio.gather(*tasks, return_exceptions=True)` for parallel sub-tool calls with graceful degradation.

**Rationale**: Spec FR-021/022/023 require combining multiple data sources. `asyncio.gather` with `return_exceptions=True` allows partial results when some sources fail.

**Pattern:**
```python
async def _drug_profile(query: str) -> str:
    drug = await _sukl_drug_search(query, 1, 1)
    sukl_code = extract_code(drug)
    detail, avail, reimb, articles = await asyncio.gather(
        _sukl_drug_details(sukl_code),
        _sukl_availability_check(sukl_code),
        _get_reimbursement(sukl_code),
        _search_pubmed(query),
        return_exceptions=True,
    )
    return format_profile(detail, avail, reimb, articles)
```

**Alternatives considered**: Sequential calls → rejected for latency; separate orchestration layer → rejected for complexity.

## R5: PIL/SPC Content Strategy

**Decision**: Enhance PIL/SPC tools to scrape actual text content from SÚKL web, with section-based filtering.

**Rationale**: Current tools return only document URL metadata. Spec FR-006/007 require actual text content with section filtering (dosage, contraindications, etc.).

**Implementation**: Parse HTML from `sukl.cz` document pages. Map section names to HTML anchors/headings.

**Alternatives considered**: PDF extraction → rejected (complex, no reliable structure); keep URL-only → rejected (doesn't meet FR-006/007).

## R6: VZP Module Repurpose

**Decision**: Repurpose VZP module from generic codebook tools to drug-specific reimbursement tools.

**Rationale**: Current VZP tools (`vzp_codebook_searcher`/`getter`) work with procedure codebooks. Spec requires drug reimbursement (`czechmed_get_vzp_reimbursement`) and drug alternative comparison (`czechmed_compare_alternatives`). These are fundamentally different data sources (VZP drug price lists vs procedure codebooks).

**Implementation**: Add VZP drug price list scraping alongside existing procedure codebook functionality.

**Alternatives considered**: Keep current codebook tools + add new drug tools → rejected because current codebook tools overlap with SZV procedure tools and don't match spec scope.

## R7: NRPZS Codebook Tool

**Decision**: Extract unique values from NRPZS CSV columns for codebook endpoint.

**Rationale**: FR-015 requires codebooks (specialties, care forms, care types). The NRPZS CSV already contains these values. No separate API endpoint needed.

**Implementation**: Parse unique sorted values from `ZZ_obor_pece`, `ZZ_forma_pece`, `ZZ_druh_pece` columns.

## R8: SZV Reimbursement Calculation

**Decision**: Implement point-to-CZK calculation using per-insurer rate tables.

**Rationale**: FR-018 requires CZK reimbursement by insurance company. Current SZV returns point_value only. Need rate table: VZP 1.15 CZK/bod, VoZP 1.10, ČPZP 1.12, etc.

**Implementation**: Hardcoded rate table (updated annually) with calculation: `reimbursement_czk = point_value * rate_per_point * count`.

## R9: Epidemiological Statistics

**Decision**: Download and parse NZIP open data CSV for diagnosis statistics.

**Rationale**: FR-012 requires case counts by gender, age, regions from NZIP data. NZIP publishes open data CSV at `nzip.cz`.

**Implementation**: New `stats.py` in `mkn/` module, loading CSV with TTL 7 days, filtering by MKN-10 code and year.

## R10: Code Quality Fixes

**Decision**: Fix known bugs during implementation.

**Issues to fix:**
1. NRPZS pagination: `(page - 1) * page_size` → `compute_skip(page, page_size)`
2. SZV timeout: hardcoded `60.0` → `CZECH_HTTP_TIMEOUT`
3. VZP timeout: hardcoded `60.0` → `CZECH_HTTP_TIMEOUT`
4. MKN-10 search: loose substring matching → proper trigram scoring
5. Pydantic model placeholders: populate `includes`/`excludes` in MKN-10
