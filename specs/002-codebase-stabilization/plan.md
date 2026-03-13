# Implementation Plan: Stabilizace a vyčištění codebase CzechMedMCP

**Branch**: `002-codebase-stabilization`
**Spec**: `spec.md`
**Tasks**: `tasks.md`
**Created**: 2026-03-13

## Technical Context

### Tech Stack
- **Backend**: Python 3.10+, FastMCP, httpx, Pydantic 2, diskcache
- **Frontend**: Next.js 15, React 19, Tailwind CSS (landing page only)
- **Build**: uv (Python), npm (Next.js)
- **Quality**: ruff (lint+format), mypy (types), pytest-xdist (tests), pre-commit
- **CI**: GitHub Actions (existující `ci.yml`)

### Aktuální stav kódu
- **163 Python souborů**, 35 845 řádků zdrojového kódu
- **129 testovacích souborů**, 25 528 řádků testů
- **713 passed, 1 failed** (known issue), **5 skipped**
- **10 mypy chyb** ve 3 souborech
- **1 ruff warning** (C901 complexity)

### Struktura projektu (skutečná)
```
biomcp/
├── src/biomcp/           # Python MCP server (60 nástrojů)
│   ├── router.py         # 2093 řádků — search() + fetch() god functions
│   ├── router_handlers.py # 408 řádků — extrahované search handlery
│   ├── individual_tools.py # 1951 řádků — 33 tool registrací
│   ├── czech/            # 23 českých nástrojů
│   └── variants/         # cBioPortal klienti (mypy chyby)
├── tests/                # 129 souborů
├── app/                  # Next.js landing page (root)
├── components/           # React komponenty landing page
├── .github/workflows/    # CI (ci.yml míří na main, ne python-main)
├── package.json          # Next.js config (NE monorepo)
├── pyproject.toml        # Python project config
├── Makefile              # make check, make test, make build
└── CLAUDE.md             # ⚠️ ZASTARALÝ — popisuje Turborepo monorepo
```

### Klíčové nesoulady s CLAUDE.md
| CLAUDE.md tvrdí | Realita |
|-----------------|---------|
| Turborepo monorepo s `apps/web/` a `apps/docs/` | Root Next.js app, žádný Turborepo |
| `npx turbo dev` | `npm run dev` |
| `npm run dev:web` / `npm run dev:docs` | Neexistují |
| CI na `main` a `develop` | Potřeba `python-main` |
| mkdocs dokumentace | mkdocs docs neexistují |

## Research: Analýza mypy chyb

### Chyby v `cbioportal_search.py` (2 chyby)

**Řádky 155, 157**: Iterace přes `cancer_types` API response. API vrací `list[dict] | str` (str při chybě). Mypy inferuje typ z `cancer_types` jako `str | list[dict]`.

**Řešení**: Type guard `if isinstance(cancer_types, list)` před iterací. API může vrátit string error message.

### Chyby v `cbioportal_mutations.py` (3 chyby)

**Řádky 257, 261, 262**: `studies` proměnná je `list[dict] | list[str]` (API vrací oba formáty). `_resolve_cancer_type(s)` očekává `dict` ale dostává prvek z listu co může být `str`.

**Řešení**: Type guard `if isinstance(s, dict)` v generátoru. Pro `str` study vrátit `s` přímo jako studyId.

### Chyby v `router.py` search() (5 chyb)

**Řádky 866, 875, 884, 893, 902**: V `search()` funkci, české domény přiřazují výsledek do `result` proměnné. Výše v funkci je `result` typován jako `dict[str, Any]` (z non-Czech domén). České search funkce vracejí `str`.

**Řešení**: Přejmenovat na jiný název proměnné (nepotřebný — výsledek jde rovnou do return) nebo přidat explicitní typovou anotaci. Nejjednodušší: české bloky už dávají `result` přímo do `return {"results": [{"content": result}]}` — stačí použít inline: `return {"results": [{"content": await _sukl_drug_search(...)}]}`.

## Implementační strategie

### Pořadí fází (oproti tasks.md — upřesněno)

```
1. T001: Baseline test verification
2. T002+T003+T004: Mypy fixes (paralelně per-file)
3. T005+T006: Verify mypy+tests
4. T007-T010: Branch merge 001-fix-sukl-search → python-main + rebase
5. T014: CI workflow update (python-main trigger, remove mkdocs)
6. T011-T013: CLAUDE.md + README update
7. T016-T017: Docs cleanup
8. T018-T022: Router fetch() refactoring
9. T025-T027: Polish
```

### Detailní řešení per-task

#### Phase 2: Mypy fixes

**T002** — `cbioportal_search.py:155,157`:
```python
# Before:
for ct in cancer_types:
    ct_id = ct.get("cancerTypeId")

# After:
if isinstance(cancer_types, list):
    for ct in cancer_types:
        ct_id = ct.get("cancerTypeId")
        if ct_id:
            _cancer_type_cache[ct_id] = ct
```

**T003** — `cbioportal_mutations.py:257,261,262`:
```python
# Before:
*(_resolve_cancer_type(s) for s in studies)
s["studyId"]: {"name": s.get("name", ""), ...}

# After:
*(_resolve_cancer_type(s) for s in studies if isinstance(s, dict))
s["studyId"]: {"name": s.get("name", ""), ...}
for s, ct in zip(studies, cancer_types, strict=False)
if isinstance(s, dict)
```

**T004** — `router.py:866,875,884,893,902`:
```python
# Before (Czech search domains):
result = await _sukl_drug_search(query_str, page, page_size)
return {"results": [{"content": result}]}

# After (inline, no intermediate variable):
return {"results": [{"content": await _sukl_drug_search(query_str, page, page_size)}]}
```
Nebo přidat explicitní `result: str = await ...` anotaci.

#### Phase 5: CI Update

**T014** — `.github/workflows/ci.yml`:
- `branches: [main, develop]` → `branches: [python-main]`
- `branches: [main]` (PR) → `branches: [python-main]`
- Smazat `check-docs` job (mkdocs neexistuje)
- Ponechat všechny ostatní joby beze změn

#### Phase 7: Router refactoring

**Dispatch table pattern** (kopíruje existující vzor z `router_handlers.py`):

```python
# fetch_handlers.py
async def handle_fda_adverse_fetch(id: str, api_key: str | None) -> dict:
    from biomcp.openfda import get_adverse_event
    result = await get_adverse_event(id, api_key=api_key)
    return {
        "title": f"FDA Adverse Event Report {id}",
        "text": result,
        "url": "",
        "metadata": {"report_id": id, "domain": "fda_adverse"},
    }
```

```python
# router.py — fetch() refactored
from .fetch_handlers import FETCH_HANDLERS

async def fetch(...) -> dict:
    # ... domain detection logic stays ...
    handler = FETCH_HANDLERS.get(domain)
    if handler:
        return await handler(id=id, detail=detail, api_key=api_key, call_benefit=call_benefit)
    raise InvalidDomainError(domain, VALID_DOMAINS)
```

**Odhad redukce**: fetch() z ~1 000 řádků na ~100 řádků (detection + dispatch). Celý `router.py` z 2 093 na ~900–1 000 řádků.

## Rizika a mitigace

| Riziko | Pravděpodobnost | Dopad | Mitigace |
|--------|----------------|-------|----------|
| Mypy fix změní runtime chování | Nízká | Vysoký | Type guards přidávají jen kontrolu, nemění logiku |
| Router refaktoring rozbije testy | Střední | Vysoký | Existující test suite (713 testů) zachytí regrese |
| Branch merge konflikty | Nízká | Střední | 001-fix-sukl-search modifikuje jiné soubory než 002 |
| CI workflow nefunguje na python-main | Nízká | Nízký | Lokální verifikace před pushem |

## Artefakty

| Artefakt | Cesta | Stav |
|----------|-------|------|
| Specifikace | `specs/002-codebase-stabilization/spec.md` | ✅ Hotovo |
| Task plán | `specs/002-codebase-stabilization/tasks.md` | ✅ Hotovo |
| Implementační plán | `specs/002-codebase-stabilization/plan.md` | ✅ Hotovo |
| Checklist | `specs/002-codebase-stabilization/checklists/requirements.md` | ✅ Hotovo |

## Další krok

Spustit implementaci podle `tasks.md` — začít Phase 1 (T001) a pokračovat sekvenčně.
