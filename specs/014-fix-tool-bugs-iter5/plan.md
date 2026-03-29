# Implementation Plan: Fix Tool Bugs Iteration 5

**Branch**: `014-fix-tool-bugs-iter5` | **Date**: 2026-03-29 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/014-fix-tool-bugs-iter5/spec.md`

## Summary

Bug fix sprint addressing 15 active bugs across 12 user stories (P0-P3). Primary focus: article_searcher latency regression (51s→<15s), SUKL cold-start elimination (10min→<2s), drug_profile server error, and 4 P1 data quality fixes. No new tools — tool count stays at 60.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastMCP, httpx, Pydantic v2, diskcache, asyncio
**Storage**: diskcache/SQLite (HTTP cache), in-memory LRU (MKN-10, SZV), SQLite (new: persistent SUKL DrugIndex)
**Testing**: pytest (asyncio_mode=auto), pytest-xdist (parallel)
**Target Platform**: Linux server (Railway), macOS (local dev)
**Project Type**: MCP server (library + CLI)
**Performance Goals**: article_searcher avg <15s P95 <30s; SUKL cold-start <2s; drug_getter <2s
**Constraints**: No new external dependencies; backward-compatible; tool count = 60
**Scale/Scope**: 15 bug fixes across 10 source files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | PASS | No new tools. Fixing existing MCP tools. |
| II. Modular Domain Architecture | PASS | All changes within existing module boundaries. No cross-domain imports added. |
| III. Authoritative Data Sources | PASS | No new data sources. Fixing integration with existing sources (PubMed E-utilities fallback for abstracts). |
| IV. CLI & MCP Dual Access | PASS | No CLI changes needed — fixes are at the domain layer, shared by both. |
| V. Testing Rigor | PASS | Regression test suite defined. Existing unit tests preserved. |
| Technical Constraints | PASS | Python 3.10+, httpx, Pydantic v2, ensure_ascii=False, ruff, mypy. |
| Development Workflow | PASS | Feature branch via speckit, conventional commits, PR to main. |

**Gate result**: ALL PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/014-fix-tool-bugs-iter5/
├── spec.md              # Feature specification (12 user stories, 18 FRs)
├── plan.md              # This file
├── research.md          # Phase 0 research (API investigation notes)
├── tasks.md             # 48 tasks across 15 phases
└── checklists/
    └── requirements.md  # Spec quality validation
```

### Source Code (changes only — existing structure)

```text
src/czechmedmcp/
├── constants.py                          # New timeout/cache constants (T001-T002)
├── articles/
│   ├── search.py                         # Latency fix, caching, page_size (T003-T008, T036)
│   ├── fetch.py                          # Abstract fallback via E-utilities (T023-T025)
│   ├── preprints.py                      # Preprints page_size propagation (T037)
│   └── unified.py                        # DOI dedup, result truncation (T018, T038)
├── czech/
│   ├── sukl/
│   │   ├── drug_index.py                 # Persistent SQLite index (T009-T012)
│   │   └── search.py                     # Pharmacy endpoint fix (T031-T032)
│   ├── diagnosis_embed/
│   │   └── searcher.py                   # Keyword→ICD-10 direct match (T027-T028)
│   ├── mkn/
│   │   └── synonyms.py                   # Extended diagnosis name map (T026)
│   ├── nrpzs/
│   │   └── search.py                     # Pharmacy API investigation (T030)
│   └── workflows/
│       └── drug_profile.py               # Server error fix (T013-T016)
├── drugs/
│   └── getter.py                         # Common name fallback (T021-T022)
├── integrations/
│   └── biothings_client.py               # MyChem.info name search (T020)
├── genes/
│   └── getter.py                         # Isoform truncation (T042-T043)
└── openfda/
    ├── drug_recalls.py                   # recall_number field fix (T033-T035)
    ├── drug_labels.py                    # Section validation (T040)
    └── drug_labels_helpers.py            # Valid sections set (T039)

tests/tdd/                                # Regression validation (T044, T046-T048)
src/czechmedmcp/arcade/                   # Arcade wrapper sync if needed (T045)
```

**Structure Decision**: All changes within existing module structure. No new modules or directories created. This follows Constitution Principle II (Modular Domain Architecture).

## Implementation Approach

### Phase Execution Order

```
Phase 1: Setup (T001-T002) ─────────────────────────────────────────┐
                                                                     │
Phase 2: Foundational — article latency (T003-T006) ────────────────┤
                                                                     │
Phase 3: US1 validate latency (T007-T008) ──────────────────────────┤
                                                                     │
     ┌── Phase 4: US2 SUKL cold-start (T009-T012) ──────────┐      │
     │                                                        │      │
     ├── Phase 5: US3 drug_profile (T013-T016) ──────────────┤      │
     │                                                        ├──────┤
     ├── Phase 7: US5 drug names (T020-T022) ────────────────┤      │
     │                                                        │      │
     ├── Phase 8: US6 article abstract (T023-T025) ──────────┤      │
     │                                                        │      │
     └── Phase 9: US7 diagnosis_assist (T026-T029) ──────────┘      │
                                                                     │
Phase 6: US4 preprints merge (T017-T019) — after Phase 2 ───────────┤
                                                                     │
Phase 12: US10 page_size (T036-T038) — after Phase 2 ───────────────┤
                                                                     │
     ┌── Phase 10: US8 pharmacies (T030-T032) ───────────────┐      │
     │                                                        │      │
     ├── Phase 11: US9 recall ID (T033-T035) ────────────────┤      │
     │                                                        ├──────┤
     ├── Phase 13: US11 label sections (T039-T041) ──────────┤      │
     │                                                        │      │
     └── Phase 14: US12 gene getter (T042-T043) ─────────────┘      │
                                                                     │
Phase 15: Polish & Regression (T044-T048) ──────────────────────────┘
```

### Key Design Decisions

1. **Article search caching**: In-memory LRU (not Redis) — no new infrastructure dependency. TTL 1h, max 500 entries. Hash of query parameters as key.

2. **SUKL persistent index**: SQLite file via diskcache (already a dependency). Load on startup, background refresh. Path: `~/.cache/czechmedmcp/sukl_index.db`.

3. **Drug name resolution**: MyChem.info query API (already used in biothings_client.py). Fallback chain: direct lookup → name search → return "Unknown" with suggestion.

4. **Abstract fallback**: PubMed E-utilities efetch API. No API key needed for low-volume. Add to existing httpx infrastructure.

5. **Diagnosis keyword matching**: Extend existing CZ_MEDICAL_SYNONYMS in synonyms.py. Insert as first step in diagnosis_assist pipeline before cluster matching.

6. **Preprints merge**: Always fetch PubMed first. When include_preprints=True, also fetch Europe PMC in parallel, merge with DOI dedup.

### Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| PubMed E-utilities rate limiting | Use existing HTTP cache; fallback gracefully |
| NRPZS pharmacy API permanently broken | Return informative error; mark as external dependency |
| MyChem.info name search low coverage | Test with target 4 drugs; document coverage gaps |
| SUKL SQLite index corruption | Detect on load, rebuild from API if corrupted |
| article_searcher still slow after fixes | Profile first (T003), iterate on bottleneck |

## Complexity Tracking

No constitution violations — no complexity justification needed.
