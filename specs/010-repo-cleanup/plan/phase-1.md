---
title: "Phase 1: Remove Duplicate Files"
status: pending
version: "1.0"
phase: 1
---

# Phase 1: Remove Duplicate Files

## Phase Context

**GATE**: Read spec.md US1 before starting.

**Specification References**:
- `[ref: spec.md/US1; FR-001]`

**Dependencies**: None — this phase can start immediately.

---

## Tasks

Removes all macOS Finder copy artifacts (" 2", " 3" suffix files/directories) from specs/.

- [ ] **T1.1 Identify and verify all duplicates** `[activity: investigation]`

  1. Prime: Read `spec.md` US1 acceptance scenarios `[ref: spec.md/US1]`
  2. Test: Run `find specs/ -name "* [23]*"` — expect 24+ matches; verify each is identical to original with `diff`
  3. Implement: Create list of files to delete; verify no duplicate has unique content
  4. Validate: All duplicates confirmed identical to originals
  5. Success: Complete inventory of duplicates with diff verification `[ref: spec.md/FR-001]`

- [ ] **T1.2 Remove spec duplicate files** `[activity: cleanup]` `[parallel: true]`

  1. Prime: Review T1.1 inventory
  2. Test: `git status` shows the files as deleted after removal
  3. Implement: `git rm` all duplicate spec files (`plan 2.md`, `spec 3.md`, `research 2.md`, `tasks 2.md`, etc.)
  4. Validate: `find specs/ -name "* [23]*"` returns empty
  5. Success: Zero " 2"/" 3" files remain in specs/ `[ref: spec.md/SC-001]`

- [ ] **T1.3 Remove spec duplicate directories** `[activity: cleanup]` `[parallel: true]`

  1. Prime: Review T1.1 inventory for directories
  2. Test: `git status` shows directories removed
  3. Implement: `git rm -r` all duplicate spec directories (`checklists 2/`, `checklists 3/`, empty `* 2/` dirs)
  4. Validate: `find specs/ -type d -name "* [23]*"` returns empty
  5. Success: Zero " 2"/" 3" directories remain in specs/ `[ref: spec.md/SC-001]`

- [ ] **T1.4 Phase Validation** `[activity: validate]`

  - Run `find specs/ -name "* [23]*"` — must return empty. Run `uv run python -m pytest tests/tdd/test_mcp_integration.py -v` — all tests pass. Verify `git diff --stat` shows only deletions.
