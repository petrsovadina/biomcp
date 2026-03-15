# Implementation Plan: Fix SUKL Drug Search Performance

**Branch**: `001-fix-sukl-search` | **Date**: 2026-03-10 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-fix-sukl-search/spec.md`

## Summary

The SUKL drug search (`czechmed_search_medicine`) currently fetches all 68,082 drug details from the SUKL API on every query, causing timeouts and blocking 3 tools. The fix builds a lazy-loaded in-memory drug index (~14 MB) from cached drug details, refreshed daily (CACHE_TTL_DAY). This follows the same pattern as MKN-10 and SZV in-memory indices already in the codebase.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: httpx (async HTTP), diskcache (caching), Pydantic v2 (models)
**Storage**: diskcache/SQLite (`~/.cache/biomcp/http_cache`) for HTTP cache; in-memory for drug index
**Testing**: pytest with pytest-xdist, asyncio_mode=auto
**Target Platform**: MCP server (STDIO/SSE/Streamable HTTP)
**Project Type**: Library / MCP server
**Performance Goals**: Search < 10s, compare_alternatives < 15s, drug_profile < 20s
**Constraints**: Cold start index build ~60s (one-time), ~14 MB memory for index
**Scale/Scope**: 68,082 drugs, single-user MCP server

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | PASS | Tools remain MCP-compliant, no interface changes |
| II. Modular Domain Architecture | PASS | Changes isolated to `czech/sukl/` module, new file follows domain pattern |
| III. Authoritative Data Sources | PASS | Still uses SUKL DLP API as sole data source; pharmacy 504 documented |
| IV. CLI & MCP Dual Access | PASS | CLI uses same underlying functions, no changes needed |
| V. Testing Rigor | PASS | Unit tests with mocked HTTP, integration tests with @pytest.mark.integration |
| ensure_ascii=False | PASS | No JSON serialization changes |

**Post-Phase 1 re-check**: All gates still pass. No new dependencies, no cross-module imports, no fabricated data.

## Project Structure

### Documentation (this feature)

```text
specs/001-fix-sukl-search/
├── plan.md              # This file
├── research.md          # Phase 0 output — SUKL API research
├── data-model.md        # Phase 1 output — DrugIndex entity design
├── quickstart.md        # Phase 1 output — implementation guide
├── contracts/           # Phase 1 output — tool contracts
│   └── tool-contracts.md
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
src/czechmedmcp/czech/sukl/
├── client.py            # Existing — SUKL API client (no changes)
├── search.py            # MODIFY — replace _sukl_drug_search() to use index
├── drug_index.py        # NEW — DrugIndex singleton, builder, search
├── getter.py            # Existing — detail fetcher (no changes)
├── availability.py      # Existing — no changes
├── reimbursement.py     # Existing — no changes
└── models.py            # Existing — may add DrugIndexEntry if needed

tests/
├── czech/
│   ├── test_sukl_search.py     # MODIFY — update mocks for new flow
│   └── test_drug_index.py      # NEW — unit tests for index
└── czech_integration/
    └── test_sukl_api.py         # Existing — add search integration test
```

**Structure Decision**: Single project, all changes in `src/czechmedmcp/czech/sukl/` following existing modular domain pattern. One new file (`drug_index.py`), one modified file (`search.py`), one new test file.
