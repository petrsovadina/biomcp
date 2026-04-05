# Deployment Verification Guide

## Pre-deployment checklist

- [ ] Root `vercel.json` exists with shared headers
- [ ] `apps/web/vercel.json` deleted
- [ ] `apps/docs/vercel.json` deleted
- [ ] Vercel dashboard: docs project Root Directory = empty
- [ ] Vercel dashboard: docs project Build Command = `npm run build:docs`
- [ ] Vercel dashboard: docs project Output Directory = `apps/docs/out`
- [ ] Vercel dashboard: docs project Install Command = `npm ci`
- [ ] Vercel dashboard: web project Root Directory = empty
- [ ] Vercel dashboard: web project Build Command = `npm run build:web`
- [ ] Vercel dashboard: web project Output Directory = `apps/web/.next`
- [ ] Vercel dashboard: web project Install Command = `npm ci`

## Verification steps

### 1. Local build (sanity check)

```bash
npm ci
npm run build:web
npm run build:docs
```

Both should complete without errors.

### 2. Push and check preview deployments

```bash
git push origin 018-fix-deploy-strategy
```

Check Vercel dashboard for both projects — both should show "Building" then "Ready".

### 3. Verify security headers

```bash
# Web app
curl -sI <preview-url> | grep -E "X-Content-Type|X-Frame|Referrer-Policy"

# Docs app
curl -sI <docs-preview-url> | grep -E "X-Content-Type|X-Frame|Referrer-Policy"
```

Expected:
```
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: strict-origin-when-cross-origin
```

### 4. Verify static asset caching

```bash
curl -sI <preview-url>/_next/static/chunks/main.js | grep Cache-Control
```

Expected: `Cache-Control: public, max-age=31536000, immutable`

### 5. Merge and verify production

After preview passes, merge to main and verify production URLs.

## Rollback plan

If the new config fails:
1. Revert the commit (restore per-app vercel.json files)
2. In Vercel dashboard, set Root Directory back to `apps/web` / `apps/docs`
3. Clear Vercel build cache and redeploy
