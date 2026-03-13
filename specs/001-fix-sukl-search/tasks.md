# Tasks: Fix SUKL Drug Search Performance

**Input**: Design documents from `/specs/001-fix-sukl-search/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Included — project uses pytest with mocked HTTP for unit tests and @pytest.mark.integration for live API tests.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup

**Purpose**: No new project setup needed — this is a modification of existing codebase. Phase 1 is minimal.

- [x] T001 Verify existing test suite passes: `uv run python -m pytest tests/tdd/ tests/czech/ -x -q`

---

## Phase 2: Foundational (DrugIndex — blocks US1, US2, US3)

**Purpose**: Build the in-memory drug index that all search-dependent user stories rely on.

**⚠️ CRITICAL**: No user story work can begin until DrugIndex is complete and tested.

- [x] T002 Create DrugIndex module with DrugIndexEntry dataclass and DrugIndex singleton in `src/biomcp/czech/sukl/drug_index.py` — include: `DrugIndexEntry` (sukl_code, name, name_normalized, strength, atc_code, atc_normalized, form, supplement, supplement_normalized, holder_code), `DrugIndex` class with `_entries`, `_built_at`, `_lock`, async `get_drug_index()` factory that fetches all codes via `_fetch_drug_list()`, fetches details from cache/API with bounded concurrency (semaphore=10), builds entries list. Use `CACHE_TTL_DAY` for expiry. Follow MKN-10/SZV lazy-init pattern.
- [x] T003 Implement `search_index(index, query, page, page_size)` function in `src/biomcp/czech/sukl/drug_index.py` — normalize query via `normalize_query()`, substring match on name_normalized, atc_normalized (exact match), supplement_normalized, holder_code. Return `(page_results, total_count)`. Apply `compute_skip()` for pagination.
- [x] T004 Create unit tests for DrugIndex in `tests/czech/test_drug_index.py` — test: index build from mocked drug list + details, search by name, search by ATC code, search with diacritics, empty results, pagination, cache expiry triggers rebuild, concurrent access (lock), cold start behavior.

**Checkpoint**: DrugIndex builds, searches, and is tested in isolation.

---

## Phase 3: User Story 1 — Search for a medicine by name (Priority: P1) 🎯 MVP

**Goal**: `czechmed_search_medicine` returns results within 10 seconds using DrugIndex instead of full 68K scan.

**Independent Test**: Call `czechmed_search_medicine` with query "ibuprofen" and verify results return within 10 seconds.

### Implementation for User Story 1

- [x] T005 [US1] Replace `_sukl_drug_search()` in `src/biomcp/czech/sukl/search.py` — remove the 68K full-scan logic (lines 107-153), replace with: call `get_drug_index()`, call `search_index()`, convert `DrugIndexEntry` results to existing `_detail_to_summary()` format, return same JSON structure. Keep error handling for API unavailability.
- [x] T006 [US1] Update unit tests in `tests/czech/test_sukl_search.py` — update mocks to patch `drug_index.get_drug_index()` and `drug_index.search_index()` instead of old `_fetch_drug_list()` + `_fetch_drug_detail()` calls. Verify same JSON output contract.
- [x] T007 [US1] Add integration test in `tests/czech_integration/test_sukl_api.py` — add `@pytest.mark.integration` test that calls `_sukl_drug_search("ibuprofen")` against live API and asserts results returned within 30 seconds, results contain expected fields (sukl_code, name, atc_code).
- [x] T008 [US1] Live validation: run `uv run python -c "import asyncio; from biomcp.core import mcp_app; print(asyncio.run(mcp_app.call_tool('czechmed_search_medicine', {'query': 'ibuprofen'}))[:500])"` and verify results within 10 seconds.

**Checkpoint**: `czechmed_search_medicine` works. Verify with T008.

---

## Phase 4: User Story 2 — Compare medicine alternatives (Priority: P2)

**Goal**: `czechmed_compare_alternatives` completes within 15 seconds by using DrugIndex for ATC-based search.

**Independent Test**: Call `czechmed_compare_alternatives` with a known SUKL code and verify response within 15 seconds.

### Implementation for User Story 2

- [x] T009 [US2] Verify `compare_alternatives` in `src/biomcp/czech/vzp/drug_reimbursement.py` — check if it calls `_sukl_drug_search()` internally. If yes, it automatically benefits from US1 fix. If it has its own search logic, update to use `get_drug_index()` + `search_index()`.
- [x] T010 [US2] Live validation: run `czechmed_compare_alternatives` with a known SUKL code and verify response within 15 seconds.

**Checkpoint**: `czechmed_compare_alternatives` responds within 15 seconds.

---

## Phase 5: User Story 3 — Get full drug profile (Priority: P3)

**Goal**: `czechmed_drug_profile` completes within 20 seconds.

**Independent Test**: Call `czechmed_drug_profile` with query "ibuprofen" and verify combined profile within 20 seconds.

### Implementation for User Story 3

- [x] T011 [US3] Verify `_resolve_sukl_code()` in `src/biomcp/czech/workflows/drug_profile.py` — confirm it calls `_sukl_drug_search()` and thus benefits from US1 fix. If it has additional search logic, update to use DrugIndex.
- [x] T012 [US3] Live validation: run `czechmed_drug_profile` with query "ibuprofen" and verify response within 20 seconds.

**Checkpoint**: `czechmed_drug_profile` responds within 20 seconds.

---

## Phase 6: User Story 4 — Find pharmacies by location (Priority: P3)

**Goal**: Investigate pharmacy API and either fix or document limitation.

**Independent Test**: Call `czechmed_find_pharmacies` with city "Praha".

### Implementation for User Story 4

- [x] T013 [US4] Investigate SUKL pharmacy API: test `GET /dlp/v1/lecebna-zarizeni` with various params (mesto, psc). If 504 persists, document as known limitation.
- [x] T014 [US4] Update `_find_pharmacies()` in `src/biomcp/czech/sukl/search.py` — if API is non-functional: return clear Czech-language message "SUKL API pro lékárny je momentálně nedostupné" via `format_czech_response()`. If API works: fix query parameters.
- [x] T015 [US4] Update `tests/czech/test_sukl_pharmacies.py` — add test for graceful 504 handling with expected error message.

**Checkpoint**: `czechmed_find_pharmacies` either returns results or clear error message.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Regression testing, cleanup, documentation.

- [x] T016 Run full test suite: `uv run python -m pytest tests/ -x --ff -n auto --dist loadscope` — ensure 0 regressions, all 990 tests pass.
- [x] T017 Verify tool count: ensure `tests/tdd/test_mcp_integration.py` still asserts exactly 60 tools.
- [ ] T018 Run live validation for all 23 Czech tools — confirm at least 20/23 return valid responses.
- [x] T019 Update CLAUDE.md Known Issues section if pharmacy API limitation is documented.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify baseline
- **Foundational (Phase 2)**: Depends on Phase 1 — DrugIndex is the core deliverable
- **US1 (Phase 3)**: Depends on Phase 2 — integrates DrugIndex into search
- **US2 (Phase 4)**: Depends on Phase 3 — relies on fixed `_sukl_drug_search()`
- **US3 (Phase 5)**: Depends on Phase 3 — relies on fixed `_sukl_drug_search()`
- **US4 (Phase 6)**: Independent of other stories — can run in parallel with US2/US3
- **Polish (Phase 7)**: Depends on all stories complete

### User Story Dependencies

- **US1 (P1)**: Depends on Foundational (DrugIndex) — core fix
- **US2 (P2)**: Depends on US1 (uses `_sukl_drug_search()` internally)
- **US3 (P3)**: Depends on US1 (uses `_resolve_sukl_code()` → `_sukl_drug_search()`)
- **US4 (P3)**: Independent — different API endpoint, no search dependency

### Within Each User Story

- Implementation before tests validation
- Core logic before live validation
- Each story completable and verifiable at its checkpoint

### Parallel Opportunities

- T002 + T003 can run sequentially (same file), T004 after both
- T009 + T011 verification can be parallel (different files, both depend on US1)
- T013 (pharmacy investigation) can run in parallel with US2/US3
- T015 (pharmacy test) can run in parallel with T016

---

## Parallel Example: After US1 Complete

```bash
# These can all run in parallel after Phase 3 (US1) is done:
Task T009: "Verify compare_alternatives uses _sukl_drug_search()"
Task T011: "Verify _resolve_sukl_code() uses _sukl_drug_search()"
Task T013: "Investigate SUKL pharmacy API status"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Verify baseline (T001)
2. Complete Phase 2: Build DrugIndex (T002-T004)
3. Complete Phase 3: Integrate into search (T005-T008)
4. **STOP and VALIDATE**: Test `czechmed_search_medicine("ibuprofen")` — must return in <10s
5. This alone fixes the critical bug

### Incremental Delivery

1. Setup + Foundational → DrugIndex ready
2. US1 → Search works → **MVP done**
3. US2 → Compare alternatives works → verify
4. US3 → Drug profile works → verify
5. US4 → Pharmacy fix or documented → verify
6. Polish → Full regression, docs updated

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Total: **19 tasks** across 7 phases
- US2 and US3 may require zero code changes if they exclusively use `_sukl_drug_search()` — T009/T011 are verification-only
- Commit after each phase checkpoint
- DrugIndex follows exact same pattern as MKN-10 (in `src/biomcp/czech/mkn/`) and SZV (in `src/biomcp/czech/szv/`)
