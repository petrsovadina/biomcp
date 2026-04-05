# Implementation Plan: Fix Deploy Strategy

**Branch**: `018-fix-deploy-strategy` | **Date**: 2026-04-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/018-fix-deploy-strategy/spec.md`

## Summary

Fix persistent Vercel deployment failures for the web app (`apps/web`) caused by npm's `idealTree` bug in a monorepo context. The solution changes both Vercel projects' Root Directory from per-app (`apps/web`, `apps/docs`) to the monorepo root (`/`), uses `npm ci` for deterministic installs, and consolidates deployment configuration.

## Technical Context

**Language/Version**: Node.js 20.x (pinned via `engines` in package.json)
**Primary Dependencies**: npm workspaces, Turborepo v2, Next.js 15, Nextra 4
**Storage**: N/A
**Testing**: Manual deployment verification (push → Vercel build → live URL)
**Target Platform**: Vercel (hosting), GitHub (CI/CD)
**Project Type**: Monorepo deployment configuration
**Performance Goals**: Build time under 2 minutes per app
**Constraints**: No Vercel project recreation; must preserve existing project IDs and domains
**Scale/Scope**: 2 Vercel projects (web + docs), 1 shared package (tsconfig)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Applies? | Status | Notes |
| --------- | -------- | ------ | ----- |
| I. MCP Protocol First | No | PASS | Deployment config, not MCP tools |
| II. Modular Domain Architecture | No | PASS | No source code changes |
| III. Authoritative Data Sources | No | PASS | No data source changes |
| IV. CLI & MCP Dual Access | No | PASS | No CLI changes |
| V. Testing Rigor | Partial | PASS | Verification via deployment, no unit tests needed for config files |

**Gate result**: PASS — no violations.

## Project Structure

### Documentation (this feature)

```text
specs/018-fix-deploy-strategy/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Vercel monorepo config research
├── quickstart.md        # Deployment verification guide
└── checklists/
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
# Files to CREATE
vercel.json                    # New root-level config (shared headers only)

# Files to DELETE
apps/web/vercel.json           # Replaced by root config + dashboard settings
apps/docs/vercel.json          # Replaced by root config + dashboard settings

# Manual changes (Vercel Dashboard) — per-project settings
# Web project (czech-med-mcp-web):
#   Root Directory: (empty)
#   Build Command: npm run build:web
#   Output Directory: apps/web/.next
#   Install Command: npm ci
#
# Docs project (czech-med-mcp-docs):
#   Root Directory: (empty)
#   Build Command: npm run build:docs
#   Output Directory: apps/docs/out
#   Install Command: npm ci
```

**Structure Decision**: Config-only change. Root `vercel.json` holds shared headers. All per-project settings (build/install/output) are in the Vercel dashboard, not in config files. This avoids the problem of two projects reading the same vercel.json with conflicting settings.

## Implementation Steps

### Step 1: Create root-level vercel.json (code change)

Create `vercel.json` at monorepo root with shared headers only:
- Security headers: X-Content-Type-Options, X-Frame-Options, Referrer-Policy
- Static asset caching: Cache-Control for `/_next/static/*`
- No `buildCommand`, `installCommand`, or `framework` — these go in dashboard

### Step 2: Delete per-app vercel.json files (code change)

Remove `apps/web/vercel.json` and `apps/docs/vercel.json`. All their content is now either in the root `vercel.json` (headers) or in dashboard settings (build/install/output).

### Step 3: Configure Vercel dashboard — docs project first (manual)

Change docs project first (lower risk — currently working):
- Root Directory: clear/empty (monorepo root)
- Build Command: `npm run build:docs`
- Output Directory: `apps/docs/out`
- Install Command: `npm ci`

Trigger a redeploy and verify it works before touching web.

### Step 4: Configure Vercel dashboard — web project (manual)

After docs succeeds:
- Root Directory: clear/empty (monorepo root)
- Build Command: `npm run build:web`
- Output Directory: `apps/web/.next`
- Install Command: `npm ci`

### Step 5: Push code changes and verify (verification)

- Commit root `vercel.json` + deletion of per-app configs
- Push to branch `018-fix-deploy-strategy`
- Verify both preview deployments succeed
- Check security headers in response
- Merge to main and verify production

### Step 6: Update CLAUDE.md deployment section (code change)

Update the Deployment table in CLAUDE.md to reflect new config approach:
- Web Vercel root = `/` (monorepo root)
- Docs Vercel root = `/` (monorepo root)
- Note that per-project settings are in Vercel dashboard

## Risk Assessment

| Risk | Impact | Mitigation |
| ---- | ------ | ---------- |
| Root Directory change breaks existing deploy | High | Test on preview branch first before merging to main |
| Headers config doesn't work from root vercel.json | Medium | Verify headers in preview deployment response |
| Docs app regresses | Medium | Verify docs preview deployment before changing web |
| Vercel project IDs change | Low | Project IDs are in `.vercel/project.json`, not affected by Root Directory |

## Complexity Tracking

No constitution violations to justify.
