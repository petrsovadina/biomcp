---
title: "Phase 3: Fix Stale Information"
status: pending
version: "1.0"
phase: 3
---

# Phase 3: Fix Stale Information

## Phase Context

**GATE**: Phases 1-2 complete. Read spec.md US3.

**Specification References**:
- `[ref: spec.md/US3; FR-004, FR-005, FR-006]`

**Dependencies**: Phases 1-2 (file deletions first, then info fixes).

---

## Tasks

Fixes incorrect URLs, outdated naming conventions, and conflicting configs.

- [ ] **T3.1 Fix pyproject.toml documentation URL** `[activity: config-fix]`

  1. Prime: Read `pyproject.toml` project.urls section `[ref: spec.md/FR-004]`
  2. Test: Current URL `https://petrsovadina.github.io/biomcp/` returns 404 or wrong content
  3. Implement: Update to `https://czech-med-mcp-docs.vercel.app` (verified working)
  4. Validate: `curl -s -o /dev/null -w "%{http_code}" <new-url>` returns 200
  5. Success: Documentation URL points to live, accessible docs `[ref: spec.md/SC-003]`

- [ ] **T3.2 Update .env.example variable naming** `[activity: config-fix]` `[parallel: true]`

  1. Prime: Read `.env.example` — identify all `BIOMCP_*` prefixed variables `[ref: spec.md/FR-005]`
  2. Test: `grep "BIOMCP_" .env.example` returns matches
  3. Implement: Rename `BIOMCP_*` to `CZECHMEDMCP_*`; add comment about old naming for backwards compat
  4. Validate: `grep "BIOMCP_" .env.example` returns zero (only in comments); `grep "CZECHMEDMCP_" .env.example` returns all new names
  5. Success: Consistent CZECHMEDMCP_* naming throughout .env.example `[ref: spec.md/FR-005]`

- [ ] **T3.3 Remove or fix root vercel.json** `[activity: config-fix]` `[parallel: true]`

  1. Prime: Read root `vercel.json` and compare with `apps/web/vercel.json`, `apps/docs/vercel.json` `[ref: spec.md/FR-006]`
  2. Test: Root vercel.json has incorrect paths (`web/.next` instead of proper monorepo paths)
  3. Implement: Remove root `vercel.json` if app-level configs are sufficient; OR fix paths
  4. Validate: Verify app-level vercel.json files are complete and authoritative
  5. Success: No conflicting Vercel configuration `[ref: spec.md/FR-006]`

- [ ] **T3.4 Phase Validation** `[activity: validate]`

  - All updated URLs return 200. No BIOMCP_ variables in .env.example (except in backward-compat comments). No conflicting vercel.json. Run `make check` — passes clean.
