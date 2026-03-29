# Feature Specification: Fix Tool Bugs Iteration 5

**Feature Branch**: `014-fix-tool-bugs-iter5`
**Created**: 2026-03-29
**Status**: Draft
**Input**: Iterace 5 bug fix sprint based on comprehensive 4-iteration test report (180+ tool calls, 28 active bugs)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Article Search Returns Results Quickly (Priority: P0)

An AI copilot user searches for biomedical articles using `article_searcher`. The search completes within acceptable time limits for real-time interaction, regardless of query complexity.

**Why this priority**: Current avg latency is 51s with P95 at 100s — unusable for real-time AI copilot. This is the single biggest blocker for production quality across all tool categories. Affects `search()` unified wrapper as cascade.

**Independent Test**: Call `article_searcher` with various queries (chemicals, diseases, genes) and verify response times are within acceptable bounds.

**Acceptance Scenarios**:

1. **Given** a standard biomedical query (e.g., "metformin type 2 diabetes"), **When** `article_searcher` is called with `preprints=false`, **Then** results are returned with avg latency < 15s and P95 < 30s
2. **Given** a complex multi-term query, **When** `article_searcher` is called, **Then** no single request exceeds 30s (hard timeout)
3. **Given** the same query is repeated within 1 hour, **When** `article_searcher` is called, **Then** cached results are returned in < 2s

---

### User Story 2 - SUKL Drug Search Without Cold-Start Block (Priority: P0)

A Czech healthcare professional searches for a medicine by name. The search returns results without requiring a 10+ minute index build.

**Why this priority**: Cold-start block makes all SUKL drug tools unusable for first-time users per session. This affects 6+ dependent tools.

**Independent Test**: Start fresh MCP server session, immediately call `czechmed_search_medicine("Metformin")`, verify results arrive within seconds.

**Acceptance Scenarios**:

1. **Given** a freshly started MCP server, **When** `czechmed_search_medicine("Metformin")` is called, **Then** results are returned in < 5s (not a "building index" message)
2. **Given** a persistent index exists from a previous session, **When** the server restarts, **Then** the index is loaded from disk in < 2s
3. **Given** the index is older than 24 hours, **When** a search is called, **Then** the index is refreshed in background while serving stale results

---

### User Story 3 - Drug Profile Provides Complete Information (Priority: P0)

A user requests a drug profile which aggregates registration, availability, reimbursement, and evidence data into a single response.

**Why this priority**: `czechmed_drug_profile` always returns server error — a key composite tool is completely broken.

**Independent Test**: Call `czechmed_drug_profile("Metformin")` and verify structured response with multiple data sections.

**Acceptance Scenarios**:

1. **Given** a valid drug name "Metformin", **When** `czechmed_drug_profile` is called, **Then** a response with registration status, availability, and evidence sections is returned
2. **Given** a SUKL code "0011114", **When** `czechmed_drug_profile` is called, **Then** the same structured profile is returned
3. **Given** a nonexistent drug name, **When** `czechmed_drug_profile` is called, **Then** a clear "not found" message is returned (not a server error)

---

### User Story 4 - Article Search Merges Preprints With Peer-Reviewed (Priority: P1)

A researcher searches for articles with preprints enabled. Results include both PubMed peer-reviewed articles and Europe PMC preprints, deduplicated.

**Why this priority**: `include_preprints=True` currently replaces PubMed results entirely with preprints, losing the most important peer-reviewed content.

**Independent Test**: Call `article_searcher` with `include_preprints=true` and verify result mix.

**Acceptance Scenarios**:

1. **Given** a disease query with `include_preprints=true`, **When** results are returned, **Then** at least 30% are peer-reviewed PubMed articles and at least 1 is a preprint
2. **Given** overlapping articles exist in PubMed and Europe PMC, **When** merged, **Then** duplicates are removed (DOI-based deduplication)
3. **Given** `include_preprints=false`, **When** results are returned, **Then** only PubMed peer-reviewed articles appear (no regression)

---

### User Story 5 - Drug Lookup by Common Name (Priority: P1)

A user looks up drug information using common drug names like "metformin", "aspirin", or "atorvastatin" and receives complete drug profiles.

**Why this priority**: The most intuitive lookup method (common name) fails for the most common drugs. Users must know DrugBank or ChEMBL IDs as workaround.

**Independent Test**: Call `drug_getter("metformin")` and verify it returns the correct drug profile.

**Acceptance Scenarios**:

1. **Given** common name "metformin", **When** `drug_getter` is called, **Then** DrugBank ID DB00331 is returned with description, indications, and mechanism
2. **Given** common name "aspirin", **When** `drug_getter` is called, **Then** DrugBank ID DB00945 is returned with complete data
3. **Given** common name "atorvastatin", **When** `drug_getter` is called, **Then** DrugBank ID DB01076 is returned
4. **Given** a DrugBank ID "DB00331", **When** `drug_getter` is called, **Then** results are identical (no regression)

---

### User Story 6 - Article Detail Shows Real Abstract (Priority: P1)

A user retrieves article details by PMID. The response includes the actual abstract, not a placeholder string.

**Why this priority**: Placeholder text "Article: 38768446" instead of real abstract makes article_getter unreliable for PMID-based lookups.

**Independent Test**: Call `article_getter("38768446")` and verify the abstract is a real scientific text.

**Acceptance Scenarios**:

1. **Given** PMID 38768446, **When** `article_getter` is called, **Then** the abstract contains actual scientific content (not "Article: 38768446")
2. **Given** a PMC ID "PMC11193658", **When** `article_getter` is called, **Then** full text is returned (no regression)
3. **Given** a PMID not indexed in PubTator3, **When** `article_getter` is called, **Then** abstract is fetched from PubMed E-utilities as fallback

---

### User Story 7 - Diagnosis Assist Recognizes Named Diagnoses (Priority: P1)

A user describes symptoms that include a direct diagnosis name (e.g., "hypertenze"). The system recognizes the named diagnosis and prioritizes the corresponding ICD-10 code.

**Why this priority**: Currently "hypertenze, bolest hlavy" returns G43 Migraine instead of I10 Hypertension — the system ignores explicitly named diagnoses.

**Independent Test**: Call `czechmed_diagnosis_assist("hypertenze, bolest hlavy, zavrate")` and verify I10 is top-ranked.

**Acceptance Scenarios**:

1. **Given** symptoms "hypertenze, bolest hlavy, zavrate, otoky nohou", **When** `diagnosis_assist` is called, **Then** I10 Hypertenze is in top-3 results
2. **Given** symptoms containing "diabetes, zizen", **When** `diagnosis_assist` is called, **Then** E11 is still in top-5 (no regression)
3. **Given** symptoms with no named diagnosis "bolest hlavy, nausea, svetloplachost", **When** `diagnosis_assist` is called, **Then** cluster-based matching still works (no regression)

---

### User Story 8 - Pharmacy Search Returns Results (Priority: P2)

A user searches for pharmacies in a Czech city and receives a list of actual pharmacy locations.

**Why this priority**: `find_pharmacies` returns 0 results for all cities — tool is nonfunctional but non-critical.

**Independent Test**: Call `czechmed_find_pharmacies(city="Brno")` and verify results.

**Acceptance Scenarios**:

1. **Given** city "Brno", **When** `find_pharmacies` is called, **Then** at least 5 pharmacies are returned with names and addresses
2. **Given** city "Praha" with `nonstop=true`, **When** `find_pharmacies` is called, **Then** results are filtered to 24h pharmacies only

---

### User Story 9 - FDA Recall Getter Returns Correct Recall (Priority: P2)

A user looks up a specific FDA recall by recall number and receives the matching recall, not a different one.

**Why this priority**: ID mapping bug returns wrong recall (progesterone instead of metformin).

**Independent Test**: Call `openfda_recall_getter("D-0328-2025")` and verify the returned recall matches.

**Acceptance Scenarios**:

1. **Given** recall number "D-0328-2025", **When** `recall_getter` is called, **Then** the returned recall contains the matching recall_number (not D-321-2016)
2. **Given** a numeric event_id, **When** `recall_getter` is called, **Then** it still works via event_id lookup (no regression)

---

### User Story 10 - Article Search Respects Page Size (Priority: P2)

A user specifies a page_size parameter for article search and receives the requested number of results.

**Why this priority**: `page_size` parameter is completely ignored — always returns default 10.

**Independent Test**: Call `article_searcher` with `page_size=3` and verify result count.

**Acceptance Scenarios**:

1. **Given** `page_size=3`, **When** `article_searcher` is called, **Then** at most 3 results are returned
2. **Given** `page_size=20`, **When** `article_searcher` is called, **Then** up to 20 results are returned

---

### User Story 11 - OpenFDA Label Section Validation (Priority: P2)

A user searches for drug labels by section name. Invalid section names produce a helpful error instead of empty results.

**Why this priority**: "warnings" and "warnings_and_precautions" silently return NOT_FOUND instead of suggesting the correct field name.

**Independent Test**: Call `openfda_label_searcher(section="warnings")` and verify the response.

**Acceptance Scenarios**:

1. **Given** section "warnings", **When** `label_searcher` is called, **Then** either the correct results are returned OR a message suggests valid alternatives (boxed_warning, contraindications, etc.)
2. **Given** section "contraindications", **When** `label_searcher` is called, **Then** results are returned (no regression)

---

### User Story 12 - Gene Getter Returns Concise Output (Priority: P3)

A user queries gene information and receives a concise summary without 500+ isoform listings.

**Why this priority**: Low priority cosmetic issue — output is too verbose but data is correct.

**Independent Test**: Call `gene_getter("BRCA1")` and verify output length is reasonable.

**Acceptance Scenarios**:

1. **Given** gene "BRCA1", **When** `gene_getter` is called, **Then** only the canonical isoform is shown with total isoform count noted
2. **Given** gene "TP53", **When** `gene_getter` is called, **Then** output is concise and complete

---

### Edge Cases

- What happens when PubMed API is down during article_searcher? System returns cached results if available, or clear timeout error within 30s.
- What happens when SUKL persistent index file is corrupted? System detects corruption, logs error, and rebuilds from scratch in background.
- What happens when drug_getter common name resolves to multiple drugs? System returns best match (highest relevance score), notes alternatives exist.
- What happens when diagnosis_assist input contains both a named diagnosis AND contradicting symptoms? Named diagnosis takes priority with cluster-based results as secondary.
- What happens when find_pharmacies NRPZS endpoint is permanently broken? System returns informative error message explaining the data source limitation.

## Requirements *(mandatory)*

### Functional Requirements

**P0 — Critical (must fix before deployment)**

- **FR-001**: `article_searcher` MUST complete all queries within 30s hard timeout. Average latency MUST be under 15s.
- **FR-002**: `article_searcher` MUST cache results for identical queries (same parameters) for 1 hour.
- **FR-003**: SUKL drug index MUST persist to disk and reload on server start in under 2s.
- **FR-004**: SUKL drug index MUST NOT block user queries during initial build or refresh.
- **FR-005**: `czechmed_drug_profile` MUST return structured data for valid drug names, SUKL codes, and ATC codes.
- **FR-006**: `czechmed_drug_profile` MUST return clear error messages for invalid inputs (not server error).

**P1 — High Priority**

- **FR-007**: `article_searcher` with `include_preprints=True` MUST return a union of PubMed and Europe PMC results, deduplicated by DOI.
- **FR-008**: `drug_getter` MUST resolve common drug names (metformin, aspirin, atorvastatin, amlodipine) to their correct DrugBank IDs.
- **FR-009**: `drug_getter` MUST use a name-search fallback when direct lookup returns "Unknown".
- **FR-010**: `article_getter` MUST fetch abstract from PubMed E-utilities when PubTator3 returns no abstract for a PMID.
- **FR-011**: `article_getter` MUST NOT return placeholder strings as abstract content.
- **FR-012**: `czechmed_diagnosis_assist` MUST check for direct diagnosis name matches in input before running cluster-based matching.
- **FR-013**: Direct diagnosis name matches MUST rank higher than cluster-based matches.

**P2 — Medium Priority**

- **FR-014**: `czechmed_find_pharmacies` MUST query the correct NRPZS endpoint for pharmacy-type providers.
- **FR-015**: `openfda_recall_getter` MUST search by `recall_number` field (not `event_id`) for D-XXXX-YYYY format inputs.
- **FR-016**: `article_searcher` MUST propagate `page_size` parameter to backend API calls.
- **FR-017**: `openfda_label_searcher` MUST validate section parameter against known valid values and suggest alternatives for invalid ones.

**P3 — Low Priority**

- **FR-018**: `gene_getter` MUST return only canonical isoform by default with total isoform count.

### Key Entities

- **Article Search Cache**: Query fingerprint (hash of parameters), result set, timestamp, TTL
- **SUKL Persistent Index**: Drug entries (code, name, ATC, supplement, holder), last_updated timestamp
- **Direct Diagnosis Map**: Czech medical term to ICD-10 code mapping (extension of existing CZ_MEDICAL_SYNONYMS)
- **Drug Name Resolution**: Common name to DrugBank/ChEMBL ID mapping via MyChem.info search API

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `article_searcher` average latency drops from 51s to under 15s (70% reduction)
- **SC-002**: `article_searcher` P95 latency drops from 100s to under 30s
- **SC-003**: No single `article_searcher` request exceeds 30s
- **SC-004**: SUKL drug search responds within 5s on cold start (was 10+ minutes)
- **SC-005**: `drug_getter` resolves metformin, aspirin, atorvastatin, amlodipine by common name (was: Unknown)
- **SC-006**: `article_getter` returns real abstracts for PMIDs (was: placeholder strings)
- **SC-007**: `czechmed_drug_profile` returns structured data (was: server error)
- **SC-008**: `diagnosis_assist("hypertenze, bolest hlavy")` returns I10 in top-3 (was: absent)
- **SC-009**: `article_searcher(preprints=true)` returns mix of PubMed + preprints (was: 100% preprints)
- **SC-010**: All 8 previously fixed bugs remain stable (regression test suite passes)
- **SC-011**: Overall tool quality score improves from 6.4/10 to at least 7.5/10
- **SC-012**: Active bug count drops from 28 to under 18

## Assumptions

- PubMed E-utilities API is available as fallback for article abstract retrieval
- MyChem.info search API supports drug name resolution with sufficient coverage for common generics
- NRPZS API has a working endpoint for pharmacy providers (needs investigation — if permanently broken, FR-014 will be marked as external dependency)
- SUKL DLP API remains stable for index building (current 68K entries)
- diskcache infrastructure is available for SUKL persistent index storage
- Existing CZ_MEDICAL_SYNONYMS dictionary in `synonyms.py` can be extended for direct diagnosis name matching
- OpenFDA API supports `recall_number` field in search queries

## Regression Test Suite

The following tests MUST pass without regression from previous iterations:

1. `search(domain="trial", query="metformin T2DM")` returns 3+ relevant NCT studies
2. No thinking-reminder appears in any `search()` result
3. `czechmed_search_diagnosis("cukrovka")` returns E11 in results
4. `czechmed_search_diagnosis("diabetes")` returns E11 as rank#1
5. `czechmed_diagnosis_assist("zizen, caste moceni...")` returns E11 in top-5
6. `article_searcher(preprints=false, page=2)` returns peer-reviewed PubMed results

## Scope Exclusions

The following known bugs are **explicitly excluded** from this iteration:

- **BUG-9**: `czechmed_get_reimbursement` — requires SUKL/AISLP DB integration (external dependency)
- **BUG-10/11**: `czechmed_get_pil/spc` — PIL/SmPC not available for older registrations (data gap)
- **BUG-17**: `czechmed_get_diagnosis_stats` — NZIP endpoint investigation only (may be external dependency)
- **BUG-18**: `get_diagnosis_detail` name_en — requires WHO ICD-10 EN API integration
- **BUG-27**: `search(domain=variant)` chromosome mapping — low priority, complex fix
- All `nci_*` and `alphagenome_predictor` tools — require external API keys
