# Tasks: CzechMedMCP Implementation

**Input**: Design documents from `/specs/001-czechmedmcp-implementation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Unit tests included per Constitution Principle V (Testing Rigor) — all new features MUST include unit tests with mocked HTTP.

**Organization**: Tasks grouped by user story. Each user story independently testable after completion.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US9)
- Exact file paths included in all task descriptions

---

## Phase 1: Setup

**Purpose**: Shared infrastructure for all new Czech tools

- [x] T001 Create dual output utility `format_czech_response()` in `src/biomcp/czech/response.py` — returns JSON string with `content` (Markdown) + `structuredContent` (dict), per FR-025 and contracts
- [x] T002 [P] Add new constants to `src/biomcp/constants.py` — SUKL reimbursement URL (`https://opendata.sukl.cz/api/v1/uhrada`), NZIP stats URL (`https://reporting.uzis.cz/cr/index.php?pg=statisticke-vystupy--mzdy-a-platy`), NZIP CSV download base URL, pharmacy API URL (`https://opendata.sukl.cz/api/v1/lecebna-zarizeni`), insurance rate table (VZP 1.15/VoZP 1.10/ČPZP 1.12/OZP 1.11/ZPŠ 1.09/ZPMV 1.13/RBP 1.08 CZK/bod), diagnosis-to-specialty mapping table (I→kardiologie, J→alergologie, M→revmatologie, etc.)
- [x] T003 [P] Create `src/biomcp/czech/workflows/__init__.py` empty module package
- [x] T004 [P] Unit test for `format_czech_response()` in `tests/czech/test_czech_response.py` — verify Markdown content + JSON structuredContent in output

**Checkpoint**: Shared utilities ready — Foundation phase can begin

---

## Phase 2: Foundation (Blocking Prerequisites)

**Purpose**: Rename all 14 existing tools to `czechmed_*` prefix (FR-024), fix known bugs

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Rename all 14 tool functions in `src/biomcp/czech/czech_tools.py` from `sukl_*/mkn_*/nrpzs_*/szv_*/vzp_*` to `czechmed_*` per research.md R1 mapping table — update function names, decorator names, `@track_performance()` metric keys
- [x] T006 Update `tests/czech/test_tool_registration.py` — change expected tool names to `czechmed_*` prefix, keep count at 14 (temporarily)
- [x] T007 Update `tests/tdd/test_mcp_integration.py` — update any tool name assertions to `czechmed_*` prefix, keep total count at 51
- [x] T008 [P] Fix NRPZS pagination bug in `src/biomcp/czech/nrpzs/search.py` — replace `(page - 1) * page_size` with `compute_skip(page, page_size)` from `biomcp.constants`
- [x] T009 [P] Fix SZV hardcoded timeout in `src/biomcp/czech/szv/search.py` — replace `60.0` with `CZECH_HTTP_TIMEOUT` from `biomcp.constants`
- [x] T010 [P] Fix VZP hardcoded timeout in `src/biomcp/czech/vzp/search.py` — replace `60.0` with `CZECH_HTTP_TIMEOUT` from `biomcp.constants`
- [x] T011 Run full test suite to verify rename + fixes: `uv run python -m pytest tests/czech/ tests/tdd/test_mcp_integration.py -v`

**Checkpoint**: Foundation ready — all existing tools renamed, bugs fixed, tests pass. User story implementation can begin.

---

## Phase 3: User Story 1 — Lékař vyhledává informace o léku (Priority: P1) 🎯 MVP

**Goal**: SÚKL base tools with `czechmed_` prefix + new reimbursement tool. Lékař může vyhledat lék, získat detail, zkontrolovat dostupnost a zjistit úhradu.

**Independent Test**: `czechmed_search_drug("ibuprofen")` → výsledky → `czechmed_get_drug_detail(sukl_code)` → detail → `czechmed_check_availability(sukl_code)` → stav → `czechmed_get_reimbursement(sukl_code)` → úhrada

### Implementation for User Story 1

- [x] T012 [P] [US1] Create `Reimbursement` Pydantic model in `src/biomcp/czech/sukl/models.py` per data-model.md — fields: sukl_code, name, manufacturer_price, max_retail_price, reimbursement_amount, patient_copay, reimbursement_group, conditions, valid_from, valid_to
- [x] T013 [P] [US1] Create `src/biomcp/czech/sukl/reimbursement.py` with `_get_reimbursement(sukl_code: str) -> str` — fetch from SÚKL API reimbursement endpoint, parse response, return via `format_czech_response()`
- [x] T014 [US1] Register `czechmed_get_reimbursement` tool in `src/biomcp/czech/czech_tools.py` — `@mcp_app.tool()`, `@track_performance("czechmedmcp.get_reimbursement")`, signature per contracts/sukl-tools.md
- [ ] T015 [P] [US1] Retrofit dual output to existing SÚKL tools — update `_sukl_drug_search()`, `_sukl_drug_details()`, `_sukl_availability_check()` in `src/biomcp/czech/sukl/search.py`, `getter.py`, `availability.py` to use `format_czech_response()`
- [x] T016 [P] [US1] Unit test for `_get_reimbursement()` in `tests/czech/test_sukl_reimbursement.py` — mock httpx response, verify Reimbursement model fields, verify dual output format
- [x] T017 [US1] Update tool count in `tests/czech/test_tool_registration.py` from 14 to 15 (added reimbursement)
- [x] T018 [US1] Update tool count in `tests/tdd/test_mcp_integration.py` from 51 to 52 (37 BioMCP + 15 Czech)

**Checkpoint**: US1 complete — 6 SÚKL tools functional (search, detail, availability, reimbursement, PIL meta, SPC meta). MVP deliverable.

---

## Phase 4: User Story 2 — Hromadná kontrola dostupnosti (Priority: P1)

**Goal**: Batch availability check for 1-50 drugs in parallel

**Independent Test**: `czechmed_batch_check_availability(["0012345", "0012346", "0012347"])` → status pro každý lék + summary counts

### Implementation for User Story 2

- [x] T019 [P] [US2] Create `BatchAvailabilityItem` and `BatchAvailabilityResult` models in `src/biomcp/czech/sukl/models.py` per data-model.md
- [x] T020 [US2] Implement `_batch_availability(sukl_codes: list[str]) -> str` in `src/biomcp/czech/sukl/availability.py` — use `asyncio.gather(*[_check_distribution(code) for code in codes], return_exceptions=True)`, aggregate results, return via `format_czech_response()`
- [x] T021 [US2] Register `czechmed_batch_check_availability` in `src/biomcp/czech/czech_tools.py` — signature per contracts/sukl-tools.md, `min_length=1, max_length=50` on `sukl_codes`
- [x] T022 [P] [US2] Unit test in `tests/czech/test_sukl_batch.py` — test parallel execution, partial failure tolerance (some codes invalid), empty list validation, >50 codes validation
- [x] T023 [US2] Update tool counts: `test_tool_registration.py` 15→16, `test_mcp_integration.py` 52→53 (37+16)

**Checkpoint**: US2 complete — batch availability functional

---

## Phase 5: User Story 4 — Kódování diagnóz a evidence (Priority: P1)

**Goal**: MKN-10 base tools enhanced + new epidemiological stats + diagnosis assistant workflow

**Independent Test**: `czechmed_search_diagnosis("akutní zánět hltanu")` → MKN-10 kódy → `czechmed_get_diagnosis_detail("J06.9")` → hierarchie → `czechmed_get_diagnosis_stats("J06", 2024)` → statistika → `czechmed_diagnosis_assistant("akutní zánět hltanu")` → kódy + PubMed

### Implementation for User Story 4

- [ ] T024 [P] [US4] Create `DiagnosisStats`, `AgeGroupStats`, `RegionStats` models in `src/biomcp/czech/mkn/models.py` per data-model.md
- [ ] T025 [P] [US4] Retrofit dual output to existing MKN-10 tools — update `_mkn_search()`, `_mkn_get()`, `_mkn_browse()` in `src/biomcp/czech/mkn/search.py` to use `format_czech_response()`
- [ ] T026 [US4] Create `src/biomcp/czech/mkn/stats.py` with `_get_diagnosis_stats(code: str, year: int | None) -> str` — download NZIP open data CSV, filter by MKN-10 code prefix, aggregate by gender/age/region, cache with TTL 7 days
- [ ] T027 [US4] Register `czechmed_get_diagnosis_stats` in `src/biomcp/czech/czech_tools.py` — signature per contracts/mkn-tools.md
- [ ] T028 [US4] Create `DiagnosisAssistantResult` model in `src/biomcp/czech/mkn/models.py` per data-model.md — fields: query, candidates, evidence, disclaimer
- [ ] T029 [US4] Create `src/biomcp/czech/workflows/diagnosis_assistant.py` with `_diagnosis_assistant(symptoms: str, max_candidates: int) -> str` — orchestrate: search MKN-10 → get detail for top → PubMed evidence via `from biomcp.articles.search import _article_searcher` → assemble with disclaimer, use `asyncio.gather` with `return_exceptions=True`
- [ ] T030 [US4] Register `czechmed_diagnosis_assistant` in `src/biomcp/czech/czech_tools.py` — signature per contracts/workflow-tools.md
- [ ] T031 [P] [US4] Unit test for stats in `tests/czech/test_mkn_stats.py` — mock NZIP CSV response, verify aggregation by gender/age/region
- [ ] T032 [P] [US4] Unit test for workflow in `tests/czech/test_workflow_diagnosis.py` — mock MKN search + PubMed, verify graceful degradation when PubMed fails, verify disclaimer present
- [ ] T033 [US4] Update tool counts: `test_tool_registration.py` 16→18, `test_mcp_integration.py` 53→55 (37+18)

**Checkpoint**: US4 complete — MKN-10 base + stats + diagnostic assistant workflow functional

---

## Phase 6: User Story 8 — Příbalová informace a SPC (Priority: P2)

**Goal**: Enhanced PIL/SPC tools with actual text content and section filtering

**Independent Test**: `czechmed_get_pil("0012345", section="side_effects")` → text sekce nežádoucích účinků

### Implementation for User Story 8

- [ ] T034 [P] [US8] Create `DocumentSection` and `DocumentContent` models in `src/biomcp/czech/sukl/models.py` per data-model.md
- [ ] T035 [US8] Enhance `_sukl_pil_getter()` in `src/biomcp/czech/sukl/getter.py` — add HTML scraping of PIL document from `sukl.cz`, parse sections (dosage, contraindications, side_effects, interactions, pregnancy, storage), return content via `format_czech_response()`, fall back to URL-only on parse error
- [ ] T036 [US8] Enhance `_sukl_spc_getter()` in `src/biomcp/czech/sukl/getter.py` — add HTML scraping of SPC document, parse numbered sections (4.1-4.9, 5.1-5.3, 6.1-6.6), add `section` parameter to tool signature in `czech_tools.py`
- [ ] T037 [P] [US8] Unit test in `tests/czech/test_sukl_pil_spc.py` — mock HTML responses, verify section parsing, verify fallback to URL on parse error, verify section filter parameter

**Checkpoint**: US8 complete — PIL/SPC return actual text content with section filtering

---

## Phase 7: User Story 6 — Kalkulace úhrad výkonů (Priority: P2)

**Goal**: SZV procedure tools + new reimbursement calculation per insurance company

**Independent Test**: `czechmed_search_procedure("EKG")` → výkon → `czechmed_get_procedure_detail("09543")` → detail → `czechmed_calculate_reimbursement("09543", insurance_code="111", count=2)` → 805.00 CZK

### Implementation for User Story 6

- [ ] T038 [P] [US6] Create `ReimbursementCalculation` model in `src/biomcp/czech/szv/models.py` per data-model.md
- [ ] T039 [P] [US6] Retrofit dual output to existing SZV tools — update `_szv_search()`, `_szv_get()` in `src/biomcp/czech/szv/search.py` to use `format_czech_response()`
- [ ] T040 [US6] Create `src/biomcp/czech/szv/reimbursement.py` with `_calculate_reimbursement(code: str, insurance_code: str, count: int) -> str` — lookup procedure point_value, lookup rate from insurance rate table in constants, calculate: unit_price = points × rate, total = unit_price × count, return via `format_czech_response()`
- [ ] T041 [US6] Register `czechmed_calculate_reimbursement` in `src/biomcp/czech/czech_tools.py` — signature per contracts/szv-tools.md with insurance_code pattern, default "111"
- [ ] T042 [P] [US6] Unit test in `tests/czech/test_szv_reimbursement.py` — verify calculation for VZP (111), VoZP (201), invalid insurance code, unknown procedure
- [ ] T043 [US6] Update tool counts: `test_tool_registration.py` 18→19, `test_mcp_integration.py` 55→56 (37+19)

**Checkpoint**: US6 complete — SZV search + detail + reimbursement calculation functional

---

## Phase 8: User Story 7 — Cenové alternativy léku (Priority: P2)

**Goal**: VZP drug reimbursement + cross-module alternative comparison (SÚKL + VZP)

**Independent Test**: `czechmed_get_vzp_reimbursement("0012345")` → úhrada VZP → `czechmed_compare_alternatives("0012345")` → alternativy seřazené dle doplatku

### Implementation for User Story 7

- [ ] T044 [P] [US7] Create `DrugReimbursement`, `DrugAlternative`, `AlternativeComparison` models in `src/biomcp/czech/vzp/models.py` per data-model.md
- [ ] T045 [US7] Repurpose `_vzp_search()` in `src/biomcp/czech/vzp/search.py` — rename to `_get_vzp_drug_reimbursement(sukl_code)`, implement VZP drug price list scraping from `vzp.cz/poskytovatele`, parse HTML, extract reimbursement group/max price/coverage/copay/conditions, return via `format_czech_response()`
- [ ] T046 [US7] Implement `_compare_alternatives(sukl_code)` in `src/biomcp/czech/vzp/search.py` — get reference drug detail from SÚKL (extract ATC), search SÚKL by ATC → get VZP reimbursement for each → sort by copay, return via `format_czech_response()`
- [ ] T047 [US7] Update tool registrations in `src/biomcp/czech/czech_tools.py` — rename `czechmed_get_vzp_reimbursement` and `czechmed_compare_alternatives` with signatures per contracts/vzp-tools.md
- [ ] T048 [P] [US7] Unit test in `tests/czech/test_vzp_drug_reimb.py` — mock VZP HTML + SÚKL API, verify reimbursement parsing, verify alternative sorting by copay, verify savings calculation, verify graceful degradation on VZP HTML change
- [ ] T049 [US7] Update existing VZP tests in `tests/czech/test_vzp_search.py` to match repurposed module

**Checkpoint**: US7 complete — VZP drug reimbursement + alternative comparison functional

---

## Phase 9: User Story 5 — Hledání specialisty pro odeslání (Priority: P2)

**Goal**: NRPZS provider tools enhanced + codebooks + referral assistant workflow

**Independent Test**: `czechmed_get_codebooks("specialties")` → číselník → `czechmed_search_provider(city="Brno", specialty="kardiologie")` → poskytovatelé → `czechmed_referral_assistant(diagnosis_code="I25.1", city="Brno")` → doporučení

### Implementation for User Story 5

- [ ] T050 [P] [US5] Create `CodebookItem` and `Codebook` models in `src/biomcp/czech/nrpzs/models.py` per data-model.md
- [ ] T051 [P] [US5] Retrofit dual output to existing NRPZS tools — update `_nrpzs_search()`, `_nrpzs_get()` in `src/biomcp/czech/nrpzs/search.py` to use `format_czech_response()`
- [ ] T052 [US5] Implement `_get_codebooks(codebook_type: str) -> str` in `src/biomcp/czech/nrpzs/search.py` — load NRPZS CSV, extract unique sorted values from `ZZ_obor_pece`/`ZZ_forma_pece`/`ZZ_druh_pece` based on type, return via `format_czech_response()`
- [ ] T053 [US5] Register `czechmed_get_codebooks` in `src/biomcp/czech/czech_tools.py` — signature per contracts/nrpzs-tools.md
- [ ] T054 [US5] Create `ReferralResult` model in `src/biomcp/czech/nrpzs/models.py` per data-model.md
- [ ] T055 [US5] Create `src/biomcp/czech/workflows/referral_assistant.py` with `_referral_assistant(diagnosis_code: str, city: str, max_providers: int) -> str` — get diagnosis detail → map chapter/block to specialty via mapping table in constants → search NRPZS by city+specialty, return via `format_czech_response()`
- [ ] T056 [US5] Register `czechmed_referral_assistant` in `src/biomcp/czech/czech_tools.py` — signature per contracts/workflow-tools.md
- [ ] T057 [P] [US5] Unit test for codebooks in `tests/czech/test_nrpzs_codebooks.py` — mock CSV, verify extraction of unique specialties/care_forms/care_types
- [ ] T058 [P] [US5] Unit test for workflow in `tests/czech/test_workflow_referral.py` — mock MKN detail + NRPZS search, verify specialty mapping, verify graceful degradation
- [ ] T059 [US5] Update tool counts: `test_tool_registration.py` 19→21, `test_mcp_integration.py` 56→58 (37+21)

**Checkpoint**: US5 complete — NRPZS providers + codebooks + referral assistant workflow functional

---

## Phase 10: User Story 3 — Kompletní profil léku (Priority: P1)

**Goal**: Drug profile workflow orchestrating SÚKL + PubMed in one call

**Depends on**: US1 (SÚKL tools must be complete)

**Independent Test**: `czechmed_drug_profile("ibuprofen")` → kompletní profil se sekcemi registration + availability + reimbursement + evidence

### Implementation for User Story 3

- [ ] T060 [P] [US3] Create `DrugProfileSection` and `DrugProfile` models in `src/biomcp/czech/sukl/models.py` per data-model.md
- [ ] T061 [US3] Create `src/biomcp/czech/workflows/drug_profile.py` with `_drug_profile(query: str) -> str` — search drug → extract sukl_code → `asyncio.gather(detail, availability, reimbursement, PubMed via from biomcp.articles.search import _article_searcher, return_exceptions=True)` → assemble sections with status per contracts/workflow-tools.md, return via `format_czech_response()`
- [ ] T062 [US3] Register `czechmed_drug_profile` in `src/biomcp/czech/czech_tools.py` — signature per contracts/workflow-tools.md
- [ ] T063 [P] [US3] Unit test in `tests/czech/test_workflow_drug.py` — mock all 4 sub-calls, verify parallel execution, verify graceful degradation (1 source fails → 3 sections OK + 1 error), verify all-fail scenario
- [ ] T064 [US3] Update tool counts: `test_tool_registration.py` 21→22, `test_mcp_integration.py` 58→59 (37+22)

**Checkpoint**: US3 complete — drug profile workflow functional with graceful degradation

---

## Phase 11: User Story 9 — Hledání lékáren (Priority: P3)

**Goal**: Pharmacy search by city, postal code, or 24/7 filter

**Independent Test**: `czechmed_find_pharmacies(city="Praha", nonstop_only=True)` → seznam lékáren

### Implementation for User Story 9

- [ ] T065 [P] [US9] Create `Pharmacy` and `PharmacySearchResult` models in `src/biomcp/czech/sukl/models.py` per data-model.md
- [ ] T066 [US9] Implement `_find_pharmacies(city, postal_code, nonstop_only, page, page_size) -> str` in `src/biomcp/czech/sukl/search.py` — fetch pharmacy list from SÚKL API, filter by city/postal_code/nonstop, paginate with `compute_skip()`, return via `format_czech_response()`
- [ ] T067 [US9] Register `czechmed_find_pharmacies` in `src/biomcp/czech/czech_tools.py` — signature per contracts/sukl-tools.md, validate at least city or postal_code provided
- [ ] T068 [P] [US9] Unit test in `tests/czech/test_sukl_pharmacies.py` — mock SÚKL pharmacy API, verify city filter, nonstop filter, missing city+postal_code validation error
- [ ] T069 [US9] Update tool counts: `test_tool_registration.py` 22→23, `test_mcp_integration.py` 59→60 (37+23)

**Checkpoint**: US9 complete — pharmacy search functional. Total: 60 tools (37 BioMCP + 23 Czech). ✓

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, integration tests

- [ ] T070 Verify final tool count — run `uv run python -m pytest tests/tdd/test_mcp_integration.py -v` and ensure exactly 60 tools registered (37 BioMCP + 23 Czech)
- [ ] T071 Verify Czech tool count — run `uv run python -m pytest tests/czech/test_tool_registration.py -v` and ensure exactly 23 Czech tools
- [ ] T072 [P] Update `CLAUDE.md` — change tool count from 51 to 60, add 9 new Czech tools to architecture section, update `czech_tools.py` description from 14 to 23 tools
- [ ] T073 [P] Update `README.md` — add new Czech tools to feature list, update total tool count
- [ ] T074 [P] Register new endpoints in `src/biomcp/utils/endpoint_registry.py` — SÚKL reimbursement, SUKL pharmacy, NZIP stats, VZP drug pricing
- [ ] T075 [P] Update `THIRD_PARTY_ENDPOINTS.md` — document all new external API endpoints with URLs, rate limits, data types
- [ ] T076 Run full test suite: `uv run python -m pytest -x --ff -n auto --dist loadscope`
- [ ] T077 Run lint + type check: `uv run ruff check src tests && uv run mypy`
- [ ] T078 [P] Create integration tests in `tests/czech_integration/test_new_tools_api.py` — live API tests for reimbursement, pharmacy, stats (all marked `@pytest.mark.integration`)
- [ ] T079 Run quickstart.md validation — follow quickstart.md steps end-to-end, verify all phases work
- [ ] T080 [P] Performance benchmark: verify SC-002 (SÚKL search <2s), SC-005 (MKN-10 offline <100ms), SC-006 (SZV offline <100ms) in `tests/czech_integration/test_performance.py` — timed assertions with `@pytest.mark.integration`
- [ ] T081 [P] Performance benchmark: verify SC-003 (batch 50 drugs <10s), SC-004 (drug profile workflow <10s) in `tests/czech_integration/test_performance.py` — timed assertions with `@pytest.mark.integration`
- [ ] T082 [P] Verify FR-026 diacritics: add test in `tests/czech/test_diacritics_new_tools.py` — search "léčivo" vs "lecivo" returns identical results for all new search tools (reimbursement, pharmacies, codebooks)
- [ ] T083 [P] Verify FR-027 caching: add test in `tests/czech/test_cache_config.py` — verify cache TTL configuration for all new endpoints (SÚKL reimbursement, NZIP stats, VZP pricing, pharmacy API)

**Checkpoint**: All 23 Czech tools implemented, tested, documented. Total: 60 tools (37 BioMCP + 23 Czech). Performance validated. Ready for deployment.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundation (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundation — MVP, start first
- **US2 (Phase 4)**: Depends on US1 (uses `_check_distribution()`)
- **US4 (Phase 5)**: Depends on Foundation — can run parallel with US1
- **US8 (Phase 6)**: Depends on Foundation — can run parallel with US1
- **US6 (Phase 7)**: Depends on Foundation — can run parallel with US1
- **US7 (Phase 8)**: Depends on US1 (needs SÚKL detail for ATC code)
- **US5 (Phase 9)**: Depends on Foundation — can run parallel with US1 (workflow part depends on US4 for MKN detail)
- **US3 (Phase 10)**: Depends on US1 (uses all SÚKL tools + reimbursement)
- **US9 (Phase 11)**: Depends on Foundation — can run parallel with US1
- **Polish (Phase 12)**: Depends on all user stories complete

### User Story Dependencies

```
Foundation ──▶ US1 (P1: SÚKL base) ──▶ US2 (P1: batch)
    │                    │                      │
    │                    ├──▶ US7 (P2: VZP alt)  │
    │                    │                      │
    │                    └──▶ US3 (P1: drug profile workflow)
    │
    ├──▶ US4 (P1: MKN-10 + diagnosis workflow)
    │         │
    │         └──▶ US5 (P2: NRPZS + referral workflow, needs MKN mapping)
    │
    ├──▶ US6 (P2: SZV reimbursement) [independent]
    ├──▶ US8 (P2: PIL/SPC enhance) [independent]
    └──▶ US9 (P3: pharmacies) [independent]
```

### Within Each User Story

- Models before implementation
- Implementation before tool registration
- Tool registration before count update
- Tests can be written in parallel [P] with models

### Parallel Opportunities

**After Foundation completes, these can run in parallel:**
- US1 + US4 + US6 + US8 + US9 (all independent)

**After US1 completes, these can start:**
- US2 + US7 + US3 (all depend on SÚKL base tools)

**Within each user story, [P] tasks can run in parallel:**
- Model creation + test writing + dual output retrofit

---

## Parallel Example: User Story 1

```bash
# These 3 tasks can run in parallel (different files):
Task T012: "Create Reimbursement model in src/biomcp/czech/sukl/models.py"
Task T015: "Retrofit dual output to existing SUKL tools"
Task T016: "Unit test for reimbursement in tests/czech/test_sukl_reimbursement.py"

# Then sequentially:
Task T013: "Create reimbursement.py" (needs T012 model)
Task T014: "Register tool" (needs T013 implementation)
Task T017-T018: "Update counts" (needs T014 registration)
```

## Parallel Example: US4 + US6 + US8 + US9

```bash
# All four user stories can run in parallel after Foundation:
Agent A: US4 (MKN-10 stats + diagnosis workflow)
Agent B: US6 (SZV reimbursement calculation)
Agent C: US8 (PIL/SPC content enhancement)
Agent D: US9 (Pharmacy search)
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup (T001-T004)
2. Complete Phase 2: Foundation (T005-T011)
3. Complete Phase 3: User Story 1 (T012-T018)
4. **STOP and VALIDATE**: Test `czechmed_search_drug` → `czechmed_get_drug_detail` → `czechmed_check_availability` → `czechmed_get_reimbursement` end-to-end
5. Deploy/demo if ready — 52 tools functional (37 BioMCP + 15 Czech)

### Incremental Delivery

1. Setup + Foundation → 51 tools (renamed, 37+14) ✅
2. + US1 → 52 tools (37+15, + reimbursement) ✅
3. + US2 → 53 tools (37+16, + batch availability) ✅
4. + US4 → 55 tools (37+18, + stats + diagnosis assistant) ✅
5. + US6 → 56 tools (37+19, + SZV calculation) ✅
6. + US5 → 58 tools (37+21, + codebooks + referral assistant) ✅
7. + US3 → 59 tools (37+22, + drug profile workflow) ✅
8. + US7 → 59 tools (repurposed, no net change) ✅
9. + US8 → 59 tools (enhanced, no net change) ✅
10. + US9 → 60 tools (37+23, + pharmacy search) ✅ FINAL

### Parallel Team Strategy

With multiple agents:

1. All complete Setup + Foundation together
2. Once Foundation done:
   - Agent A: US1 → US2 → US3 (SÚKL chain)
   - Agent B: US4 → US5 (MKN/NRPZS chain)
   - Agent C: US6 + US8 + US9 (independent tools)
   - Agent D: US7 (after Agent A finishes US1)
3. All agents join for Phase 12: Polish

---

## Notes

- [P] tasks = different files, no dependencies — safe for parallel execution
- [Story] labels map every task to its user story for traceability
- Each user story is independently testable after its checkpoint
- All tools return dual output (Markdown + JSON) via `format_czech_response()`
- All `json.dumps()` must use `ensure_ascii=False` per constitution
- All HTTP timeouts must use `CZECH_HTTP_TIMEOUT` constant
- All pagination must use `compute_skip()` function
- Run `uv run python -m pytest -x --ff -n auto --dist loadscope` after each phase
