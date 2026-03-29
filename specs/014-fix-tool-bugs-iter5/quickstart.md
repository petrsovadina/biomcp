# Quickstart: Fix Tool Bugs Iteration 5

## Validation Script

After implementation, run these tests to validate all fixes:

### P0 Validation

```bash
# 1. Article searcher latency (should be < 15s avg)
uv run czechmedmcp article search --chemicals metformin --diseases "type 2 diabetes"

# 2. SUKL cold-start (should respond in < 5s, not "building index")
uv run czechmedmcp czech search-medicine "Metformin"

# 3. Drug profile (should return structured data, not server error)
uv run czechmedmcp czech drug-profile "Metformin"
```

### P1 Validation

```bash
# 4. Preprints merge (should show mix of PubMed + preprints)
uv run czechmedmcp article search --chemicals metformin --include-preprints

# 5. Drug getter common name (should return DB00331)
uv run czechmedmcp drug get metformin

# 6. Article getter abstract (should show real abstract)
uv run czechmedmcp article get 38768446

# 7. Diagnosis assist (should have I10 in results)
# Run via MCP Inspector: czechmed_diagnosis_assist("hypertenze, bolest hlavy")
```

### Regression Suite

```bash
# Must all pass
uv run python -m pytest tests/tdd/ -x --ff -n auto --dist loadscope
```

### Full Quality Check

```bash
uv run ruff check src tests
uv run mypy
uv run python -m pytest -x --ff -n auto --dist loadscope
```
