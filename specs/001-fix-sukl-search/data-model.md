# Data Model: Fix SUKL Drug Search

## Entities

### DrugIndexEntry (new, in-memory)

In-memory representation of a drug for search indexing.

| Field | Type | Source | Notes |
|-------|------|--------|-------|
| sukl_code | str | kodSUKL | 7-digit identifier, primary key |
| name | str | nazev | Drug name |
| name_normalized | str | computed | Lowercase, diacritics stripped |
| strength | str | sila | Dosage strength |
| atc_code | str | ATCkod | ATC classification |
| atc_normalized | str | computed | Lowercase |
| form | str | lekovaFormaKod | Pharmaceutical form |
| supplement | str | doplnek | Full description text |
| supplement_normalized | str | computed | Lowercase, diacritics stripped |
| holder_code | str | drzitelKod | Marketing authorization holder |

### DrugIndex (new, singleton)

In-memory searchable index, lazy-initialized on first query.

| Field | Type | Notes |
|-------|------|-------|
| entries | list[DrugIndexEntry] | All 68K drugs |
| _built_at | datetime | When index was last built |
| _lock | asyncio.Lock | Prevents concurrent builds |

**Lifecycle**:
1. `None` → first query triggers build
2. `Built` → serves queries from memory
3. `Expired` (built_at + CACHE_TTL_DAY < now) → rebuild on next query

### DrugSummary (existing)

Returned to user in search results. No changes needed.

| Field | Type | Notes |
|-------|------|-------|
| sukl_code | str | 7-digit SUKL code |
| name | str | Drug name |
| strength | str | Dosage |
| atc_code | str | ATC code |
| pharmaceutical_form | str | Form (tablet, injection, etc.) |

## Relationships

```
DrugIndex 1 ──── * DrugIndexEntry
DrugIndexEntry → (maps to) → DrugSummary (on search hit)
DrugIndexEntry.sukl_code → (fetches) → full Drug Detail (on demand)
```

## State Transitions

```
DrugIndex: None → Building → Ready → Expired → Building → Ready → ...
```

## Data Volume

- Drug list: 68,082 codes (665 KB raw JSON)
- Drug index in memory: ~14 MB (68K × ~200 bytes per entry)
- Individual detail cache: existing diskcache entries (1 per code)
