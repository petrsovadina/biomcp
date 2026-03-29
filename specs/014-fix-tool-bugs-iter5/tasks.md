# Tasks: Fix Tool Bugs Iteration 5

**Input**: Design documents from `/specs/014-fix-tool-bugs-iter5/`
**Prerequisites**: plan.md, spec.md

**Tests**: Not explicitly requested — tests included only for regression validation in final phase.

**Organization**: Tasks grouped by user story priority (P0 → P1 → P2 → P3). Each story is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add constants and shared helpers needed across multiple bug fixes

- [x] T001 Add PUBTATOR_TIMEOUT, ARTICLE_SEARCH_CACHE_TTL, ARTICLE_SEARCH_HARD_TIMEOUT constants in src/czechmedmcp/constants.py
- [x] T002 Add SUKL_INDEX_DB_PATH constant for persistent index location in src/czechmedmcp/constants.py

---

## Phase 2: Foundational — Article Search Performance (Blocking)

**Purpose**: Fix article_searcher latency regression (BUG-34/39) — this blocks US1 and cascades to search() unified wrapper (BUG-35)

**CRITICAL**: This phase must complete before US1 can be validated. The unified `search()` wrapper performance depends on article backend.

- [x] T003 Profile article_searcher pipeline to identify bottleneck in src/czechmedmcp/articles/search.py — measure time spent in PubMed vs PubTator3 vs Europe PMC calls
- [x] T004 Add hard 10s timeout per individual PubMed/PubTator3 API call in src/czechmedmcp/articles/search.py
- [x] T005 Implement in-memory LRU cache (TTL 1h, max 500 entries) for article search results in src/czechmedmcp/articles/search.py
- [x] T006 Add 30s hard timeout on the overall article_searcher function in src/czechmedmcp/articles/search.py — return partial results if timeout fires

**Checkpoint**: article_searcher avg latency should be under 15s after this phase

---

## Phase 3: User Story 1 — Article Search Returns Results Quickly (Priority: P0)

**Goal**: Validate that article_searcher meets latency targets (avg < 15s, P95 < 30s, max 30s)

**Independent Test**: Call `article_searcher("metformin type 2 diabetes")` 5 times, verify avg < 15s

### Implementation for User Story 1

- [x] T007 [US1] Verify search() unified wrapper latency improves as cascade effect in src/czechmedmcp/router_handlers.py — no code change expected, just validate
- [x] T008 [US1] Add performance logging for article_searcher with per-phase timing in src/czechmedmcp/articles/search.py

**Checkpoint**: US1 validated — article_searcher meets latency targets

---

## Phase 4: User Story 2 — SUKL Drug Search Without Cold-Start Block (Priority: P0)

**Goal**: SUKL drug index loads from persistent storage in < 2s on cold start

**Independent Test**: Restart MCP server, immediately call `czechmed_search_medicine("Metformin")`, verify results in < 5s

### Implementation for User Story 2

- [x] T009 [US2] Add SQLite-based persistent storage for DrugIndex in src/czechmedmcp/czech/sukl/drug_index.py — save_to_disk() and load_from_disk() methods
- [x] T010 [US2] Modify DrugIndex initialization to try loading from disk first, fall back to API build in src/czechmedmcp/czech/sukl/drug_index.py
- [x] T011 [US2] Add background refresh: if index loaded from disk but older than CACHE_TTL_DAY, trigger non-blocking API rebuild in src/czechmedmcp/czech/sukl/drug_index.py
- [x] T012 [US2] Update search_index() to return results from stale index while rebuild is in progress in src/czechmedmcp/czech/sukl/drug_index.py

**Checkpoint**: US2 validated — cold-start responds in < 5s

---

## Phase 5: User Story 3 — Drug Profile Provides Complete Information (Priority: P0)

**Goal**: `czechmed_drug_profile` returns structured data instead of server error

**Independent Test**: Call `czechmed_drug_profile("Metformin")`, verify non-error response with data sections

### Implementation for User Story 3

- [x] T013 [US3] Investigate root cause of server error in src/czechmedmcp/czech/workflows/drug_profile.py — read _drug_profile() function and trace error
- [x] T014 [US3] Fix drug_profile to handle SUKL index not-ready state gracefully in src/czechmedmcp/czech/workflows/drug_profile.py
- [x] T015 [US3] Add error handling for each sub-query (registration, availability, reimbursement, evidence) to return partial results in src/czechmedmcp/czech/workflows/drug_profile.py
- [x] T016 [US3] Add support for SUKL code and ATC code as input (not just drug name) in src/czechmedmcp/czech/workflows/drug_profile.py

**Checkpoint**: US3 validated — drug_profile returns structured data for "Metformin"

---

## Phase 6: User Story 4 — Article Search Merges Preprints (Priority: P1)

**Goal**: `include_preprints=True` returns union of PubMed + Europe PMC, not replacement

**Independent Test**: Call `article_searcher(preprints=true)`, verify mix of peer-reviewed + preprints

### Implementation for User Story 4

- [x] T017 [US4] Fix preprints logic in src/czechmedmcp/articles/search.py — change from REPLACE to UNION: always fetch PubMed first, add Europe PMC preprints when flag is true
- [x] T018 [US4] Implement DOI-based deduplication in merged results in src/czechmedmcp/articles/unified.py
- [x] T019 [US4] Verify article_searcher(preprints=false) still returns only PubMed results (no regression)

**Checkpoint**: US4 validated — preprints=true returns mixed results

---

## Phase 7: User Story 5 — Drug Lookup by Common Name (Priority: P1)

**Goal**: `drug_getter("metformin")` returns DB00331 with full profile

**Independent Test**: Call `drug_getter("metformin")`, verify DrugBank ID = DB00331

### Implementation for User Story 5

- [x] T020 [P] [US5] Add MyChem.info name-search fallback function in src/czechmedmcp/integrations/biothings_client.py — search by name, return best DrugBank/ChEMBL ID
- [x] T021 [US5] Modify get_drug() to use name-search fallback when direct lookup returns "Unknown" in src/czechmedmcp/drugs/getter.py
- [x] T022 [US5] Verify drug_getter with DrugBank IDs still works (no regression) — test DB00331, DB00945

**Checkpoint**: US5 validated — metformin, aspirin, atorvastatin, amlodipine resolve by name

---

## Phase 8: User Story 6 — Article Detail Shows Real Abstract (Priority: P1)

**Goal**: `article_getter(PMID)` returns real abstract, not placeholder

**Independent Test**: Call `article_getter("38768446")`, verify abstract is scientific text

### Implementation for User Story 6

- [x] T023 [US6] Add PubMed E-utilities efetch fallback for abstract retrieval in src/czechmedmcp/articles/fetch.py — when PubTator3 returns no abstract
- [x] T024 [US6] Remove placeholder string generation (f"Article: {pmid}") and replace with efetch fallback in src/czechmedmcp/articles/fetch.py
- [x] T025 [US6] Verify PMC ID-based article_getter still returns full text (no regression)

**Checkpoint**: US6 validated — PMID abstracts are real scientific text

---

## Phase 9: User Story 7 — Diagnosis Assist Recognizes Named Diagnoses (Priority: P1)

**Goal**: `diagnosis_assist("hypertenze, bolest hlavy")` returns I10 in top-3

**Independent Test**: Call `czechmed_diagnosis_assist("hypertenze, bolest hlavy, zavrate")`, verify I10 ranked high

### Implementation for User Story 7

- [x] T026 [P] [US7] Extend DIRECT_DIAGNOSIS_KEYWORDS mapping in src/czechmedmcp/czech/mkn/synonyms.py — add hypertenze→I10, astma→J45, epilepsie→G40 and other common Czech diagnosis names
- [x] T027 [US7] Add direct keyword→ICD-10 lookup as first step in diagnosis_assist before cluster matching in src/czechmedmcp/czech/diagnosis_embed/searcher.py
- [x] T028 [US7] Ensure direct keyword matches rank above cluster-based matches in merged results in src/czechmedmcp/czech/diagnosis_embed/searcher.py
- [x] T029 [US7] Verify existing diagnosis_assist("zizen, caste moceni") still returns E11 in top-5 (no regression)

**Checkpoint**: US7 validated — "hypertenze" input returns I10 in top-3

---

## Phase 10: User Story 8 — Pharmacy Search Returns Results (Priority: P2)

**Goal**: `find_pharmacies(city="Brno")` returns pharmacy results

**Independent Test**: Call `czechmed_find_pharmacies(city="Brno")`, verify >= 5 results

### Implementation for User Story 8

- [x] T030 [US8] Investigate NRPZS API endpoint for pharmacy-type providers — test direct API calls in src/czechmedmcp/czech/nrpzs/search.py
- [x] T031 [US8] Fix pharmacy filter parameter (DruhZdravotnichSluzeb or equivalent) in src/czechmedmcp/czech/sukl/search.py
- [x] T032 [US8] If NRPZS pharmacy endpoint is broken, add informative error message instead of silent 0 results in src/czechmedmcp/czech/sukl/search.py

**Checkpoint**: US8 validated — pharmacy search returns results or clear error

---

## Phase 11: User Story 9 — FDA Recall Getter Returns Correct Recall (Priority: P2)

**Goal**: `recall_getter("D-0328-2025")` returns matching recall

**Independent Test**: Call `openfda_recall_getter("D-0328-2025")`, verify recall_number matches

### Implementation for User Story 9

- [x] T033 [US9] Investigate recall_number vs event_id field mapping in src/czechmedmcp/openfda/drug_recalls.py — verify current search query format
- [x] T034 [US9] Fix recall lookup to use recall_number field for D-XXXX-YYYY format inputs in src/czechmedmcp/openfda/drug_recalls.py
- [x] T035 [US9] Verify numeric event_id lookup still works (no regression)

**Checkpoint**: US9 validated — correct recall returned for D-0328-2025

---

## Phase 12: User Story 10 — Article Search Respects Page Size (Priority: P2)

**Goal**: `article_searcher(page_size=3)` returns at most 3 results

**Independent Test**: Call `article_searcher(page_size=3)`, verify result count <= 3

### Implementation for User Story 10

- [x] T036 [US10] Propagate page_size parameter to PubMed API retmax in src/czechmedmcp/articles/search.py
- [x] T037 [US10] Propagate page_size to Europe PMC pageSize parameter in src/czechmedmcp/articles/preprints.py
- [x] T038 [US10] Truncate final result list to page_size in unified search in src/czechmedmcp/articles/unified.py

**Checkpoint**: US10 validated — page_size controls result count

---

## Phase 13: User Story 11 — OpenFDA Label Section Validation (Priority: P2)

**Goal**: Invalid section names produce helpful error with valid alternatives

**Independent Test**: Call `openfda_label_searcher(section="warnings")`, verify helpful response

### Implementation for User Story 11

- [x] T039 [US11] Add VALID_LABEL_SECTIONS set with known valid values in src/czechmedmcp/openfda/drug_labels_helpers.py
- [x] T040 [US11] Add section validation with alias mapping (warnings→boxed_warning suggestion) in src/czechmedmcp/openfda/drug_labels.py
- [x] T041 [US11] Verify existing valid sections (contraindications, adverse_reactions) still work

**Checkpoint**: US11 validated — invalid sections produce helpful suggestions

---

## Phase 14: User Story 12 — Gene Getter Returns Concise Output (Priority: P3)

**Goal**: `gene_getter("BRCA1")` shows canonical isoform only, not 500+ isoforms

**Independent Test**: Call `gene_getter("BRCA1")`, verify output is concise

### Implementation for User Story 12

- [x] T042 [US12] Add isoform truncation logic in src/czechmedmcp/genes/getter.py — show only canonical isoform, add "and N other isoforms" note
- [x] T043 [US12] Verify gene_getter("TP53") still returns complete data (no regression)

**Checkpoint**: US12 validated — gene output is concise

---

## Phase 15: Polish & Cross-Cutting Concerns

**Purpose**: Regression validation, Arcade sync, cleanup

- [x] T044 Run full regression test suite: 6 tests from previous iterations in tests/tdd/
- [x] T045 [P] Sync Arcade wrappers if any tool signatures changed in src/czechmedmcp/arcade/
- [x] T046 [P] Update expected tool count (still 60) in tests/tdd/test_mcp_integration.py if needed
- [x] T047 Run full pytest suite: `uv run python -m pytest -x --ff -n auto --dist loadscope`
- [x] T048 Run quality checks: `uv run ruff check src tests && uv run mypy`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS US1 validation
- **US1 (Phase 3)**: Depends on Phase 2 — validation of latency improvements
- **US2 (Phase 4)**: Depends on Phase 1 only — independent of article search
- **US3 (Phase 5)**: Depends on Phase 1 only — independent of article search
- **US4-US7 (Phase 6-9)**: Depend on Phase 1 only — can run in parallel
- **US8-US12 (Phase 10-14)**: Depend on Phase 1 only — can run in parallel
- **Polish (Phase 15)**: Depends on all desired stories being complete

### User Story Dependencies

- **US1** (article latency): Depends on Phase 2 foundational work
- **US2** (SUKL cold-start): Independent — can start after Phase 1
- **US3** (drug_profile): Independent — may benefit from US2 (SUKL index ready)
- **US4** (preprints merge): Independent — touches same files as Phase 2, run after
- **US5** (drug_getter names): Independent
- **US6** (article abstract): Independent — touches articles/fetch.py (different from search.py)
- **US7** (diagnosis_assist): Independent
- **US8** (pharmacies): Independent — needs API investigation first
- **US9** (recall ID): Independent
- **US10** (page_size): Depends on Phase 2 (same file: articles/search.py) — run after
- **US11** (label sections): Independent
- **US12** (gene getter): Independent

### Parallel Opportunities

After Phase 1 + 2 complete, these groups can run in parallel:

**Group A** (articles/search.py changes — sequential):
- US1 → US4 → US10

**Group B** (Czech modules — parallel):
- US2, US3, US7, US8

**Group C** (independent modules — parallel):
- US5, US6, US9, US11, US12

---

## Parallel Example: Group B (Czech modules)

```bash
# These can all run in parallel after Phase 1:
Task: T009-T012 [US2] SUKL persistent index in drug_index.py
Task: T013-T016 [US3] Drug profile fix in workflows/drug_profile.py
Task: T026-T029 [US7] Diagnosis assist in diagnosis_embed/searcher.py + mkn/synonyms.py
Task: T030-T032 [US8] Pharmacy search in nrpzs/search.py
```

---

## Implementation Strategy

### MVP First (P0 Stories Only)

1. Complete Phase 1: Setup (constants)
2. Complete Phase 2: Article search performance (foundational)
3. Complete Phase 3: US1 — Validate article latency
4. Complete Phase 4: US2 — SUKL cold-start
5. Complete Phase 5: US3 — Drug profile
6. **STOP and VALIDATE**: All P0 bugs fixed, deploy candidate

### Incremental Delivery

1. Setup + Foundational → Article search fast
2. P0 stories → Deploy (biggest impact: latency + SUKL + drug_profile)
3. P1 stories → Deploy (preprints, drug names, abstracts, diagnosis)
4. P2 stories → Deploy (pharmacies, recall, page_size, labels)
5. P3 story → Deploy (gene getter)

### Estimated Scope

- **Total tasks**: 48
- **P0 tasks**: 16 (T001-T016)
- **P1 tasks**: 13 (T017-T029)
- **P2 tasks**: 13 (T030-T041)
- **P3 tasks**: 2 (T042-T043)
- **Polish tasks**: 5 (T044-T048)

---

## Notes

- No new tools are added — tool count stays at 60
- All fixes are backward-compatible (no breaking changes)
- Arcade wrappers may need sync if tool parameter signatures change
- Focus on existing tests passing, not adding new test files (unless regression test needed)
- Commit after each phase or logical group
