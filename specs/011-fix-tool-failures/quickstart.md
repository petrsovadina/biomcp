# Quickstart: 011-fix-tool-failures

## Prerekvizity

```bash
uv sync --all-extras
uv run pre-commit install
```

## Ověření aktuálního stavu

```bash
# Spustit existující testy — musí projít
uv run python -m pytest -x --ff -n auto --dist loadscope

# Ověřit počet nástrojů (60)
uv run python -m pytest tests/tdd/test_mcp_integration.py -v

# Lint + type check
uv run ruff check src tests
uv run mypy
```

## Pořadí implementace

1. **Fáze 1 — Kritické opravy (P0)**
   - ArticleGetter: PMC ID support + error handling
   - SZV: Debug Excel download + error handling
   - DiagnosisAssist: Embedding pipeline

2. **Fáze 2 — Vysoká priorita (P1)**
   - OpenFDA Recall: Debug query/Arcade wrapper
   - DrugsProfile: Graceful partial return
   - CompareAlternatives: VZP fallback
   - VariantSearcher: Gene-only validace
   - GetMedicineDetail: Substance names + SPC/PIL

3. **Fáze 3 — Datové zdroje (P1)**
   - VZP statický dataset
   - NZIP fallback/statický dataset

4. **Fáze 4 — Střední/nízká priorita (P2-P3)**
   - DeviceGetter MDR key
   - NRPZS multi-field lookup
   - GetPerformanceMetrics default
   - Arcade wrapper sync

## Testování po každé fázi

```bash
# Unit testy
uv run python -m pytest -x --ff -n auto -m "not integration"

# Regresní test 60 nástrojů
uv run python -m pytest tests/tdd/test_mcp_integration.py tests/tdd/test_arcade_integration.py -v

# Kvalita kódu
make check
```

## Nové závislosti (DiagnosisAssist)

```bash
# sqlite-vec pro vektorový index
uv add sqlite-vec

# NEBO faiss-cpu (alternativa)
uv add faiss-cpu
```

Embedding model: Potřebuje API klíč pro Cohere embed-multilingual-light-v3.0, NEBO lokální sentence-transformers model.
