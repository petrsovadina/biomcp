# Implementation Plan: Dark/Light Mode pro Landing Page

**Branch**: `008-dark-light-mode` | **Date**: 2026-03-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/008-dark-light-mode/spec.md`

## Summary

Přidání dark/light mode přepínače na landing page (apps/web). Stránka aktuálně používá 87 hardcoded dark barev napříč 10 komponentami. Přístup: next-themes + Tailwind CSS `dark:` varianty + CSS proměnné v globals.css.

## Technical Context

**Language/Version**: TypeScript, Next.js 15, React 19, Tailwind CSS v4
**Primary Dependencies**: next-themes (nová), existující Next.js + Tailwind
**Storage**: localStorage (persistence volby přes next-themes)
**Testing**: Vizuální kontrola, WCAG contrast checker
**Target Platform**: Web (Vercel deployment)
**Project Type**: Frontend landing page
**Performance Goals**: Přepnutí < 0.3s, žádný flash při načtení
**Constraints**: 87 hardcoded barev v 10 komponentách, kódové bloky zůstávají dark
**Scale/Scope**: 10 komponent (~665 řádků), 1 layout, 1 CSS soubor, 1 nová závislost

## Constitution Check

| Principle | Relevance | Status |
|-----------|-----------|--------|
| I. MCP Protocol First | N/A — čistě frontend | PASS |
| II. Modular Domain Architecture | N/A — apps/web je oddělený | PASS |
| III. Authoritative Data Sources | N/A | PASS |
| IV. CLI & MCP Dual Access | N/A | PASS |
| V. Testing Rigor | ALIGNS — vizuální validace | PASS |
| Development Workflow | ALIGNS — feature branch | PASS |

**Gate Result**: PASS

## Project Structure

### Files to CREATE

```text
apps/web/components/theme-toggle.tsx    # Přepínací tlačítko (slunce/měsíc ikona)
apps/web/components/theme-provider.tsx  # next-themes wrapper
```

### Files to EDIT

```text
apps/web/app/layout.tsx                 # Obalit ThemeProvider
apps/web/app/globals.css                # Přidat light theme CSS proměnné
apps/web/components/navbar.tsx          # Přidat ThemeToggle + dark: varianty
apps/web/components/hero.tsx            # dark: varianty
apps/web/components/features.tsx        # dark: varianty
apps/web/components/problem-solution.tsx # dark: varianty
apps/web/components/tool-catalog.tsx    # dark: varianty
apps/web/components/how-it-works.tsx    # dark: varianty
apps/web/components/code-example.tsx    # dark: varianty
apps/web/components/testimonial.tsx     # dark: varianty
apps/web/components/cta.tsx             # dark: varianty
apps/web/components/footer.tsx          # dark: varianty
apps/web/package.json                   # Přidat next-themes
```

## Implementation Strategy

### Přístup: CSS proměnné + dark: prefix

Místo přepisování každé barvy inline, použijeme **duální strategii**:

1. **globals.css** — definujeme dvě sady CSS proměnných (`:root` pro light, `.dark` pro dark)
2. **Komponenty** — nahradíme hardcoded barvy za:
   - CSS proměnné pro základní barvy (pozadí, text, borders)
   - Tailwind `dark:` prefix pro specifické elementy

### Barevná paleta Light Mode

| Element | Dark Mode | Light Mode |
|---------|-----------|------------|
| Pozadí stránky | `#030303` | `#ffffff` |
| Primární text | `white` | `#111111` |
| Sekundární text | `white/50` | `#6b7280` (gray-500) |
| Terciální text | `white/30` | `#9ca3af` (gray-400) |
| Bordery | `white/[0.08]` | `gray-200` |
| Karty pozadí | `white/[0.03]` | `gray-50` |
| Navbar pozadí | `#030303/80` | `white/80` |
| CTA tlačítko | `bg-white text-dark` | `bg-gray-900 text-white` |
| Kódové bloky | tmavé (zachovat) | tmavé (zachovat) |
| Accent barvy | blue-400, emerald-400 | blue-600, emerald-600 (tmavší pro kontrast) |

## Implementation Phases

### Phase 1: Infrastruktura (US3 — no flash prerekvizita)

1. Nainstalovat `next-themes`
2. Vytvořit `theme-provider.tsx` s `attribute="class"` a `defaultTheme="dark"`
3. Vytvořit `theme-toggle.tsx` s ikonou slunce/měsíc
4. Obalit layout do `<ThemeProvider>`
5. Aktualizovat `globals.css` — definovat light/dark CSS proměnné
6. Přidat `suppressHydrationWarning` na `<html>` pro eliminaci flash

### Phase 2: Komponenty — základní barvy (US2 část 1)

Nahradit hardcoded barvy za CSS proměnné/dark: prefix v:
- `navbar.tsx` — pozadí, text, borders (+ přidat ThemeToggle)
- `footer.tsx` — pozadí, text, borders
- `hero.tsx` — pozadí, gradienty, texty, tlačítka
- `cta.tsx` — pozadí, texty, tlačítka

### Phase 3: Komponenty — karty a sekce (US2 část 2)

- `features.tsx` — karty, ikony, badge barvy
- `tool-catalog.tsx` — karty, badge barvy (6 variant)
- `problem-solution.tsx` — karty, texty
- `testimonial.tsx` — statistiky, karty
- `how-it-works.tsx` — kroky, kódové bloky
- `code-example.tsx` — chat bubbles, kódové bloky (kód zůstává dark)

### Phase 4: Validace

1. Toggle funguje v obou směrech
2. Preference se persistuje v localStorage
3. Systémová preference se respektuje
4. Žádný flash při načtení
5. WCAG AA kontrast ve všech sekcích

## Build Sequence

```text
Phase 1 (infrastruktura)
    ↓
Phase 2 (základní komponenty)  ← závisí na Phase 1
    ↓
Phase 3 (karty a sekce)       ← závisí na Phase 1, paralelní s Phase 2
    ↓
Phase 4 (validace)             ← závisí na Phase 2 + 3
```

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Flash of wrong theme | Medium | Medium | next-themes script injection + suppressHydrationWarning |
| Nekonzistentní barvy | Medium | Medium | Centralizace přes CSS proměnné |
| Špatný kontrast v light mode | Medium | Low | WCAG checker po každé komponentě |
| Rozbití animací/gradientů | Low | Medium | Gradienty přizpůsobit, ne inverovat |
