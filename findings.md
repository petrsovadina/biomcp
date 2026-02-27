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

---

## MZ ČR Atlassian Wiki — Klíčové nálezy (2026-02-26)

> Zdroj: https://mzcr.atlassian.net/wiki/spaces

### Nalezené spaces

| Space | Název | Relevance |
|-------|-------|-----------|
| **EPZS** | Manuál EZ pro PZS | **KLÍČOVÝ** — 50 stránek s API dokumentací |
| **RS** | Registr Standardů | Prázdný (ve vývoji) |
| **RSTP** | Registr standardů – testovací prostředí | Testovací |
| **EZTEST** | EZ test | 7 stránek, interní testování |

### Nový eHealth ekosystém MZ ČR (CSEZ)

MZ ČR provozuje **centrální eHealth API gateway** — zcela nový systém nahrazující staré NRPZS/UZIS endpointy:

| Prostředí | Base URL |
|-----------|----------|
| **Test (T2)** | `https://gwy-ext-sec-t2.csez.cz/` |
| **Produkce** | `https://api.csez.gov.cz/` |
| **JWT Token (test)** | `https://jsuint-auth-t2.csez.cz/connect/token` |
| **JWT Token (prod)** | `https://jsuint-auth-ez.csez.cz/connect/token` |

**Autentizace:** Certifikát registrovaný přes EZCA II + JWT assertion (RS256). Client ID formát: `<IČO>_<CN>` nebo `<IČO>_SHA256(der)`.

### Dostupné služby na API gateway

| Služba | Path (test i prod) | Relevance pro CzechMedMCP |
|--------|---------------------|---------------------------|
| **KRPZS** (Registr poskytovatelů) | `/krpzs/` | **NAHRAZUJE naši NRPZS** |
| **Terminologický server** | `/terminologie/` (test) `/termx-fhir/` (prod) | **MKN-10, ATC, SNOMED** |
| KRP (Registr pacientů) | `/krp/` | Ne — vyžaduje registraci PZS |
| KRZP (Registr prac.) | `/krzp/` | Ne |
| Dočasné úložiště | `/docasneUloziste/` | Ne |
| eŽádanky | `/eZadanky/` | Ne |
| Notifikace | `/notifikace/` | Ne |
| Registr oprávnění | `/registrOpravneni/` | Ne |
| Sdílený zdravotní záznam | `/sdilenyZdravotniZaznam/` | Ne |

### KRPZS API — Swagger specifikace (nový NRPZS)

**Swagger soubor:** `KZR_KRPZS_PZS_swagger.json` (35 KB)

**Endpointy:**

| Metoda | Path | Popis |
|--------|------|-------|
| POST | `/api/v1/Poskytovatel/hledat/{zadostId}/ico` | Hledání poskytovatele podle IČO |
| POST | `/api/v1/Poskytovatel/hledat/{zadostId}/misto` | Hledání podle místa (kraj) |
| POST | `/api/v1/Poskytovatel/hledat/{zadostId}/nazev` | Hledání podle názvu |
| POST | `/api/v1/Poskytovatel/reklamuj/{zadostId}/udaj` | Reklamace údajů |
| POST | `/api/v1/Poskytovatel/nastavit/{zadostId}/urlpronotifikace` | Nastavení notifikačního URL |

**Klíčové modely:**
- `PoskytovatelZdravotnichSluzeb` — název, adresa, kontakty, typ, oprávnění
- `VerejneUdajePZS` — IČO, veřejné kontakty, oprávnění
- `KZROdpoved` — base response s `odpovedId`, `zadostId`, `stav`, chyby

**PROBLÉM:** API vyžaduje certifikát + JWT. Není veřejně přístupné bez registrace u CSEZ.

### Terminologický server (NTS) — Zdroj MKN-10

**Web rozhraní (T2):** `https://termx-web-t2-pub.csez.cz/landing`
**FHIR API (T2):** `https://termx-api-t2-pub.csez.cz/fhir`
**Swagger:** `https://termx-swagger-web-t2-pub.csez.cz/swagger/?urls.primaryName=termx-fhir`
**Přístup:** Guest role, ale vyžaduje institucionální certifikát

**FHIR operace dostupné:**
- `CodeSystem/$lookup` — detail kódu (MKN-10, ATC, SNOMED)
- `CodeSystem/$validate-code` — ověření kódu
- `CodeSystem/$subsumes` — hierarchické vztahy
- `ValueSet/$expand` — rozbalení sady hodnot
- `ValueSet/$validate-code` — validace proti sadě
- `ConceptMap/$translate` — překlad mezi systémy

**Swagger soubor:** `terminologicky_server_fhir_swagger.yml` (56 KB)

**Produkční NTS plánován od 1.1.2026.**

### Dopad na CzechMedMCP

| Modul | Současný stav | Nový zdroj z CSEZ | Proveditelnost |
|-------|---------------|-------------------|----------------|
| **NRPZS** | API 404 | KRPZS na `api.csez.gov.cz/krpzs/` | **Vyžaduje certifikát** — nelze bez registrace |
| **MKN-10** | XML se nenačítá | NTS FHIR `CodeSystem/$lookup` | **Vyžaduje certifikát** — alternativně embed XML |
| **SZV** | NZIP 0 výsledků | Není na CSEZ | Zůstává problém — CSV fallback |
| **VZP** | API 404 | Není na CSEZ | Zůstává problém — hledat jiný zdroj |

### Klíčový závěr

CSEZ gateway je **budoucnost českého eHealth**, ale vyžaduje **institucionální certifikát a registraci**. Pro CzechMedMCP to znamená:

1. **Krátkodobě (teď):** Opravit SUKL (kódový bug) + MKN-10 (embed XML) + graceful degradation pro NRPZS/SZV/VZP
2. **Střednědobě (Medevio integrace):** Medevio jako PZS může získat certifikát a přistupovat ke KRPZS a NTS
3. **Dlouhodobě:** Plná integrace s CSEZ gateway jako primární zdroj dat
