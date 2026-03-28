# Implementation Plan: Fix Tool Quality — E2E Test Report Bugs

**Branch**: `013-fix-tool-quality` | **Date**: 2026-03-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-fix-tool-quality/spec.md`

## Summary

Oprava 27 bugu nalezených v kompletnim E2E testu CzechMed-MCP serveru (58/60 nástrojů otestováno). Celkové skóre 4.9/10 — cíl je zvýšit na 7+/10 opravou SUKL performance (cold start 68K requestů), search() query routingu, diagnosis_assist klinického rankingu, drug_getter name resolution, article preprint mergingu a dalších bugů v českých registrech a OpenFDA.

## Technical Context

**Language/Version**: Python 3.10+ (existující codebase)
**Primary Dependencies**: FastMCP, httpx, Pydantic v2, diskcache, asyncio
**Storage**: diskcache/SQLite (HTTP cache), in-memory (DrugIndex, MKN-10, SZV)
**Testing**: pytest (asyncio_mode=auto), ruff, mypy
**Target Platform**: MCP server (STDIO, HTTP, SSE)
**Project Type**: MCP server (bug-fix feature — no new tools)
**Performance Goals**: SUKL tools <10s response, search() returns relevant results
**Constraints**: Keep 60 tools registered, backward compatible, no architecture changes
**Scale/Scope**: 27 bugs across 11 source files, ~25 modified files total

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | PASS | No new tools — fixing existing 60 tools |
| II. Modular Domain Architecture | PASS | Changes stay within existing modules |
| III. Authoritative Data Sources | PASS | All data from SUKL, NRPZS, PubMed, ClinicalTrials.gov, OpenFDA |
| IV. CLI & MCP Dual Access | PASS | Fixes apply to both MCP and CLI paths |
| V. Testing Rigor | PASS | Unit tests added for each fix, mocked HTTP |
| ensure_ascii=False | PASS | No changes to serialization |
| Conventional commits | PASS | Will use fix: prefix |

No gate violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/013-fix-tool-quality/
├── plan.md              # This file
├── spec.md              # Feature specification (27 bugs, 7 user stories)
├── research.md          # Phase 0 output (root cause analysis)
├── quickstart.md        # Test/validation scenarios
├── tasks.md             # Task list (55 tasks, 10 phases)
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (modified files)

```text
src/czechmedmcp/
├── constants.py                    # T006: SUKL_TOOL_TIMEOUT constant
├── router.py                       # T016-T020: search() thinking-reminder, trial query, domain handlers
├── fetch_handlers.py               # T030: drug fetch name resolution
├── utils/
│   └── circuit_breaker.py          # T005: NEW — circuit breaker utility
├── czech/
│   ├── czech_tools.py              # T010-T013: SUKL timeout handling
│   ├── sukl/
│   │   ├── drug_index.py           # T008-T009: timeout + circuit breaker
│   │   └── getter.py               # T037-T038: PIL/SPC availability
│   ├── mkn/
│   │   ├── search.py               # T041, T045-T046: English names, synonyms, ranking
│   │   ├── stats.py                # T040: NZIP data source
│   │   └── synonyms.py            # T024, T044: NEW — Czech synonym dictionary
│   ├── nrpzs/
│   │   └── search.py               # T036: pharmacy query fix
│   ├── vzp/
│   │   └── search.py               # T039: reimbursement lookup
│   └── workflows/
│       └── diagnosis_assistant.py  # T023-T026: clinical ranking
├── drugs/
│   └── getter.py                   # T029: name resolution
├── integrations/
│   └── biothings_client.py         # T028: resolve_drug_name()
├── articles/
│   ├── search.py                   # T032-T033: preprint merging, page_size
│   ├── unified.py                  # Preprint+PubMed merge logic
│   └── fetch.py                    # T034: PubMed E-utilities fallback
├── openfda/
│   ├── drug_recalls.py             # T043: recall_number mapping
│   ├── drug_recalls_helpers.py     # T043: recall search params
│   └── device_events.py            # T047: device name filtering
├── trials/
│   └── search.py                   # T017: query.term passthrough
└── arcade/
    ├── czech_tools.py              # T015: Arcade SUKL timeout
    └── individual_tools.py         # T022, T054: Arcade search/drug wrappers

tests/
├── tdd/
│   ├── test_circuit_breaker.py     # T007: NEW
│   ├── test_sukl_timeout.py        # T014: NEW
│   ├── test_router_fixes.py        # T021: NEW
│   ├── test_diagnosis_assist_quality.py  # T027: NEW
│   ├── test_drug_name_resolution.py      # T031: NEW
│   ├── test_article_fixes.py       # T035: NEW
│   └── test_minor_fixes.py         # T049: NEW
└── czech/
    └── test_registry_fixes.py      # T042: NEW
```

**Structure Decision**: Existing project structure preserved. 1 new utility file (`circuit_breaker.py`), 1 new data file (`synonyms.py`), 8 new test files. All other changes are modifications to existing files.

## Research Findings Summary

### Root Cause: SUKL Cold Start (BUG-3, BUG-4, BUG-5, BUG-7)

**Problem**: DrugIndex cold start makes ~68,001 HTTP requests (1 list + 68K detail fetches) with semaphore(20). This takes 4-14 minutes.

**Solution**: Cannot skip full index build (DrugIndex.ensure_built() is mandatory). Instead:
1. Add `asyncio.wait_for(10s)` timeout wrapper around search calls
2. Return "Index building, try again in ~2 minutes" message
3. Add circuit breaker for SUKL API failures
4. Index is cached to disk after first build — subsequent starts load in ~1s

### Root Cause: Trial Search Query (BUG-1)

**Problem**: ClinicalTrials.gov API at `https://clinicaltrials.gov/api/v2/studies` uses `query.cond`, `query.term`, `query.intr` parameters. Router.py's trial handler may not pass `query.term` when user provides free-text query through unified search().

**Solution**: Ensure unified search() passes query as `query.term` to trial search handler.

### Root Cause: Article Preprints (BUG-14)

**Problem**: Actually NOT a replacement — `unified.py` already runs PubMed and preprints in parallel. The issue may be in deduplication (DOI-based) or result ordering. Fetch multiplier 3x applied for deduplication.

**Solution**: Verify dedup logic doesn't incorrectly remove PubMed results. Check if PubMed results are properly returned before preprints.

### Root Cause: Article Getter Placeholder (BUG-15)

**Problem**: PubTator3 `Article.abstract` computed field returns `f"Article: {self.pmid}"` when no abstract passages exist. Europe PMC fallback exists but may also fail.

**Solution**: Add PubMed E-utilities fallback as third option after PubTator3 and Europe PMC.

### Root Cause: Drug Getter Name (BUG-8)

**Problem**: `biothings_client.py` already has `_query_drug()` for name-based search at `mychem.info/v1/query`. It already routes "metformin" to name search. Issue is in hit scoring/relevance threshold filtering (lines 451-471).

**Solution**: Lower relevance threshold or adjust scoring to accept common drug names.

### Root Cause: Pharmacies (BUG-12)

**Problem**: NRPZS uses CSV download from UZIS, not API. Pharmacy filtering depends on `ZZ_obec` column matching. "Brno" may not match actual values in CSV (could be "Brno-město" or similar).

**Solution**: Check actual CSV values, adjust matching to handle city variants (substring match + normalization).

### Root Cause: NZIP Stats (BUG-17)

**Problem**: URL `https://reporting.uzis.cz/cr/data/hospitalizace_{year}.csv`. Local fallback exists with ±5 year search. Bundled data in `data/` directory.

**Solution**: Verify remote URL accessibility. If down, ensure bundled 2024 CSV exists as fallback.

### Root Cause: Recall Getter (BUG-16)

**Problem**: `get_drug_recall()` already uses `recall_number:"{value}"` exact match. Bug may be in how the recall number format is normalized or in API response parsing.

**Solution**: Debug actual API response for "D-0328-2025" — may need format normalization.

## Implementation Approach

### Per User Story

| US | Approach | Key Files | Complexity |
|----|----------|-----------|------------|
| US1 SUKL | Timeout wrappers + circuit breaker | drug_index.py, czech_tools.py | Medium |
| US2 Search | Fix query routing + remove thinking-reminder | router.py, trials/search.py | Medium |
| US3 Diagnosis | Symptom mapping + post-filter | diagnosis_assistant.py, synonyms.py | High |
| US4 Drug | Adjust relevance threshold | biothings_client.py | Low |
| US5 Articles | Fix dedup + add E-utilities fallback | unified.py, fetch.py | Medium |
| US6 Czech | Fix CSV matching + NZIP URL + PIL/SPC | nrpzs/search.py, stats.py, getter.py | Medium |
| US7 Minor | Recall mapping + synonyms + ranking | drug_recalls.py, mkn/search.py | Low |

### Risk Mitigations

1. **SUKL index can't be faster**: Mitigated by timeout + user message + disk cache
2. **NRPZS CSV format unknown**: Research in T003 will reveal actual column values
3. **Drug name scoring too strict**: Can be tuned iteratively with test cases
4. **Diagnosis assist needs clinical expertise**: Use explicit symptom-to-ICD mappings for top 20 conditions
