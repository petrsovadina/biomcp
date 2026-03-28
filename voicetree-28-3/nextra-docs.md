---
color: green
isContextNode: false
agent_name: Ben
---
# apps/docs/ — Nextra Documentation

Nextra 4.6.1 dokumentace s 39 MDX stránkami v 7 sekcích + 7 `_meta.ts` navigačních souborů. České UI texty. Static export (`output: 'export'`), `images: { unoptimized: true }`.

**Stack:** Nextra ^4.6.1, nextra-theme-docs ^4.6.1, Next.js ^15.5.12, React ^19.2.4, `@napi-rs/simple-git-linux-x64-gnu: 0.1.19` (pinned)

### Structure (7 sections, 39 MDX pages)

```
_meta.ts (root: 7 sections + separator + GitHub link)
├─ Úvod (index) — full layout, no sidebar/toc/breadcrumb/pagination
├─ Začínáme (4): Instalace, Claude Desktop, API klíče, První dotaz
├─ Nástroje (7): SUKL, MKN-10, NRPZS, SZV, VZP, Globální, Workflow
├─ Příručka (7): Workflow, Léky, Diagnostika, Varianty, Studie, Řešení problémů, FAQ
├─ Architektura (6): Overview, HTTP pipeline, Router, České moduly, cBioPortal, Výjimky
├─ Pro vývojáře (5): Overview, Lokální vývoj, Testy, Styl kódu, Deployment
├─ Reference (4): Overview, CLI, Konfigurace, Changelog
└─ GitHub (external link)
```

### Layout Config (layout.tsx)
- **Navbar:** `🏥 CzechMedMCP` (fontWeight 800), GitHub project link
- **Footer:** MIT {year} © Petr Sovadina, MCP protocol link
- **Czech UI:** `editLink='Upravit stránku'`, `feedback.content='Máte otázku? Dejte nám vědět →'`, `toc.title='Na této stránce'`
- **Sidebar:** `defaultMenuCollapseLevel: 1`
- **docsRepositoryBase:** `github.com/petrsovadina/CzechMedMCP/tree/main/apps/docs`
- **Metadata:** cs locale, OG + description, 8 keywords
- **PageMap:** `await getPageMap()` (async server layout)

### Build Config (next.config.mjs)
```js
import nextra from 'nextra'
const withNextra = nextra({})  // minimal config
export default withNextra({ output: 'export', images: { unoptimized: true } })
```

### Vercel Deploy
- `installCommand: "cd ../.. && npm install"` — navigates to monorepo root
- `buildCommand: "cd ../.. && npx turbo build --filter=czechmedmcp-docs"`
- Has own `package-lock.json` (247KB) — potential dependency drift vs root

### Gotchas
- `@napi-rs/simple-git-linux-x64-gnu` explicitly pinned as dep — needed by Nextra's git-based features (last modified dates). Node 24 breaks this.
- `nextra({})` — empty config object, no custom plugins/extensions
- No custom CSS, no MDX components besides nextra-theme-docs builtins
- `mdx-components.tsx` exists at docs root (Nextra requirement)
- Docs layout is async server component (Next.js 15 pattern)

[[frontend-overview]]
