# Tasks: Stabilizace a vyčištění codebase CzechMedMCP

**Input**: `specs/002-codebase-stabilization/spec.md`
**Branch**: `002-codebase-stabilization`

**Tests**: Existující test suite (713+ testů). Žádné nové testy vyžadovány — tato feature je refaktoring a údržba.

**Organization**: Tasky seskupeny do fází podle závislostí. US4 (mypy) a US2 (CI) jsou prerekvizity pro vše ostatní.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Lze spustit paralelně (různé soubory, žádné závislosti)
- **[Story]**: Uživatelský scénář z spec.md (US1–US5)

---

## Phase 1: Setup

**Purpose**: Ověřit výchozí stav, nic nepokazit.

- [x] T001 Ověřit aktuální test suite: `uv run python -m pytest -x --ff -n auto --dist loadscope -m "not integration"` — musí projít 713+ testů

---

## Phase 2: Foundational — Typová bezpečnost (blokuje US2, US4)

**Purpose**: Opravit mypy chyby, které blokují CI pipeline i typovou důvěryhodnost. Musí být hotovo před CI setupem.

**⚠️ CRITICAL**: CI workflow (US2) spouští `uv run mypy` — dokud nejsou chyby opraveny, CI bude vždy fail.

- [x] T002 [P] [US4] Opravit 2 mypy chyby v `src/czechmedmcp/variants/cbioportal_search.py` (řádky 155, 157) — proměnná typovaná jako `dict[str, Any]` dostává `str` hodnotu. Přidat runtime type guard `if isinstance(study, str): study = {"studyId": study}` nebo opravit typovou anotaci dle skutečného API response formátu.

- [x] T003 [P] [US4] Opravit 3 mypy chyby v `src/czechmedmcp/variants/cbioportal_mutations.py` (řádky 257, 261, 262) — `_resolve_cancer_type()` dostává `str` místo `dict`. Přidat type guard nebo opravit caller aby předával správný typ.

- [x] T004 [US4] Opravit 5 mypy chyb v `src/czechmedmcp/router.py` (řádky 866, 875, 884, 893, 902) — FDA domain bloky přiřazují `str` do `dict[str, Any]` proměnné. Tyto chyby jsou pravděpodobně ve `fetch()` function v FDA case blocích. Opravit typové anotace nebo přidat správnou konverzi.

- [x] T005 Ověřit nulový počet mypy chyb: `uv run mypy` — musí hlásit `Found 0 errors`

- [x] T006 Ověřit, že test suite stále prochází po mypy opravách: `uv run python -m pytest -x --ff -n auto --dist loadscope -m "not integration"`

**Checkpoint**: `uv run mypy` → 0 chyb, 713+ testů stále prochází.

---

## Phase 3: US3 — Branch merge a cleanup

**Purpose**: Mergovat hotové feature branches do `python-main`, vyčistit working tree.

**Goal**: `python-main` obsahuje všechny hotové změny, žádné orphaned branche.

**Independent Test**: `git log python-main --oneline -5` ukazuje DrugIndex commit.

- [x] T007 [US3] Mergovat branch `001-fix-sukl-search` do `python-main` — `git checkout python-main && git merge 001-fix-sukl-search --no-ff -m "Merge 001-fix-sukl-search: DrugIndex for SUKL search"`

- [x] T008 [US3] Ověřit test suite po merge: `uv run python -m pytest -x --ff -n auto --dist loadscope -m "not integration"` — 713+ testů

- [x] T009 [US3] Vyhodnotit stash `stash@{0}` (WIP: docs restructure) — rozhodnout co ponechat (README.md, pyproject.toml změny) a co zahodit (smazané docs soubory z neexistujícího `apps/docs/`)

- [x] T010 [US3] Rebase `002-codebase-stabilization` na aktuální `python-main`: `git checkout 002-codebase-stabilization && git rebase python-main`

**Checkpoint**: `python-main` obsahuje DrugIndex commit, branch `002-codebase-stabilization` je rebasovaný.

---

## Phase 4: US1 — Dokumentace a CLAUDE.md

**Purpose**: Projektová dokumentace přesně odráží skutečnou strukturu.

**Goal**: Nový vývojář se může zorientovat bez zmatků.

**Independent Test**: Všechny cesty a příkazy zmíněné v CLAUDE.md existují a fungují.

- [x] T011 [P] [US1] Aktualizovat CLAUDE.md — Monorepo sekce:
  - Odstranit Turborepo tabulku s `apps/web/` a `apps/docs/`
  - Popsat skutečnou strukturu: root Next.js landing page (`app/`, `components/`), Python MCP server (`src/czechmedmcp/`)
  - Aktualizovat příkazy: `npm run dev` (landing page), `uv run czechmedmcp run` (server)
  - Odstranit `npx turbo dev`, `npm run dev:web`, `npm run dev:docs`

- [x] T012 [P] [US1] Aktualizovat CLAUDE.md — CI sekce:
  - Přidat sekci popisující existující `.github/workflows/ci.yml`
  - Dokumentovat dostupné CI joby (quality, tests, build-package, test-mcp, integration-tests)

- [x] T013 [US1] Aktualizovat README.md — odstranit odkaz na `docs-sovadina.vercel.app` pokud docs web nefunguje, ponechat pouze funkční odkazy

**Checkpoint**: `grep -r "apps/web\|apps/docs\|turbo" CLAUDE.md` vrací 0 výsledků.

---

## Phase 5: US2 — CI Pipeline

**Purpose**: CI automaticky ověřuje kvalitu kódu na každém push/PR.

**Goal**: Push na `python-main` spustí CI pipeline, která projde zeleně.

**Independent Test**: `gh workflow run ci.yml` spustí pipeline, všechny joby zelené.

- [x] T014 [US2] Aktualizovat `.github/workflows/ci.yml`:
  - Branch trigger: `main` → `python-main` (push i PR)
  - Ponechat `develop` pokud existuje
  - Odstranit nebo opravit `check-docs` job — `uv run mkdocs build -s` selhává protože mkdocs docs neexistují. Buď job smazat, nebo přepnout na validaci, která odpovídá aktuálnímu stavu.

- [x] T015 [US2] Ověřit, že CI workflow projde lokálně — spustit stejné příkazy jako CI:
  - `uv run ruff check src tests`
  - `uv run mypy`
  - `uv run python -m pytest tests -m "not integration" -x`
  - `make check` (pokud Makefile existuje)

**Checkpoint**: Všechny CI příkazy projdou lokálně, workflow míří na `python-main`.

---

## Phase 6: US5 — Stav dokumentace

**Purpose**: Docs web je v konzistentním stavu.

**Goal**: Buď funkční docs web, nebo čistě odstraněný bez orphaned souborů.

- [x] T016 [US5] Vyhodnotit stav docs — zjistit zda `docs-sovadina.vercel.app` je funkční a co servíruje. Pokud nefunguje, odstranit deploy-docs.yml workflow a všechny reference.

- [x] T017 [US5] Vyčistit orphaned docs soubory — stash `stash@{0}` obsahuje 40+ smazaných souborů z `apps/docs/`. Pokud `apps/docs/` na branch neexistuje, tyto deletes jsou irelevantní a stash lze dropnout (docs část).

**Checkpoint**: Žádné reference na nefunkční docs URL, žádné orphaned soubory.

---

## Phase 7: US4 — Router refaktoring (fáze 1)

**Purpose**: Snížit velikost `router.py` extrakcí `fetch()` handlerů.

**Goal**: `router.py` pod 1 000 řádků, zachovaná zpětná kompatibilita.

**Independent Test**: Všechny testy v `tests/tdd/test_router.py` prochází beze změn.

- [x] T018 [P] [US4] Vytvořit `src/czechmedmcp/fetch_handlers.py` — extrahovat FDA domain handlery (6 bloků, řádky 865–930):
  - `handle_fda_adverse_fetch(id)`
  - `handle_fda_label_fetch(id)`
  - `handle_fda_device_fetch(id)`
  - `handle_fda_approval_fetch(id)`
  - `handle_fda_recall_fetch(id)`
  - `handle_fda_shortage_fetch(id)`
  - Každý handler vrací stejný typ jako aktuální inline kód

- [x] T019 [P] [US4] Extrahovat NCI fetch handlery do `src/czechmedmcp/fetch_handlers.py`:
  - `handle_nci_organization_fetch(id)`
  - `handle_nci_intervention_fetch(id)`
  - `handle_nci_disease_fetch(id)`

- [x] T020 [P] [US4] Extrahovat české fetch handlery do `src/czechmedmcp/fetch_handlers.py`:
  - `handle_sukl_drug_fetch(id)`
  - `handle_mkn_diagnosis_fetch(id)`
  - `handle_nrpzs_provider_fetch(id)`
  - `handle_szv_procedure_fetch(id)`
  - `handle_vzp_reimbursement_fetch(id)`

- [x] T021 [US4] Extrahovat core domain fetch handlery (article, trial, variant, gene, drug, disease) do `src/czechmedmcp/fetch_handlers.py` — tyto jsou nejdelší a mají nejvíce logiky

- [x] T022 [US4] Refaktorovat `fetch()` v `src/czechmedmcp/router.py` — nahradit inline domain bloky dispatch table voláním handlerů z `fetch_handlers.py`:
  ```python
  FETCH_HANDLERS = {
      "article": handle_article_fetch,
      "trial": handle_trial_fetch,
      ...
  }
  handler = FETCH_HANDLERS.get(domain)
  if handler:
      return await handler(id, ...)
  ```

- [x] T023 [US4] Ověřit, že `router.py` je pod 1 000 řádků: `wc -l src/czechmedmcp/router.py`

- [x] T024 [US4] Ověřit plnou zpětnou kompatibilitu — spustit celou test suite: `uv run python -m pytest -x --ff -n auto --dist loadscope -m "not integration"` — 713+ testů

**Checkpoint**: `wc -l src/czechmedmcp/router.py` < 1000, všechny testy zelené.

---

## Phase 8: Polish & Cross-Cutting

**Purpose**: Vyčistit zbývající lint warningy, finální verifikace.

- [x] T025 Opravit ruff C901 warning v `src/czechmedmcp/czech/mkn/parser.py:74` (`_parse_csv` complexity 14 > 10) — extrahovat pomocné funkce nebo přidat `# noqa: C901` s komentářem proč je komplexita akceptovatelná (CSV parser s mnoha sloupci)

- [x] T026 Finální verifikace — spustit kompletní quality check:
  - `uv run ruff check src tests` → 0 errors
  - `uv run mypy` → 0 errors
  - `uv run python -m pytest -x --ff -n auto --dist loadscope -m "not integration"` → 713+ passed
  - `wc -l src/czechmedmcp/router.py` → < 1000

- [x] T027 Aktualizovat CLAUDE.md s finálním stavem — aktualizovat počet řádků router.py, přidat zmínku o `fetch_handlers.py`

---

## Dependencies

```
Phase 1 (Setup) → Phase 2 (Mypy fixes)
Phase 2 → Phase 3 (Branch merge) [merge needs clean mypy]
Phase 3 → Phase 4 (CLAUDE.md) [need merged state]
Phase 2 → Phase 5 (CI) [CI runs mypy]
Phase 3 → Phase 6 (Docs) [need clean working tree]
Phase 2 → Phase 7 (Router refactor) [mypy must pass first]
All phases → Phase 8 (Polish)
```

```
Phase 2 ──┬── Phase 3 ──┬── Phase 4 (CLAUDE.md)
          │             └── Phase 6 (Docs)
          ├── Phase 5 (CI)
          └── Phase 7 (Router refactor)
                              ↓
                        Phase 8 (Polish)
```

## Parallel Execution Opportunities

| Tasky | Důvod paralelizace |
|-------|-------------------|
| T002 + T003 | Různé soubory (cbioportal_search.py vs cbioportal_mutations.py) |
| T011 + T012 | Různé sekce CLAUDE.md — ale pozor na merge conflicts |
| T018 + T019 + T020 | Různé domain skupiny, všechny do fetch_handlers.py — vyžaduje koordinaci |
| Phase 5 + Phase 7 | CI setup a router refaktoring jsou nezávislé po Phase 2 |

## Implementation Strategy

1. **MVP**: Phase 1–3 (mypy opravy + branch merge) — okamžitý dopad na stabilitu
2. **Increment 2**: Phase 4–5 (CLAUDE.md + CI) — zlepšení DX
3. **Increment 3**: Phase 6–7 (docs + router refactor) — architektonické zlepšení
4. **Final**: Phase 8 (polish) — finální leštění
