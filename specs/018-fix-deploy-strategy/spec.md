# Feature Specification: Fix Deploy Strategy

**Feature Branch**: `018-fix-deploy-strategy`
**Created**: 2026-04-01
**Status**: Draft
**Input**: User description: "Analyze and fix deployment strategy after monorepo implementation — Vercel web deploy persistently failing with idealTree npm bug"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Successful Web App Deployment (Priority: P1)

As a developer, when I push code to `main`, the landing page (`apps/web`) successfully deploys to Vercel without manual intervention, so that the public-facing website stays up to date.

**Why this priority**: The web app has been failing to deploy for 14+ hours across 5+ fix attempts. This is the primary blocker — the public website cannot be updated.

**Independent Test**: Push a trivial change to `apps/web` (e.g., update a text string) and verify the Vercel deployment completes successfully with a live preview URL.

**Acceptance Scenarios**:

1. **Given** code is pushed to `main` with changes in `apps/web`, **When** Vercel triggers a build, **Then** the build completes successfully and the preview/production URL is accessible
2. **Given** the monorepo has workspace dependencies (`@czechmedmcp/tsconfig`), **When** Vercel installs dependencies, **Then** all workspace packages resolve correctly without "idealTree" or resolution errors
3. **Given** a clean Vercel build cache, **When** the first build runs, **Then** it succeeds without requiring manual cache clearing

---

### User Story 2 - Consistent Docs App Deployment (Priority: P2)

As a developer, the docs app (`apps/docs`) continues to deploy reliably after any deployment configuration changes, maintaining the same stability it has today.

**Why this priority**: Docs deploys currently work. Any changes to the deployment strategy must not regress this. Lower priority because it's not broken.

**Independent Test**: Verify that a push affecting `apps/docs` still produces a successful Vercel deployment after the fix is applied.

**Acceptance Scenarios**:

1. **Given** the deployment strategy is updated for `apps/web`, **When** `apps/docs` is deployed, **Then** it continues to build and deploy successfully
2. **Given** both apps share the same monorepo root install, **When** dependencies are installed, **Then** both apps resolve their workspace dependencies correctly

---

### User Story 3 - Reliable CI Pipeline (Priority: P3)

As a developer, the CI pipeline (GitHub Actions) builds the frontend apps using the same approach as Vercel, so that CI success predicts deployment success.

**Why this priority**: CI frontend job uses `npm ci` (deterministic) while Vercel uses `npm install` (non-deterministic). Aligning these reduces "works in CI, fails on deploy" surprises.

**Independent Test**: Run the CI pipeline and verify the frontend build job passes with the same install strategy as the Vercel config.

**Acceptance Scenarios**:

1. **Given** CI and Vercel use aligned install commands, **When** CI frontend build passes, **Then** Vercel deployment also succeeds for the same commit

---

### Edge Cases

- What happens when Vercel's build cache is corrupted from a previous failed build?
- What happens when a new workspace package is added to `packages/`?
- What happens when `package-lock.json` has merge conflicts and is resolved incorrectly?
- What happens when Vercel's default Node.js version changes?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Web app (`apps/web`) MUST deploy successfully on Vercel from a monorepo context with npm workspace dependencies
- **FR-002**: Install command MUST use deterministic dependency resolution (`npm ci`) to avoid non-reproducible installs
- **FR-003**: Build command MUST correctly resolve and build workspace dependencies before building the target app
- **FR-004**: Vercel configuration MUST explicitly pin the Node.js version to match the project's `engines` field (20.x)
- **FR-005**: Both Vercel projects (web + docs) MUST use a consistent deployment configuration pattern
- **FR-006**: The deployment MUST NOT depend on clearing npm cache as a workaround — the root cause must be fixed
- **FR-007**: Security and caching headers (X-Content-Type-Options, X-Frame-Options, Cache-Control for static assets) MUST be preserved in the updated configuration

### Key Entities

- **Vercel Project (web)**: Landing page, project ID `prj_Tfqm0cruS2P8bpPXgTLcVblnQk2N`, root directory currently `apps/web`
- **Vercel Project (docs)**: Documentation site, project ID `prj_OIls5yfu3RcTuIGurNlquEP16cak`, root directory currently `apps/docs`
- **Workspace Package (tsconfig)**: Shared TypeScript config at `packages/tsconfig/`, referenced as `@czechmedmcp/tsconfig`

## Root Cause Analysis

### Why "idealTree already exists" happens

The npm `idealTree` error occurs when npm's internal package resolution state becomes inconsistent. In this monorepo setup, the specific chain of failure is:

1. Vercel sets Root Directory to `apps/web` (or `apps/docs`)
2. The `installCommand` does `cd ../..` to navigate to the monorepo root
3. `npm install` (not `npm ci`) runs at the root, attempting to resolve the full workspace dependency tree
4. Vercel's build container retains cached npm metadata from previous builds
5. The cached metadata conflicts with the current lockfile state, causing the `idealTree` resolution to fail

### Why previous fixes didn't work

| Attempt | What was tried | Why it failed |
| ------- | -------------- | ------------- |
| Commit ccfb44b | Added `npm cache clean` | npm 7+ ignores `--force` in some container contexts |
| Commit 93c0985 | Removed `node_modules` + `package-lock.json` | Doesn't address cached npm internal state |
| Commit 7c8c303 | Cleared only `/vercel/.npm/_cacache` | Only removes HTTP cache, not package resolution metadata |

### The actual fix

The root cause is twofold:

1. **Using `npm install` instead of `npm ci`** in a CI/CD context. `npm ci` deletes `node_modules` automatically, installs exactly from `package-lock.json` (no resolution step = no idealTree), and is designed for CI/CD environments.
2. **The `cd ../..` hack** to escape Vercel's Root Directory is fragile. Vercel should be configured to install from the monorepo root natively.

## Chosen Solution: Set Vercel Root Directory to monorepo root

Configure both Vercel projects to use the monorepo root as their Root Directory via Vercel dashboard settings, with app-specific build commands:

- **Root Directory**: `/` (monorepo root, set in Vercel dashboard)
- **Install Command**: `npm ci`
- **Build Command**: `npm run build:web` (or `build:docs`)
- **Output Directory**: `apps/web/.next` (or `apps/docs/out`)

This eliminates the `cd ../..` hack and lets Vercel handle workspace resolution natively. The per-app `vercel.json` files are consolidated into a single root-level config (or removed if redundant).

**Decision rationale**: Option A chosen over Option B (keeping `cd ../..` with `npm ci`) because it provides a cleaner, more maintainable long-term solution. The `cd ../..` pattern is inherently fragile and depends on Vercel's internal directory structure assumptions. Root-level config aligns with Vercel's native monorepo support.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Web app deploys successfully on Vercel on the first attempt after configuration change, without any cache-clearing workarounds
- **SC-002**: Docs app continues to deploy successfully with no regressions
- **SC-003**: Deployment build time is under 2 minutes for both apps
- **SC-004**: No "idealTree", "ERESOLVE", or npm resolution errors appear in Vercel build logs
- **SC-005**: Both apps serve correctly at their production URLs with security headers intact

## Clarifications

### Session 2026-04-02

- Q: Deployment approach — Option A (root directory) vs Option B (keep `cd ../..` with `npm ci`) vs Option C (B now, A later)? → A: Option A — change Root Directory to monorepo root in Vercel dashboard for both projects

## Assumptions

- Vercel supports `npm ci` in custom install commands
- Changing the Root Directory in Vercel dashboard is feasible without recreating the project
- The `package-lock.json` in the repository is up to date and consistent with `package.json`
- Node.js 20.x is available as a Vercel build runtime option
- GitHub Actions billing issue is separate and will be resolved independently
