# Quickstart: Verifying Bug Fixes

**Feature**: 012-fix-mcp-tool-bugs

## Prerequisites

```bash
uv sync --all-extras
```

## After Phase P1 (Critical Fixes)

```bash
# 1. Run all unit tests (MUST pass)
uv run python -m pytest -x --ff -n auto --dist loadscope -m "not integration"

# 2. Regression test — must still be 60 tools
uv run python -m pytest tests/tdd/test_mcp_integration.py -v

# 3. Live verification of P1 fixes (optional, needs network)
uv run python -m pytest -m "integration" -k "search_medicine or nrpzs or szv or article_search" -v
```

### Manual spot-checks via MCP Inspector

```bash
make inspector
# Then test:
# - SearchMedicine(query="ibuprofen") → should return results
# - SearchProviders(city="Praha") → should return providers
# - SearchProcedures(query="EKG") → should return procedures
# - ArticleSearcher(keywords="BRCA1") → should return articles
```

## After Phase P2 (Medium Fixes)

```bash
# Unit tests
uv run python -m pytest -x --ff -n auto --dist loadscope -m "not integration"

# Specific P2 tests
uv run python -m pytest -k "sukl_code_normalization or diagnosis_stats or reimbursement or error_format" -v
```

## After Phase P3 (Low Priority)

```bash
# Full test suite
uv run python -m pytest -x --ff -n auto --dist loadscope

# Quality checks
make check
```

## Success Verification

After all 3 phases, run the complete test report reproduction:

```bash
# All unit tests pass
uv run python -m pytest -m "not integration" -v --tb=short

# Tool count unchanged
uv run python -m pytest tests/tdd/test_mcp_integration.py -v

# Integration smoke test
uv run python -m pytest -m "integration" --timeout 120 -v
```

Expected outcome: success rate 75%+ (up from 46%).
