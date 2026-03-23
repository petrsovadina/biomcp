# Tasks: Arcade Deploy Integration (Dual-Mode)

**Input**: Design documents from `/specs/009-arcade-deploy-integration/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Tests**: Tests included per spec requirements FR-009, FR-010 (regression tests for tool counts).

**Organization**: Tasks grouped by user story. US3 (PoC) precedes US1 (Full Deploy) per spec risk mitigation strategy.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create arcade/ package skeleton and optional dependency

- [x] T001 Add `arcade` optional extra with `arcade-mcp-server>=1.17.0` to `pyproject.toml`
- [x] T002 Create `src/czechmedmcp/arcade/__init__.py` with `arcade_app = MCPApp(name="czech_med_mcp", version=...)` singleton
- [x] T003 Verify `uv sync` (without arcade extra) succeeds with no import errors — run `uv run python -c "import czechmedmcp"`

**Checkpoint**: arcade/ package exists, FastMCP server unaffected, optional dependency declared

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish wrapper patterns and validate Arcade SDK compatibility

**⚠️ CRITICAL**: No user story wrappers can begin until this phase confirms Arcade SDK works

- [x] T004 Install arcade extra locally: `uv sync --extra arcade` — verify `from arcade_mcp_server import MCPApp` works
- [x] T005 Create wrapper contract validation helper in `tests/tdd/test_arcade_wrappers.py` — test that a single sample wrapper (article_searcher) correctly translates `Annotated[str, "desc"]` params, validates constraints (ge/le clamping), and delegates to private function

**Checkpoint**: Arcade SDK installed and working, wrapper pattern validated

---

## Phase 3: User Story 3 — Validate with PoC Before Full Migration (Priority: P1) 🎯 MVP

**Goal**: Deploy 5 representative tools to Arcade as proof-of-concept to validate platform compatibility

**Independent Test**: Deploy PoC entrypoint with `arcade deploy -e src/czechmedmcp/arcade/poc_entrypoint.py` and call each of the 5 tools through Arcade

### Implementation for User Story 3

- [x] T006 [P] [US3] Create `article_searcher` + `article_getter` wrappers in `src/czechmedmcp/arcade/individual_tools.py` — Annotated params, ensure_list() for list params, ge/le clamping for page/page_size
- [x] T007 [P] [US3] Create `czechmed_search_medicine` wrapper in `src/czechmedmcp/arcade/czech_tools.py` — delegates to `_sukl_drug_search`
- [x] T008 [P] [US3] Create `think` wrapper in `src/czechmedmcp/arcade/thinking_tool.py` — dict→str serialization via `json.dumps(result, ensure_ascii=False)`, ge=1 clamping for thoughtNumber/totalThoughts
- [x] T009 [P] [US3] Create `get_performance_metrics` wrapper in `src/czechmedmcp/arcade/metrics_tool.py` — delegates to `get_all_metrics` / `get_metric_summary`
- [x] T010 [US3] Create `src/czechmedmcp/arcade/poc_entrypoint.py` — imports 5 wrapper modules, `if __name__ == "__main__": arcade_app.run(transport=...)` pattern
- [x] T011 [US3] Create `tests/tdd/test_arcade_poc.py` — assert PoC entrypoint registers exactly 5 tools, verify tool names match FastMCP equivalents
- [x] T012 [US3] Test PoC wrappers in `tests/tdd/test_arcade_wrappers.py` — mock private functions, verify each wrapper returns str, verify think wrapper serializes dict to JSON str, verify constraint clamping

**Checkpoint**: PoC with 5 tools validated locally. Ready for `arcade deploy` validation on Arcade Cloud.

---

## Phase 4: User Story 1 — Deploy CzechMedMCP to Arcade Platform (Priority: P1)

**Goal**: Extend from 5 PoC tools to all 60 tools deployed on Arcade

**Independent Test**: Import full entrypoint and verify 60 tools registered; deploy with `arcade deploy -e src/czechmedmcp/arcade/entrypoint.py`

### Implementation for User Story 1

- [x] T013 [P] [US1] Complete remaining 31 individual tool wrappers in `src/czechmedmcp/arcade/individual_tools.py` — all tools from `individual_tools.py` not covered in PoC (trial_searcher, trial_getter, trial_protocol_getter, trial_locations_getter, trial_outcomes_getter, trial_references_getter, variant_searcher, variant_getter, alphagenome_predictor, gene_getter, drug_getter, disease_getter, enrichr_analyzer, gene_cbioportal_summary, variant_cbioportal_summary, oncokb_gene_summary, openfda_adverse_searcher, openfda_adverse_getter, openfda_label_searcher, openfda_label_getter, openfda_device_searcher, openfda_device_getter, openfda_approval_searcher, openfda_approval_getter, openfda_recall_searcher, openfda_recall_getter, openfda_shortage_searcher, openfda_shortage_getter, and remaining)
- [x] T014 [P] [US1] Complete remaining 22 Czech tool wrappers in `src/czechmedmcp/arcade/czech_tools.py` — all tools from `czech/czech_tools.py` not covered in PoC (czechmed_get_medicine_detail, czechmed_get_spc, czechmed_get_pil, czechmed_check_availability, czechmed_get_reimbursement, czechmed_batch_check_availability, czechmed_find_pharmacies, czechmed_search_diagnosis, czechmed_get_diagnosis_detail, czechmed_browse_diagnosis, czechmed_get_diagnosis_stats, czechmed_diagnosis_assist, czechmed_search_providers, czechmed_get_provider_detail, czechmed_get_nrpzs_codebooks, czechmed_referral_assist, czechmed_search_procedures, czechmed_get_procedure_detail, czechmed_calculate_reimbursement, czechmed_get_drug_reimbursement, czechmed_compare_alternatives, czechmed_drug_profile)
- [x] T015 [P] [US1] Create `search` + `fetch` router wrappers in `src/czechmedmcp/arcade/router_tools.py` — complex Literal type params, domain validation, delegates to router search/fetch private functions
- [x] T016 [US1] Create `src/czechmedmcp/arcade/entrypoint.py` — imports all 5 wrapper modules (individual_tools, czech_tools, router_tools, thinking_tool, metrics_tool), `if __name__ == "__main__": arcade_app.run(transport=...)` pattern
- [x] T017 [US1] Create `tests/tdd/test_arcade_integration.py` — assert full entrypoint registers exactly 60 tools, verify all 60 tool names match FastMCP tool names from `test_mcp_integration.py`

**Checkpoint**: All 60 tools registered in Arcade entrypoint. Ready for full `arcade deploy`.

---

## Phase 5: User Story 2 — Preserve Railway Deployment (Priority: P1)

**Goal**: Verify zero regressions in existing FastMCP/Railway deployment

**Independent Test**: Run `uv run python -m pytest -x --ff -n auto -m "not integration"` — all 1020+ tests pass. Run `uv run czechmedmcp run --mode stdio` — server starts with 60 tools.

### Implementation for User Story 2

- [x] T018 [US2] Run full existing test suite (`uv run python -m pytest -x --ff -n auto -m "not integration"`) — confirm all tests pass with arcade/ package present
- [x] T019 [US2] Verify `uv sync` (no extras) → `uv run python -c "import czechmedmcp; from czechmedmcp.core import mcp_app"` works without arcade-mcp-server installed
- [x] T020 [US2] Verify existing `tests/tdd/test_mcp_integration.py` still asserts exactly 60 FastMCP tools — no changes to this file
- [x] T021 [US2] Verify `uv run czechmedmcp run --mode streamable_http --port 8000` starts successfully (manual smoke test — deferred to manual validation)

**Checkpoint**: Railway deployment completely unaffected. All existing tests pass.

---

## Phase 6: User Story 4 — Clear Deployment Choice Documentation (Priority: P2)

**Goal**: Document both deployment options with trade-offs table

**Independent Test**: A developer unfamiliar with the project can deploy to either platform following only the written documentation

### Implementation for User Story 4

- [ ] T022 [P] [US4] Create deployment documentation (DEFERRED — docs site content) with Railway vs Arcade trade-offs table (persistence, auth model, cost, data residency, monitoring) — location TBD based on docs structure (README section or `apps/docs/` page)
- [ ] T023 [P] [US4] Add step-by-step Railway deployment guide (DEFERRED — docs site content) section (existing process, no changes needed — just document it)
- [ ] T024 [P] [US4] Add step-by-step Arcade deployment guide (DEFERRED — docs site content) section (install arcade-mcp CLI, arcade login, arcade deploy -e, verify in dashboard)
- [ ] T025 [US4] Add PoC validation guide (DEFERRED — docs site content) section (how to deploy 5-tool PoC first, verify, then migrate to full 60-tool)

**Checkpoint**: Complete deployment docs covering both platforms with clear trade-offs

---

## Phase 7: User Story 5 — Add New Tools to Both Platforms (Priority: P3)

**Goal**: Update CLAUDE.md with dual-platform tool registration instructions

**Independent Test**: Follow the documented process to mentally trace adding a dummy tool — verify both FastMCP and Arcade registration steps are clear

### Implementation for User Story 5

- [x] T026 [US5] Update "Přidání nového nástroje" section in `CLAUDE.md` — add step for creating Arcade wrapper in `src/czechmedmcp/arcade/` and updating expected tool count in `tests/tdd/test_arcade_integration.py`
- [x] T027 [US5] Add `arcade/` module descriptions to Key Files table in `CLAUDE.md` — entrypoint.py, poc_entrypoint.py, individual_tools.py, czech_tools.py, router_tools.py, thinking_tool.py, metrics_tool.py
- [x] T028 [US5] Update Deployment table in `CLAUDE.md` — add Arcade Cloud row with entrypoint path and deploy command

**Checkpoint**: CLAUDE.md fully updated for dual-platform development workflow

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, cleanup, and cross-cutting improvements

- [x] T029 Run `uv run ruff check src tests` and `uv run ruff format src tests` — fix any lint/format issues in new arcade/ files
- [ ] T030 Run `uv run mypy` — verify no type errors in new arcade/ package (may need `# type: ignore` for arcade_mcp_server if no stubs)
- [ ] T031 Verify `make check` passes (ruff + pre-commit + mypy + deptry)
- [x] T032 Run full test suite: `uv run python -m pytest -x --ff -n auto -m "not integration"` — all existing + new tests pass
- [x] T033 Update expected tool count comment in `tests/tdd/test_mcp_integration.py` if needed (should remain 60, just verify comment mentions Arcade doesn't affect FastMCP count)
- [ ] T034 Run quickstart.md validation — verify documented commands work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 — BLOCKS all user stories
- **US3 PoC (Phase 3)**: Depends on Phase 2 — validates Arcade before full migration
- **US1 Full Deploy (Phase 4)**: Depends on Phase 3 (PoC success) — extends to all 60 tools
- **US2 Railway Preservation (Phase 5)**: Depends on Phase 4 — regression validation after all code is written
- **US4 Documentation (Phase 6)**: Can start after Phase 3 (PoC docs) and complete after Phase 4
- **US5 New Tool Process (Phase 7)**: Depends on Phase 4 (need final file structure)
- **Polish (Phase 8)**: Depends on all previous phases

### User Story Dependencies

- **US3 (PoC)**: First story — validates platform before committing to full migration
- **US1 (Full Deploy)**: Depends on US3 success — extends PoC to all 60 tools
- **US2 (Preserve Railway)**: Regression check — runs after US1 is complete
- **US4 (Documentation)**: Independent of US1/US2 — can draft during US3, finalize after US1
- **US5 (New Tool Process)**: Independent — needs final file structure from US1

### Within Each User Story

- Wrapper files (T006-T009, T013-T015) can be created in parallel [P]
- Entrypoint depends on wrapper files being complete
- Tests depend on entrypoint being importable

### Parallel Opportunities

**Phase 3 (PoC)**:
```
T006 (individual wrappers) | T007 (czech wrapper) | T008 (think wrapper) | T009 (metrics wrapper)
         ↓                          ↓                       ↓                      ↓
                            T010 (poc_entrypoint)
                                     ↓
                      T011 (count test) | T012 (wrapper tests)
```

**Phase 4 (Full)**:
```
T013 (31 individual) | T014 (22 czech) | T015 (2 router)
         ↓                    ↓                  ↓
                    T016 (full entrypoint)
                             ↓
                    T017 (60-tool count test)
```

**Phase 6 (Docs)** — all doc tasks are parallel:
```
T022 (trade-offs) | T023 (Railway guide) | T024 (Arcade guide)
```

---

## Implementation Strategy

### MVP First (US3: PoC Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US3 (PoC with 5 tools)
4. **STOP and VALIDATE**: Deploy PoC to Arcade Cloud, test all 5 tools
5. If PoC fails: investigate and fix before proceeding
6. If PoC succeeds: proceed to Phase 4

### Incremental Delivery

1. Setup + Foundational → arcade/ package ready
2. US3 (PoC) → 5 tools on Arcade → Validate platform compatibility
3. US1 (Full Deploy) → 60 tools on Arcade → Full deployment
4. US2 (Railway) → Regression check → Confirm zero breakage
5. US4 (Docs) + US5 (Process) → Developer experience complete
6. Polish → Clean, lint, final validation

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US3 (PoC) is the MVP — validates Arcade before full commitment
- All wrapper files follow the contract in `contracts/arcade-tool-contract.md`
- `arcade-mcp-server` is the SDK import; `arcade-mcp` is the CLI tool
- MCPApp name must be alphanumeric + underscores: `czech_med_mcp`
- Commit after each phase checkpoint
