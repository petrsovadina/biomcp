# Research: Dark/Light Mode pro Landing Page

**Branch**: `008-dark-light-mode` | **Date**: 2026-03-17

## R-001: Theme management library

**Decision**: `next-themes` v0.4+
**Rationale**: De-facto standard pro Next.js dark mode. Řeší flash prevention (script injection), localStorage persistence, system preference detection, SSR kompatibilitu. Jedna závislost, 3KB gzipped.
**Alternatives considered**:
- Vlastní implementace (mediaQuery + localStorage) — více práce, chybí flash prevention
- `use-dark-mode` — zastaralý, nekompatibilní s App Router

## R-002: Přístup ke konverzi barev

**Decision**: Hybridní — CSS proměnné pro základ + Tailwind `dark:` prefix pro specifika
**Rationale**:
- CSS proměnné (`--background`, `--foreground`, `--border`, `--card`) pokryjí ~60% barev (pozadí, text, bordery)
- Tailwind `dark:` prefix pokryje zbývajících ~40% (gradient barvy, accent barvy, specifické opacity)
- Tailwind v4 podporuje CSS proměnné nativně přes `@theme`
**Alternatives considered**:
- Čisté CSS proměnné — příliš mnoho proměnných (87+), nepřehledné
- Čistý dark: prefix — duplikace tříd na každém elementu, nafouklý JSX

## R-003: Flash prevention

**Decision**: next-themes `attribute="class"` + `<html suppressHydrationWarning>`
**Rationale**: next-themes injektuje `<script>` před hydratací, který nastaví `class="dark"` na `<html>` element. Díky tomu se CSS přepne ještě před vykreslením. `suppressHydrationWarning` eliminuje React warning.
**Alternatives considered**:
- CSS `@media (prefers-color-scheme)` only — nepodporuje manuální override
- Cookie-based — server-side rendering, ale zbytečná komplexita pro statický landing page

## R-004: Stav aktuálních CSS proměnných

**Decision**: Rozšířit existující proměnné v globals.css
**Rationale**: globals.css už definuje `--color-background`, `--color-foreground` atd. — ale pouze dark hodnoty. Přidáme light hodnoty do `:root` a dark do `.dark`.
**Alternatives considered**:
- Nový soubor theme.css — zbytečná fragmentace

## R-005: Scope komponent

**Decision**: 10 komponent + layout + globals.css + 2 nové soubory = 14 souborů celkem
**Rationale**: Audit identifikoval 87 hardcoded barev v 10 komponentách. `fade-in.tsx` nemá barvy. Všechny musí být konvertovány.
**Alternatives considered**: N/A — scope je jednoznačný z auditu
