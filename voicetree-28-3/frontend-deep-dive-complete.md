---
color: green
isContextNode: false
agent_name: Bob
---
# Frontend Apps Deep Dive Complete

Comprehensive exploration of both frontend apps (apps/web/ and apps/docs/). Updated all 3 Voicetree nodes with verified architecture details, exact file counts, component inventories, build configs, and gotchas.

## Web Landing Page (apps/web/)
- **909 lines** across 13 TSX/CSS files
- 10-section single page: Navbar → Hero → ProblemSolution → Features → ToolCatalog → HowItWorks → CodeExample → Testimonial → CTA → Footer
- Stack: Next.js ^15, React ^19, Tailwind CSS ^4 (via @tailwindcss/postcss), next-themes, clsx, tailwind-merge
- 3 Client components (FadeIn, ThemeProvider, ThemeToggle), rest Server
- FadeIn: IntersectionObserver with 4 directions (up/left/right/scale), CSS transitions 0.7s
- 5 custom CSS keyframes: hero-fade-up, float-slow/reverse/medium, nav-slide-down
- Tailwind 4 @theme + @custom-variant dark syntax
- No next.config — pure defaults
- SEO: cs_CZ OG, Twitter card, 10 keywords

## Nextra Docs (apps/docs/)
- **39 MDX pages** in 7 sections + 7 _meta.ts nav files
- Stack: Nextra ^4.6.1, nextra-theme-docs ^4.6.1, Next.js ^15.5.12, React ^19.2.4
- Static export with `output: 'export'`, `images: { unoptimized: true }`
- Czech UI: editLink, feedback, toc titles all in Czech
- Async server layout with `await getPageMap()`
- Pinned `@napi-rs/simple-git-linux-x64-gnu: 0.1.19` for Vercel builds

## Monorepo
- Turborepo v2 with 3 tasks (build, dev, lint)
- npm workspaces: apps/*, packages/* (packages/ currently empty)
- Node 20.x pinned globally (engines field in root + both apps)
- Each app has own vercel.json; docs uses `cd ../..` pattern for monorepo root install

## Files Changed

- voicetree-28-3/frontend-overview.md
- voicetree-28-3/web-landing-page.md
- voicetree-28-3/nextra-docs.md

### NOTES

- lucide-react is in web node_modules but not actually imported by any component — dead dependency
- packages/ workspace dir exists but has no shared packages — both apps are fully independent
- docs has own package-lock.json (247KB) separate from root — dependency drift risk
- No next.config in web app — static export must be handled by Vercel build, not Next.js config

[[frontend-overview]]
