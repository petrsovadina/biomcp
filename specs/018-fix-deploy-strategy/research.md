# Research: Vercel Monorepo Deployment Configuration

**Date**: 2026-04-02
**Feature**: 018-fix-deploy-strategy

## Key Findings

### 1. vercel.json is per-project, not global

- A `vercel.json` applies only to the project whose Root Directory contains it
- If Root Directory = "/" for both projects, both read the same root `vercel.json`
- This is fine when both apps share the same headers — differentiation happens in dashboard settings

**Decision**: Use a single root `vercel.json` with shared headers. All project-specific settings (build command, output directory, install command) go in the Vercel dashboard.

### 2. Build differentiation via dashboard

When Root Directory = "/" for multiple projects in the same repo:
- Build Command, Output Directory, Install Command are set per-project in the dashboard
- These override anything in `vercel.json`
- No `cd ../..` needed since Vercel already runs from the root

**Decision**: Configure all build/install/output settings in the Vercel dashboard, not in vercel.json.

### 3. npm ci works but has caching tradeoffs

- `npm ci` deletes `node_modules` before installing, which means Vercel's node_modules cache is invalidated every build
- This makes builds slightly slower but completely eliminates the `idealTree` bug
- Alternative: use `.npmrc` with specific settings for better compatibility

**Decision**: Use `npm ci` as install command. The reliability tradeoff is worth a few extra seconds of build time. The `idealTree` bug is caused by stale cached state, and `npm ci` eliminates this entirely.

### 4. Node.js version is dashboard-only

- `nodeVersion` is NOT a valid `vercel.json` field
- Set via Project Settings > Node.js Version in the dashboard
- Can also be set via `engines.node` in `package.json` (which we already have: `"node": "20.x"`)

**Decision**: Rely on `engines.node` in root `package.json` (already set to `20.x`). No vercel.json change needed.

### 5. Output directory for subdirectory builds

- When Root Directory = "/", `outputDirectory` must be relative to root
- For web: `apps/web/.next`
- For docs: `apps/docs/out` (Nextra uses `output: 'export'`)

**Decision**: Set output directories in dashboard — `apps/web/.next` for web, `apps/docs/out` for docs.

## Revised Implementation Approach

Instead of putting all configuration in vercel.json, the approach is:

1. **Root `vercel.json`**: Only shared headers (security + caching)
2. **Dashboard settings per project**: Build command, install command, output directory, Node.js version
3. **Delete per-app vercel.json files**: No longer needed

### Web Project Dashboard Settings
| Setting | Value |
| ------- | ----- |
| Root Directory | (empty — monorepo root) |
| Build Command | `npm run build:web` |
| Install Command | `npm ci` |
| Output Directory | `apps/web/.next` |
| Node.js Version | 20.x (from package.json engines) |

### Docs Project Dashboard Settings
| Setting | Value |
| ------- | ----- |
| Root Directory | (empty — monorepo root) |
| Build Command | `npm run build:docs` |
| Install Command | `npm ci` |
| Output Directory | `apps/docs/out` |
| Node.js Version | 20.x (from package.json engines) |

## Alternatives Considered

### Keep per-app Root Directory + npm ci (Option B from spec)
- Keeps `cd ../..` pattern
- Simpler dashboard change (only install command)
- **Rejected**: `cd ../..` is fragile and doesn't align with Vercel's monorepo support

### Use vercel.ts (programmatic config)
- TypeScript-based config with dynamic logic
- Overkill for this simple monorepo
- **Rejected**: Adds complexity; headers-only vercel.json is sufficient

## Sources
- Vercel Monorepo Docs: https://vercel.com/docs/monorepos
- Vercel Project Configuration: https://vercel.com/docs/project-configuration/vercel-json
- Vercel Node.js Versions: https://vercel.com/docs/functions/runtimes/node-js/node-js-versions
