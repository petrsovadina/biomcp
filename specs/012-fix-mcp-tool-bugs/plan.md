# Implementation Plan: Oprava selhávajících MCP nástrojů (46% → 80%+)

**Branch**: `012-fix-mcp-tool-bugs` | **Date**: 2026-03-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/012-fix-mcp-tool-bugs/spec.md`

## Summary

Oprava 18 bugů (BUG-001 až BUG-018) identifikovaných v test reportu z 26. 3. 2026. Cíl: zvýšit success rate z 46% na 75%+. Hlavní root causes: timeout při lazy-load dat (NRPZS CSV, SZV Excel, SUKL DrugIndex), chybějící retry/graceful degradation u PubTator3, null PIL/SmPC URLs v SUKL DLP API, prázdná VZP reimbursement data. Přístup: debug a opravit existující implementace, ne přepisovat.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastMCP, httpx, Pydantic v2, diskcache, openpyxl, FAISS/sqlite-vec, cohere
**Storage**: diskcache/SQLite (HTTP cache), in-memory LRU (MKN-10, SZV), in-memory DrugIndex (SUKL)
**Testing**: pytest s `asyncio_mode = "auto"`, pytest-xdist pro paralelizaci
**Target Platform**: Linux server (Railway), macOS (lokální vývoj)
**Project Type**: MCP server (library + CLI)
**Performance Goals**: Každý nástroj musí odpovědět do 30s (CZECH_HTTP_TIMEOUT), SearchMedicine < 60s (cold start)
**Constraints**: 60 registrovaných nástrojů, žádná regrese existujících testů
**Scale/Scope**: 18 bugů, ~25 souborů k úpravě, 3 delivery fáze

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. MCP Protocol First | PASS | Opravujeme existující MCP nástroje, nepřidáváme nové |
| II. Modular Domain Architecture | PASS | Opravy v rámci existujících modulů, žádné cross-domain importy |
| III. Authoritative Data Sources | PASS | Všechny datové zdroje jsou autoritativní (SUKL, ÚZIS, PubMed, OpenFDA) |
| IV. CLI & MCP Dual Access | PASS | Opravy se projeví v obou přístupech (sdílená implementace) |
| V. Testing Rigor | PASS | Unit testy s mocked HTTP, integration testy s `@pytest.mark.integration` |
| Technical Constraints | PASS | Python 3.10+, httpx, ruff, mypy, ensure_ascii=False |
| Development Workflow | PASS | Feature branch, conventional commits, speckit-driven |

**Gate result: ALL PASS** — žádné violations.

## Project Structure

### Documentation (this feature)

```text
specs/012-fix-mcp-tool-bugs/
├── plan.md              # This file
├── research.md          # Phase 0: Root cause analysis per bug
├── data-model.md        # Phase 1: N/A (no new data models)
├── quickstart.md        # Phase 1: How to verify fixes
├── contracts/           # Phase 1: N/A (no new API contracts)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/czechmedmcp/
├── czech/
│   ├── sukl/
│   │   ├── drug_index.py      # BUG-001: SearchMedicine timeout/index build
│   │   ├── getter.py          # BUG-004: PIL/SmPC document URLs
│   │   ├── client.py          # BUG-007: SUKL code normalization
│   │   ├── search.py          # BUG-001: search_medicine entry point
│   │   └── reimbursement.py   # BUG-010: Reimbursement empty data
│   ├── nrpzs/
│   │   └── search.py          # BUG-002: CSV download timeout/parsing
│   ├── szv/
│   │   ├── search.py          # BUG-003: Excel download timeout/parsing
│   │   └── reimbursement.py   # BUG-003: CalculateReimbursement
│   ├── vzp/
│   │   └── drug_reimbursement.py  # BUG-010: VZP data source
│   ├── mkn/                   # BUG-008, BUG-009, BUG-014: MKN-10 fixes
│   ├── czech_tools.py         # BUG-005: DrugProfile, CompareAlternatives
│   └── diacritics.py          # Shared normalization utility
├── articles/
│   ├── search.py              # BUG-006: PubTator3 search
│   └── autocomplete.py        # BUG-006: Entity resolution
├── drugs/                     # BUG-017: DrugGetter MyChem.info
├── genes/                     # BUG-018: GeneGetter verbosity
├── openfda/
│   └── recall.py              # BUG-011: OpenFDA recall search
├── individual_tools.py        # BUG-013, BUG-016, BUG-017: Tool wrappers
├── metrics_handler.py         # BUG-015: GetPerformanceMetrics
├── constants.py               # Timeout constants
└── exceptions.py              # Error format standardization

tests/
├── tdd/                       # Unit tests with mocked HTTP
│   ├── test_sukl_search.py
│   ├── test_nrpzs.py
│   ├── test_szv.py
│   ├── test_article_search.py
│   └── test_mcp_integration.py  # Regression: 60 tools
├── czech/                     # Czech module tests
└── integration/               # Live API tests
```

**Structure Decision**: Existující struktura — žádné nové soubory mimo testy. Všechny opravy v existujících modulech.

## Complexity Tracking

> Žádné constitution violations — tabulka prázdná.

---

## Phase 0: Research — Root Cause Analysis

### R-001: SearchMedicine (BUG-001) — DrugIndex cold start failure

**Root cause**: `DrugIndex._ensure_built()` stahuje ~68K SUKL kódů, pak pro každý fetchuje detail (semaphore=20). Celý proces trvá ~10 min. Při prvním dotazu přes MCP klienta pravděpodobně nastane timeout na klientské straně, nebo chyba při bulk fetchi (jedno selhání → celý index selže).

**Decision**: Implementovat persistent disk cache pro DrugIndex. Po prvním úspěšném buildu uložit index do diskcache. Následné dotazy načtou index z disku (~1s) místo rebuildu (~10 min). Přidat graceful partial build — index se vytvoří i z částečných dat.

**Alternatives considered**:
- Přepis na server-side search API — SUKL DLP nemá search endpoint
- Předgenerovaný index v repu — příliš velký (~14MB), rychle zastarává

### R-002: NRPZS (BUG-002) — CSV download failure

**Root cause**: `_download_csv()` stahuje velký CSV z `datanzis.uzis.gov.cz` s 30s timeoutem. CSV soubor je ~50MB+. Buď timeout, nebo ÚZIS server neodpovídá.

**Decision**: Zvýšit timeout pro NRPZS CSV download na 120s. Přidat retry logiku (3 pokusy s exponential backoff). Přidat validaci CSV headers po stažení. Pokud download selže, vrátit informativní chybu místo generic server error.

**Alternatives considered**:
- Statický CSV v repu — zastarává, velký
- Periodický background refresh — overhead pro MCP server

### R-003: SZV (BUG-003) — Excel download failure

**Root cause**: `_download_excel()` stahuje Excel z `szv.mzcr.cz/Vykon/Export/` s 30s timeoutem. Openpyxl parsing může selhat na neočekávaném formátu sheetu.

**Decision**: Zvýšit timeout na 120s. Přidat retry logiku. Validovat sheet name a strukturu. Graceful error handling.

### R-004: PIL/SmPC (BUG-004) — Document metadata missing

**Root cause**: `getter.py` volá SUKL DLP API `/dlp/api/v1/dokumenty-metadata/{code}?typ=pil|spc`. API vrací prázdný seznam (404 nebo no docs) → `pil_url = None`. Některé léky nemají dokumenty v DLP API, ale mají je na webu SUKL.

**Decision**: Rozšířit implementaci o alternativní zdroj: konstruovat URL pattern pro SUKL web (`https://www.sukl.cz/modules/medication/detail.php?code={code}`) a ověřit HTTP HEAD requestem. Pokud DLP API vrátí null, zkusit konstruovanou URL.

### R-005: Reimbursement (BUG-010) — VZP data source

**Root cause**: `reimbursement.py` volá `https://opendata.sukl.cz/api/v1/uhrada/{code}`. API může být mimo provoz nebo vrací prázdná data. VZP static CSV fallback existuje ale může být zastaralý.

**Decision**: Debug opendata.sukl.cz endpoint. Aktualizovat VZP static CSV data. Přidat retry logiku.

### R-006: ArticleSearcher (BUG-006) — PubTator3 failure

**Root cause**: `search_articles()` volá PubTator3 search endpoint. Předtím provádí entity autocomplete pro geny/diseases/chemicals. Selhání autocomplete → selhání celého search. Chybí graceful degradation.

**Decision**: Přidat fallback: pokud PubTator3 autocomplete selže, použít raw query parametry přímo v PubMed E-utilities API. Přidat retry logiku pro PubTator3. Zvýšit timeout.

### R-007: DrugProfile/CompareAlternatives (BUG-005) — Cascading failures

**Root cause**: Agregátorové nástroje v `czech/workflows/drug_profile.py` závisejí na SearchMedicine (pro name→code resolution) a Reimbursement. Pokud SearchMedicine selže, celý DrugProfile selže.

**Decision**: Opravit SearchMedicine (R-001) a Reimbursement (R-005) nejdřív. DrugProfile/CompareAlternatives se opraví automaticky díky opravám pod-závislostí. Přidat error isolation v asyncio.gather (return_exceptions=True).

### R-008: SUKL code normalization (BUG-007)

**Decision**: Přidat `sukl_code = sukl_code.strip().zfill(7)` do `client.py` centrální funkce, která se volá ze všech SUKL nástrojů.

### R-009: DiagnosisStats (BUG-008) — NZIP endpoint

**Root cause**: Pravděpodobně nefunkční NZIP endpoint. `GetDiagnosisStats` volá API, které vrací null data.

**Decision**: Ověřit NZIP API endpoint. Pokud nefunkční, implementovat fallback na ÚZIS otevřená data nebo statická data.

### R-010: DiagnosisAssist (BUG-009) — Empty candidates

**Root cause**: FAISS/sqlite-vec embedding index nemusí být inicializovaný, nebo embedding model (cohere) selhává.

**Decision**: Debug embedding pipeline. Ověřit inicializaci FAISS indexu a Cohere API key. Přidat fallback na keyword-based matching pokud embeddings selžou.

### R-011: OpenFDA Recall (BUG-011)

**Decision**: Debug OpenFDA recall endpoint query construction. Pravděpodobně chyba v query parametrech (field names).

### R-012: Substance names (BUG-012)

**Decision**: Přidat resolver substance_code → substance_name do `getter.py`. SUKL DLP API má endpoint pro účinné látky.

### R-013: Error format standardization (BUG-013)

**Decision**: Vytvořit utility funkci `format_error(tool_name, message, code)` v `exceptions.py`. Nahradit ad-hoc error formáty v jednotlivých nástrojích.

### R-014-018: P3 bugs

- **BUG-014 SearchDiagnosis text**: Debug normalize_query() a MKN-10 fulltext search
- **BUG-015 GetPerformanceMetrics**: Ověřit `@track_performance` dekorátor
- **BUG-016 ArticleGetter abstract**: Debug PubMed abstract fetch
- **BUG-017 DrugGetter metformin**: Debug MyChem.info query normalization
- **BUG-018 GeneGetter verbosity**: Přidat field filtering pro RefSeq

---

## Phase 1: Implementation Design

### Fáze P1 — Kritické opravy (commit 1)

**1.1 SearchMedicine fix** (BUG-001, BUG-005)
- File: `src/czechmedmcp/czech/sukl/drug_index.py`
- Změna: Persistent cache pro DrugIndex → `diskcache` pro serializovaný index
- Změna: Partial build tolerance — index se vytvoří i z 50%+ úspěšných fetchů
- Změna: Timeout zvýšení pro bulk operations
- Test: `tests/tdd/test_sukl_search.py` — mock DrugIndex build, verify partial results

**1.2 NRPZS fix** (BUG-002)
- File: `src/czechmedmcp/czech/nrpzs/search.py`
- Změna: Timeout 30s → 120s pro CSV download
- Změna: 3x retry s exponential backoff
- Změna: CSV header validation
- Změna: Informativní error messages místo generic server error
- Test: `tests/czech/test_nrpzs.py` — mock CSV responses

**1.3 SZV fix** (BUG-003)
- File: `src/czechmedmcp/czech/szv/search.py`
- Změna: Timeout 30s → 120s pro Excel download
- Změna: 3x retry s exponential backoff
- Změna: Sheet validation
- Test: `tests/czech/test_szv.py` — mock Excel responses

**1.4 PIL/SmPC fix** (BUG-004)
- File: `src/czechmedmcp/czech/sukl/getter.py`
- Změna: Fallback URL construction pro chybějící DLP metadata
- Změna: HTTP HEAD check na konstruovanou URL
- Test: `tests/tdd/test_sukl_getter.py`

**1.5 ArticleSearcher fix** (BUG-006)
- File: `src/czechmedmcp/articles/search.py`, `autocomplete.py`
- Změna: Graceful degradation — pokud autocomplete selže, použít raw query
- Změna: Retry logika pro PubTator3
- Změna: Fallback na PubMed E-utilities
- Test: `tests/tdd/test_article_search.py`

### Fáze P2 — Středně závažné opravy (commit 2)

**2.1 SUKL code normalization** (BUG-007)
- File: `src/czechmedmcp/czech/sukl/client.py`
- Změna: `sukl_code.strip().zfill(7)` v centrální funkci
- Test: Parametrized test s 5, 6, 7 místnými kódy

**2.2 DiagnosisStats fix** (BUG-008)
- File: `src/czechmedmcp/czech/mkn/` — epidemiologický modul
- Změna: Debug NZIP endpoint, opravit data mapping
- Test: Mock NZIP response s nenulovými daty

**2.3 DiagnosisAssist fix** (BUG-009)
- File: `src/czechmedmcp/czech/mkn/` — embedding pipeline
- Změna: Debug FAISS initialization, přidat keyword fallback
- Test: Mock embedding responses

**2.4 Reimbursement fix** (BUG-010)
- File: `src/czechmedmcp/czech/sukl/reimbursement.py`, `czech/vzp/`
- Změna: Debug opendata.sukl.cz, aktualizovat VZP CSV, retry logika
- Test: Mock reimbursement responses

**2.5 OpenFDA Recall fix** (BUG-011)
- File: `src/czechmedmcp/openfda/recall.py`
- Změna: Debug query construction
- Test: Mock OpenFDA responses

**2.6 Substance names** (BUG-012)
- File: `src/czechmedmcp/czech/sukl/getter.py`
- Změna: Resolver substance_code → human-readable name
- Test: Mock substance resolver

**2.7 Error format standardization** (BUG-013)
- File: `src/czechmedmcp/exceptions.py`, all tool files
- Změna: Centrální `format_tool_error()` utility
- Test: Verify consistent error format across tools

### Fáze P3 — Nízká priorita (commit 3)

**3.1** SearchDiagnosis text search (BUG-014)
**3.2** GetPerformanceMetrics (BUG-015)
**3.3** ArticleGetter abstract placeholder (BUG-016)
**3.4** DrugGetter metformin (BUG-017)
**3.5** GeneGetter verbosity (BUG-018)

---

## Quickstart: How to Verify Fixes

Po každé fázi spustit:

```bash
# Unit testy (musí PASS)
uv run python -m pytest -x --ff -n auto --dist loadscope -m "not integration"

# Regresní test 60 nástrojů
uv run python -m pytest tests/tdd/test_mcp_integration.py -v

# Ruční ověření opravených nástrojů (live API)
uv run python -m pytest -m "integration" -k "sukl or nrpzs or szv or article" --timeout 120
```
