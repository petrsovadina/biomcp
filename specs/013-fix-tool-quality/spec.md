# Feature Specification: Fix Tool Quality — E2E Test Report Bugs

**Feature Branch**: `013-fix-tool-quality`
**Created**: 2026-03-28
**Status**: Draft
**Input**: Kompletni systematicky testovaci report (58/60 nastroju, 27 BUGu, tema: E11 Diabetes + Metformin)
**Test Report**: Notion backup https://www.notion.so/331f7f27154d81c7bde4f5cd76ff6559

## Overview

Kompletni E2E testovani CzechMed-MCP serveru odhalilo 27 bugu ruzne zavaznosti. Celkove skore serveru je 4.9/10 — 48% nastroju je production-ready, 31% funguje s vyhradami, 21% je nefunkcnich. Tato specifikace pokryva opravu vsech identifikovanych problemu s prioritizaci dle klinickeho dopadu a pouzitelnosti.

**Klicova statistika z testu:**
- 7 CRITICAL bugu (BUG-1 az BUG-7)
- 8 HIGH bugu (BUG-8 az BUG-15)
- 8 MEDIUM bugu (BUG-16 az BUG-23)
- 4 LOW bugu (BUG-24 az BUG-27)

## User Scenarios & Testing

### User Story 1 - SUKL nastroje odpovidaji v prijatelnem case (Priority: P1)

Lekar nebo AI copilot pouziva SUKL nastroje (`czechmed_search_medicine`, `czechmed_get_medicine_detail`, `czechmed_get_drug_reimbursement`, `czechmed_compare_alternatives`) a ocekava odpoved do 10 sekund. Aktualne latence dosahuji 4-14 minut, coz je zcela nepouzitelne.

**Why this priority**: SUKL performance je nejkritictejsi problem — ovlivnuje 5 BUGu (BUG-3, BUG-4, BUG-5, BUG-7) a blokuje pouziti vsech SUKL-zavislych nastroju vcetne `czechmed_drug_profile` a `czechmed_compare_alternatives`. Bez opravy je cela ceska farmaceuticka cast serveru nepouzitelna.

**Independent Test**: Zavolat `czechmed_search_medicine("Metformin")` a overit, ze odpoved prijde do 10 sekund. Zavolat `czechmed_compare_alternatives("0011114")` a overit, ze nevisne.

**Acceptance Scenarios**:

1. **Given** uzivatel hleda lek pomoci `czechmed_search_medicine`, **When** zada "Metformin", **Then** odpoved prijde do 10 sekund s relevantnimi vysledky
2. **Given** uzivatel ziska detail leku pomoci `czechmed_get_medicine_detail`, **When** zada SUKL kod, **Then** odpoved prijde do 10 sekund
3. **Given** uzivatel hleda uhradova data pomoci `czechmed_get_drug_reimbursement`, **When** zada SUKL kod, **Then** bud vrati data do 10 sekund, nebo jasnou chybovou zpravu (ne tichy timeout)
4. **Given** uzivatel porovnava alternativy pomoci `czechmed_compare_alternatives`, **When** zada SUKL kod, **Then** odpoved prijde do 30 sekund nebo vrati jasnou chybovou zpravu

---

### User Story 2 - Unified search() wrapper vraci relevantni vysledky (Priority: P1)

AI agent pouziva `search(domain="trial", query="metformin type 2 diabetes")` a ocekava klinicke studie o metforminu a T2DM. Aktualne dostava ECMO, testikulorni torzi a sarcopenii — query je zcela ignorovano.

**Why this priority**: `search()` je primarni vstupni bod pro AI agenty. Nefunkcni query routing znamena, ze agent dostava aktivne zavadejici data bez varovani. Navic `thinking-reminder` injection jako datovy zaznam matouci pro vsechny LLM konzumenty.

**Independent Test**: Zavolat `search(domain="trial", query="metformin")` a overit, ze vsechny vysledky obsahuji "metformin" v nazvu nebo popisu. Overit, ze prvni zaznam neni `thinking-reminder`.

**Acceptance Scenarios**:

1. **Given** agent hleda klinicke studie, **When** zada `search(domain="trial", query="metformin type 2 diabetes")`, **Then** vsechny vysledky se tykaji metforminu a/nebo T2DM
2. **Given** agent hleda v jakekoli domene, **When** zavola `search()`, **Then** `thinking-reminder` neni soucasti pole vysledku
3. **Given** agent hleda MKN-10 diagnozy, **When** zada `search(domain="mkn_diagnosis", query="E11")`, **Then** vrati E11 a subkategorie (shodne s primym toolem)

---

### User Story 3 - Diagnosis assist vraci klinicky relevantni diagnozy (Priority: P1)

Lekar zada symptomy "zizen, caste moceni, unava, vysoky krevni cukr" do `czechmed_diagnosis_assist` a ocekava E11 (Diabetes mellitus 2. typu) v top vysledcich. Aktualne dostava C84 (Lymfom) — potencialne nebezpecny klinicky bug.

**Why this priority**: V regulovanem zdravotnickem prostredi je navrh zcela irelevantni diagnozy (hematoonkologie misto endokrinologie) potencialne nebezpecny. Tento bug blokuje produkci cele `czechmed_diagnosis_assist` funkcionality.

**Independent Test**: Zavolat `czechmed_diagnosis_assist("zizen, caste moceni, unava, vysoky krevni cukr")` a overit, ze E11 je v top-5 vysledcich.

**Acceptance Scenarios**:

1. **Given** uzivatel zada klasickou triadu diabetickych symptomu, **When** zavola `czechmed_diagnosis_assist`, **Then** E11 (Diabetes mellitus 2. typu) je v top-3 vysledcich
2. **Given** uzivatel zada symptomy, **When** dostane vysledky, **Then** zadna z navrhovanych diagnoz neni z zcela nesouvisejicho oboru (napr. onkologie pro metabolicke symptomy)
3. **Given** uzivatel zada ceske hovorove symptomy, **When** zavola `czechmed_diagnosis_assist`, **Then** system rozpozna klinicky relevantni kody

---

### User Story 4 - Drug getter akceptuje nazvy leku (Priority: P2)

Vyzkumnik zada `drug_getter("metformin")` a ocekava informace o metforminu. Aktualne dostava "Drug: Unknown" — funguje pouze DrugBank ID (`drug_getter("DB00331")`).

**Why this priority**: Vetsina uzivatelu nezna DrugBank ID. Name-based lookup je zakladni ocekavani pro lekovy nastroj. Tento bug ovlivnuje i `fetch(domain="drug")` wrapper.

**Independent Test**: Zavolat `drug_getter("metformin")` a overit, ze vrati informace o metforminu (ATC A10BA02, ChEMBL1431).

**Acceptance Scenarios**:

1. **Given** uzivatel hleda lek podle nazvu, **When** zada `drug_getter("metformin")`, **Then** vrati kompletni informace o metforminu
2. **Given** uzivatel hleda lek podle DrugBank ID, **When** zada `drug_getter("DB00331")`, **Then** vrati stejne informace (zpetna kompatibilita)
3. **Given** uzivatel zada neexistujici nazev, **When** zavola `drug_getter("neexistujicilekxyz")`, **Then** vrati srozumitelnou chybovou zpravu

---

### User Story 5 - Article searcher spravne kombinuje preprints a PubMed (Priority: P2)

Vyzkumnik hleda clanky s `include_preprints=true` a ocekava mix PubMed peer-reviewed clanku a Europe PMC preprintu. Aktualne PubMed vysledky zcela zmizi a vrati se pouze preprints.

**Why this priority**: Literarni reserse je jedna z nejcastejsich use case. Ztrata peer-reviewed vysledku pri zapnuti preprintu je kriticka chyba pro vedeckou praxi.

**Independent Test**: Zavolat `article_searcher(chemicals="metformin", diseases="type 2 diabetes", include_preprints=true)` a overit, ze vysledky obsahuji jak peer-reviewed clanky (s PMID), tak preprints.

**Acceptance Scenarios**:

1. **Given** uzivatel hleda s `include_preprints=true`, **When** zavola `article_searcher`, **Then** vysledky obsahuji jak PubMed clanky, tak Europe PMC preprints
2. **Given** uzivatel nastavi `page_size=3`, **When** zavola `article_searcher`, **Then** vrati maximalne 3 vysledky
3. **Given** uzivatel ziska PMID pres searcher, **When** zavola `article_getter(PMID)`, **Then** vrati kompletni abstrakt (ne placeholder "Article: XXXXX")

---

### User Story 6 - Ceske registry vracejici chybejici data (Priority: P2)

Lekar hleda lekarny v Brne, PIL/SPC dokumenty a uhradova data pro bezne leky. Aktualne vsechny tyto nastroje vracejici prazdne vysledky nebo chyby.

**Why this priority**: Lekarny, PIL/SPC a uhradova data jsou klicove pro ceskou zdravotnickou praxi. Bez nich je ceska cast serveru neuplna.

**Independent Test**: Zavolat `czechmed_find_pharmacies(city="Brno")` a overit, ze vrati alespon 1 lekarnu. Zavolat `czechmed_get_pil("0011114")` a overit dostupnost.

**Acceptance Scenarios**:

1. **Given** uzivatel hleda lekarny, **When** zada `czechmed_find_pharmacies(city="Brno")`, **Then** vrati seznam lekaren v Brne
2. **Given** uzivatel hleda PIL dokument, **When** zada `czechmed_get_pil` s validnim SUKL kodem, **Then** bud vrati dokument, nebo jasne uvede duvod nedostupnosti
3. **Given** uzivatel hleda uhradova data, **When** zada `czechmed_get_reimbursement` pro hrazeny lek, **Then** vrati uhradove informace
4. **Given** uzivatel hleda statistiky diagnoz, **When** zada `czechmed_get_diagnosis_stats("E11")`, **Then** vrati epidemiologicka data

---

### User Story 7 - FDA a dalsi minor fixy (Priority: P3)

Opravy mensich bugu: OpenFDA recall getter vraci spatny recall, device searcher ma slaby filtering, MKN-10 search chybi ceska synonyma, variant search ma spatne coordinates.

**Why this priority**: Tyto bugy snizuji kvalitu, ale neblokuji zakladni funkcionalitu.

**Independent Test**: Zavolat `openfda_recall_getter("D-0328-2025")` a overit, ze vrati recall pro Glenmark metformin (ne progesterone).

**Acceptance Scenarios**:

1. **Given** uzivatel hleda konkretni FDA recall, **When** zada recall cislo, **Then** vrati spravny recall (ne jiny)
2. **Given** uzivatel hleda diagnozu cesky, **When** zada "cukrovka", **Then** vrati E10/E11
3. **Given** uzivatel hleda diagnozu "diabetes", **When** dostane vysledky, **Then** E11 (T2DM) je pred E10 (T1DM)

---

### Edge Cases

- Co se stane pri SUKL API nedostupnosti? System musi vracet jasnou chybovou zpravu do 10 sekund, ne viset.
- Co se stane pri concurrent volanich na DrugIndex? Singleton s async lock musi korektne serialized pristupy.
- Co kdyz MyChem.info name lookup vrati vice DrugBank ID pro jeden nazev? Pouzit prvni vysledek s nejvyssim skore.
- Co kdyz ClinicalTrials.gov API zmeni format odpovedi? Graceful error handling s logem.
- Co kdyz NZIP CSV zmeni URL nebo format? Vracet posledni dostupna data s upozornenim na stari.

## Requirements

### Functional Requirements

#### P0 — CRITICAL (BUG-1 az BUG-7)

- **FR-001**: System MUST mit maximalni dobu odezvy 10 sekund na vsechna SUKL API volani — pri prekroceni vrati chybovou zpravu
- **FR-002**: System MUST mit ochranu proti viseni na SUKL endpointy — po 2 po sobe jdoucich selhanich docasne preskoci endpoint
- **FR-003**: System MUST predavat uzivateluv dotaz do ClinicalTrials.gov pri hledani klinickych studii
- **FR-004**: System MUST zajistit, ze vysledky hledani klinickych studii odpovidaji zadanemu dotazu
- **FR-005**: System MUST nezarazovat interni UX pripominek (thinking-reminder) do pole datovych vysledku
- **FR-006**: System MUST vracet E11 v top-5 vysledcich diagnostickeho asistenta pro symptomy polydipsie + polyurie + hyperglykemie
- **FR-007**: System MUST neprodukovat diagnozy z nesouvisejicich oboru (napr. onkologie pro metabolicke symptomy)

#### P1 — HIGH (BUG-8 az BUG-15)

- **FR-008**: System MUST podporovat vyhledavani leku podle nazvu (ne jen podle databazoveho ID)
- **FR-009**: System MUST zachovat zpetnou kompatibilitu s vyhledavanim leku podle ID
- **FR-010**: System MUST vracet uhradove informace pro leky, ktere jsou hrazeny ze zdravotniho pojisteni
- **FR-011**: System MUST pri nedostupnosti PIL dokumentu vracet konkretni duvod nedostupnosti
- **FR-012**: System MUST pri nedostupnosti SPC dokumentu vracet konkretni duvod nedostupnosti
- **FR-013**: System MUST vracet seznam lekaren pro ceska mesta
- **FR-014**: System MUST pri zapnuti preprintu kombinovat PubMed a Europe PMC vysledky (ne nahrazovat)
- **FR-015**: System MUST pro clanky neindexovane v PubTator3 poskytnout abstrakt z alternativniho zdroje

#### P2 — MEDIUM (BUG-16 az BUG-23)

- **FR-016**: System MUST pri hledani konkretniho FDA recallu vracet recall odpovidajici zadanemu cislu
- **FR-017**: System MUST pouzivat aktualni zdroj epidemiologickych dat pro diagnozy
- **FR-018**: System MUST vracet anglicke nazvy diagnoz kdyz jsou dostupne
- **FR-019**: System MUST respektovat uzivateluv pozadavek na pocet vysledku pri hledani clanku
- **FR-020**: System MUST pri hledani MKN-10 diagnoz pres unified wrapper vracet vysledky shodne s primym nastrojem
- **FR-021**: System MUST pri hledani leku pres unified wrapper vracet zaznamy s nazvy a popisy
- **FR-022**: System MUST pri hledani FDA labelu filtrovat podle nazvu leku v dotazu

#### P3 — LOW (BUG-24 az BUG-27)

- **FR-023**: System SHOULD podporovat ceska hovorova synonyma pri hledani diagnoz (napr. "cukrovka" -> E11)
- **FR-024**: System SHOULD radit prevalentnější diagnozy vyse (E11 pred E10 pro "diabetes")
- **FR-025**: System SHOULD presneji filtrovat zdravotnicke prostredky podle nazvu
- **FR-026**: System SHOULD pri hledani variant vracet vysledky na spravnem chromozomu

### Key Entities

- **SUKL DrugIndex**: In-memory index 68K kodu, cold start zabira minuty kvuli budovani indexu ze SUKL DLP API
- **ClinicalTrials.gov API**: Verejne dostupne REST API pro klinicke studie
- **MyChem.info**: Verejne dostupne REST API pro name-to-ID resolution leku
- **NRPZS**: Cesky registr poskytovatelu zdravotnich sluzeb
- **PubTator3**: NLM anotacni sluzba — ne vsechny PMIDy indexovany

## Success Criteria

### Measurable Outcomes

- **SC-001**: Vsechna SUKL volani odpovidaji do 30 sekund nebo vraceji jasnou chybovou zpravu
- **SC-002**: Hledani klinickych studii vraci vysledky relevantni zadanemu dotazu — alespon 80% vysledku obsahuje klicova slova
- **SC-003**: Diagnosticky asistent vraci E11 v top-5 pro klasicke diabeticke symptomy
- **SC-004**: Lekovy nastroj uspesne vraci data pro alespon 10 nejbeznejsich leku podle nazvu
- **SC-005**: Hledani clanku s preprints=true vraci mix peer-reviewed + preprintu
- **SC-006**: Parametr pro pocet vysledku je respektovan pri hledani clanku
- **SC-007**: Interni UX pripominka se neobjevuje v poli vysledku
- **SC-008**: Celkovy pocet production-ready nastroju stoupne z 28 (48%) na alespon 40 (67%)
- **SC-009**: Pocet kriticke zavaznosti bugu klesne z 7 na 0
- **SC-010**: Vsech 60 nastroju serveru zustane funkcionalnich (regresni test)

## Assumptions

- SUKL DLP API ma stabilni endpointy — vysoky latence jsou zpusobeny DrugIndex cold start, ne API nedostupnosti
- MyChem.info query endpoint je verejne dostupny bez API klice
- ClinicalTrials.gov API podporuje full-text search pres query parametr
- NRPZS API ma endpoint pro lekarny — je treba najit spravny filter
- PubMed E-utilities jsou dostupne jako fallback pro abstrakty
- Ceska synonyma pro MKN-10 diagnozy lze pokryt slovnikem s ~50-100 terminy

## Non-Goals

- Zmena architektury serveru (zustava FastMCP)
- Pridavani novych nastroju
- Zmena deployment infrastruktury (Railway, Arcade)
- Oprava NCI toolsu (vyzaduji externi API klic — mimo scope)
- Oprava alphagenome_predictor (vyzaduje DeepMind API klic — mimo scope)
- Kompletni rewrite search() wrapperu — opravujeme jen identifikovane bugy

## Risk Assessment

| Risk | Pravdepodobnost | Dopad | Mitigace |
|------|-----------------|-------|----------|
| SUKL DrugIndex cold start nelze zkratit pod 30s | Vysoka | Vysoky | Background prebuild + progress indicator |
| NRPZS API nema endpoint pro lekarny | Stredni | Stredni | Alternativni zdroje (OpenStreetMap, Google Places) |
| NZIP data source je permanentne nedostupny | Stredni | Nizky | Staticka data z posledniho dostupneho roku |
| PubTator3 fallback pridava latenci | Nizka | Nizky | Fallback jen pro neindexovane PMIDs |

## Bug Reference Map

| Bug ID | Priorita | User Story | FR | Nastroj |
|--------|----------|------------|-----|---------|
| BUG-1 | CRITICAL | US-2 | FR-003, FR-004 | search(domain="trial") |
| BUG-2 | CRITICAL | US-2 | FR-005 | search() vsechny domeny |
| BUG-3 | CRITICAL | US-1 | FR-001 | czechmed_search_medicine |
| BUG-4 | CRITICAL | US-1 | FR-001 | czechmed_get_medicine_detail |
| BUG-5 | CRITICAL | US-1 | FR-001 | czechmed_get_drug_reimbursement |
| BUG-6 | CRITICAL | US-3 | FR-006, FR-007 | czechmed_diagnosis_assist |
| BUG-7 | CRITICAL | US-1 | FR-002 | czechmed_compare_alternatives |
| BUG-8 | HIGH | US-4 | FR-008, FR-009 | drug_getter |
| BUG-9 | HIGH | US-6 | FR-010 | czechmed_get_reimbursement |
| BUG-10 | HIGH | US-6 | FR-011 | czechmed_get_pil |
| BUG-11 | HIGH | US-6 | FR-012 | czechmed_get_spc |
| BUG-12 | HIGH | US-6 | FR-013 | czechmed_find_pharmacies |
| BUG-14 | HIGH | US-5 | FR-014 | article_searcher(preprints=true) |
| BUG-15 | HIGH | US-5 | FR-015 | article_getter |
| BUG-16 | MEDIUM | US-7 | FR-016 | openfda_recall_getter |
| BUG-17 | MEDIUM | US-6 | FR-017 | czechmed_get_diagnosis_stats |
| BUG-18 | MEDIUM | US-6 | FR-018 | czechmed_get_diagnosis_detail |
| BUG-19 | MEDIUM | US-5 | FR-019 | article_searcher(page_size) |
| BUG-20 | MEDIUM | US-2 | FR-020 | search(domain="mkn_diagnosis") |
| BUG-21 | MEDIUM | US-2 | FR-021 | search(domain="drug") |
| BUG-23 | MEDIUM | US-2 | FR-022 | search(domain="fda_label") |
| BUG-24 | LOW | US-7 | FR-023 | czechmed_search_diagnosis |
| BUG-25 | LOW | US-7 | FR-024 | czechmed_search_diagnosis |
| BUG-26 | LOW | US-7 | FR-025 | openfda_device_searcher |
| BUG-27 | LOW | US-7 | FR-026 | search(domain="variant") |
