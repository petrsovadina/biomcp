# findings.md — CzechMedMCP Gap Analysis

## Aktuální stav vs. specifikace v2.1

### Stav nástrojů (tools)

| Oblast | Aktuální | Cíl (spec) | Gap |
|--------|----------|------------|-----|
| **BioMCP globální** | 37 (33 individual + 2 router + 1 think + 1 metrics) | 36 | Spec nepočítá metrics_handler |
| **Czech SUKL** | 5 (search, getter, spc, pil, availability) | 8 (+batch_availability, +reimbursement, +find_pharmacies) | **+3 nové** |
| **Czech MKN-10** | 3 (search, get, browse) | 4 (+diagnosis_stats) | **+1 nový** |
| **Czech NRPZS** | 2 (search, get) | 3 (+codebooks) | **+1 nový** |
| **Czech SZV** | 2 (search, get) | 3 (+calculate_reimbursement) | **+1 nový** |
| **Czech VZP** | 2 (search, get) | 2 (+compare_alternatives, spec říká 2 ale popisuje 3) | **+1 nový** |
| **Workflow** | 0 | 3 (drug_profile, diagnosis_assist, referral_assist) | **+3 nové** |
| **CELKEM** | 51 | 60+ | **+10 nových nástrojů** |

### Kritické problémy z live testingu (2026-02-26)

1. **SUKL search nevrací `sukl_code`** — API vrací výsledky ale pole sukl_code je prázdné, takže getter/SPC/PIL/availability chain je nefunkční
2. **MKN-10 data se nenačítají** — ClaML XML soubory nejsou automaticky načteny při startu serveru
3. **NRPZS API vrací 404** — `nrpzs.uzis.cz/api/v1` endpoint nefunguje
4. **SZV procedury vrací 0 výsledků** — buď chybí data soubory nebo API je mimo provoz
5. **VZP codebooks vrací 0 výsledků** — stejný problém jako SZV
6. **NCI nástroje vyžadují API klíč** — `NCI_API_KEY` env var chybí (4 nástroje)

### Architektonické mezery

1. **Czech domény chybí v `router.py`** — `constants.py:VALID_DOMAINS` neobsahuje české domény → unified `search()` a `fetch()` je nepodporují
2. **Czech handlery chybí v `domain_handlers.py`** — žádný český handler pro formátování výsledků
3. **Czech moduly nepoužívají `http_client.request_api()`** — používají `httpx.AsyncClient` přímo, obcházejí circuit breaker a retry

### Spec vs. realita — nesrovnalosti

| Bod ve specifikaci | Realita | Dopad |
|--------------------|---------|-------|
| Přejmenování na `czechmedmcp` | Package je `biomcp`, 100+ importů | **NEDOPORUČUJI** — příliš destruktivní, rozbije upstream sync |
| `lxml` + `unidecode` jako nové deps | `lxml` i `unidecode` **už jsou v pyproject.toml** | Žádný — splněno |
| Spec říká 36 BioMCP nástrojů | Máme 37 (spec nepočítá `get_performance_metrics`) | Kosmetické |
| `core.py` přejmenování serveru | Aktuálně `"BioMCP"` | Nízká priorita — 1 řádek |
| Workflow nástroje | Neexistují | Střední priorita — závisí na funkčních českých API |

### Datové zdroje — stav připravenosti

| Zdroj | Stav | Akce potřebná |
|-------|------|---------------|
| SUKL Open Data | Endpoint existuje, ale API vrací neúplná data | Analyzovat API response, opravit mapping polí |
| MKN-10 ClaML XML | Soubory existují v `data/` ale nenačítají se | Opravit parser inicializaci |
| NRPZS REST API | 404 | Najít nový endpoint nebo fallback |
| SZV (MZ ČR CSV) | Prázdné odpovědi | Ověřit CSV soubory v `data/` |
| VZP ceníky | Prázdné odpovědi | Ověřit zdroj dat |
| PubMed/ClinicalTrials | Funkční | Žádná |
| OpenFDA | Funkční (správné parametry: `drug`, `name`, `device`) | Žádná |
| MyVariant/MyGene | Funkční | Žádná |

### Rizika

1. **Externí API nestabilita** — NRPZS, SZV, VZP se mohou kdykoliv změnit
2. **SUKL scraping** — PIL/SPC závisí na HTML struktuře prehledy.sukl.cz
3. **Upstream divergence** — čím víc měníme existující soubory, tím hůře se merguje
4. **Package rename** — pokud se provede, rozbije všechny existující integrace
