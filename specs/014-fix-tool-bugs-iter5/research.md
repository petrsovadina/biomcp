# Research: Fix Tool Bugs Iteration 5

**Created**: 2026-03-29
**Status**: Pending investigation during implementation

## R1: NRPZS Pharmacy Endpoint

**Question**: What is the correct NRPZS API endpoint and filter to list pharmacies by city?

**Decision**: Investigate during T030. Current `_find_pharmacies()` in `czech/sukl/search.py` uses NRPZS API. Need to verify:
- Correct OborPece/DruhZdravotnichSluzeb filter for "Lékárenská péče"
- Whether the endpoint is functional at all (may be permanently broken)

**Fallback**: If NRPZS pharmacy endpoint is permanently broken, return informative error message.

## R2: OpenFDA recall_number Search Format

**Question**: Does OpenFDA support `search=recall_number:"D-0328-2025"` query format?

**Decision**: Investigate during T033. Current code in `drug_recalls.py:194` already uses `recall_number:"{recall_number}"` format. Need to verify if the issue is in the search query construction or result matching.

**Rationale**: The code appears to search by recall_number correctly. Bug may be in how results are filtered/matched, not in the query itself.

## R3: PubMed E-utilities efetch for Abstracts

**Question**: What is the API call to retrieve an abstract by PMID via E-utilities?

**Decision**: Use `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={pmid}&rettype=abstract&retmode=text`

**Rationale**: Standard NCBI E-utilities API. No API key required for low-volume usage. Existing httpx infrastructure supports this.

**Alternatives considered**:
- PubMed Central API — only works for PMC-indexed articles
- Europe PMC REST API — additional dependency, same data source

## R4: MyChem.info Name Search

**Question**: How to resolve common drug names (metformin, aspirin) to DrugBank/ChEMBL IDs via MyChem.info?

**Decision**: Use `GET https://mychem.info/v1/query?q={name}&fields=drugbank.id,chembl.molecule_chembl_id,drugbank.name&size=1`

**Rationale**: MyChem.info query endpoint supports free-text drug name search. Returns structured data with DrugBank and ChEMBL IDs. Already used in existing `biothings_client.py`.

**Alternatives considered**:
- Static name→ID dictionary — incomplete, requires maintenance
- PubChem API — additional external dependency

## R5: drug_profile Root Cause

**Question**: Why does `_drug_profile()` in `czech/workflows/drug_profile.py` always return server error?

**Decision**: Investigate during T013. Likely causes:
1. SUKL DrugIndex not initialized (cold-start issue — related to US2)
2. Missing error handling for sub-query failures
3. Broken aggregation logic

**Approach**: Read the function, add try/except per sub-query, return partial results on failure.
