# Feature Specification: Fix SUKL Drug Search Performance

**Feature Branch**: `001-fix-sukl-search`
**Created**: 2026-03-10
**Status**: Draft
**Input**: User description: "Fix SUKL drug search performance - search_medicine fetches all 68K drugs causing timeout, blocking 3 tools"

## Clarifications

### Session 2026-03-10

- Q: Jak často se má vyhledávací index aktualizovat? → A: Použít stávající denní cache TTL (CACHE_TTL_DAY), konzistentní se zbytkem projektu.
- Q: Co se má stát při prvním spuštění, kdy index neexistuje? → A: Sestavit index on-demand při prvním dotazu (stejný vzor jako MKN-10 a SZV moduly).
- Q: Jaký rozsah opravy pro pharmacy API? → A: Vyšetřit a opravit pouze pokud jde o jednoduchý fix; jinak zdokumentovat limitaci a vyřadit z tohoto scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Search for a medicine by name (Priority: P1)

A healthcare professional or AI assistant searches the Czech drug registry (SUKL) by medicine name, active substance, or ATC code. The system returns matching results within a reasonable timeframe without fetching the entire drug database.

**Why this priority**: This is the core broken functionality. Three tools (`czechmed_search_medicine`, `czechmed_compare_alternatives`, `czechmed_drug_profile`) are completely unusable due to this issue. It blocks the primary use case of the Czech medical module.

**Independent Test**: Can be tested by calling `czechmed_search_medicine` with query "ibuprofen" and verifying results return within 10 seconds.

**Acceptance Scenarios**:

1. **Given** a user searches for "ibuprofen", **When** the search executes, **Then** relevant results are returned within 10 seconds with matching medicine names, strengths, and ATC codes.
2. **Given** a user searches for ATC code "M01AE01", **When** the search executes, **Then** results matching that ATC code are returned within 10 seconds.
3. **Given** a user searches for a non-existent medicine "xyznonexistent", **When** the search executes, **Then** an empty result set is returned within 5 seconds (not a timeout).
4. **Given** the SUKL API is temporarily unavailable, **When** a search is attempted, **Then** a graceful error message is returned within the timeout period.

---

### User Story 2 - Compare medicine alternatives (Priority: P2)

A user requests comparison of alternative medicines for a given drug. The system finds the original medicine and its alternatives (same ATC group) without requiring a full database scan.

**Why this priority**: This is the second most impacted tool. It depends on `search_medicine` internally, so fixing search automatically unblocks this.

**Independent Test**: Can be tested by calling `czechmed_compare_alternatives` with a known SUKL code and verifying alternatives are returned within 15 seconds.

**Acceptance Scenarios**:

1. **Given** a user requests alternatives for SUKL code "0029216", **When** the comparison runs, **Then** medicines with the same ATC code are returned within 15 seconds.
2. **Given** a medicine has no alternatives in the same ATC group, **When** comparison is requested, **Then** the system returns the original medicine details with an empty alternatives list.

---

### User Story 3 - Get full drug profile (Priority: P3)

A user requests a comprehensive drug profile combining data from SUKL search, availability, reimbursement, and PIL/SPC. The system assembles this profile without timing out.

**Why this priority**: This is a workflow tool that orchestrates multiple sub-tools. It depends on search_medicine being functional.

**Independent Test**: Can be tested by calling `czechmed_drug_profile` with query "ibuprofen" and verifying a combined profile is returned within 20 seconds.

**Acceptance Scenarios**:

1. **Given** a user requests a drug profile for "ibuprofen", **When** the profile is assembled, **Then** search results, availability status, and reimbursement data are combined and returned within 20 seconds.

---

### User Story 4 - Find pharmacies by location (Priority: P3)

A user searches for pharmacies in a specific city. The system returns results from the SUKL pharmacy API.

**Why this priority**: Currently returns empty results for valid cities like Praha. Lower priority but should be investigated and fixed if possible.

**Independent Test**: Can be tested by calling `czechmed_find_pharmacies` with city "Praha" and verifying non-empty results or a clear explanation of API limitations.

**Acceptance Scenarios**:

1. **Given** a user searches for pharmacies in "Praha", **When** the search executes, **Then** either pharmacy results are returned or a clear message explains the data source limitations.

---

### Edge Cases

- What happens when the SUKL DLP API changes its response format?
- How does the system handle partial API responses (some drug codes return 404)?
- What happens when the search query contains Czech diacritics (e.g., "léčivo")?
- How does the system behave when the drug list cache is stale but the API is down?
- What happens when a search matches thousands of results (e.g., very common substance)?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The drug search MUST return results within 10 seconds for any query, regardless of the total number of medicines in the registry.
- **FR-002**: The drug search MUST NOT fetch details for all medicines in the registry to perform a search. It MUST use a local searchable index built from the cached drug list, refreshed with daily TTL (CACHE_TTL_DAY). On cold start (no index exists), the index MUST be built on-demand during the first query.
- **FR-003**: The search MUST support querying by medicine name, active substance name, and ATC code.
- **FR-004**: The search MUST correctly handle Czech diacritics (e.g., "léčivo" should match "LECIVO" and vice versa).
- **FR-005**: The search results MUST include pagination (page, page_size, total count).
- **FR-006**: The `compare_alternatives` tool MUST complete within 15 seconds.
- **FR-007**: The `drug_profile` tool MUST complete within 20 seconds.
- **FR-008**: All three tools MUST gracefully handle SUKL API unavailability with a clear error message (no stack traces, no hanging).
- **FR-009**: Cached data MUST be used when available to avoid redundant API calls.
- **FR-010**: The `find_pharmacies` tool SHOULD be investigated for correct SUKL API parameters. If the endpoint is functional, fix the query. If the endpoint is non-functional, document the limitation and return a clear message to the user.

### Key Entities

- **Drug (Léčivý přípravek)**: SUKL code, name, strength, ATC code, pharmaceutical form, holder
- **Drug List**: Complete list of SUKL codes (~68K items, cacheable)
- **Drug Detail**: Full detail for a single SUKL code (fetched on demand)
- **Pharmacy (Lékárna)**: ID, name, city, postal code, address, phone, 24/7 status

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `czechmed_search_medicine` returns results for "ibuprofen" within 10 seconds (currently times out after 5+ minutes)
- **SC-002**: `czechmed_compare_alternatives` returns results within 15 seconds (currently times out)
- **SC-003**: `czechmed_drug_profile` returns results within 20 seconds (currently times out)
- **SC-004**: All 23 Czech tools pass their existing unit tests with no regressions
- **SC-005**: At least 20 of 23 Czech tools return valid responses in live API testing (allowing for external API downtime)
- **SC-006**: `czechmed_find_pharmacies` returns non-empty results for major Czech cities, or documents API limitations if the SUKL endpoint no longer supports this query

## Assumptions

- A local searchable index will be built from the cached complete drug list (refreshed daily via CACHE_TTL_DAY). The index is built on-demand at first query, consistent with MKN-10 and SZV in-memory initialization patterns.
- The existing cache infrastructure (diskcache) is suitable for storing a searchable drug index.
- The pharmacy API endpoint is still functional; empty results may be due to incorrect query parameters.
- Czech diacritics normalization via `normalize_query()` is working correctly and does not need changes.
