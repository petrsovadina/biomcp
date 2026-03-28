# Research: Root Cause Analysis — 18 MCP Tool Bugs

**Feature**: 012-fix-mcp-tool-bugs
**Date**: 2026-03-27

## Findings Summary

| Bug | Root Cause | Fix Category |
|-----|-----------|--------------|
| BUG-001 SearchMedicine | DrugIndex cold start timeout (~10 min), no persistent cache | Timeout + caching |
| BUG-002 NRPZS (5 tools) | CSV download timeout (30s for ~50MB file from ÚZIS) | Timeout + retry |
| BUG-003 SZV (3 tools) | Excel download timeout (30s from szv.mzcr.cz) | Timeout + retry |
| BUG-004 PIL/SmPC | DLP API returns empty metadata, no fallback URL | Add fallback URL |
| BUG-005 DrugProfile/CompareAlternatives | Cascading failure from BUG-001 + BUG-010 | Fix dependencies |
| BUG-006 ArticleSearcher | PubTator3 autocomplete failure kills entire search | Graceful degradation |
| BUG-007 SUKL code normalization | No zero-padding for codes < 7 digits | Input sanitization |
| BUG-008 DiagnosisStats | NZIP endpoint returns empty data | Debug endpoint |
| BUG-009 DiagnosisAssist | FAISS/embedding pipeline initialization failure | Debug init + fallback |
| BUG-010 Reimbursement | opendata.sukl.cz returns empty, VZP CSV stale | Debug + update data |
| BUG-011 OpenFDA Recall | Query parameter construction error | Debug query format |
| BUG-012 Substance names | substance_code without human-readable mapping | Add resolver |
| BUG-013 Error format | Ad-hoc error formats per tool | Centralize utility |
| BUG-014 SearchDiagnosis text | MKN-10 fulltext search returns irrelevant results | Fix search logic |
| BUG-015 GetPerformanceMetrics | @track_performance not collecting data | Debug decorator |
| BUG-016 ArticleGetter abstract | PubMed abstract fetch returns placeholder | Debug fetch logic |
| BUG-017 DrugGetter metformin | MyChem.info name normalization missing | Add normalization |
| BUG-018 GeneGetter verbosity | RefSeq IDs not filtered | Add field filter |

## Detailed Analysis

### Pattern A: Timeout/Download Failures (BUG-001, 002, 003)

All three share the same pattern: lazy-loaded data from external source with `CZECH_HTTP_TIMEOUT = 30.0s` which is insufficient for large datasets.

**NRPZS**: Downloads ~50MB CSV from ÚZIS at `datanzis.uzis.gov.cz`. File: `czech/nrpzs/search.py`, function `_download_csv()`. Uses `httpx.AsyncClient(timeout=CZECH_HTTP_TIMEOUT)`.

**SZV**: Downloads Excel from `szv.mzcr.cz/Vykon/Export/`. File: `czech/szv/search.py`, function `_download_excel()`. Same timeout.

**SUKL DrugIndex**: Fetches ~68K drug codes, then individual details with semaphore=20. File: `czech/sukl/drug_index.py`, class `DrugIndex`. Cold start ~10 min.

**Solution pattern**: Increase timeout for bulk downloads to 120s. Add 3x retry with exponential backoff. Persistent diskcache for SUKL DrugIndex.

### Pattern B: Empty Data Structures (BUG-008, 009, 010)

Tools return correct JSON structure but all fields are null/empty/0.

**DiagnosisStats**: Calls NZIP API, gets 0 cases. The API endpoint likely changed or requires different parameters.

**DiagnosisAssist**: FAISS index not populated. Requires Cohere embeddings — if no API key, index stays empty.

**Reimbursement**: opendata.sukl.cz may be down or endpoint changed.

### Pattern C: Missing Fallback (BUG-004, 006)

**PIL/SmPC**: DLP API metadata endpoint returns empty for many drugs. Documents exist on SUKL web but URLs aren't constructed as fallback.

**ArticleSearcher**: PubTator3 autocomplete failure kills entire search chain. No fallback to direct PubMed search.

### Pattern D: Input Normalization (BUG-007, 012, 017)

Simple input sanitization issues. Fix location: centralized utility functions.

## Technology Decisions

| Decision | Rationale | Alternatives Rejected |
|----------|-----------|----------------------|
| Fix existing implementations (not rewrite) | Pattern analysis shows config/timeout issues, not architectural flaws | Full rewrite — too risky, too slow |
| SUKL DLP API for PIL/SmPC + fallback URL | Extends existing API integration | Web scraping (fragile), emc.europa.eu (different data) |
| Persistent diskcache for DrugIndex | Eliminates 10-min cold start | In-memory only (current, causes timeout), pre-built index in repo (stale) |
| PubMed E-utilities as ArticleSearcher fallback | Public, stable, no auth needed | PubTator3-only (current, fragile) |
| 3 fáze delivery (P1→P2→P3 commits) | Incremental testing, reduced regression risk | Single PR (too large for review) |
