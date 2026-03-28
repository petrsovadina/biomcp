---
color: green
isContextNode: false
agent_name: Amy
---
# Czech Healthcare Modules — Architecture Overview

23 MCP nástrojů v 6 submodulech + 3 workflow orchestrátory. Všechny sdílí lazy-init vzor s diskcache a diacritics-insensitive search.

## Architektura (23 nástrojů, `src/czechmedmcp/czech/`)

| Submodul | Nástroje | Datový zdroj | Init vzor |
|----------|----------|--------------|----------|
| **sukl/** | 8 | SUKL DLP API (REST) | Lazy DrugIndex singleton (~46K entries, ~14MB) |
| **mkn/** | 4 | ÚZIS CSV open data | In-memory LRU (~20MB), synonym dict |
| **nrpzs/** | 4 | ÚZIS CSV open data | In-memory list, diskcache raw CSV |
| **szv/** | 3 | MZ ČR Excel (openpyxl) | In-memory list, 1-day cache |
| **vzp/** | 2 | Via SUKL DrugIndex | Sdílí SUKL init |
| **workflows/** | 3 | Orchestrace ostatních | Žádný vlastní state |

### Registrace
Všech 23 v `czech_tools.py` přes `@mcp_app.tool()` s prefixem `czechmed_`. Tenké wrappery delegují na privátní `_function()`. SUKL tools mají `asyncio.wait_for()` timeout.

### Sdílená infrastruktura
- **diacritics.py**: NFD normalization → strip combining marks → lowercase. Použito všude.
- **response.py**: Dual output (`content` Markdown + `structuredContent` dict) dle FR-025.
- Všechny modules: module-level `None` sentinel → lazy async init → diskcache → in-memory.

## Diagram

```mermaid
graph TD
    CT[czech_tools.py<br/>23 registrations] --> SUKL[sukl/ 8 tools]
    CT --> MKN[mkn/ 4 tools]
    CT --> NRPZS[nrpzs/ 4 tools]
    CT --> SZV[szv/ 3 tools]
    CT --> VZP[vzp/ 2 tools]
    CT --> WF[workflows/ 3 tools]
    SUKL --> DI[DrugIndex singleton]
    MKN --> SYN[synonyms.py 130+ terms]
    WF --> DA[diagnosis_assistant]
    WF --> DP[drug_profile]
    WF --> RA[referral_assistant]
    DIA[diacritics.py] -.-> SUKL
    DIA -.-> MKN
    DIA -.-> NRPZS
    DIA -.-> SZV
```

[[czechhealthcare]]
