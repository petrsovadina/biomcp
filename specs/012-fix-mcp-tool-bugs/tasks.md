# Tasks: Oprava selhávajících MCP nástrojů (46% → 80%+)

**Input**: Design documents from `/specs/012-fix-mcp-tool-bugs/`
**Prerequisites**: plan.md (required), spec.md (required), research.md

**Tests**: Included — unit testy s mocked HTTP responses pro opravené nástroje (viz CLAUDE.md Testing Rigor).

**Organization**: Tasks grouped by delivery phase (P1 → P2 → P3) matching spec user stories and plan implementation design. Each phase is independently testable and committable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Shared utilities and constants needed by all bug fixes

- [ ] T001 Add retry utility function `async_retry(fn, max_retries=3, backoff_base=2)` in src/czechmedmcp/utils/retry.py
- [ ] T002 [P] Add `BULK_DOWNLOAD_TIMEOUT = 120.0` constant in src/czechmedmcp/constants.py
- [ ] T003 [P] Add `format_tool_error(tool_name, message, code=None)` utility in src/czechmedmcp/exceptions.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: SUKL code normalization used by all SUKL tools (US1, US4, US5, US7)

**CRITICAL**: Must complete before US1 and US4–US7

- [ ] T004 Add `normalize_sukl_code(code: str) -> str` with `strip().zfill(7)` in src/czechmedmcp/czech/sukl/client.py
- [ ] T005 Apply `normalize_sukl_code()` to all public SUKL functions in src/czechmedmcp/czech/sukl/client.py (fetch_drug_detail, etc.)
- [ ] T006 [P] Write parametrized unit test for normalize_sukl_code (5, 6, 7 digit codes, whitespace) in tests/tdd/test_sukl_normalization.py

**Checkpoint**: SUKL code normalization works — `GetMedicineDetail("124137")` returns same result as `GetMedicineDetail("0124137")`

---

## Phase 3: User Story 1 — SearchMedicine fix (Priority: P1) — BUG-001, BUG-005

**Goal**: SearchMedicine returns results for common drug names; DrugProfile/CompareAlternatives work as a consequence.

**Independent Test**: `SearchMedicine(query="ibuprofen")` returns 1+ results with valid SUKL code, name, ATC code.

### Implementation for User Story 1

- [ ] T007 [US1] Add persistent diskcache serialization for DrugIndex — save built index to disk after successful build, load from disk on subsequent calls, in src/czechmedmcp/czech/sukl/drug_index.py
- [ ] T008 [US1] Add partial build tolerance — DrugIndex builds successfully even if 30%+ individual drug detail fetches fail, in src/czechmedmcp/czech/sukl/drug_index.py
- [ ] T009 [US1] Increase DrugIndex bulk fetch timeout and add retry logic using async_retry for individual drug detail calls, in src/czechmedmcp/czech/sukl/drug_index.py
- [ ] T010 [US1] Add error isolation in DrugProfile asyncio.gather (return_exceptions=True) in src/czechmedmcp/czech/workflows/drug_profile.py
- [ ] T011 [P] [US1] Write unit test — mock DrugIndex build with partial failures, verify search returns results in tests/tdd/test_sukl_search.py
- [ ] T012 [P] [US1] Write unit test — mock DrugProfile aggregation with partial sub-tool failures in tests/tdd/test_drug_profile.py

**Checkpoint**: `SearchMedicine(query="ibuprofen")` returns results. `DrugProfile(query="ibuprofen")` returns partial profile even if reimbursement sub-call fails. Run: `uv run python -m pytest tests/tdd/test_sukl_search.py tests/tdd/test_drug_profile.py -v`

---

## Phase 4: User Story 2 — NRPZS + SZV fix (Priority: P1) — BUG-002, BUG-003

**Goal**: All 8 NRPZS/SZV tools return data instead of server error.

**Independent Test**: `SearchProviders(city="Brno")` returns providers. `SearchProcedures(query="EKG")` returns procedures.

### Implementation for User Story 2

- [ ] T013 [P] [US2] Fix NRPZS CSV download — increase timeout to BULK_DOWNLOAD_TIMEOUT, add 3x retry with async_retry, add CSV header validation, return informative error on failure in src/czechmedmcp/czech/nrpzs/search.py
- [ ] T014 [P] [US2] Fix SZV Excel download — increase timeout to BULK_DOWNLOAD_TIMEOUT, add 3x retry with async_retry, validate sheet name "Export", return informative error on failure in src/czechmedmcp/czech/szv/search.py
- [ ] T015 [P] [US2] Write unit test — mock NRPZS CSV download success, timeout, and malformed CSV in tests/czech/test_nrpzs.py
- [ ] T016 [P] [US2] Write unit test — mock SZV Excel download success, timeout, and missing sheet in tests/czech/test_szv.py

**Checkpoint**: NRPZS and SZV tools return data or informative error. Run: `uv run python -m pytest tests/czech/test_nrpzs.py tests/czech/test_szv.py -v`

---

## Phase 5: User Story 3 — ArticleSearcher fix (Priority: P1) — BUG-006

**Goal**: ArticleSearcher returns results for gene, chemical, disease, and keyword queries.

**Independent Test**: `ArticleSearcher(genes="BRCA1")` returns article list.

### Implementation for User Story 3

- [ ] T017 [US3] Add graceful degradation to autocomplete — if PubTator3 autocomplete fails for an entity type, proceed with raw query string instead of raising, in src/czechmedmcp/articles/autocomplete.py
- [ ] T018 [US3] Add retry logic with async_retry for PubTator3 search API call in src/czechmedmcp/articles/search.py
- [ ] T019 [US3] Add PubMed E-utilities fallback — if PubTator3 search returns error after retries, fall back to NCBI esearch/efetch in src/czechmedmcp/articles/search.py
- [ ] T020 [P] [US3] Write unit test — mock PubTator3 autocomplete failure, verify search proceeds with raw query in tests/tdd/test_article_search.py
- [ ] T021 [P] [US3] Write unit test — mock PubTator3 search failure, verify PubMed E-utilities fallback returns results in tests/tdd/test_article_search.py

**Checkpoint**: ArticleSearcher returns results even when PubTator3 autocomplete fails. Run: `uv run python -m pytest tests/tdd/test_article_search.py -v`

---

## Phase 6: User Story 4 — PIL/SmPC + profil léku (Priority: P1) — BUG-004

**Goal**: GetPil/GetSpc return document content or functional URL. DrugProfile returns complete profile.

**Independent Test**: `GetSpc("0124137")` returns SmPC content or URL.

### Implementation for User Story 4

- [ ] T022 [US4] Add fallback URL construction for PIL/SmPC — when DLP API metadata returns null, construct SUKL web URL pattern and verify with HTTP HEAD request, in src/czechmedmcp/czech/sukl/getter.py
- [ ] T023 [US4] Update GetPil/GetSpc to try DLP API first, then fallback URL, returning whichever succeeds in src/czechmedmcp/czech/sukl/getter.py
- [ ] T024 [P] [US4] Write unit test — mock DLP API returning null metadata, verify fallback URL is constructed and returned in tests/tdd/test_sukl_getter.py

**Checkpoint**: GetPil/GetSpc return content or URL for common drugs. Run: `uv run python -m pytest tests/tdd/test_sukl_getter.py -v`

---

## Phase 7: P1 Commit Checkpoint

**Purpose**: Verify all P1 bugs are fixed before committing.

- [ ] T025 Run full unit test suite and verify no regressions: `uv run python -m pytest -x --ff -n auto --dist loadscope -m "not integration"`
- [ ] T026 Run tool count regression test: `uv run python -m pytest tests/tdd/test_mcp_integration.py -v` — must report exactly 60 tools
- [ ] T027 Commit P1 fixes: `git add -A && git commit -m "fix: oprava P1 kritických bugů (BUG-001 až BUG-006) — SearchMedicine, NRPZS, SZV, PIL/SmPC, ArticleSearcher"`

---

## Phase 8: User Story 5 — SUKL code normalization (Priority: P2) — BUG-007

**Goal**: All SUKL tools accept 5-7 digit codes transparently.

**Independent Test**: `GetMedicineDetail("124137")` returns same result as `GetMedicineDetail("0124137")`.

*Note: Core normalization already done in Phase 2 (T004-T006). This phase verifies end-to-end behavior.*

- [ ] T028 [US5] Verify normalize_sukl_code is applied in all SUKL tool entry points (czech_tools.py wrappers) — add calls where missing in src/czechmedmcp/czech/czech_tools.py

**Checkpoint**: Already verified by T006 test. Additional e2e confirmation through integration test.

---

## Phase 9: User Story 6 — DiagnosisStats + DiagnosisAssist (Priority: P2) — BUG-008, BUG-009

**Goal**: GetDiagnosisStats returns non-zero epidemiological data. DiagnosisAssist returns candidate diagnoses.

**Independent Test**: `GetDiagnosisStats(code="E11")` returns `total_cases > 0`. `DiagnosisAssist(symptoms="bolest na hrudi, dušnost")` returns non-empty candidates.

### Implementation for User Story 6

- [ ] T029 [US6] Debug GetDiagnosisStats — verify NZIP API endpoint URL and response parsing, fix data mapping if endpoint changed, in src/czechmedmcp/czech/mkn/ stats module
- [ ] T030 [US6] Debug DiagnosisAssist — verify FAISS index initialization, Cohere API connectivity, add keyword-based fallback if embeddings fail, in src/czechmedmcp/czech/mkn/ diagnosis_assist module
- [ ] T031 [P] [US6] Write unit test — mock NZIP API response with non-zero data, verify GetDiagnosisStats returns populated fields in tests/czech/test_mkn_stats.py
- [ ] T032 [P] [US6] Write unit test — mock DiagnosisAssist with embedding failure, verify keyword fallback returns candidates in tests/czech/test_diagnosis_assist.py

**Checkpoint**: Run: `uv run python -m pytest tests/czech/test_mkn_stats.py tests/czech/test_diagnosis_assist.py -v`

---

## Phase 10: User Story 7 — Reimbursement + Error format (Priority: P2) — BUG-010, BUG-011, BUG-012, BUG-013

**Goal**: Reimbursement returns populated data. OpenFDA recall works. Substance names resolved. Error format consistent.

**Independent Test**: `GetReimbursement("0094113")` returns non-null data. Any tool error uses consistent JSON format.

### Implementation for User Story 7

- [ ] T033 [P] [US7] Debug opendata.sukl.cz reimbursement endpoint — verify URL, response format, update VZP static CSV fallback data, add retry in src/czechmedmcp/czech/sukl/reimbursement.py and src/czechmedmcp/czech/vzp/drug_reimbursement.py
- [ ] T034 [P] [US7] Debug OpenFDA recall query construction — fix field names and query format in src/czechmedmcp/openfda/recall.py
- [ ] T035 [P] [US7] Add substance_code → substance_name resolver using SUKL DLP API endpoint in src/czechmedmcp/czech/sukl/getter.py
- [ ] T036 [US7] Apply format_tool_error() from T003 to all Czech tool error paths in src/czechmedmcp/czech/czech_tools.py and src/czechmedmcp/individual_tools.py
- [ ] T037 [P] [US7] Write unit test — mock reimbursement API with populated data, verify non-null fields in tests/czech/test_reimbursement.py
- [ ] T038 [P] [US7] Write unit test — mock OpenFDA recall with results for "ibuprofen" in tests/tdd/test_openfda_recall.py
- [ ] T039 [P] [US7] Write unit test — verify error format consistency across 5+ tool error scenarios in tests/tdd/test_error_format.py

**Checkpoint**: Run: `uv run python -m pytest tests/czech/test_reimbursement.py tests/tdd/test_openfda_recall.py tests/tdd/test_error_format.py -v`

---

## Phase 11: P2 Commit Checkpoint

- [ ] T040 Run full unit test suite: `uv run python -m pytest -x --ff -n auto --dist loadscope -m "not integration"`
- [ ] T041 Run tool count regression: `uv run python -m pytest tests/tdd/test_mcp_integration.py -v`
- [ ] T042 Commit P2 fixes: `git add -A && git commit -m "fix: oprava P2 středně závažných bugů (BUG-007 až BUG-013) — normalizace, diagnózy, úhrady, error format"`

---

## Phase 12: User Story 8 — Drobné opravy kvality (Priority: P3) — BUG-014 to BUG-018

**Goal**: SearchDiagnosis text search returns relevant results. GetPerformanceMetrics works. ArticleGetter returns real abstracts. DrugGetter handles "metformin". GeneGetter output is compact.

**Independent Test**: `SearchDiagnosis(query="hypertenze")` returns hypertension-related results. `DrugGetter("metformin")` returns drug info.

### Implementation for User Story 8

- [ ] T043 [P] [US8] Fix SearchDiagnosis fulltext — debug normalize_query() for Czech text, verify MKN-10 index search logic in src/czechmedmcp/czech/mkn/ search module
- [ ] T044 [P] [US8] Fix GetPerformanceMetrics — debug @track_performance decorator, verify metrics collection persists across calls in src/czechmedmcp/metrics_handler.py
- [ ] T045 [P] [US8] Fix ArticleGetter abstract placeholder — debug PubMed abstract fetch for non-PMC articles, ensure real abstract text is returned in src/czechmedmcp/articles/getter.py
- [ ] T046 [P] [US8] Fix DrugGetter "metformin" — add name normalization for MyChem.info lookup (try lowercase, try synonyms) in src/czechmedmcp/drugs/getter.py
- [ ] T047 [P] [US8] Add field filtering for GeneGetter — limit RefSeq output to top 10 transcripts by default, add summary parameter in src/czechmedmcp/genes/getter.py

**Checkpoint**: Run: `uv run python -m pytest -k "diagnosis_search or metrics or article_getter or drug_getter or gene_getter" -v`

---

## Phase 13: P3 Commit + Final Validation

- [ ] T048 Run full unit test suite: `uv run python -m pytest -x --ff -n auto --dist loadscope -m "not integration"`
- [ ] T049 Run tool count regression: `uv run python -m pytest tests/tdd/test_mcp_integration.py -v`
- [ ] T050 Run `make check` (ruff + pre-commit + mypy + deptry)
- [ ] T051 Commit P3 fixes: `git add -A && git commit -m "fix: oprava P3 bugů (BUG-014 až BUG-018) — text search, metrics, abstrakty, normalizace"`

---

## Phase 14: Polish & Cross-Cutting Concerns

**Purpose**: Final cleanup before PR

- [ ] T052 Update CLAUDE.md Known Issues section — remove fixed issues, document any remaining
- [ ] T053 Run quickstart.md full validation sequence
- [ ] T054 Create PR: `gh pr create --title "fix: oprava 18 MCP tool bugů (46%→80%+ success rate)" --base main`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on T001 (retry util) from Setup
- **US1–US4 (Phases 3–6)**: Depend on Foundational (Phase 2). Can proceed in parallel within P1 group.
- **US5 (Phase 8)**: Depends on Phase 2 (normalization already done)
- **US6–US7 (Phases 9–10)**: Depend on Phase 2. Independent of each other.
- **US8 (Phase 12)**: Independent of other user stories
- **Commit checkpoints (7, 11, 13)**: Sequential gates
- **Polish (Phase 14)**: After all commits

### User Story Dependencies

- **US1 (SearchMedicine)**: Depends on Phase 2. Unlocks DrugProfile/CompareAlternatives.
- **US2 (NRPZS+SZV)**: Depends on Phase 1. Fully independent.
- **US3 (ArticleSearcher)**: Depends on Phase 1. Fully independent.
- **US4 (PIL/SmPC)**: Depends on Phase 2 (SUKL normalization). Independent of US1-US3.
- **US5 (SUKL normalization)**: Core done in Phase 2, verification only.
- **US6 (DiagnosisStats+Assist)**: Fully independent.
- **US7 (Reimbursement+errors)**: Depends on Phase 1 (error util).
- **US8 (P3 quality)**: Fully independent.

### Parallel Opportunities

**Within P1 (Phases 3-6)**:
```
T013 (NRPZS) || T014 (SZV) — different modules, no dependencies
T015 (NRPZS test) || T016 (SZV test) — different test files
T017-T019 (ArticleSearcher) — can run parallel with T013-T014
T022-T024 (PIL/SmPC) — can run parallel with T013-T019
```

**Within P2 (Phases 8-10)**:
```
T029 (DiagnosisStats) || T030 (DiagnosisAssist) — different modules
T033 (Reimbursement) || T034 (OpenFDA) || T035 (Substance names) — different files
All P2 tests (T031-T032, T037-T039) — can run in parallel
```

**Within P3 (Phase 12)**:
```
All T043-T047 are [P] — 5 different modules, fully parallel
```

---

## Implementation Strategy

### MVP First (P1 Only)

1. Complete Phase 1: Setup (T001-T003)
2. Complete Phase 2: Foundational normalization (T004-T006)
3. Complete Phases 3-6: All P1 user stories
4. **STOP and VALIDATE**: Commit P1, run full test suite
5. Expected improvement: 46% → ~65% success rate

### Incremental Delivery

1. P1 commit → 46% → ~65% (critical tools working)
2. P2 commit → ~65% → ~75% (data quality + error consistency)
3. P3 commit → ~75% → ~80%+ (polish + edge cases)

### Single Developer Sequential

```
Day 1: T001-T006 (Setup + Foundational) + T007-T012 (SearchMedicine)
Day 2: T013-T016 (NRPZS+SZV) + T017-T021 (ArticleSearcher)
Day 3: T022-T024 (PIL/SmPC) + T025-T027 (P1 commit)
Day 4: T028-T039 (all P2) + T040-T042 (P2 commit)
Day 5: T043-T054 (P3 + polish + PR)
```

---

## Notes

- [P] tasks = different files, no dependencies — safe to parallelize
- [Story] label maps task to specific user story for traceability
- Commit after each priority phase (P1, P2, P3) — not after each task
- Run `tests/tdd/test_mcp_integration.py` after every commit — tool count must stay 60
- Do NOT use `--timeout` pytest flag (plugin not installed)
- All async tests run automatically (asyncio_mode = "auto")
