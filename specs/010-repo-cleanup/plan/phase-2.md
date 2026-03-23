---
title: "Phase 2: Clean Root Directory"
status: pending
version: "1.0"
phase: 2
---

# Phase 2: Clean Root Directory

## Phase Context

**GATE**: Phase 1 complete. Read spec.md US2.

**Specification References**:
- `[ref: spec.md/US2; FR-002, FR-003, FR-007]`

**Dependencies**: Phase 1 (spec duplicates removed first to keep diffs clean).

---

## Tasks

Removes screenshots, duplicate configs, and build artifacts from repository root.

- [ ] **T2.1 Remove screenshot images from root** `[activity: cleanup]`

  1. Prime: Read `spec.md` US2 acceptance scenarios `[ref: spec.md/US2]`
  2. Test: `ls *.jpeg *.png 2>/dev/null` in root — expect 17 files
  3. Implement: `git rm` all .jpeg and .png files from root (dark-*.jpeg, light-*.png, etc.)
  4. Validate: `ls *.jpeg *.png 2>/dev/null` returns empty; `git diff --stat` shows ~2.4MB removed
  5. Success: Zero image files in root directory `[ref: spec.md/FR-002, SC-007]`

- [ ] **T2.2 Remove duplicate config files** `[activity: cleanup]` `[parallel: true]`

  1. Prime: Verify `.dockerignore 3`, `.dockerignore 4`, `Caddyfile 3` are identical to originals
  2. Test: `diff .dockerignore ".dockerignore 3"` shows no differences
  3. Implement: `git rm ".dockerignore 3" ".dockerignore 4" "Caddyfile 3"` (if they exist)
  4. Validate: Only `.dockerignore` and `Caddyfile` remain (without numbered variants)
  5. Success: Zero duplicate config files `[ref: spec.md/FR-003, SC-001]`

- [ ] **T2.3 Remove build/ directory** `[activity: cleanup]` `[parallel: true]`

  1. Prime: Check if `build/` is tracked by git
  2. Test: `git ls-files build/` shows tracked files
  3. Implement: `git rm -r build/` to remove from tracking
  4. Validate: `build/` no longer in `git ls-files` output
  5. Success: build/ removed from git tracking `[ref: spec.md/FR-007]`

- [ ] **T2.4 Phase Validation** `[activity: validate]`

  - Count root files: `ls -1 | wc -l` — must be under 30. Run `uv run python -m pytest tests/tdd/ -v` — all pass. No image files or duplicate configs in root.
