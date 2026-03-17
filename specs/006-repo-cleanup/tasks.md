# Tasks: Repository Cleanup

**Input**: Design documents from `/specs/006-repo-cleanup/`
**Prerequisites**: plan.md (required), spec.md (required), research.md

**Tests**: Not requested. Validation via existing test suite.

**Organization**: US1 → US2 (sequential, pydantic-ai safe after test deletion) → US3 (validation).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Pre-flight Verification

**Purpose**: Confirm targets are truly unused before deletion.

- [x] T001 Verify `request_batcher.py` has zero imports: `grep -r "request_batcher" src/ tests/` returns empty
- [x] T002 Verify `search_optimized` has zero imports: `grep -r "search_optimized" src/ tests/` returns empty
- [x] T003 Verify `pydantic_ai` is only in the xfail test: `grep -r "pydantic.ai\|pydantic_ai" src/ tests/` returns only `test_pydantic_ai_integration.py`

**Checkpoint**: All 3 targets confirmed safe to delete.

---

## Phase 2: User Story 1 — Odstranění mrtvého kódu (Priority: P1) 🎯 MVP

**Goal**: Delete 3 unused source/test files.

**Independent Test**: `uv run python -m pytest tests/tdd/test_mcp_integration.py` passes with 60 tools.

- [x] T004 [P] [US1] Delete unused request batcher: `git rm src/czechmedmcp/request_batcher.py`
- [x] T005 [P] [US1] Delete unused search optimization: `git rm src/czechmedmcp/articles/search_optimized.py`
- [x] T006 [P] [US1] Delete permanently broken pydantic-ai test: `git rm tests/test_pydantic_ai_integration.py`
- [x] T007 [US1] Verify MCP tool count unchanged: `uv run python -m pytest tests/tdd/test_mcp_integration.py -v` passes with 60 tools

**Checkpoint**: 3 files deleted, MCP server unaffected.

---

## Phase 3: User Story 2 — Pročištění závislostí (Priority: P1)

**Goal**: Remove 6 unused dev dependencies from pyproject.toml.

**Independent Test**: `uv sync --group dev` succeeds. `uv run deptry .` reports no unused deps.

- [x] T008 [US2] Remove `mkdocs>=1.4.2` from dev group in pyproject.toml
- [x] T009 [US2] Remove `mkdocs-material>=8.5.10` from dev group in pyproject.toml
- [x] T010 [US2] Remove `mkdocstrings[python]>=0.26.1` from dev group in pyproject.toml
- [x] T011 [US2] Remove `PyYAML>=6.0.0` and its comment from dev group in pyproject.toml
- [x] T012 [US2] Remove `tomlkit>=0.13.2` from dev group in pyproject.toml
- [x] T013 [US2] Remove `pydantic-ai>=0.0.14` and its comment from dev group in pyproject.toml
- [x] T014 [US2] Run `uv sync --group dev` to update lockfile (uv.lock)
- [x] T015 [US2] Verify no import errors: `uv run python -c "import czechmedmcp"` succeeds

**Checkpoint**: 6 dependencies removed, project installs cleanly.

Phase 2 → Phase 3 dependency: pydantic-ai removal depends on T006 (test file deletion).

---

## Phase 4: User Story 3 — Aktualizace dokumentace a validace (Priority: P2)

**Goal**: Update CLAUDE.md, run full validation suite.

**Independent Test**: `make check` passes. CLAUDE.md has no stale references.

- [x] T016 [US3] Update CLAUDE.md — remove `test_pydantic_ai_integration.py` mention from Known Issues section in CLAUDE.md
- [x] T017 [US3] Run ruff check: `uv run ruff check src tests` passes
- [x] T018 [US3] Run mypy: `uv run mypy` passes
- [x] T019 [US3] Run deptry: `uv run deptry .` reports no issues
- [x] T020 [US3] Run full test suite: `uv run python -m pytest -m "not integration" -x --ff -n auto` passes
- [x] T021 [US3] Verify MCP server startup: `timeout 10s uv run czechmedmcp run || true` (exit 124 = timeout = OK)

**Checkpoint**: All quality checks pass. Project is clean.

---

## Phase 5: Final Commit

- [x] T022 Commit all changes with message `chore: remove dead code and unused dev dependencies`

---

## Dependencies & Execution Order

```text
Phase 1 (pre-flight)
    ↓
Phase 2 (US1: delete files)  ← T004-T006 can run in parallel
    ↓
Phase 3 (US2: remove deps)  ← depends on Phase 2 (pydantic-ai safe after T006)
    ↓
Phase 4 (US3: validate)  ← depends on Phase 3 (need clean deps for deptry)
    ↓
Phase 5 (commit)
```

### Parallel Opportunities

- **Phase 2**: T004, T005, T006 can run in parallel (different files)
- **Phase 3**: T008-T013 are all edits to same file (pyproject.toml) — must be sequential
- **Phase 4**: T017, T018, T019 can run in parallel (independent checks)

---

## Implementation Strategy

### MVP (US1 only)
1. Phase 1: Pre-flight
2. Phase 2: Delete 3 files
3. Verify MCP tools = 60
4. This alone removes the dead code

### Full Delivery
1. MVP + US2 (remove 6 deps) + US3 (validate)
2. Single commit at the end
