# Tasks: Systematické pročištění repozitáře

**Input**: Design documents from `/specs/010-repo-cleanup/`
**Prerequisites**: plan.md (required), spec.md (required)

**Tests**: Regression only — FR-009 requires all 1020+ tests pass after cleanup.

**Organization**: Tasks grouped by user story. US1-US3 (P1) execute sequentially for clean diffs. US4-US5 (P2) follow.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: Verify current state and create inventory of files to remove

- [x] T001 Run `find specs/ -name "* [23]*"` to inventory all duplicate spec files and directories
- [x] T002 Run `ls *.jpeg *.png 2>/dev/null` in root to inventory all screenshot files
- [x] T003 Run `ls ".dockerignore 3" ".dockerignore 4" "Caddyfile 3" 2>/dev/null` to verify duplicate configs exist

**Checkpoint**: Complete inventory of all files to remove

---

## Phase 2: Foundational

**Purpose**: Verify duplicates are identical to originals before deletion

**CRITICAL**: Must confirm no unique content before any deletion

- [x] T004 For each duplicate in `specs/006-repo-cleanup/` — diff against original (`diff "plan.md" "plan 2.md"` etc.) and confirm identical
- [x] T005 For each duplicate in `specs/007-validate-ui-content/` — diff against original and confirm identical
- [x] T006 [P] Verify `.dockerignore 3` and `.dockerignore 4` are identical to `.dockerignore` via `diff`
- [x] T007 [P] Verify `Caddyfile 3` is identical to `Caddyfile` via `diff` (if both exist)

**Checkpoint**: All duplicates confirmed identical — safe to delete

---

## Phase 3: User Story 1 — Odstranění duplicitních souborů ze specs/ (Priority: P1) 🎯 MVP

**Goal**: Remove all macOS " 2"/" 3" copy artifacts from specs/

**Independent Test**: `find specs/ -name "* [23]*"` returns empty

- [x] T008 [P] [US1] `git rm` empty duplicate directories: `specs/000-czechmedmcp-implementation 2/`, `specs/001-fix-sukl-search 2/`, `specs/002-codebase-stabilization 2/`
- [x] T009 [P] [US1] `git rm` duplicate files in `specs/006-repo-cleanup/`: `plan 2.md`, `plan 3.md`, `spec 2.md`, `spec 3.md`, `research 2.md`, `research 3.md`, `tasks 2.md`, `tasks 3.md`
- [x] T010 [P] [US1] `git rm -r` duplicate directories in `specs/006-repo-cleanup/`: `checklists 2/`, `checklists 3/`
- [x] T011 [P] [US1] `git rm` duplicate files in `specs/007-validate-ui-content/`: `plan 2.md`, `plan 3.md`, `spec 2.md`, `spec 3.md`, `research 2.md`, `research 3.md`, `tasks 2.md`, `tasks 3.md`
- [x] T012 [P] [US1] `git rm -r` duplicate directories in `specs/007-validate-ui-content/`: `checklists 2/`, `checklists 3/`
- [x] T013 [US1] Validate: `find specs/ -name "* [23]*"` returns empty result

**Checkpoint**: Zero " 2"/" 3" files in specs/. SC-001 partially met.

---

## Phase 4: User Story 2 — Odstranění obrázků a dočasných souborů z kořene (Priority: P1)

**Goal**: Remove screenshots, duplicate configs, build artifacts from root

**Independent Test**: `ls *.jpeg *.png 2>/dev/null` returns empty; root file count < 25

- [x] T014 [US2] `git rm` all screenshot files from root: `dark-full.jpeg`, `dark-hero-detail.png`, `dark-mode-after-fix.png`, `dark-mode-full.png`, `dark-mode-toggled.png`, `final-light.jpeg`, `light-code-example.png`, `light-cta-footer.png`, `light-features-detail.png`, `light-final.jpeg`, `light-full.jpeg`, `light-hero.png`, `light-howto-detail.png`, `light-mode-after-fix.png`, `light-problem-section.png`, `light-sections-1500.png`, `light-sections-3000.png`
- [x] T015 [P] [US2] `git rm` duplicate config files: `.dockerignore 3`, `.dockerignore 4`, `Caddyfile 3`
- [x] T016 [P] [US2] `git rm -r build/` to remove build artifacts from tracking (if tracked)
- [x] T017 [US2] Validate: `ls *.jpeg *.png 2>/dev/null` returns empty; `ls -1 | wc -l` < 30

**Checkpoint**: Clean root directory. SC-001 fully met, SC-002 met, SC-007 met.

---

## Phase 5: User Story 3 — Oprava nepravdivých a zastaralých informací (Priority: P1)

**Goal**: Fix incorrect URLs, env var naming, Vercel config

**Independent Test**: Updated URLs return HTTP 200; no BIOMCP_* vars in .env.example

- [x] T018 [US3] Fix `pyproject.toml` line 42: change `Documentation = "https://petrsovadina.github.io/biomcp/"` to `Documentation = "https://czech-med-mcp-docs.vercel.app"`
- [x] T019 [US3] Update `.env.example`: rename all `BIOMCP_*` prefixed variables to `CZECHMEDMCP_*` with backward-compatibility comment
- [x] T020 [US3] Remove root `vercel.json` via `git rm vercel.json` (app-level configs in `apps/web/` and `apps/docs/` are authoritative)
- [x] T021 [US3] Validate: `grep "BIOMCP_" .env.example` returns zero matches outside comments; `curl -s -o /dev/null -w "%{http_code}" https://czech-med-mcp-docs.vercel.app` returns 200

**Checkpoint**: All information accurate. SC-003 met.

---

## Phase 6: User Story 4 — Archivace dokončených specifikací (Priority: P2)

**Goal**: Mark completed specs with clear status indicators

**Independent Test**: `grep "Status:" specs/*/spec.md` shows accurate status for each spec

- [x] T022 [P] [US4] Update `Status: Draft` to `Status: Merged` in spec.md for specs: 001-fix-sukl-search, 002-codebase-stabilization, 003-git-workflow
- [x] T023 [P] [US4] Update `Status: Draft` to `Status: Completed` in spec.md for specs: 004-deployment-readiness, 005-deployment-cleanup, 006-repo-cleanup, 007-validate-ui-content, 008-dark-light-mode
- [x] T024 [US4] Validate: `grep "Status:" specs/*/spec.md` shows no "Draft" for completed features

**Checkpoint**: Every spec has accurate status. FR-010 met.

---

## Phase 7: User Story 5 — Aktualizace .gitignore (Priority: P2)

**Goal**: Add patterns preventing future duplicate file commits

**Independent Test**: `git check-ignore "test 2.md"` returns positive

- [x] T025 [US5] Add macOS copy artifact patterns to `.gitignore`: `*\ [0-9]*`, `*\ [0-9]`, `*\ [0-9].*`
- [x] T026 [US5] Add build artifact and screenshot patterns to `.gitignore`: `build/`, `/*.jpeg`, `/*.png`
- [x] T027 [US5] Validate: `echo "test 2.md" | git check-ignore --stdin` returns match; `echo "build/" | git check-ignore --stdin` returns match

**Checkpoint**: .gitignore prevents future issues. SC-006 met.

---

## Phase 8: Polish & Final Validation

**Purpose**: Regression testing and final success criteria verification

- [x] T028 Run full test suite: `uv run python -m pytest -x --ff -n auto -m "not integration"` — all 1020+ tests pass
- [x] T029 Run `uv run ruff check src tests` — lint passes
- [x] T030 Verify all 7 success criteria:
  - SC-001: `find . -name "* [23]*" -not -path "./.git/*"` returns empty
  - SC-002: root file count < 25
  - SC-003: docs URL returns 200
  - SC-004: tests pass (T028)
  - SC-005: root files are recognizable
  - SC-006: .gitignore blocks test patterns
  - SC-007: `git diff --stat HEAD` shows > 2MB removed
- [x] T031 Clean up auto-generated `Active Technologies` / `Recent Changes` noise from CLAUDE.md if present

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — inventory only
- **Foundational (Phase 2)**: Depends on Phase 1 — verifies before deletion
- **US1 specs/ (Phase 3)**: Depends on Phase 2 — safe to delete after verification
- **US2 root (Phase 4)**: Depends on Phase 2 — independent of Phase 3
- **US3 info (Phase 5)**: Independent — can run after Phase 2
- **US4 status (Phase 6)**: Independent — can run anytime
- **US5 gitignore (Phase 7)**: Should run after Phases 3-4 (deleted files first, then prevent)
- **Polish (Phase 8)**: Depends on all previous phases

### Parallel Opportunities

**Phase 3 (US1)**: T008-T012 all parallel (different directories)
**Phase 4 (US2)**: T015-T016 parallel with each other
**Phase 5 (US3)**: T018-T020 parallel (different files)
**Phase 6 (US4)**: T022-T023 parallel (different spec directories)

---

## Implementation Strategy

### MVP First (US1: spec duplicates)

1. Phase 1-2: Inventory + verify
2. Phase 3: Remove spec duplicates
3. **VALIDATE**: `find specs/ -name "* [23]*"` empty
4. If clean, continue to Phase 4+

### Incremental Delivery

1. Phases 1-2 → safe to delete verified
2. Phase 3 (US1) → spec duplicates gone
3. Phase 4 (US2) → root clean
4. Phase 5 (US3) → info corrected
5. Phase 6-7 (US4-5) → prevention + archivace
6. Phase 8 → final validation + commit

---

## Notes

- All deletions use `git rm` (not `rm`) to properly track in git
- Verify before delete — Phase 2 is the safety gate
- No source code changes — only file deletions and config edits
- Commit after each phase checkpoint for clean git history
