---
title: "Systematické pročištění repozitáře"
status: COMPLETE
version: "1.0"
---

# Implementation Plan

## Validation Checklist

### CRITICAL GATES (Must Pass)

- [x] All `[NEEDS CLARIFICATION: ...]` markers have been addressed
- [x] All specification file paths are correct and exist
- [x] Each phase follows TDD: Prime -> Test -> Implement -> Validate
- [x] Every task has verifiable success criteria
- [x] A developer could follow this plan independently

### QUALITY CHECKS (Should Pass)

- [x] Context priming section is complete
- [x] All implementation phases are defined with linked phase files
- [x] Dependencies between phases are clear (no circular dependencies)
- [x] Parallel work is properly tagged with `[parallel: true]`
- [x] Activity hints provided for specialist selection `[activity: type]`
- [x] Every phase references relevant spec sections
- [x] Every test references spec acceptance criteria
- [x] Integration & E2E tests defined in final phase
- [x] Project commands match actual project setup

---

## Context Priming

*GATE: Read all files in this section before starting any implementation.*

**Specification**:

- `specs/010-repo-cleanup/spec.md` - Feature Specification (5 user stories, 10 FRs, 7 SCs)
- `specs/010-repo-cleanup/checklists/requirements.md` - Quality Checklist

**Key Design Decisions**:

- **ADR-1**: Delete duplicates, don't move them - macOS " 2"/" 3" copies are exact duplicates, verified by audit
- **ADR-2**: Remove root screenshots, don't relocate - they're development artifacts, not project assets
- **ADR-3**: Rename env vars BIOMCP_* to CZECHMEDMCP_* with backward-compat comments
- **ADR-4**: Remove root vercel.json - app-level configs in apps/web/ and apps/docs/ are authoritative

**Implementation Context**:

```bash
# Testing
uv run python -m pytest -x --ff -n auto --dist loadscope  # All tests
uv run python -m pytest -m "not integration"                # Unit only

# Quality
uv run ruff check src tests    # Linting
uv run mypy                    # Type checking
make check                     # Full validation

# Verify cleanup
find specs/ -name "* [23]*"    # Should return empty
ls *.jpeg *.png 2>/dev/null    # Should return empty
```

---

## Implementation Phases

Each phase is defined in a separate file. Tasks follow red-green-refactor: **Prime** (understand context), **Test** (red), **Implement** (green), **Validate** (refactor + verify).

- [ ] [Phase 1: Remove Duplicate Files](phase-1.md)
- [ ] [Phase 2: Clean Root Directory](phase-2.md)
- [ ] [Phase 3: Fix Stale Information](phase-3.md)
- [ ] [Phase 4: Gitignore & Spec Status + Final Validation](phase-4.md)

---

## Plan Verification

| Criterion | Status |
|-----------|--------|
| A developer can follow this plan without additional clarification | ✅ |
| Every task produces a verifiable deliverable | ✅ |
| All spec acceptance criteria map to specific tasks | ✅ |
| Dependencies are explicit with no circular references | ✅ |
| Parallel opportunities are marked with `[parallel: true]` | ✅ |
| Each task has specification references `[ref: ...]` | ✅ |
| Project commands in Context Priming are accurate | ✅ |
| All phase files exist and are linked from this manifest as `[Phase N: Title](phase-N.md)` | ✅ |
