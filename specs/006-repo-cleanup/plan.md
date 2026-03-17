# Implementation Plan: Repository Cleanup

**Branch**: `006-repo-cleanup` | **Date**: 2026-03-16 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/006-repo-cleanup/spec.md`

## Summary

Odstranění 3 mrtvých zdrojových souborů a 6 nepoužívaných dev závislostí. Čistě destruktivní operace (mazání) s následnou validací. Žádný nový kód.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: pyproject.toml (uv)
**Storage**: N/A
**Testing**: pytest, ruff, mypy, deptry
**Target Platform**: N/A (cleanup)
**Project Type**: Code cleanup (file deletion + dependency removal)
**Performance Goals**: N/A
**Constraints**: MCP server musí po cleanup registrovat přesně 60 nástrojů
**Scale/Scope**: 3 soubory + 6 závislostí + 1 doc update

## Constitution Check

| Principle | Relevance | Status |
|-----------|-----------|--------|
| I. MCP Protocol First | N/A — žádné nové nástroje, počet 60 se nemění | PASS |
| II. Modular Domain Architecture | ALIGNS — odstraňujeme mrtvé moduly, ne aktivní | PASS |
| III. Authoritative Data Sources | N/A | PASS |
| IV. CLI & MCP Dual Access | N/A | PASS |
| V. Testing Rigor | ALIGNS — odstraňujeme permanentně xfail test | PASS |
| Development Workflow | ALIGNS — feature branch, conventional commits | PASS |

**Gate Result**: PASS

## Project Structure

### Files to DELETE

```text
src/czechmedmcp/request_batcher.py       # Zero imports across entire codebase
src/czechmedmcp/articles/search_optimized.py  # Zero imports, superseded by unified search
tests/test_pydantic_ai_integration.py    # Permanently xfail, no resolution path
```

### Files to EDIT

```text
pyproject.toml                           # Remove 6 dev dependencies
CLAUDE.md                                # Remove pydantic_ai known issue mention
```

### Files PROTECTED (explicitly NOT removing)

```text
src/czechmedmcp/http_client_simple.py    # Imported by http_client.py as fallback
src/czechmedmcp/czech/*/__init__.py      # Standard Python package markers
tests/data/*                             # Active test fixtures
specs/*                                  # Historical documentation
example_scripts/*                        # User-facing reference code
```

## Phase 0: Research

### R-001: request_batcher.py usage verification

**Decision**: Safe to delete.
**Evidence**: `grep -r "request_batcher" src/ tests/` returns zero matches outside the file itself.

### R-002: articles/search_optimized.py usage verification

**Decision**: Safe to delete.
**Evidence**: `grep -r "search_optimized" src/ tests/` returns zero matches.

### R-003: pydantic-ai dependency chain

**Decision**: Safe to remove pydantic-ai from dev deps.
**Evidence**: Only imported in `tests/test_pydantic_ai_integration.py` which is being deleted. No other imports of `pydantic_ai` exist.

### R-004: PyYAML usage beyond mkdocs

**Decision**: Safe to remove.
**Evidence**: `grep -r "import yaml\|from yaml" src/ tests/` returns zero matches. Comment in pyproject.toml says "Used for mkdocs.yml parsing in scripts" — mkdocs is not used.

### R-005: tomlkit usage

**Decision**: Safe to remove.
**Evidence**: `grep -r "import tomlkit\|from tomlkit" src/ tests/` returns zero matches.

### R-006: mkdocs dependencies

**Decision**: Safe to remove all three (mkdocs, mkdocs-material, mkdocstrings).
**Evidence**: No mkdocs.yml in repo. Project uses Nextra (`apps/docs/`) for documentation.

## Implementation Phases

### Phase 1: Delete dead files (US1)

1. `git rm src/czechmedmcp/request_batcher.py`
2. `git rm src/czechmedmcp/articles/search_optimized.py`
3. `git rm tests/test_pydantic_ai_integration.py`
4. Verify: `uv run python -m pytest tests/tdd/test_mcp_integration.py` — 60 tools

### Phase 2: Remove unused dependencies (US2)

Edit `pyproject.toml` dev group — remove:
1. `mkdocs>=1.4.2`
2. `mkdocs-material>=8.5.10`
3. `mkdocstrings[python]>=0.26.1`
4. `PyYAML>=6.0.0`
5. `tomlkit>=0.13.2`
6. `pydantic-ai>=0.0.14`

Then: `uv sync --group dev` to update lockfile.

### Phase 3: Update docs + validate (US3)

1. Update CLAUDE.md — remove pydantic_ai mention from Known Issues
2. Run `make check` (ruff + mypy + pre-commit + deptry)
3. Run full test suite: `uv run python -m pytest -m "not integration" -x`
4. Verify MCP startup: `timeout 10s uv run czechmedmcp run || true`

## Build Sequence

```text
Phase 1 (delete files)
    ↓
Phase 2 (remove deps)  ← depends on Phase 1 (pydantic-ai only safe after test deletion)
    ↓
Phase 3 (validate)  ← depends on Phase 2 (need clean deps for deptry check)
```

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Deleted file was actually used at runtime | High | Very Low | grep verification in research phase |
| Removed dep breaks test suite | Medium | Low | uv sync + full test run in Phase 3 |
| MCP tool count changes | High | None | Integration test verifies exactly 60 |
