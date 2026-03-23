---
title: "Phase 4: Gitignore & Spec Status + Final Validation"
status: pending
version: "1.0"
phase: 4
---

# Phase 4: Gitignore & Spec Status + Final Validation

## Phase Context

**GATE**: Phases 1-3 complete. Read spec.md US4, US5.

**Specification References**:
- `[ref: spec.md/US4; FR-010]`
- `[ref: spec.md/US5; FR-008]`

**Dependencies**: Phases 1-3 (all cleanup done before preventive measures).

---

## Tasks

Updates .gitignore to prevent recurrence, marks completed specs, runs final validation.

- [ ] **T4.1 Update .gitignore with new patterns** `[activity: config-fix]`

  1. Prime: Read current `.gitignore` `[ref: spec.md/FR-008]`
  2. Test: `git check-ignore "test 2.md"` returns negative (pattern not yet present)
  3. Implement: Add patterns for macOS copy artifacts (`* [0-9].*`, `* [0-9]`), `build/`, root screenshots (`/*.jpeg`, `/*.png`), `.next/` cache
  4. Validate: `git check-ignore "test 2.md"` returns positive; `git check-ignore build/` returns positive
  5. Success: .gitignore prevents 5+ new categories of problematic files `[ref: spec.md/SC-006]`

- [ ] **T4.2 Update completed spec statuses** `[activity: documentation]` `[parallel: true]`

  1. Prime: Read each spec.md to determine current status `[ref: spec.md/FR-010]`
  2. Test: `grep "Status:" specs/*/spec.md` — some show "Draft" despite being merged
  3. Implement: Update `Status:` field in merged specs (001-003, 004-008) to "Merged" or "Completed"
  4. Validate: `grep "Status:" specs/*/spec.md` — all reflect actual state
  5. Success: Every spec has accurate status indicator `[ref: spec.md/FR-010]`

- [ ] **T4.3 Final Integration Validation** `[activity: validate]`

  1. Prime: Review all changes across phases 1-4
  2. Test: Run complete test suite `uv run python -m pytest -x --ff -n auto -m "not integration"`
  3. Implement: Fix any regressions found (expect zero)
  4. Validate:
     - `find specs/ -name "* [23]*"` returns empty (SC-001)
     - `ls *.jpeg *.png 2>/dev/null` returns empty in root (SC-002)
     - Root directory file count < 25 (SC-002)
     - All tests pass (SC-004)
     - `.gitignore` blocks test patterns (SC-006)
  5. Success: All 7 success criteria met `[ref: spec.md/SC-001 through SC-007]`
