# Feature Specification: Codebase Refactor

**Feature Branch**: `015-codebase-refactor`
**Created**: 2026-03-30
**Status**: Implementation (fast-track from analysis)

## Summary

Systematic refactoring based on codebase analysis. No functional changes — all 60 MCP tools remain unchanged. Focus on DRY, parameter naming, and code hygiene.

## Scope

1. Fix `id` parameter shadowing → domain-specific names (20+ files)
2. Consolidate `json.dumps(ensure_ascii=False)` into shared helper
3. Clean up noqa A002 suppressions

## Out of Scope

- Splitting individual_tools.py (high risk, requires tool re-registration)
- Router search() refactoring (complex, dedicated sprint)
- Adding missing tests (separate feature)

## Success Criteria

- All existing tests pass (467+)
- 60 MCP tools registered
- Ruff + mypy clean
- Zero `# noqa: A002` suppressions
