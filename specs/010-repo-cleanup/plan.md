# Implementation Plan: Systematické pročištění repozitáře

**Branch**: `010-repo-cleanup` | **Date**: 2026-03-23 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-repo-cleanup/spec.md`

## Summary

Systematické odstranění ~60+ problémů v repozitáři: duplicitní soubory v specs/ (macOS " 2"/" 3" kopie), 17 screenshotů a duplicitní configs v kořeni, nepravdivé URL a zastaralé env var názvy, a prevence recidivy přes .gitignore aktualizaci. Čistě mechanická práce — žádné změny zdrojového kódu, žádné nové funkce.

## Technical Context

**Language/Version**: N/A (repo maintenance, no code changes)
**Primary Dependencies**: git, bash (file operations only)
**Storage**: N/A
**Testing**: `uv run python -m pytest -x --ff -n auto -m "not integration"` (regression check)
**Target Platform**: Git repository (GitHub)
**Project Type**: Repository maintenance / cleanup
**Performance Goals**: N/A
**Constraints**: Zero regressions in existing 1020+ tests; no source code changes
**Scale/Scope**: ~60+ files to remove/fix; 10 FRs; 7 SCs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | **N/A** | No MCP tools added/modified. Cleanup only. |
| II. Modular Domain Architecture | **N/A** | No source code changes. |
| III. Authoritative Data Sources | **N/A** | No data source changes. |
| IV. CLI & MCP Dual Access | **N/A** | No functionality changes. |
| V. Testing Rigor | **PASS** | FR-009 requires all 1020+ tests pass after cleanup. |
| Technical Constraints | **PASS** | Uses uv, ruff, mypy as mandated. |
| Development Workflow | **PASS** | Feature branch via speckit, conventional commits. |

**No violations. No complexity tracking needed.**

## Project Structure

### Files to Remove (~40+ files)

```text
# Duplicate spec files (macOS " 2"/" 3" copies)
specs/000-czechmedmcp-implementation 2/   # Empty directory
specs/001-fix-sukl-search 2/              # Empty directory
specs/002-codebase-stabilization 2/       # Empty directory
specs/006-repo-cleanup/plan 2.md          # Identical to plan.md
specs/006-repo-cleanup/plan 3.md          # Identical to plan.md
specs/006-repo-cleanup/spec 2.md          # Identical to spec.md
specs/006-repo-cleanup/spec 3.md          # Identical to spec.md
specs/006-repo-cleanup/research 2.md      # Identical to research.md
specs/006-repo-cleanup/research 3.md      # Identical to research.md
specs/006-repo-cleanup/tasks 2.md         # Identical to tasks.md
specs/006-repo-cleanup/tasks 3.md         # Identical to tasks.md
specs/006-repo-cleanup/checklists 2/      # Duplicate directory
specs/006-repo-cleanup/checklists 3/      # Duplicate directory
specs/007-validate-ui-content/plan 2.md   # + same pattern (8 more files)
specs/007-validate-ui-content/...

# Root screenshots (17 files, ~2.4 MB)
dark-full.jpeg, dark-hero-detail.png, dark-mode-*.png
light-*.jpeg, light-*.png, final-light.jpeg

# Duplicate configs
.dockerignore 3, .dockerignore 4, Caddyfile 3

# Build artifacts
build/
```

### Files to Modify (4 files)

```text
pyproject.toml          # Fix Documentation URL
.env.example            # Rename BIOMCP_* → CZECHMEDMCP_*
.gitignore              # Add new prevention patterns
vercel.json             # Remove or fix (root level)
specs/*/spec.md         # Update Status field in completed specs
```

**Structure Decision**: Pure deletion and file editing. No new files created (except this plan and tasks). No source code touched.

## Implementation Phases

### Phase 1: Remove Duplicates (specs/)

**Goal**: Remove all " 2"/" 3" duplicate files and directories from specs/.

1. Verify each duplicate is identical to original via `diff`
2. `git rm` all duplicate files and directories
3. Validate: `find specs/ -name "* [23]*"` returns empty

### Phase 2: Clean Root Directory

**Goal**: Remove screenshots, duplicate configs, build artifacts.

1. `git rm` all .jpeg/.png screenshots from root
2. `git rm` duplicate configs (`.dockerignore 3/4`, `Caddyfile 3`)
3. `git rm -r build/` if tracked
4. Validate: root contains < 25 files

### Phase 3: Fix Stale Information

**Goal**: Correct URLs, env var names, Vercel config.

1. Fix `pyproject.toml` Documentation URL
2. Rename `BIOMCP_*` → `CZECHMEDMCP_*` in `.env.example`
3. Remove or fix root `vercel.json`
4. Validate: all URLs return 200

### Phase 4: Prevention & Finalization

**Goal**: Update .gitignore, mark completed specs, run final validation.

1. Add patterns to `.gitignore`: macOS copies, build/, root screenshots
2. Update `Status:` in completed spec.md files
3. Run full test suite — zero regressions
4. Validate all 7 success criteria

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Duplicate handling | Delete (not move) | Audit confirmed all are exact copies |
| Screenshot handling | Delete (not relocate) | Development artifacts, not project assets |
| Env var rename | CZECHMEDMCP_* + backward-compat comment | Consistent naming without breaking existing setups |
| Root vercel.json | Remove | App-level configs are authoritative |
| Completed specs | Update status field | Keep as historical record, clearly marked |

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Duplicate has unique content | Medium | Diff-verify before each deletion |
| Root vercel.json removal breaks deploy | Low | App-level configs verified as complete |
| Env var rename confuses users | Low | Backward-compat comment in .env.example |
| Git history bloat from deleted binaries | Low | Out of scope (history rewriting) |

## Dependencies Between Phases

```
Phase 1 (spec duplicates) → Phase 2 (root cleanup) → Phase 3 (info fixes) → Phase 4 (prevention)
```

Sequential execution — each phase builds on clean state from previous.
