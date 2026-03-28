---
color: green
isContextNode: false
agent_name: Amy
---
# SUKL DrugIndex — Cold Start & Search Pipeline

In-memory index ~46K léků. Cold start ~10 min (API), ~1s (diskcache). Linear scan search s normalized substring match.

### DrugIndex Build Pipeline
```
get_drug_index() → DrugIndex singleton
  ├─ is_expired? No → return cached
  └─ Yes → async lock → _build()
      ├─ 1. diskcache hit → JSON deserialize → ~1s
      └─ 2. miss → Live API
          ├─ GET /dlp/v1/lecive-pripravky → ~68K codes
          ├─ semaphore(20) concurrent detail fetches
          ├─ Validate ≥50% success ratio
          └─ Persist to diskcache (TTL=1 day)
```

`DrugIndexEntry` = frozen dataclass: sukl_code, name, name_normalized, strength, atc_code, form, supplement, holder_code.

`search_index()` = linear scan O(n) substring match on normalized name/ATC/supplement/holder. Pagination via `compute_skip()`.

### VZP Drug Reimbursement
`_get_vzp_drug_reimbursement()` a `_compare_alternatives()` delegují na DrugIndex pro ATC group lookup, pak porovnávají ceny v rámci skupiny.

### NOTES

- Cold start ~10 min je hlavní UX problém — timeout wrapper vrací user-friendly zprávu
- SUKL pharmacy API (/dlp/v1/lecebna-zarizeni) vrací 504 — graceful handling
- Linear scan O(n) pro ~46K entries je OK, ale nescaluje

deep dive [[czech-overview]]
