# Research: Fix Tool Failures

## R1: ArticleGetter — PubTator3 / Europe PMC

**Decision**: Přidat PMC ID support přes NCBI ID Converter API + opravit error handling
**Rationale**: PubTator3 i Europe PMC API fungují korektně. "Regrese" v kole 3 testování je pravděpodobně transientní chyba. PMC ID (`PMC11193658`) nikdy nebylo podporováno — test explicitně rejektuje. PubTator3 přijímá pouze PMID, Europe PMC přijímá DOI.
**Alternatives considered**:
- Přímé Europe PMC API pro PMC ID → nefunguje (Europe PMC vrací metadata, ne full text)
- Pouze PMID + DOI bez PMC → nesplní FR-001

**Implementace**:
1. `is_pmc_id()` detekce (regex `^PMC\d{7,8}$`)
2. `convert_pmc_to_pmid()` přes `https://pmc.ncbi.nlm.nih.gov/tools/idconv/api/v1/articles/`
3. PMC ID → konverze na PMID → PubTator3 flow
4. Robustnější error handling s fallback na Europe PMC při PubTator3 selhání

## R2: SZV (SearchProcedures / GetProcedureDetail)

**Decision**: Debug a opravit Excel download + parsing; přidat resilientní error handling
**Rationale**: SZV modul stahuje Excel z `https://szv.mzcr.cz/Vykon/Export/` a parsuje přes openpyxl. Kód je strukturálně správný — error handling existuje (`raise_for_status()` → error JSON). Server error v testovací zprávě naznačuje buď timeout při stahování, nebo chybu v Arcade wrapper vrstvě.
**Alternatives considered**:
- Statický SZV dataset místo live download → zbytečné, Excel export je stabilní
- Scraping SZV webu → křehčí než Excel export

**Klíčové konstanty**: `CZECH_HTTP_TIMEOUT=30s`, cache TTL=7 dní, ~5000 výkonů

## R3: NRPZS (GetProviderDetail)

**Decision**: Opravit lookup field — přidat IČO support vedle ZZ_misto_poskytovani_ID
**Rationale**: Modul hledá podle `ZZ_misto_poskytovani_ID` (facility location ID), ale uživatelé zadávají IČO. CSV má oba sloupce. Přidat multi-field lookup.
**Alternatives considered**:
- Pouze ZZ_misto_poskytovani_ID → uživatelé neznají interní ID
- Pouze IČO → jedno IČO může mít více pracovišť

**Implementace**: Rozšířit `_nrpzs_get()` o kaskádový lookup: IČO → ZZ_misto_poskytovani_ID → ZZ_nazev substring

## R4: DiagnosisAssist — Embedding Pipeline

**Decision**: Hybridní Symbolic + Embedding pipeline (dle clarifikace)
**Rationale**: Aktuální implementace používá keyword matching na MKN-10 názvech — prázdné výsledky, protože symptomy (bolest hlavy) se neshodují s diagnózami (cefalea). Embedding řeší sémantickou podobnost.
**Alternatives considered**:
- Keyword matching s mapovacím slovníkem → nízká kvalita pro neočekávané vstupy
- Plný LLM → závislost na externím modelu

**Nové závislosti**: `sqlite-vec` nebo `faiss-cpu`, embedding model API (Cohere embed-multilingual-light-v3.0 nebo lokální model)
**Fallback**: Pokud embedding nedostupný, keyword match jako degradovaný režim

## R5: OpenFDA RecallSearcher / RecallGetter

**Decision**: Query builder je korektní — problém je jinde (Arcade wrapper nebo transientní API issue)
**Rationale**: Live testy potvrzují funkčnost API. `openfda.brand_name:"metformin"` vrací 32 výsledků. Kód v `drug_recalls_helpers.py` správně konstruuje query. Recall number formát `D-0325-2021` funguje.
**Alternatives considered**:
- Změna query field names → nepotřebné, stávající jsou správné
- Přidání API key → OpenFDA funguje bez klíče (rate limit 240 req/min)

**Implementace**: Debug Arcade wrapper; přidat robustnější error handling a logging pro diagnostiku

## R6: DrugsProfile — Graceful Partial Return

**Decision**: Částečná data + indikátor nedostupnosti per sekce (dle clarifikace)
**Rationale**: Workflow závisí na `_resolve_sukl_code()` jako single point of failure. Paralelní fetch 4 sub-komponent přes `asyncio.gather(return_exceptions=True)` existuje, ale chybí graceful presentation.
**Alternatives considered**:
- All-or-nothing → ztráta dat při jednom selhání
- Retry → zvýšená latence

**Implementace**: Upravit výstupní formátování — každá sekce s `status: "ok"/"unavailable"/"error"`

## R7: CompareAlternatives

**Decision**: Opravit kaskádové selhání — VZP reimbursement → SUKL fallback
**Rationale**: Závisí na `_fetch_reimbursement()` která vrací `{}` při jakékoliv výjimce. Prázdný dict propaguje null pole. Navíc pokud drug detail nemá ATC kód, alternativy jsou prázdné.
**Implementace**: Graceful handling — vrátit alternativy i bez reimbursement dat; zobrazit "úhrada nedostupná" per alternativa

## R8: VZP / NZIP — Statický Dataset

**Decision**: Statický dataset z veřejných exportů (dle clarifikace)
**Rationale**: VZP reimbursement deleguje na SUKL — fields null když SUKL nemá data. NZIP hospitalization CSV z `https://reporting.uzis.cz/cr/data/hospitalizace_{year}.csv` — returns 0 když CSV nedostupné nebo diagnóza ne hospitalizovaná.
**Implementace**:
- VZP: Stáhnout úhradový seznam z `https://media.vzpstatic.cz/` → CSV → in-memory index
- NZIP: Ověřit URL, přidat fallback na statický dataset pokud CSV nedostupné

## R9: GetMedicineDetail — Substance Names + SPC/PIL

**Decision**: Přidat substance name lookup + validace SPC/PIL URL
**Rationale**: SUKL DLP API `/slozeni/{sukl_code}` vrací `kodLatky` (číslo) bez názvu. Substance names vyžadují separátní lookup. SPC/PIL URL se konstruují z metadata endpointu ale nevalidují se.
**Implementace**:
- Substance: SUKL DLP API `/latky/{kodLatky}` pro název (s cache)
- SPC/PIL: Validace URL existence před vrácením; pokud metadata prázdná → null s vysvětlením

## R10: VariantSearcher — Gene-Only Validace

**Decision**: Přidat pre-emptivní validaci v Pydantic modelu
**Rationale**: `VariantQuery` model povoluje gene-only query. MyVariant.info vrací obrovský payload pro gene=TP53 → timeout. Validace po faktu (v error handling) nestačí.
**Implementace**: `@model_validator` — pokud gene zadán bez hgvsp/rsid/region → raise `InvalidParameterError` s návodem

## R11: GetPerformanceMetrics — BIOMCP_METRICS_ENABLED

**Decision**: Změnit default na `true` nebo dokumentovat env var
**Rationale**: `@track_performance` je aplikován na 59/60 nástrojů, ale sběr je gated env var `BIOMCP_METRICS_ENABLED` (default `false`). Proto "No metrics collected yet" — není chyba kódu, je to konfigurace.
**Implementace**: Změnit default na `true`; přidat do dokumentace

## R12: DeviceGetter — MDR Key Format

**Decision**: Debug přesný formát MDR key mezi Searcher a Getter
**Rationale**: Oba query stejný endpoint. Searcher vrací výsledky s `mdr_report_key`. Getter přijímá tentýž klíč. Problém může být v Arcade wrapperu nebo v tom, že Searcher nevrací klíč v zobrazitelné formě.
**Implementace**: Přidat MDR key do Searcher výstupu explicitně; validovat v Getter
