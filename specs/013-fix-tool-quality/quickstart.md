# Quickstart: Fix Tool Quality — Validation Scenarios

**Feature**: 013-fix-tool-quality
**Date**: 2026-03-28

## Pre-requisites

```bash
# Activate virtual environment
source .venv/bin/activate

# Ensure dependencies are installed
uv sync --all-extras
```

## Validation Scenarios

### Scenario 1: SUKL Timeout (US1)

**What to test**: All SUKL tools respond within 10-30s or return clear error.

```bash
# Run SUKL timeout unit tests
uv run python -m pytest tests/tdd/test_sukl_timeout.py -v

# Manual MCP test via inspector
make inspector
# Then call: czechmed_search_medicine("Metformin")
# Expected: response within 10s OR "SUKL index is building" message
# Then call: czechmed_compare_alternatives("0011114")
# Expected: response within 30s OR clear timeout error
```

**Pass criteria**: No call takes >30s. Error messages are user-friendly.

---

### Scenario 2: Search Wrapper (US2)

**What to test**: search() returns relevant results. No thinking-reminder.

```bash
# Run search router unit tests
uv run python -m pytest tests/tdd/test_router_fixes.py -v

# Manual MCP test via inspector
# Call: search(domain="trial", query="metformin type 2 diabetes")
# Expected: results contain "metformin" or "diabetes" in titles
# Expected: NO result with id="thinking-reminder"

# Call: search(domain="mkn_diagnosis", query="E11")
# Expected: E11 + subkategorie (E11.0-E11.9)
```

**Pass criteria**: Trial results are relevant. No thinking-reminder in results.

---

### Scenario 3: Diagnosis Assist (US3)

**What to test**: E11 in top-5 for diabetes symptoms.

```bash
# Run diagnosis quality tests
uv run python -m pytest tests/tdd/test_diagnosis_assist_quality.py -v

# Manual MCP test via inspector
# Call: czechmed_diagnosis_assist("zizen, caste moceni, unava, vysoky krevni cukr")
# Expected: E11 (Diabetes mellitus 2. typu) in top-5
# Expected: NO C84 (Lymphom) in top-10
```

**Pass criteria**: E11 appears in top-5. No irrelevant oncology codes.

---

### Scenario 4: Drug Name Lookup (US4)

**What to test**: drug_getter accepts common drug names.

```bash
# Run drug name resolution tests
uv run python -m pytest tests/tdd/test_drug_name_resolution.py -v

# Manual MCP test via inspector
# Call: drug_getter("metformin")
# Expected: full drug profile (DrugBank DB00331, ATC A10BA02)
# Call: drug_getter("DB00331")
# Expected: same result (backward compatibility)
```

**Pass criteria**: Both name and ID lookups return correct drug data.

---

### Scenario 5: Article Search + Preprints (US5)

**What to test**: Preprints merged with PubMed, page_size works.

```bash
# Run article fix tests
uv run python -m pytest tests/tdd/test_article_fixes.py -v

# Manual MCP test via inspector
# Call: article_searcher(chemicals="metformin", include_preprints=true, page_size=3)
# Expected: max 3 results, mix of PubMed + preprints
# Call: article_getter("41088928")
# Expected: full abstract (not "Article: 41088928")
```

**Pass criteria**: Mix of sources returned. page_size respected. No placeholder abstracts.

---

### Scenario 6: Czech Registry Data (US6)

**What to test**: Pharmacies, PIL/SPC, reimbursement, diagnosis stats.

```bash
# Run Czech registry tests
uv run python -m pytest tests/czech/test_registry_fixes.py -v

# Manual MCP tests:
# Call: czechmed_find_pharmacies(city="Brno")
# Expected: at least 1 pharmacy
# Call: czechmed_get_diagnosis_stats("E11", year=2023)
# Expected: epidemiological data OR clear unavailability reason
```

---

### Scenario 7: Minor Fixes (US7)

```bash
# Run minor fix tests
uv run python -m pytest tests/tdd/test_minor_fixes.py -v

# Manual MCP tests:
# Call: czechmed_search_diagnosis("cukrovka")
# Expected: E10/E11 results
# Call: czechmed_search_diagnosis("diabetes")
# Expected: E11 (T2DM) ranked before E10 (T1DM)
```

---

## Regression Testing

```bash
# Full unit test suite (must all pass)
uv run python -m pytest -x --ff -n auto --dist loadscope

# MCP integration test (60 tools registered)
uv run python -m pytest tests/tdd/test_mcp_integration.py -v

# Arcade integration test (60 tools registered)
uv run python -m pytest tests/tdd/test_arcade_integration.py -v

# Lint check
uv run ruff check src tests
```

**Pass criteria**: All tests pass. 60 MCP + 60 Arcade tools. No lint violations.

## Smoke Test Order

For quick validation after implementation:

1. `uv run python -m pytest tests/tdd/test_sukl_timeout.py -v` (US1 — most critical)
2. `uv run python -m pytest tests/tdd/test_router_fixes.py -v` (US2)
3. `uv run python -m pytest tests/tdd/test_mcp_integration.py -v` (regression — 60 tools)
4. `uv run python -m pytest -x --ff -n auto --dist loadscope` (full suite)
