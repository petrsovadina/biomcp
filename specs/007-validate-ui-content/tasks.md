# Tasks: Validace UI obsahu

**Input**: Design documents from `/specs/007-validate-ui-content/`
**Prerequisites**: plan.md (required), spec.md (required), research.md

**Tests**: Not requested. Validation via grep checks in final phase.

**Organization**: US1+US2 are both P1 (can run in parallel — different files). US3 depends on US1 for overlapping file. US4 is validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Pre-flight Verification

**Purpose**: Confirm exact locations of all issues before editing.

- [x] T001 Verify all `python-main` occurrences: `grep -r "python-main" apps/`
- [x] T002 Verify all `cd biomcp` occurrences: `grep -r "cd biomcp" apps/`
- [x] T003 Verify all `BioMCPError` occurrences: `grep -r "BioMCPError" apps/`
- [x] T004 Verify all `docs-site` occurrences: `grep -r "docs-site" apps/`
- [x] T005 Verify `--transport sse` occurrence: `grep -r "transport sse" apps/`
- [x] T006 Verify `v0.7.3` occurrence: `grep -r "v0.7.3" apps/`

**Checkpoint**: All targets located and confirmed.

---

## Phase 2: User Story 1 — Oprava zastaralých referencí na branch a adresáře (Priority: P1) 🎯 MVP

**Goal**: Nahradit všechny zastaralé reference na `python-main`, `cd biomcp`, `docs-site/` správnými hodnotami.

**Independent Test**: `grep -r "python-main\|cd biomcp\|docs-site" apps/` vrátí 0 výsledků.

- [x] T0\1 [P] [US1] Opravit `python-main` → `main` a `cd biomcp` → `cd CzechMedMCP` v `apps/docs/app/vyvojari/page.mdx`
- [x] T0\1 [P] [US1] Opravit `python-main` → `main`, `cd biomcp` → `cd CzechMedMCP`, `docs-site/` → `apps/docs/`, `biomcp/` → `czechmedmcp/` v `apps/docs/app/vyvojari/lokalni-vyvoj/page.mdx`
- [x] T0\1 [P] [US1] Opravit `cd biomcp` → `cd CzechMedMCP`, `python-main` → `main` v `apps/docs/app/zaciname/instalace/page.mdx`
- [x] T0\1 [P] [US1] Opravit `docs-site` → `apps/docs` (2x) v `apps/docs/app/vyvojari/deployment/page.mdx`

**Checkpoint**: Všechny zastaralé reference opraveny. `grep -r "python-main\|cd biomcp\|docs-site" apps/docs/` vrátí 0.

---

## Phase 3: User Story 2 — Oprava nesprávných příkazů a názvů (Priority: P1)

**Goal**: Opravit nesprávné CLI flagy, názvy výjimek a zastaralou verzi.

**Independent Test**: `grep -r "BioMCPError\|transport sse\|v0\.7\.3" apps/` vrátí 0 výsledků.

- [x] T0\1 [P] [US2] Opravit `--transport sse` → `--mode streamable_http` v `apps/docs/app/reference/konfigurace/page.mdx`
- [x] T0\1 [P] [US2] Opravit `BioMCPError` → `CzechMedMCPError` (a všechny podtřídy) v `apps/docs/app/architektura/vyjimky/page.mdx`
- [x] T0\1 [P] [US2] Opravit `v0.7.3` → `v0.8.0` v `apps/web/src/components/hero.tsx`

**Checkpoint**: Všechny nesprávné příkazy a názvy opraveny.

---

## Phase 4: User Story 3 — Oprava instalačních instrukcí (Priority: P2)

**Goal**: Aktualizovat instalační instrukce tak, aby odpovídaly realitě (balíček není na PyPI).

**Independent Test**: Instalační stránka jasně uvádí funkční metodu instalace (git clone + uv).

- [x] T0\1 [US3] Aktualizovat primární instalační metodu v `apps/docs/app/zaciname/instalace/page.mdx` — preferovat `uv tool install git+https://github.com/petrsovadina/CzechMedMCP.git`, pip označit jako budoucí možnost
- [x] T0\1 [P] [US3] Aktualizovat quick reference instalační příkaz v `apps/docs/app/reference/page.mdx`

**Checkpoint**: Instalační instrukce odpovídají dostupným metodám.

Phase 2 → Phase 4 dependency: T009 a T014 editují stejný soubor (`zaciname/instalace/page.mdx`).

---

## Phase 5: User Story 4 — Validace (Priority: P3)

**Goal**: Ověřit, že žádné zastaralé reference nezůstaly.

**Independent Test**: Všechny grep kontroly vrátí 0 výsledků.

- [x] T0\1 [US4] Grep validace: `python-main` v `apps/` → 0 výsledků
- [x] T0\1 [US4] Grep validace: `cd biomcp` v `apps/` → 0 výsledků
- [x] T0\1 [US4] Grep validace: `BioMCPError` v `apps/` → 0 výsledků
- [x] T0\1 [US4] Grep validace: `--transport sse` v `apps/` → 0 výsledků
- [x] T0\1 [US4] Grep validace: `docs-site` v `apps/` → 0 výsledků
- [x] T0\1 [US4] Ověřit verzi na landing page = v0.8.0
- [x] T0\1 [US4] Lokální build docs: `cd apps/docs && npm run build` projde bez chyby

---

## Phase 6: Final Commit

- [ ] T023 Commit všech změn: `docs: fix outdated references and incorrect commands in UI`

---

## Dependencies & Execution Order

```text
Phase 1 (pre-flight verification)
    ↓
Phase 2 (US1: branch/dir refs)  ← T007-T010 can all run in parallel
    ↓
Phase 3 (US2: commands/names)   ← T011-T013 can all run in parallel, independent of Phase 2
    ↓
Phase 4 (US3: install docs)     ← T014 depends on T009 (same file)
    ↓
Phase 5 (US4: validation)       ← depends on all previous phases
    ↓
Phase 6 (commit)
```

### Parallel Opportunities

- **Phase 1**: T001-T006 — all grep checks can run in parallel
- **Phase 2**: T007-T010 — all edit different files, fully parallel
- **Phase 3**: T011-T013 — all edit different files, fully parallel
- **Phase 2 + Phase 3**: Can run in parallel (no file overlap between US1 and US2)
- **Phase 4**: T014-T015 — T015 is parallel, T014 depends on T009 completing

---

## Implementation Strategy

### MVP (US1 + US2 only)
1. Phase 1: Pre-flight
2. Phase 2: Fix branch/directory references (4 files)
3. Phase 3: Fix commands/names (3 files)
4. Phase 5: Validate
5. This alone fixes all blocking developer issues

### Full Delivery
1. MVP + US3 (install docs) + US4 (full validation)
2. Single commit at the end
