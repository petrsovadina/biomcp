# Tasks: Fix Tool Quality — E2E Test Report Bugs

**Input**: Design documents from `/specs/013-fix-tool-quality/`
**Prerequisites**: spec.md (27 bugs, 7 user stories)

**Tests**: Unit tests will be added/updated for each bug fix to prevent regression.

**Organization**: Tasks grouped by user story (P1 first), enabling independent implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup & Research

**Purpose**: Understand root causes before fixing. No code changes yet.

- [x] T001 Research SUKL DrugIndex cold start bottleneck — profile `_fetch_all_details()` in `src/czechmedmcp/czech/sukl/drug_index.py` lines 217-250 to identify if semaphore(20) or individual request latency is primary cause
- [x] T002 [P] Research ClinicalTrials.gov API query parameter format — verify `query.term` or `query.cond` is correct endpoint for full-text search
- [x] T003 [P] Research NRPZS API for pharmacy endpoints — find correct `DruhZdravotnichSluzeb` code for lekarny (currently returns 0 results)
- [x] T004 [P] Research NZIP CSV current URL — verify if `NZIP_CSV_BASE_URL` in `src/czechmedmcp/czech/mkn/stats.py` line 1-30 is still valid or find updated URL

**Checkpoint**: Root causes understood, ready to implement fixes

---

## Phase 2: Foundational (Shared Infrastructure Fixes)

**Purpose**: Core infrastructure improvements that multiple user stories depend on

**CRITICAL**: These must complete before user story work begins

- [x] T005 Add circuit breaker utility in `src/czechmedmcp/utils/circuit_breaker.py` — implement simple state machine (closed/open/half-open) with configurable failure threshold (default 2) and recovery timeout (default 60s)
- [x] T006 [P] Add SUKL-specific timeout constant `SUKL_TOOL_TIMEOUT = 10` (seconds) in `src/czechmedmcp/constants.py` — separate from `CZECH_HTTP_TIMEOUT` which controls individual HTTP calls
- [x] T007 [P] Add unit test for circuit breaker in `tests/tdd/test_circuit_breaker.py`

**Checkpoint**: Foundation ready — circuit breaker and timeout constants available for all phases

---

## Phase 3: User Story 1 — SUKL Performance (Priority: P1) — MVP

**Goal**: All SUKL tools respond within 10s or return clear error message. BUG-3, BUG-4, BUG-5, BUG-7.

**Independent Test**: `czechmed_search_medicine("Metformin")` responds in <10s. `czechmed_compare_alternatives("0011114")` does not hang.

### Implementation for User Story 1

- [x] T008 [US1] Add `asyncio.wait_for()` timeout wrapper (10s) around DrugIndex search in `src/czechmedmcp/czech/sukl/drug_index.py` — wrap `search_index()` call so it raises `TimeoutError` after 10s instead of waiting indefinitely for cold start
- [x] T009 [US1] Add circuit breaker integration to `_fetch_all_details()` in `src/czechmedmcp/czech/sukl/drug_index.py` — if SUKL DLP API fails 2x consecutively, skip further fetches for 60s and return partial index
- [x] T010 [US1] Add timeout handling in `czechmed_search_medicine` tool in `src/czechmedmcp/czech/czech_tools.py` — catch `TimeoutError` and `asyncio.TimeoutError`, return user-friendly message "SUKL index is building, try again in ~2 minutes" instead of hanging
- [x] T011 [P] [US1] Add timeout handling in `czechmed_get_medicine_detail` tool in `src/czechmedmcp/czech/czech_tools.py` — catch timeout, return clear error message
- [x] T012 [P] [US1] Add timeout handling in `czechmed_get_drug_reimbursement` tool in `src/czechmedmcp/czech/czech_tools.py` — catch timeout, return clear error message
- [x] T013 [US1] Add timeout handling in `czechmed_compare_alternatives` tool in `src/czechmedmcp/czech/czech_tools.py` — wrap entire comparison flow with `asyncio.wait_for(30s)` to prevent infinite hang (BUG-7)
- [x] T014 [US1] Add unit tests for SUKL timeout handling in `tests/tdd/test_sukl_timeout.py` — mock slow DrugIndex, verify timeout triggers within 10s, verify error messages are user-friendly
- [x] T015 [US1] Update Arcade wrappers for SUKL tools in `src/czechmedmcp/arcade/czech_tools.py` — ensure timeout handling is consistent with FastMCP tools

**Checkpoint**: All SUKL tools respond within 10-30s or return clear error. No more 14-minute hangs.

---

## Phase 4: User Story 2 — Unified search() Wrapper Fixes (Priority: P1)

**Goal**: search() returns relevant results for all domains. thinking-reminder removed from results. BUG-1, BUG-2, BUG-20, BUG-21, BUG-23.

**Independent Test**: `search(domain="trial", query="metformin")` returns metformin studies. No `thinking-reminder` in results.

### Implementation for User Story 2

- [x] T016 [US2] Remove thinking-reminder injection from `format_results()` in `src/czechmedmcp/router.py` lines 99-111 — delete the conditional block that prepends thinking-reminder to results list (BUG-2)
- [x] T017 [US2] Fix trial search query routing in `src/czechmedmcp/router.py` — ensure `query` parameter is passed as `query.term` to ClinicalTrials.gov API in the trial search handler (BUG-1)
- [x] T018 [P] [US2] Fix `search(domain="mkn_diagnosis")` handler in `src/czechmedmcp/router.py` — synchronize with `czechmed_search_diagnosis` direct tool to return matching results (BUG-20)
- [x] T019 [P] [US2] Fix `search(domain="drug")` handler in `src/czechmedmcp/router.py` — enrich drug search results with names and descriptions from MyChem.info instead of returning ID-only records (BUG-21)
- [x] T020 [P] [US2] Fix `search(domain="fda_label")` handler in `src/czechmedmcp/router.py` — extract drug name from query and use as required filter in OpenFDA label API call (BUG-23)
- [x] T021 [US2] Add unit tests for search router fixes in `tests/tdd/test_router_fixes.py` — test trial query passthrough, thinking-reminder absence, mkn/drug/fda_label domain handlers
- [x] T022 [US2] Update Arcade search wrapper in `src/czechmedmcp/arcade/individual_tools.py` — ensure thinking-reminder is not injected via Arcade path either

**Checkpoint**: search() wrapper returns relevant results for trial, mkn_diagnosis, drug, fda_label domains. No thinking-reminder pollution.

---

## Phase 5: User Story 3 — Diagnosis Assist Clinical Ranking (Priority: P1)

**Goal**: czechmed_diagnosis_assist returns clinically relevant diagnoses. E11 in top-5 for diabetes symptoms. BUG-6.

**Independent Test**: `czechmed_diagnosis_assist("zizen, caste moceni, unava, vysoky krevni cukr")` returns E11 in top-5.

### Implementation for User Story 3

- [x] T023 [US3] Investigate current embedding model performance in `src/czechmedmcp/czech/workflows/diagnosis_assistant.py` — test with diabetes symptoms, log raw similarity scores, identify why E11 is not ranked
- [x] T024 [US3] Add clinical symptom-to-diagnosis mapping dictionary in `src/czechmedmcp/czech/mkn/synonyms.py` — create explicit CZ symptom cluster mappings for common conditions (polydipsie+polyurie+hyperglykemie -> E11, bolest na hrudi+dusnost -> I21, etc.) with at least 20 mappings
- [x] T025 [US3] Integrate symptom mapping as pre-filter in `src/czechmedmcp/czech/workflows/diagnosis_assistant.py` — before embedding search, check if symptom cluster matches any explicit mapping; if so, boost those codes in results
- [x] T026 [US3] Add post-filter validation in `src/czechmedmcp/czech/workflows/diagnosis_assistant.py` — filter out results where diagnosis category (MKN chapter) is completely unrelated to symptom domain (e.g., remove oncology codes for metabolic symptoms)
- [x] T027 [US3] Add unit tests for diagnosis assist fixes in `tests/tdd/test_diagnosis_assist_quality.py` — test diabetes triada -> E11 in top-5, chest pain -> I21/I20 in top-5, headache+nausea -> no oncology codes in top-3

**Checkpoint**: Diagnosis assist returns clinically meaningful results. No irrelevant oncology suggestions for metabolic symptoms.

---

## Phase 6: User Story 4 — Drug Getter Name Lookup (Priority: P2)

**Goal**: drug_getter accepts drug names, not just DrugBank IDs. BUG-8.

**Independent Test**: `drug_getter("metformin")` returns metformin info.

### Implementation for User Story 4

- [x] T028 [US4] Add name-to-ID resolution function in `src/czechmedmcp/integrations/biothings_client.py` — implement `resolve_drug_name(name: str) -> str | None` that queries MyChem.info `/v1/query?q={name}&fields=drugbank.id` and returns first DrugBank ID
- [x] T029 [US4] Integrate name resolution into `drug_getter` in `src/czechmedmcp/drugs/getter.py` — if input is not a DrugBank ID (doesn't match `DB\d+` pattern), call `resolve_drug_name()` first, then proceed with existing logic
- [x] T030 [US4] Update `fetch(domain="drug")` handler in `src/czechmedmcp/fetch_handlers.py` — apply same name resolution logic so `fetch(domain="drug", id="metformin")` works
- [x] T031 [US4] Add unit tests for drug name resolution in `tests/tdd/test_drug_name_resolution.py` — test "metformin" -> DB00331, "aspirin" -> DB00945, "nonexistent_drug_xyz" -> clear error, "DB00331" -> passes through unchanged

**Checkpoint**: drug_getter("metformin") returns full drug profile. Backward compatible with DrugBank IDs.

---

## Phase 7: User Story 5 — Article Searcher & Getter Fixes (Priority: P2)

**Goal**: Preprints merge correctly with PubMed. page_size respected. article_getter has PubMed fallback. BUG-14, BUG-15, BUG-19.

**Independent Test**: `article_searcher(include_preprints=true)` returns mix of PubMed + preprints. `page_size=3` returns max 3.

### Implementation for User Story 5

- [x] T032 [US5] Fix preprint merging logic in `src/czechmedmcp/articles/search.py` — when `include_preprints=true`, fetch PubMed results first, then append preprints (UNION), instead of replacing PubMed results (BUG-14)
- [x] T033 [US5] Fix `page_size` parameter passthrough in `src/czechmedmcp/articles/search.py` — ensure `limit` parameter is correctly passed to PubTator3 request and used in result slicing (BUG-19)
- [x] T034 [US5] Add PubMed E-utilities fallback in `src/czechmedmcp/articles/fetch.py` — when PubTator3 returns placeholder abstract ("Article: {pmid}"), call PubMed efetch API `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&rettype=abstract` as fallback (BUG-15)
- [x] T035 [US5] Add unit tests for article fixes in `tests/tdd/test_article_fixes.py` — test preprint+PubMed merge, page_size enforcement, PubTator3 fallback

**Checkpoint**: Article search returns correct mix of sources. page_size works. No placeholder abstracts.

---

## Phase 8: User Story 6 — Czech Registry Data Fixes (Priority: P2)

**Goal**: Fix find_pharmacies, PIL/SPC availability, reimbursement data, diagnosis stats, english names. BUG-9, BUG-10, BUG-11, BUG-12, BUG-17, BUG-18.

**Independent Test**: `czechmed_find_pharmacies(city="Brno")` returns pharmacies. `czechmed_get_diagnosis_stats("E11")` returns data.

### Implementation for User Story 6

- [x] T036 [US6] Fix pharmacy query in `src/czechmedmcp/czech/nrpzs/search.py` — update NRPZS API query to use correct `DruhZdravotnichSluzeb` code for pharmacies (based on T003 research) (BUG-12)
- [x] T037 [P] [US6] Fix PIL getter in `src/czechmedmcp/czech/sukl/getter.py` — improve `_fetch_doc_metadata()` to try alternative SUKL document endpoints, return specific unavailability reason ("PIL not digitized for registrations before 2010" vs "SUKL API error") (BUG-10)
- [x] T038 [P] [US6] Fix SPC getter in `src/czechmedmcp/czech/sukl/getter.py` — same pattern as PIL, try alternative endpoints, return specific unavailability reason (BUG-11)
- [x] T039 [P] [US6] Fix reimbursement data lookup in `src/czechmedmcp/czech/vzp/search.py` — verify VZP codebook ZIP URL is current (version `_VZP_VERSION`), check if SUKL code mapping is correct for reimbursement lookup (BUG-9)
- [x] T040 [P] [US6] Update NZIP data source URL in `src/czechmedmcp/czech/mkn/stats.py` — based on T004 research, update `NZIP_CSV_BASE_URL` or add local CSV fallback with bundled 2023 data (BUG-17)
- [x] T041 [P] [US6] Add English names to diagnosis detail in `src/czechmedmcp/czech/mkn/search.py` — add WHO ICD-10 English name lookup, populate `name_en` field when available (BUG-18)
- [x] T042 [US6] Add unit tests for Czech registry fixes in `tests/czech/test_registry_fixes.py` — test pharmacy search, PIL/SPC error messages, reimbursement lookup, NZIP stats, English names

**Checkpoint**: Czech registry tools return data or clear explanations for unavailability.

---

## Phase 9: User Story 7 — Minor Fixes (Priority: P3)

**Goal**: Fix OpenFDA recall mapping, device filtering, MKN synonyms, diagnosis ranking, variant coordinates. BUG-16, BUG-24, BUG-25, BUG-26, BUG-27.

**Independent Test**: `openfda_recall_getter("D-0328-2025")` returns correct Glenmark recall. `czechmed_search_diagnosis("cukrovka")` returns E10/E11.

### Implementation for User Story 7

- [x] T043 [P] [US7] Fix recall_number to event_id mapping in `src/czechmedmcp/openfda/drug_recalls.py` and `src/czechmedmcp/openfda/drug_recalls_helpers.py` — use `recall_number` field (not event_id) for lookup filter in OpenFDA Enforcement API (BUG-16)
- [x] T044 [P] [US7] Add Czech synonym dictionary in `src/czechmedmcp/czech/mkn/synonyms.py` — add ~50 common Czech colloquial medical terms mapped to ICD-10 codes: cukrovka->E11, vysoky tlak->I10, infarkt->I21, rakovina->C80, astma->J45, etc. (BUG-24)
- [x] T045 [P] [US7] Integrate synonym lookup into `search_diagnoses()` in `src/czechmedmcp/czech/mkn/search.py` — if query matches synonym dict, return mapped code(s) before falling back to text search (BUG-24)
- [x] T046 [P] [US7] Fix diagnosis relevance ranking in `src/czechmedmcp/czech/mkn/search.py` — boost E11 over E10 for "diabetes" query based on prevalence (E11 is ~10x more common than E10) (BUG-25)
- [x] T047 [P] [US7] Improve device searcher query filtering in `src/czechmedmcp/openfda/device_events.py` — add exact device name matching via `device.generic_name` field instead of generic full-text search (BUG-26)
- [x] T048 [P] [US7] Fix variant coordinate mapping in `src/czechmedmcp/router.py` variant search handler — validate that returned chromosome matches gene's known chromosome from MyGene.info (BUG-27)
- [x] T049 [US7] Add unit tests for minor fixes in `tests/tdd/test_minor_fixes.py` — test recall mapping, Czech synonyms, diagnosis ranking, device filtering

**Checkpoint**: All minor bugs fixed. Quality score improvement across all domains.

---

## Phase 10: Polish & Regression Testing

**Purpose**: Final validation, regression tests, tool count verification

- [x] T050 Run full unit test suite `uv run python -m pytest -x --ff -n auto --dist loadscope` — verify all 787+ tests pass, no regressions
- [x] T051 Run MCP integration test `tests/tdd/test_mcp_integration.py` — verify exactly 60 tools registered
- [x] T052 [P] Run Arcade integration test `tests/tdd/test_arcade_integration.py` — verify exactly 60 Arcade tools registered
- [x] T053 [P] Run ruff lint check `uv run ruff check src tests` — verify no lint violations
- [x] T054 Update Arcade wrappers for all changed tools in `src/czechmedmcp/arcade/` — ensure Arcade tools match FastMCP tool behavior for all fixes
- [x] T055 Update expected tool count if any tools were added/removed in `tests/tdd/test_mcp_integration.py` and `tests/tdd/test_arcade_integration.py`

**Checkpoint**: All tests pass. 60 tools registered. No lint violations. Ready for PR.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Research)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: No hard dependencies but T005-T007 should complete before Phase 3
- **Phase 3 (US1 SUKL)**: Depends on T005 (circuit breaker), T006 (timeout constant)
- **Phase 4 (US2 Search)**: Independent — can run parallel with Phase 3
- **Phase 5 (US3 Diagnosis)**: Independent — can run parallel with Phase 3-4
- **Phase 6 (US4 Drug)**: Independent — can run parallel with Phase 3-5
- **Phase 7 (US5 Articles)**: Independent — can run parallel with Phase 3-6
- **Phase 8 (US6 Czech)**: Depends on T003, T004 research from Phase 1
- **Phase 9 (US7 Minor)**: Independent — can run parallel
- **Phase 10 (Polish)**: Depends on ALL previous phases

### User Story Dependencies

- **US1 (SUKL Performance)**: Depends on Phase 2 (circuit breaker). No cross-story deps.
- **US2 (Search Wrapper)**: Independent. Can start after Phase 1.
- **US3 (Diagnosis Assist)**: Independent. Can start immediately.
- **US4 (Drug Getter)**: Independent. Can start immediately.
- **US5 (Articles)**: Independent. Can start immediately.
- **US6 (Czech Registry)**: Depends on T003, T004 research.
- **US7 (Minor Fixes)**: Independent. Can start immediately.

### Parallel Opportunities

Within phases, tasks marked [P] can run concurrently:
- Phase 1: T002, T003, T004 in parallel
- Phase 2: T006, T007 in parallel
- Phase 3: T011, T012 in parallel
- Phase 4: T018, T019, T020 in parallel
- Phase 8: T037, T038, T039, T040, T041 in parallel
- Phase 9: All T043-T048 in parallel
- Phase 10: T052, T053 in parallel

---

## Parallel Example: Phases 3-5 (P1 Stories)

```
# After Phase 2 completes, launch all P1 stories simultaneously:

# US1 (SUKL Performance):
T008 → T009 → T010 → T011+T012 (parallel) → T013 → T014 → T015

# US2 (Search Wrapper) — fully independent:
T016 → T017 → T018+T019+T020 (parallel) → T021 → T022

# US3 (Diagnosis Assist) — fully independent:
T023 → T024 → T025 → T026 → T027
```

---

## Implementation Strategy

### MVP First (Phase 1-3 Only)

1. Complete Phase 1: Research (T001-T004)
2. Complete Phase 2: Foundational (T005-T007)
3. Complete Phase 3: US1 SUKL Performance
4. **STOP and VALIDATE**: All SUKL tools respond within 10s
5. This alone fixes 5 of 7 CRITICAL bugs

### Incremental Delivery

1. Phase 1-2 → Foundation ready
2. Phase 3 (US1) → SUKL performance fixed → 5 CRITICAL bugs resolved
3. Phase 4 (US2) → Search wrapper fixed → 2 remaining CRITICAL bugs resolved
4. Phase 5 (US3) → Diagnosis assist fixed → Clinical safety bug resolved
5. Phase 6-7 (US4-5) → Drug getter + Articles fixed → HIGH bugs resolved
6. Phase 8-9 (US6-7) → Czech registry + Minor fixes → MEDIUM+LOW bugs resolved
7. Phase 10 → Final validation → PR ready

### Bug Resolution Milestones

| After Phase | CRITICAL Remaining | HIGH Remaining | Total Fixed |
|-------------|-------------------|----------------|-------------|
| Phase 3     | 2 (BUG-1,2,6)    | 8              | 5/27        |
| Phase 4     | 1 (BUG-6)        | 8              | 10/27       |
| Phase 5     | 0                 | 8              | 11/27       |
| Phase 6-7   | 0                 | 0              | 19/27       |
| Phase 8     | 0                 | 0              | 25/27       |
| Phase 9     | 0                 | 0              | 27/27       |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Commit after each task or logical group
- All SUKL timeout values use `SUKL_TOOL_TIMEOUT` from constants.py (T006)
- Circuit breaker (T005) is reusable for any flaky external API
- Research tasks (Phase 1) may change implementation approach for later tasks
- Keep tool count at exactly 60 — no tools added or removed
