# Implementation Plan: CzechMedMCP

**Branch**: `001-czechmedmcp-implementation` | **Date**: 2026-03-02 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-czechmedmcp-implementation/spec.md`

## Summary

Rozšíření BioMCP forku o 9 nových českých zdravotnických nástrojů (batch availability, reimbursement, pharmacy search, diagnosis stats, codebooks, SZV calculation, 3 workflow orchestrace) a přejmenování 14 existujících nástrojů na prefix `czechmed_`. Výsledek: 60 MCP nástrojů (37 BioMCP + 23 Czech) s dual output (Markdown + JSON structuredContent).

Technický přístup: aditivní rozšíření stávající `src/biomcp/czech/` struktury, sdílený `httpx.AsyncClient` + `diskcache` pattern, `asyncio.gather` pro workflow orchestrace s graceful degradation.

## Technical Context

**Language/Version**: Python 3.10+ (pyproject.toml: `>=3.10,<4.0`)
**Primary Dependencies**: `mcp[cli]>=1.12.3,<2.0.0`, `httpx>=0.28.1`, `pydantic>=2.10.6`, `diskcache>=5.6.3`, `lxml>=5.0.0`, `openpyxl>=3.1.0`
**Storage**: diskcache/SQLite (`~/.cache/biomcp/http_cache`) pro HTTP cache; in-memory LRU pro MKN-10 (~20 MB) a SZV (~5 MB)
**Testing**: pytest + pytest-xdist (parallel), pytest-asyncio (auto mode), pytest-bdd; `asyncio_mode = "auto"`
**Target Platform**: Linux/macOS server (MCP server), stdio + Streamable HTTP + Docker
**Project Type**: MCP server (library + CLI)
**Performance Goals**: SÚKL search <2s, MKN-10/SZV offline <100ms, batch 50 drugs <10s, workflow <10s, 50-100 req/s per instance
**Constraints**: ~50 MB RAM per instance, stateless, `ensure_ascii=False` pro českou diakritiku, line-length 79 (ruff)
**Scale/Scope**: 4000+ lékařů, 200 peak sessions, 3 instance minimum

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. MCP Protocol First** | PASS | Všech 23 nástrojů registrováno přes `@mcp_app.tool()` |
| **II. Modular Domain Architecture** | PASS | Czech moduly pod `src/biomcp/czech/`, registrace v `czech_tools.py`, žádné cross-module importy |
| **III. Authoritative Data Sources** | PASS | SÚKL, MKN-10/ÚZIS, NRPZS, SZV/MZ ČR, VZP — všechny autoritativní české zdroje |
| **IV. CLI & MCP Dual Access** | DEFERRED | Nové nástroje dostanou CLI v budoucím PR; stávající CLI pattern zachován |
| **V. Testing Rigor** | PASS | Unit testy (mocked httpx) + integration testy (`@pytest.mark.integration`), `asyncio_mode = "auto"` |
| **TC: Python 3.10+** | PASS | Žádné 3.11+ features |
| **TC: httpx async** | PASS | Všechny Czech moduly používají `httpx.AsyncClient` |
| **TC: Pydantic v2** | PASS | Všechny modely `BaseModel` s `model_dump()` |
| **TC: ruff** | PASS | line-length 79, configured in pyproject.toml |
| **TC: ensure_ascii=False** | PASS | Všechny `json.dumps()` s `ensure_ascii=False` |
| **TC: MIT license** | PASS | Žádné nekompatibilní dependencies |

**Violation: CLI Dual Access (Principle IV)**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| CLI pro 9 nových nástrojů odloženo | Prioritou je MCP server; CLI mirror je follow-up | CLI pro 14 existujících nástrojů již funguje; nové CLI nemá blokující prioritu |

## Project Structure

### Documentation (this feature)

```text
specs/001-czechmedmcp-implementation/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 research findings
├── data-model.md        # Phase 1 entity definitions
├── quickstart.md        # Phase 1 dev quickstart
├── contracts/           # Phase 1 tool contracts
│   ├── sukl-tools.md
│   ├── mkn-tools.md
│   ├── nrpzs-tools.md
│   ├── szv-tools.md
│   ├── vzp-tools.md
│   └── workflow-tools.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

```text
src/biomcp/
├── constants.py                  # + nové URL konstanty, rate limity
├── czech/
│   ├── czech_tools.py            # 14→23 @mcp_app.tool() registrací (přejmenované)
│   ├── diacritics.py             # beze změny
│   ├── response.py               # NEW: format_czech_response() pro dual output
│   ├── sukl/
│   │   ├── search.py             # + _batch_availability(), _find_pharmacies()
│   │   ├── getter.py             # enhance PIL/SPC: section-based content
│   │   ├── reimbursement.py      # NEW: _get_reimbursement()
│   │   └── models.py             # + BatchAvailabilityResult, Pharmacy, Reimbursement
│   ├── mkn/
│   │   ├── search.py             # + trigram scoring
│   │   ├── stats.py              # NEW: _get_diagnosis_stats() z NZIP CSV
│   │   └── models.py             # + DiagnosisStats
│   ├── nrpzs/
│   │   ├── search.py             # fix pagination bug + _get_codebooks()
│   │   └── models.py             # + Codebook
│   ├── szv/
│   │   ├── search.py             # fix timeout
│   │   ├── reimbursement.py      # NEW: _calculate_reimbursement()
│   │   └── models.py             # + ReimbursementCalculation
│   ├── vzp/
│   │   ├── search.py             # repurpose: drug reimbursement + alternatives
│   │   └── models.py             # + DrugReimbursement, DrugAlternative
│   └── workflows/
│       ├── __init__.py            # NEW
│       ├── drug_profile.py        # NEW: _drug_profile()
│       ├── diagnosis_assistant.py # NEW: _diagnosis_assistant()
│       └── referral_assistant.py  # NEW: _referral_assistant()

tests/
├── tdd/
│   └── test_mcp_integration.py   # 51→60 tool count assertion
├── czech/
│   ├── test_tool_registration.py  # 14→23 tool count
│   ├── test_czech_response.py     # NEW: dual output tests
│   ├── test_sukl_batch.py         # NEW
│   ├── test_sukl_reimbursement.py # NEW
│   ├── test_sukl_pharmacies.py    # NEW
│   ├── test_mkn_stats.py          # NEW
│   ├── test_nrpzs_codebooks.py    # NEW
│   ├── test_szv_reimbursement.py  # NEW
│   ├── test_vzp_drug_reimb.py     # NEW
│   ├── test_workflow_drug.py      # NEW
│   ├── test_workflow_diagnosis.py # NEW
│   └── test_workflow_referral.py  # NEW
└── czech_integration/
    └── test_workflow_api.py       # NEW: E2E workflow tests
```

**Structure Decision**: Rozšíření stávající `src/biomcp/czech/` struktury (Option 1: Single project). Nový `workflows/` subdirectory pro orchestrační nástroje. Nový `response.py` pro sdílenou dual-output logiku.

## Implementation Phases

### Phase 1: Foundation & Cross-cutting (estimated: ~12h)

**Goal**: Infrastruktura pro všechny nové nástroje

1. **Rename all 14 existing tools** to `czechmed_*` prefix in `czech_tools.py`
2. **Update all tests** referencing old tool names
3. **Update tool count** in `test_mcp_integration.py` (51→51, count stays same during rename)
4. **Create `response.py`** with `format_czech_response(data, tool_name)` for dual output
5. **Add constants** for new API URLs, rate limits to `constants.py`
6. **Fix known bugs**: NRPZS pagination, SZV/VZP hardcoded timeouts

### Phase 2: SÚKL Extensions (estimated: ~16h)

**Goal**: 3 nové SÚKL nástroje (batch, reimbursement, pharmacy)

1. **`czechmed_batch_check_availability`** — `asyncio.gather` přes existing `_check_distribution()`
2. **`czechmed_get_reimbursement`** — SÚKL API endpoint pro úhradové informace
3. **`czechmed_find_pharmacies`** — SÚKL API pro lékárny
4. **Enhance PIL/SPC** — section-based text content scraping
5. **Unit tests** pro všechny 3 nové + enhanced PIL/SPC

### Phase 3: MKN-10 + NRPZS + SZV Extensions (estimated: ~16h)

**Goal**: 3 nové nástroje (stats, codebooks, reimbursement calculation)

1. **`czechmed_get_diagnosis_stats`** — NZIP open data CSV parsing
2. **`czechmed_get_codebooks`** — Extract unique NRPZS column values
3. **`czechmed_calculate_reimbursement`** — Point-to-CZK calculation with insurer rate table
4. **Improve MKN-10 search** — trigram scoring for fuzzy matching
5. **Unit tests** pro všechny 3 nové

### Phase 4: VZP Drug Reimbursement (estimated: ~12h)

**Goal**: 2 VZP drug nástroje (repurpose existing module)

1. **`czechmed_get_vzp_reimbursement`** — VZP drug price list scraping
2. **`czechmed_compare_alternatives`** — Cross-module SÚKL + VZP alternativy
3. **Unit tests** s mockovanými VZP HTML responses

### Phase 5: Workflow Orchestration (estimated: ~16h)

**Goal**: 3 workflow nástroje

1. **`czechmed_drug_profile`** — search → parallel (detail + availability + reimbursement + PubMed)
2. **`czechmed_diagnosis_assistant`** — search MKN-10 → details → PubMed evidence + disclaimer
3. **`czechmed_referral_assistant`** — diagnosis → specialty mapping → NRPZS provider search
4. **Graceful degradation** tests (partial source failure)
5. **Unit tests** pro všechny 3 workflow + degradation scenarios

### Phase 6: Integration & Finalization (estimated: ~8h)

**Goal**: E2E validace, dokumentace, regresní testy

1. **Update `test_mcp_integration.py`** — assert 60 tools
2. **Update `test_tool_registration.py`** — assert 23 Czech tools
3. **Integration tests** — live API tests pro nové nástroje
4. **Update `CLAUDE.md`** — nové nástroje, tool count 60
5. **Update `README.md`** — rozšířený tool list
6. **Update `THIRD_PARTY_ENDPOINTS.md`** — nové endpointy

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| CLI commands deferred (Principle IV) | 9 nových nástrojů bez CLI mirror | CLI pro stávajících 14 funguje; nové CLI v follow-up PR |
| `workflows/` subdirectory | Orchestrační logika potřebuje oddělení | Vložení do `czech_tools.py` by překročilo 500+ řádků |
| VZP module repurpose | Spec vyžaduje drug reimbursement, ne procedury | Přidání vedle existujících by zdvojilo modul scope |
