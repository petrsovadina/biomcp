# Implementation Plan: Fix Tool Failures

**Branch**: `011-fix-tool-failures` | **Date**: 2026-03-24 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/011-fix-tool-failures/spec.md`

## Summary

Oprava 8 FAILujících a 7 PARTIAL MCP nástrojů identifikovaných v testovací zprávě v2. Cíl: zvýšit PASS rate z 62% na 85%+. Zahrnuje opravy ArticleGetter (regrese), SZV bloku, DiagnosisAssist (nový embedding pipeline), OpenFDA Recall, DrugsProfile/CompareAlternatives (graceful partial return), VariantSearcher (input validace), GetMedicineDetail (substance names, SPC/PIL URL), VZP/NZIP (statický dataset fallback), DeviceGetter (MDR key formát), NRPZS a performance metriky. Arcade wrappery synchronizovány.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: FastMCP, httpx, Pydantic v2, diskcache, openpyxl, FAISS/sqlite-vec, cohere (embed-multilingual-light-v3.0)
**Storage**: diskcache/SQLite (HTTP cache), in-memory LRU (MKN-10, SZV), FAISS/SQLite-vec (DiagnosisAssist embeddings)
**Testing**: pytest, pytest-xdist, pytest-bdd; asyncio_mode=auto
**Target Platform**: Linux server (Railway), Arcade Cloud
**Project Type**: MCP server (library + CLI + HTTP service)
**Performance Goals**: Tool response <30s (CZECH_HTTP_TIMEOUT), DiagnosisAssist embedding search <500ms po cold start
**Constraints**: Line length 79 (ruff), mypy strict, 60 registrovaných nástrojů, 60 Arcade nástrojů
**Scale/Scope**: 60 MCP nástrojů, 1020+ testů, ~15 souborů k úpravě

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princip | Status | Poznámka |
| ------- | ------ | -------- |
| I. MCP Protocol First | PASS | Všechny opravy zůstávají jako MCP tools registrované přes @mcp_app.tool() |
| II. Modular Domain Architecture | PASS | Opravy v existujících doménových modulech, žádný cross-domain import |
| III. Authoritative Data Sources | PASS | Pouze autorizované zdroje (SÚKL, VZP, NZIP, OpenFDA, PubMed, MyVariant.info); nefunkční API → graceful degradation s dokumentací |
| IV. CLI & MCP Dual Access | PASS | CLI příkazy sdílejí implementace s MCP tools |
| V. Testing Rigor | PASS | Nové unit testy s mockovaným HTTP; integration testy s @pytest.mark.integration |
| Technical Constraints | PASS | Python 3.10+, httpx, Pydantic v2, ruff, mypy, ensure_ascii=False |
| Development Workflow | PASS | Feature branch 011-fix-tool-failures, speckit workflow, conventional commits |

## Project Structure

### Documentation (this feature)

```text
specs/011-fix-tool-failures/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (DiagnosisAssist embedding schema)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API behavior contracts)
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (via /speckit.tasks)
```

### Source Code (repository root)

```text
src/czechmedmcp/
├── articles/
│   └── fetch.py                    # FIX: ArticleGetter — PubTator3/Europe PMC fallback
├── variants/
│   └── search.py                   # FIX: VariantSearcher — gene-only validace
├── openfda/
│   ├── drug_recalls.py             # FIX: RecallSearcher — query builder
│   └── device_events.py            # FIX: DeviceGetter — MDR key formát
├── czech/
│   ├── workflows/
│   │   ├── drug_profile.py         # FIX: DrugsProfile — graceful partial return
│   │   └── diagnosis_assistant.py  # FIX: DiagnosisAssist — embedding pipeline
│   ├── sukl/
│   │   └── getter.py               # FIX: GetMedicineDetail — substance names, SPC/PIL URL
│   ├── vzp/
│   │   ├── drug_reimbursement.py   # FIX: GetDrugReimbursement/CompareAlternatives
│   │   └── data/                   # NEW: Statický VZP dataset (CSV)
│   ├── mkn/
│   │   ├── statistics.py           # FIX: GetDiagnosisStats — NZIP fallback
│   │   └── data/                   # NEW: Statický NZIP dataset (CSV)
│   ├── szv/
│   │   └── search.py               # FIX: SearchProcedures/GetProcedureDetail
│   ├── nrpzs/
│   │   └── search.py               # FIX: GetProviderDetail — IČO lookup
│   └── diagnosis_embed/            # NEW: Embedding index pro DiagnosisAssist
│       ├── __init__.py
│       ├── indexer.py              # MKN-10 → embedding index builder
│       └── searcher.py            # Symptom → MKN-10 hybrid search
├── metrics_handler.py              # FIX: @track_performance dekorátor aplikace
├── individual_tools.py             # Případné úpravy tool registrací
└── arcade/
    ├── individual_tools.py         # SYNC: Arcade wrappery
    └── czech_tools.py              # SYNC: Arcade české wrappery

tests/
├── tdd/
│   ├── test_article_getter.py      # NEW/FIX: ArticleGetter unit testy
│   ├── test_variant_search.py      # NEW: gene-only validace test
│   ├── test_recall.py              # NEW: RecallSearcher/Getter testy
│   ├── test_device.py              # NEW: DeviceGetter MDR key test
│   ├── test_drug_profile.py        # NEW: DrugsProfile partial return test
│   ├── test_diagnosis_assist.py    # NEW: DiagnosisAssist embedding testy
│   ├── test_medicine_detail.py     # NEW: substance names test
│   ├── test_szv.py                 # NEW: SZV search/detail testy
│   └── test_metrics.py             # NEW: Performance metrics test
└── czech/
    ├── test_vzp_reimbursement.py   # NEW: VZP statický dataset test
    ├── test_nzip_stats.py          # NEW: NZIP fallback test
    └── test_nrpzs.py              # NEW: NRPZS provider detail test
```

**Structure Decision**: Opravy v existujících souborech. Nový modul `czech/diagnosis_embed/` pro embedding pipeline. Nové `data/` adresáře pro statické VZP/NZIP datasety.

## Complexity Tracking

> Žádné porušení constitution — tracking nepotřebný.
