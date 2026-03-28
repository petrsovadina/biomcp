---
color: orange
isContextNode: false
agent_name: Aki
status: claimed
---
# Router & Tool Registration

Registrace **60 MCP nástrojů** přes `@mcp_app.tool()` dekorátor, unified search/fetch dispatcher přes 21 domén, query parsing, parameter routing a domain-specific formatting.

**Root path:** `src/czechmedmcp/` — 10 souborů, **6 575 řádků celkem**

| Soubor | Řádky | Účel |
|--------|-------|------|
| `individual_tools.py` | 1 951 | 33 individuálních nástrojů (article, trial, variant, gene, drug, disease, enrichr, cbioportal, oncokb, NCI, OpenFDA) |
| `router_handlers.py` | 996 | 21 search handlerů + `SEARCH_HANDLERS` dispatch dict |
| `fetch_handlers.py` | 931 | 20 fetch handlerů + `FETCH_HANDLERS` dispatch dict |
| `router.py` | 821 | Unified `search()` + `fetch()` tools, `_unified_search()`, `format_results()` |
| `domain_handlers.py` | 630 | Result formatting — ArticleHandler, TrialHandler, VariantHandler atd. |
| `query_parser.py` | 464 | Unified query language parser (`gene:BRAF AND disease:melanoma`) |
| `query_router.py` | 402 | QueryRouter → RoutingPlan → parallel execution across domains |
| `parameter_parser.py` | 192 | JSON array / CSV / single-value normalizace parametrů |
| `thinking_tool.py` | 121 | Sequential thinking tool (REQUIRED first step) |
| `metrics_handler.py` | 67 | Performance metrics tool |

## Architektura registrace nástrojů

5 registračních bodů importovaných v `__init__.py`:
1. **`individual_tools.py`** — 33 nástrojů (article_searcher, trial_searcher, variant_searcher/getter, gene/drug/disease_getter, enrichr, cbioportal, oncokb, NCI ×4, OpenFDA ×6)
2. **`router.py`** — 2 unified nástroje (`search` + `fetch`)
3. **`thinking_tool.py`** — 1 tool (`think`)
4. **`metrics_handler.py`** — 1 tool (`get_performance_metrics`)
5. **`czech/czech_tools.py`** — 23 českých nástrojů (SUKL, MKN, NRPZS, SZV, VZP, diagnosis_assist, referral_assist)

## Search flow — dva režimy

### 1. Unified Query Mode (query bez domain)
```
query="gene:BRAF AND trials.phase:3"
→ QueryParser.parse() → ParsedQuery (terms + cross_domain_fields)
→ QueryRouter.route() → RoutingPlan (tools_to_call + field_mappings)
→ execute_routing_plan() → asyncio.gather (parallel across domains)
→ format per-domain via domain_handlers → unified results dict
```

### 2. Domain-Specific Mode (domain + params)
```
domain="article", genes=["BRAF"]
→ ParameterParser.parse_list_param() (JSON/CSV/single normalizace)
→ SEARCH_HANDLERS[domain]() → handler function v router_handlers.py
→ handler returns (items, total) nebo dict
→ format_results() → OpenAI MCP format {results: [{id, title, text, url}]}
```

### Fetch flow — auto-detection + dispatch
```
fetch(id="NCT04280705")
→ Auto-detect domain: NCT* → trial, numeric → article, rs* → variant
→ FETCH_HANDLERS[domain]() → handler function v fetch_handlers.py
→ Returns {id, title, text, url, metadata: {...}}
```

## 21 podporovaných domén
**Biomedicínské:** article, trial, variant, gene, drug, disease
**NCI:** nci_organization, nci_intervention, nci_biomarker, nci_disease
**OpenFDA:** fda_adverse, fda_label, fda_device, fda_approval, fda_recall, fda_shortage
**České:** sukl_drug, mkn_diagnosis, nrpzs_provider, szv_procedure, vzp_reimbursement

## Známé problémy / Tech debt
- `_unified_search()` v router.py má `# noqa: C901` — komplexní orchestrace s cBioPortal summary injection
- `search()` funkce má 30+ parametrů — boundary mezi unified a domain-specific mode je křehká
- Fetch auto-detection selhává pro gene/drug/disease ID — defaultuje na "article"
- `SEARCH_HANDLERS` má 21 entries vs `FETCH_HANDLERS` 20 entries (chybí nci_biomarker fetch)
- Lazy imports v handlerech (`from czechmedmcp.articles.search import ...`) — zamezuje circular imports ale zpomaluje first-call

[[welcome_to_voicetree]]
