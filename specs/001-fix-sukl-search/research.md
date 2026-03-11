# Research: Fix SUKL Drug Search Performance

**Date**: 2026-03-10
**Branch**: `001-fix-sukl-search`

## Key Findings

### SUKL DLP API v1 Capabilities

**Decision**: SUKL API does NOT support server-side search. A local searchable index must be built.

**Rationale**: Tested all plausible query parameters (`nazev`, `atcKod`, `q`) on `/dlp/v1/lecive-pripravky` — all silently ignored, always returns full 68,082-code list. The API is code-list + detail-lookup only, no filtering.

**Alternatives considered**:
- Server-side filtering — not available
- Alternative SUKL endpoint — none found that supports search
- opendata.sukl.cz — also lacks search; some endpoints (e.g., reimbursement) are returning 504

### Drug List Endpoint

- `GET /dlp/v1/lecive-pripravky?typSeznamu=dlpo` returns **68,082 bare SUKL code strings** (665 KB)
- No metadata (no names, ATC codes, or substance info) in the list
- Each drug detail requires individual `GET /dlp/v1/lecive-pripravky/{kodSUKL}`

### Drug Detail Structure

Key searchable fields from detail endpoint:
- `nazev` — drug name (e.g., "CELSENTRI")
- `sila` — strength (e.g., "150MG")
- `ATCkod` — ATC classification (e.g., "J05AX09")
- `doplnek` — supplement text with form/packaging info
- `drzitelKod` — MAH holder code
- `leciveLatky` — active substance codes (array of ints)

### Pharmacy API Status

**Decision**: Pharmacy endpoint is non-functional (504 Gateway Timeout). Document limitation.

**Rationale**: `GET /dlp/v1/lecebna-zarizeni` returns 504. The `opendata.sukl.cz` alternative returns 404. No working pharmacy search endpoint found.

**Alternatives considered**:
- Wait for API to come back — unreliable timeline
- Scrape web interface — not in scope per clarification (best-effort only)

### Workflow Tool Dependencies

**`drug_profile`** calls `_resolve_sukl_code(query)` → `_sukl_drug_search(query, page=1, page_size=1)` → full 68K scan just to resolve name → code.

**`compare_alternatives`** gets ATC code from detail, then calls `_sukl_drug_search(atc_code)` → another full 68K scan to find same-ATC medicines.

Both are blocked by the same root cause.

## Architecture Decision: Local Drug Index

**Decision**: Build an in-memory searchable index from cached drug details.

**Rationale**: The only alternative is 68K individual HTTP requests per search, which takes 5+ minutes. An in-memory index provides sub-second search after initial build.

**Design**:
1. Fetch all 68K codes from list endpoint (665 KB, cached CACHE_TTL_DAY)
2. Fetch details for all codes in batches (using existing per-detail cache with CACHE_TTL_DAY)
3. Build in-memory index mapping: `{normalized_name → [sukl_code], normalized_atc → [sukl_code], normalized_holder → [sukl_code]}`
4. Search queries scan the index (O(n) substring match on ~68K entries in memory = ~10ms)
5. Return matched SUKL codes, then fetch full details only for the page results

**Cold start**: First query triggers full index build. Subsequent queries use in-memory index.
**Refresh**: Index invalidated when cache TTL expires (CACHE_TTL_DAY).

**Similar pattern in codebase**: MKN-10 (~20 MB in-memory) and SZV (~5 MB in-memory) use identical on-demand initialization.

**Memory estimate**: 68K entries × ~200 bytes (code + name + ATC + holder) ≈ **~14 MB** — well within acceptable range.
