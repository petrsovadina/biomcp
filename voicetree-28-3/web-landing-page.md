---
color: green
isContextNode: false
agent_name: Ben
---
# apps/web/ — Landing Page Architecture

Single-page Next.js 15 + React 19 + Tailwind 4 landing page. 909 lines across 13 files. Dark-first theme (next-themes, class strategy), Geist Sans/Mono fonts, IntersectionObserver scroll animations. Static export, no next.config.

**Stack:** Next.js ^15, React ^19, Tailwind CSS ^4 (`@tailwindcss/postcss`), next-themes ^0.4.6, clsx ^2, tailwind-merge ^3

### Page Flow (10 sections in order)
```
Navbar → Hero → ProblemSolution → Features → ToolCatalog → HowItWorks → CodeExample → Testimonial → CTA → Footer
```

### Components (13 total)

| Component | Type | Lines | Purpose |
|-----------|------|-------|---------|
| `layout.tsx` | Server | 45 | Root: Metadata (cs_CZ OG), ThemeProvider, Geist fonts, `lang="cs"` |
| `page.tsx` | Server | 27 | Composes 10 sections, zero logic |
| `navbar.tsx` | Client | ~60 | Fixed nav, mobile hamburger, docs link, theme toggle |
| `hero.tsx` | Server | 99 | Gradient hero, 3 floating orbs (CSS keyframe), terminal block |
| `features.tsx` | Server | 83 | 6-card grid: SUKL(8), MKN-10(4), NRPZS(3), SZV+VZP(5), PubMed(8), Genomika(29) |
| `tool-catalog.tsx` | Server | 62 | 12/60 tools sampled, group color badges (6 colors) |
| `fade-in.tsx` | Client | 53 | IntersectionObserver (threshold 0.1), 4 directions, CSS transition |
| `theme-provider.tsx` | Client | ~15 | next-themes (attribute=class, defaultTheme=dark) |
| `theme-toggle.tsx` | Client | ~20 | Dark/light sun/moon toggle |
| `problem-solution.tsx` | Server | ~50 | Problem → solution comparison |
| `how-it-works.tsx` | Server | ~60 | Step-by-step guide |
| `code-example.tsx` | Server | ~50 | Code snippets |
| `cta.tsx` | Server | ~30 | Call to action + footer combined |
| `footer.tsx` | Server | ~40 | Links, credits |
| `testimonial.tsx` | Server | ~40 | User testimonial cards |

### CSS Architecture: Tailwind 4 `@theme` + Custom Keyframes
- **Theme vars:** `@theme` block defines dark colors, `:root` overrides for light, `.dark` restores dark
- **Custom variant:** `@custom-variant dark (&:where(.dark, .dark *))` — Tailwind 4 syntax
- **5 keyframe animations:** `hero-fade-up` (0.8s blur→clear), `float-slow/reverse/medium` (10-15s infinite), `nav-slide-down` (0.5s)
- **FadeIn system:** `.fade-in` + `.fade-in-{up,left,right,scale}` + `.fade-in-visible` — IntersectionObserver adds visible class, CSS handles transitions (0.7s ease)
- **Color palette:** primary blue-500, emerald accent, gray/white neutral, amber/violet/rose/cyan for tool groups

### SEO & Metadata
- OpenGraph: cs_CZ locale, website type
- Twitter: summary_large_image
- Keywords: MCP, AI, zdravotnictví, SUKL, MKN-10, PubMed, Claude, Cursor
- Title: "CzechMedMCP — AI napojení na české zdravotnictví"

### Gotchas
- No `next.config.ts/mjs` — relies on Next.js defaults (static export likely via Vercel build)
- Terminal block in hero always dark regardless of theme (hardcoded `bg-[#0a0a0a]`)
- `lib/utils.ts` exists (likely cn() helper) but only FadeIn uses client-side JS
- No lucide-react icons actually used despite being in node_modules

[[frontend-overview]]
