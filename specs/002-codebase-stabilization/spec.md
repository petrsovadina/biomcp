# Specifikace: Stabilizace a vyčištění codebase CzechMedMCP

**Stav**: Draft
**Vytvořeno**: 2026-03-13
**Branch**: `002-codebase-stabilization`

## Shrnutí

Systematické vyčištění technického dluhu, oprava typových chyb, aktualizace projektové dokumentace a zavedení CI/CD pipeline. Cílem je přivést projekt do stabilního, udržovatelného stavu před dalším feature vývojem.

## Kontext a motivace

Projekt CzechMedMCP prošel intenzivním vývojem (60 nástrojů, 23 českých zdravotnických modulů, DrugIndex refaktoring). Během tohoto vývoje se nahromadil technický dluh:

- **10 mypy typových chyb** v produkčním kódu (potenciální runtime bugy)
- **CLAUDE.md popisuje neexistující Turborepo monorepo strukturu** — nesoulad s realitou
- **Necommitnutá migrace dokumentace** (57 souborů) bez jasného cíle
- **Žádná CI/CD pipeline** — kvalita se kontroluje pouze lokálně
- **2 093řádkový router.py** s god functions — největší architektonický dluh
- **Feature branch `001-fix-sukl-search`** čeká na merge do `python-main`

## Uživatelské scénáře

### US1: Vývojář přispívající do projektu
Jako vývojář chci, aby projektová dokumentace (CLAUDE.md, README) přesně odrážela skutečnou strukturu projektu, abych se mohl rychle zorientovat a přispívat bez zmatků.

### US2: Vývojář odesílající pull request
Jako vývojář chci, aby CI pipeline automaticky ověřila testy, lint a typovou kontrolu, abych dostal okamžitou zpětnou vazbu o kvalitě kódu.

### US3: Maintainer mergující změny
Jako maintainer chci, aby `python-main` branch obsahoval všechny hotové feature branche a neexistovaly orphaned změny v working tree, abych měl jasný přehled o stavu projektu.

### US4: Vývojář pracující s cBioPortal/router kódem
Jako vývojář chci, aby typová kontrola mypy procházela bez chyb, abych měl jistotu, že kód správně zpracovává API odpovědi a nedochází k runtime chybám.

### US5: Uživatel dokumentace
Jako uživatel chci, aby dokumentační web byl v konzistentním a funkčním stavu — buď plně deploynutý, nebo jasně označený jako WIP.

## Funkční požadavky

### FR1: Oprava typových chyb (mypy)
- Opravit všech 10 mypy chyb ve 3 souborech (`router.py`, `cbioportal_search.py`, `cbioportal_mutations.py`)
- Opravy nesmí měnit chování — pouze typovou správnost
- Po opravě musí `uv run mypy` procházet s 0 chybami

### FR2: Aktualizace CLAUDE.md
- CLAUDE.md musí přesně popisovat aktuální strukturu projektu
- Odstranit reference na Turborepo, `apps/web/`, `apps/docs/`, workspaces
- Dokumentovat skutečnou strukturu: root Next.js landing page + Python MCP server v `src/`
- Aktualizovat příkazy pro spuštění odpovídající realitě

### FR3: Vyřešení stavu dokumentace
- Rozhodnout o stavu docs: buď dokončit migraci, nebo revertovat na funkční stav
- Zajistit konzistenci mezi README odkazy a skutečným deploymentem
- Uncommitnuté doc changes (57 souborů) musí být buď commitnuty, nebo revertovány

### FR4: Zavedení GitHub Actions CI
- Vytvořit workflow pro push/PR na `python-main`
- CI musí spouštět: pytest (unit testy), ruff check, mypy
- CI musí běžet na Python 3.10, 3.11, 3.12
- Failure v kterémkoli kroku blokuje merge

### FR5: Merge hotových feature branches
- `001-fix-sukl-search` mergovat do `python-main` (DrugIndex je hotový, testy prochází)
- Zajistit, že po merge všechny testy stále prochází

### FR6: Refaktoring router.py (fáze 1)
- Extrahovat `fetch()` god function (926 řádků) do dispatch table vzoru
- Podobně jako existující `router_handlers.py` pro `search()`
- Cíl: `router.py` pod 1 000 řádků, každý handler v samostatné funkci
- Zachovat 100% zpětnou kompatibilitu — žádné změny v API/tooling

### FR7: Oprava ruff lint warning
- Vyřešit zbývající C901 complexity warning v `mkn/parser.py`
- Buď zjednodušit funkci, nebo explicitně potlačit s odůvodněním

## Úspěšnostní kritéria

| Kritérium | Měřítko |
|-----------|---------|
| Typová bezpečnost | 0 mypy chyb na celém projektu |
| Testovací pokrytí | 713+ testů prochází, 0 nových selhání |
| Kvalita kódu | 0 ruff chyb/warningů |
| CI spolehlivost | CI pipeline úspěšně proběhne na 3 verzích Pythonu |
| Dokumentační přesnost | CLAUDE.md popisuje skutečný stav, žádné reference na neexistující adresáře |
| Kódová čistota | `router.py` pod 1 000 řádků |
| Branch hygiena | 0 orphaned feature branches s hotovou prací |

## Předpoklady

- Stávající `test_pydantic_ai_integration.py` failure je known issue a nebude opravován v rámci této specifikace
- Refaktoring `router.py` se omezí na extrakci `fetch()` handlerů — `search()` handlery již existují v `router_handlers.py`
- Docs web (`docs-sovadina.vercel.app`) bude dočasně odstraněn z README pokud nebude funkční
- CI workflow bude využívat `uv` pro reprodukovatelné buildy

## Scope

### V rozsahu
- Mypy opravy, CLAUDE.md update, CI setup, branch merge, router refaktoring fáze 1, ruff fix, docs rozhodnutí

### Mimo rozsah
- Nové features nebo nástroje
- Refaktoring `individual_tools.py` (1 951 řádků)
- Upgrade na upstream Rust verzi
- Performance optimalizace
- Refaktoring `search()` v router.py (již částečně hotový v `router_handlers.py`)
