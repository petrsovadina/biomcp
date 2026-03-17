# Tasks: Dark/Light Mode pro Landing Page

**Input**: Design documents from `/specs/008-dark-light-mode/`
**Prerequisites**: plan.md (required), spec.md (required), research.md

**Tests**: Not requested. Validation via visual check + WCAG contrast.

**Organization**: US1 (toggle) a US3 (no-flash) sdílejí infrastrukturu → Phase 2. US2 (visual consistency) je největší práce → Phase 3+4. Validace → Phase 5.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup

**Purpose**: Nainstalovat závislosti.

- [x] T0\1 Nainstalovat `next-themes` do `apps/web/`: `cd apps/web && npm install next-themes`

---

## Phase 2: Foundational — Theme infrastruktura (blokuje US1, US2, US3)

**Purpose**: Vytvořit theme provider, toggle komponentu a CSS proměnné. MUSÍ být hotovo před jakoukoliv komponentou.

- [x] T0\1 Vytvořit `apps/web/components/theme-provider.tsx` — client component obalující `next-themes` ThemeProvider s `attribute="class"`, `defaultTheme="dark"`, `enableSystem`
- [x] T0\1 Vytvořit `apps/web/components/theme-toggle.tsx` — tlačítko s ikonou slunce/měsíc, volající `setTheme()` z `useTheme()`
- [x] T0\1 Aktualizovat `apps/web/app/layout.tsx` — obalit children do `<ThemeProvider>`, přidat `suppressHydrationWarning` na `<html>`, přidat class `dark` jako default
- [x] T0\1 Aktualizovat `apps/web/app/globals.css` — definovat light theme CSS proměnné v `:root` (bg white, text dark, border gray-200, card gray-50) a dark theme v `.dark` (stávající barvy #030303, white/opacity atd.)

**Checkpoint**: Toggle se zobrazí v navbaru, přepíná class na `<html>`, ale komponenty ještě nemají light varianty.

---

## Phase 3: User Story 1+2 — Toggle + Základní komponenty (Priority: P1)

**Goal**: Přepínač v navbaru funguje a 4 základní komponenty mají light variantu.

**Independent Test**: Klik na toggle přepne navbar, hero, CTA a footer na světlé barvy.

- [x] T0\1 [US1] Přidat `<ThemeToggle />` do navbar (desktop i mobile menu) v `apps/web/components/navbar.tsx`
- [x] T0\1 [US2] Konvertovat barvy navbar na dark:/light v `apps/web/components/navbar.tsx` — bg, text, borders, button
- [x] T0\1 [P] [US2] Konvertovat barvy hero na dark:/light v `apps/web/components/hero.tsx` — pozadí, gradienty, texty, tlačítka, terminál (terminál zůstává dark)
- [x] T0\1 [P] [US2] Konvertovat barvy CTA na dark:/light v `apps/web/components/cta.tsx` — pozadí, texty, kódový blok (zůstává dark), tlačítka
- [x] T0\1 [P] [US2] Konvertovat barvy footer na dark:/light v `apps/web/components/footer.tsx` — pozadí, text, borders, links

**Checkpoint**: Navbar, hero, CTA a footer fungují v obou režimech. Toggle persistuje volbu.

---

## Phase 4: User Story 2 — Karty a sekce (Priority: P1)

**Goal**: Všech zbývajících 6 komponent má konzistentní light variantu.

**Independent Test**: Celá stránka je vizuálně konzistentní ve světlém režimu od hero po footer.

- [x] T0\1 [P] [US2] Konvertovat barvy features na dark:/light v `apps/web/components/features.tsx` — karty, ikony (6 barevných variant), badge, texty
- [x] T0\1 [P] [US2] Konvertovat barvy tool-catalog na dark:/light v `apps/web/components/tool-catalog.tsx` — karty, badge (6 skupin: SUKL/MKN-10/NRPZS/SZV/Workflow/Global), texty
- [x] T0\1 [P] [US2] Konvertovat barvy problem-solution na dark:/light v `apps/web/components/problem-solution.tsx` — karty, problem/solution text, strikethrough
- [x] T0\1 [P] [US2] Konvertovat barvy testimonial na dark:/light v `apps/web/components/testimonial.tsx` — stat karty, čísla, texty
- [x] T0\1 [P] [US2] Konvertovat barvy how-it-works na dark:/light v `apps/web/components/how-it-works.tsx` — kroky, čísla, kódové bloky (zůstávají dark)
- [x] T0\1 [P] [US2] Konvertovat barvy code-example na dark:/light v `apps/web/components/code-example.tsx` — chat bubbles, AI odpověď, function tags (kód zůstává dark)

**Checkpoint**: 100% sekcí vizuálně konzistentních v obou režimech.

---

## Phase 5: User Story 3 — Validace no-flash + finální kontrola (Priority: P2)

**Goal**: Žádný flash při načtení, persistence funguje, WCAG kontrast splněn.

- [x] T0\1 [US3] Ověřit no-flash: otevřít stránku s light preferencí v localStorage — nesmí bliknout tmavý režim
- [x] T0\1 [US3] Ověřit system preference: smazat localStorage, nastavit `prefers-color-scheme: light` — stránka se zobrazí ve světlém režimu
- [x] T0\1 [US3] Ověřit persistence: přepnout na light, zavřít a znovu otevřít — zůstane light
- [x] T0\1 [US2] Ověřit WCAG AA kontrast (4.5:1) ve všech sekcích v light mode
- [x] T0\1 [US2] Ověřit že kódové bloky (hero terminál, how-it-works, code-example, CTA) zůstávají dark v obou režimech
- [x] T0\1 Lokální build: `cd apps/web && npm run build` projde bez chyby

---

## Phase 6: Commit

- [x] T0\1 Commit: `feat(web): add dark/light mode toggle to landing page`

---

## Dependencies & Execution Order

```text
Phase 1 (npm install)
    ↓
Phase 2 (theme infrastructure: T002-T005 sequential)
    ↓
Phase 3 (toggle + basic components)
  T006-T007 sequential (same file: navbar)
  T008, T009, T010 parallel (different files)
    ↓
Phase 4 (cards & sections: T011-T016 ALL parallel)
    ↓
Phase 5 (validation: T017-T022 sequential)
    ↓
Phase 6 (commit)
```

### Parallel Opportunities

- **Phase 3**: T008 (hero), T009 (cta), T010 (footer) — plně paralelní
- **Phase 4**: T011-T016 — všech 6 komponent plně paralelní (různé soubory, žádné závislosti)
- **Phase 3 + Phase 4**: Mohou běžet paralelně po dokončení T006-T007 (navbar)

---

## Implementation Strategy

### MVP (Phase 1-3 only)
1. Install + infrastructure + toggle v navbar
2. Konverze 4 základních komponent (navbar, hero, CTA, footer)
3. Toggle funguje, základní stránka je čitelná v obou režimech
4. **Deployjitelné jako MVP**

### Full Delivery
1. MVP + Phase 4 (6 dalších komponent)
2. Phase 5 (validace)
3. Kompletní dark/light mode na celé stránce

### Konverzní vzor pro každou komponentu

Pro každý soubor platí stejný postup:
1. Nahradit `bg-[#030303]` → `bg-white dark:bg-[#030303]`
2. Nahradit `text-white` → `text-gray-900 dark:text-white`
3. Nahradit `text-white/XX` → `text-gray-500 dark:text-white/XX` (dle opacity)
4. Nahradit `border-white/[0.XX]` → `border-gray-200 dark:border-white/[0.XX]`
5. Nahradit `bg-white/[0.0X]` → `bg-gray-50 dark:bg-white/[0.0X]`
6. Kódové bloky/terminály: přidat wrapper s `dark` class (vždy tmavé)
