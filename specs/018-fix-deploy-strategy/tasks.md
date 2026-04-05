# Tasks: Fix Deploy Strategy

**Input**: Design documents from `/specs/018-fix-deploy-strategy/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: No automated tests — verification is via live Vercel deployment.

**Organization**: Tasks ordered by execution dependency. Dashboard changes (manual) are sequenced to minimize risk (docs first, then web).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1=web deploy, US2=docs deploy, US3=CI alignment)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Code Changes)

**Purpose**: Create root config and remove old per-app configs

- [x] T001 Create root-level Vercel config with shared headers in `vercel.json`
- [x] T002 [P] Delete web app Vercel config `apps/web/vercel.json`
- [x] T003 [P] Delete docs app Vercel config `apps/docs/vercel.json`

**Checkpoint**: Root `vercel.json` exists, per-app configs removed. Ready for dashboard changes.

---

## Phase 2: User Story 2 — Consistent Docs Deployment (Priority: P2) — First because lower risk

**Goal**: Reconfigure docs project to use monorepo root, verify it keeps working

**Independent Test**: Push a change and verify docs Vercel preview deployment succeeds

**Why docs first**: Docs currently works. If the new approach breaks docs, we know the strategy is wrong before touching the broken web project.

### Implementation

- [ ] T004 [US2] Configure Vercel dashboard for docs project: Root Directory = empty, Build Command = `npm run build:docs`, Output Directory = `apps/docs/out`, Install Command = `npm ci`, Node.js Version = 20.x
- [ ] T005 [US2] Trigger docs redeploy and verify preview deployment succeeds
- [ ] T006 [US2] Verify security headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy) on docs preview URL

**Checkpoint**: Docs deploys successfully with new config. Proceed to web.

---

## Phase 3: User Story 1 — Successful Web Deployment (Priority: P1) 🎯 MVP

**Goal**: Fix the persistently failing web deploy by reconfiguring to monorepo root

**Independent Test**: Push a change and verify web Vercel preview deployment succeeds (no idealTree errors)

### Implementation

- [ ] T007 [US1] Configure Vercel dashboard for web project: Root Directory = empty, Build Command = `npm run build:web`, Output Directory = `apps/web/.next`, Install Command = `npm ci`, Node.js Version = 20.x
- [ ] T008 [US1] Trigger web redeploy and verify preview deployment succeeds
- [ ] T009 [US1] Verify security headers on web preview URL
- [ ] T010 [US1] Verify static asset caching header (`Cache-Control: public, max-age=31536000, immutable`) on `/_next/static/*`

**Checkpoint**: Both apps deploy successfully. Core problem solved.

---

## Phase 4: User Story 3 — CI Alignment (Priority: P3)

**Goal**: Ensure CI frontend build uses the same install approach as Vercel

**Independent Test**: CI pipeline frontend job passes with `npm ci`

### Implementation

- [ ] T011 [US3] Verify CI workflow `.github/workflows/ci.yml` frontend job already uses `npm ci` (it does — confirm no changes needed)

**Checkpoint**: CI and Vercel use aligned install strategy.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Documentation updates and final verification

- [ ] T012 Update deployment section in `CLAUDE.md` — change Vercel root directory references from `apps/web/` and `apps/docs` to monorepo root, note dashboard settings
- [ ] T013 Commit all changes, push to branch `018-fix-deploy-strategy`
- [ ] T014 Verify both preview deployments succeed on the PR branch
- [ ] T015 Run full verification from `specs/018-fix-deploy-strategy/quickstart.md`
- [ ] T016 Create PR to main

**Checkpoint**: All changes committed, PR ready for merge.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — code changes only
- **Phase 2 (Docs/US2)**: Depends on Phase 1 — test new config on working app first
- **Phase 3 (Web/US1)**: Depends on Phase 2 success — only proceed if docs works
- **Phase 4 (CI/US3)**: Independent — can run in parallel with Phase 2/3
- **Phase 5 (Polish)**: Depends on Phases 1-3 completion

### Critical Path

```
T001 → T002+T003 (parallel) → T004 → T005+T006 → T007 → T008+T009+T010 → T012 → T013 → T014 → T016
```

### Parallel Opportunities

- T002 + T003: Delete both per-app configs simultaneously
- T005 + T006: Verify deploy + check headers after docs dashboard change
- T008 + T009 + T010: Verify deploy + check headers + check caching after web dashboard change
- T011 runs independently of all other tasks

---

## Implementation Strategy

### Execution Plan

1. **Code changes first** (T001-T003): Create root config, delete old configs
2. **Docs validation** (T004-T006): Lower-risk app confirms strategy works
3. **Web fix** (T007-T010): Apply proven strategy to broken app
4. **Documentation + PR** (T012-T016): Clean up and ship

### Rollback Plan

If docs deployment fails after Phase 2:
1. Revert dashboard settings (Root Directory back to `apps/docs`)
2. Revert code changes (`git checkout main -- apps/docs/vercel.json`)
3. Reconsider approach (possibly fall back to Option B: `cd ../.. && npm ci`)

---

## Notes

- Dashboard changes (T004, T007) are manual — must be done by the developer in Vercel UI
- Verification tasks (T005-T006, T008-T010) require waiting for Vercel build to complete (~1-2 min)
- T011 is likely a no-op since CI already uses `npm ci`
- Commit after each logical group, not after each individual task
