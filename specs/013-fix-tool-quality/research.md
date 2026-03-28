# Research: Fix Tool Quality — E2E Test Report Bugs

**Date**: 2026-03-28
**Feature**: 013-fix-tool-quality

## Root Cause Analysis

### BUG-1: search(domain="trial") Query Ignored

**Decision**: Fix query passthrough in router.py trial handler
**Rationale**: ClinicalTrials.gov API v2 uses `query.term` for free-text search. Router.py must pass user query as `query.term` parameter. Currently the unified search() handler may construct parameters differently than the direct `trial_searcher` tool.
**Alternatives considered**:
- Rewrite entire search() wrapper — too risky, out of scope
- Add separate trial-specific search params — unnecessary, API supports `query.term`

### BUG-2: thinking-reminder in Results

**Decision**: Remove thinking-reminder from `format_results()` in router.py
**Rationale**: Lines 99-111 in router.py prepend a pseudo-result with `id="thinking-reminder"` to every search() call. This pollutes data results. LLM consumers cannot distinguish it from actual data.
**Alternatives considered**:
- Move to response metadata — MCP protocol doesn't have standard metadata field for this
- Keep but mark differently — still confusing for LLM consumers
- **Selected**: Remove entirely — the think tool exists as a separate MCP tool, no need to inject reminders

### BUG-3/4/5: SUKL Performance (9-14 min latency)

**Decision**: Add asyncio.wait_for() timeout + circuit breaker + informative error message
**Rationale**: DrugIndex cold start requires ~68,001 HTTP requests (1 list + 68K details) with semaphore(20). Cannot be avoided — full index is required for substring search. However:
- Index is cached to disk after first build (`_INDEX_DISK_KEY`) — subsequent starts load in ~1s
- Cold start happens only once per deployment or cache expiry (CACHE_TTL_DAY)
- Timeout wrapper prevents indefinite waiting
- Circuit breaker prevents retry storms if SUKL API is down
**Alternatives considered**:
- Increase semaphore to 50+ — may trigger SUKL rate limiting
- Implement pagination-based lazy loading — DrugIndex requires full index for substring match
- Direct API search without index — SUKL DLP API doesn't have server-side search
- **Selected**: Timeout (10s for search, 30s for compare) + circuit breaker (2 failures → 60s cooldown)

### BUG-6: czechmed_diagnosis_assist Returns C84 for Diabetes Symptoms

**Decision**: Add explicit symptom-cluster-to-ICD mapping + post-filter validation
**Rationale**: Current embedding-based search uses semantic similarity which doesn't capture clinical reasoning (symptom clusters → differential diagnosis). "Únava" (fatigue) appears in many conditions including lymphoma (C84), causing false matches.
**Alternatives considered**:
- Retrain embedding model — requires labeled clinical dataset, out of scope
- Use LLM for clinical reasoning — adds latency and API dependency
- **Selected**: Two-layer approach:
  1. Pre-filter: Explicit mappings for top 20 Czech clinical presentations (polydipsie+polyurie+hyperglykemie → E11, bolest na hrudi+dusnost → I21, etc.)
  2. Post-filter: Remove results where MKN chapter is completely unrelated to symptom domain

### BUG-7: czechmed_compare_alternatives Hangs

**Decision**: Wrap with asyncio.wait_for(30s) timeout
**Rationale**: compare_alternatives depends on search_medicine (which depends on DrugIndex). If DrugIndex is building, the entire chain hangs. 30s timeout allows for cached index usage while preventing indefinite hang on cold start.
**Alternatives considered**: Same as BUG-3/4/5

### BUG-8: drug_getter("metformin") Returns Unknown

**Decision**: Adjust relevance threshold in biothings_client.py hit scoring
**Rationale**: MyChem.info `_query_drug()` already queries `/v1/query?q=metformin`. The issue is in hit scoring logic (lines 451-471) which filters by relevance threshold. Common drug names like "metformin" should pass the threshold.
**Alternatives considered**:
- Add separate name-resolution function — unnecessary, infrastructure exists
- Cache common drug names locally — adds maintenance burden
- **Selected**: Lower relevance threshold + add fallback to top-1 result if no hits pass threshold

### BUG-9: czechmed_get_reimbursement Returns No Data

**Decision**: Verify VZP codebook version and SUKL code mapping
**Rationale**: VZP codebook uses version `_VZP_VERSION = "01460"` downloaded from VZP CDN. Reimbursement lookup depends on correct SUKL-to-VZP code mapping. Metformin is definitively covered by VZP — if lookup fails, the mapping or codebook version is wrong.
**Alternatives considered**: Direct SUKL reimbursement API — doesn't exist separately

### BUG-10/11: PIL/SPC Not Available

**Decision**: Improve error messaging + try alternative SUKL endpoints
**Rationale**: SUKL getter.py already has `_fetch_doc_metadata()` + `_build_doc_url()` + `_url_is_reachable()`. For older registrations (2005), documents may genuinely not be digitized. User needs to know whether it's "document doesn't exist" vs "API error".
**Alternatives considered**: Scrape SUKL web portal — fragile, out of scope

### BUG-12: find_pharmacies Returns 0 Results

**Decision**: Fix city name matching in NRPZS CSV filtering
**Rationale**: NRPZS uses CSV download from UZIS. Filtering checks `ZZ_obec` column. "Brno" may not match actual values (could be "Brno-město", "Brno-střed", etc.). Need to check actual CSV content and adjust matching.
**Alternatives considered**: Switch to NRPZS REST API — CSV is more reliable and complete

### BUG-14: Preprints Replace PubMed Results

**Decision**: Verify deduplication logic in unified.py
**Rationale**: Code already runs PubMed + preprints in parallel (lines 164-176). DOI-based deduplication may incorrectly remove PubMed results when preprint DOIs differ from published DOIs. Need to verify merge order and dedup logic.
**Alternatives considered**: Remove deduplication — would cause duplicates

### BUG-15: Article Getter Placeholder Abstract

**Decision**: Add PubMed E-utilities fallback after PubTator3 + Europe PMC
**Rationale**: fetch.py returns `f"Article: {pmid}"` when PubTator3 has no abstract passages. Europe PMC fallback exists but may also fail. PubMed E-utilities (`efetch.fcgi?db=pubmed&id={pmid}&rettype=abstract`) is definitive source.
**Alternatives considered**: Only Europe PMC fallback — already exists but insufficient

### BUG-16: openfda_recall_getter Returns Wrong Recall

**Decision**: Debug recall_number exact match behavior
**Rationale**: Code uses `recall_number:"{value}"` which should be exact match. May need format normalization (e.g., "D-0328-2025" vs "D-328-2025") or there may be multiple recalls with similar numbers.
**Alternatives considered**: Use event_id instead — less user-friendly

### BUG-17: NZIP CSV Not Found

**Decision**: Verify URL accessibility + ensure local fallback data is bundled
**Rationale**: URL `https://reporting.uzis.cz/cr/data/hospitalizace_{year}.csv`. Local fallback with ±5 year search already exists. Need to ensure `hospitalizace_2024.csv` is bundled in `data/` directory.
**Alternatives considered**: Alternative data source — UZIS is authoritative

### BUG-19: article_searcher page_size Ignored

**Decision**: Verify limit passthrough in article search pipeline
**Rationale**: Code has fetch multiplier 3x for deduplication. Final pagination via `merged_results[offset:offset+limit]` should respect limit. Need to trace where limit parameter gets lost or overridden.
**Alternatives considered**: Remove page_size parameter — breaks API contract

### BUG-24/25: Czech Synonyms and Ranking

**Decision**: Add synonym dictionary + prevalence-based ranking boost
**Rationale**: MKN-10 search uses text matching on official Czech names. Colloquial terms ("cukrovka") are not in official nomenclature. A ~50-term dictionary covers most common medical terms. E11 prevalence is ~10x E10 — ranking should reflect this.
**Alternatives considered**: NLP synonym expansion — overkill for ~50 terms
