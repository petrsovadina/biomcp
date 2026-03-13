# Feature Specification: CzechMedMCP Implementation

**Feature Branch**: `001-czechmedmcp-implementation`
**Created**: 2026-03-01
**Status**: Draft
**Input**: CzechMedMCP — rozšíření BioMCP forku o 23 nových českých zdravotnických nástrojů (8 SÚKL, 4 MKN-10, 3 NRPZS, 3 SZV, 2 VZP, 3 Workflow) integrovaných s 37 zděděnými BioMCP nástroji (33 individual + 2 router + 1 think + 1 metrics). Celkem 60 MCP nástrojů pro české lékaře v platformě Medevio (4000+ lékařů, 1M pacientů).

## Clarifications

### Session 2026-03-02

- Q: Vyžaduje samotný CzechMedMCP server autentizaci od klientů? → A: Autentizaci řeší Medevio API gateway. MCP server bez vlastní auth. Tři deployment režimy: (1) stdio mód (dev/demo) — žádná auth, (2) HTTP mód (Medevio produkce) — za gateway s auth/rate limiting/logging, (3) HTTP mód (standalone) — volitelný Bearer token z existujícího BioMCP auth.py jako opt-in basic protection.
- Q: Kolik současných sessions server očekává a jaký je concurrent model? → A: Bezstavový server, horizontální škálování přes gateway. Každá instance obsluhuje 50-100 req/s. Peak: 200 aktivních sessions (~6-7 req/s). Minimum pro produkci: 3 instance za load balancerem. In-memory data (MKN-10 ~20 MB, SZV ~5 MB) se načítají při startu každé instance. Disk cache sdílitelný přes shared volume ale ne vyžadovaný. ~50 MB RAM per instance.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Lékař vyhledává a zjišťuje informace o léku (Priority: P1)

Praktický lékař potřebuje vyhledat lék v české SÚKL databázi, získat kompletní detail přípravku, zkontrolovat jeho dostupnost na trhu a zjistit úhradové informace včetně doplatku pacienta. Toto je nejčastější denní workflow — při každém předpisu.

**Why this priority**: SÚKL nástroje (8 z 23) tvoří jádro systému. Informace o léku, dostupnosti a úhradě jsou základní potřebou 4000+ lékařů při každém předpisu. Blokuje workflow nástroje i porovnání alternativ.

**Independent Test**: Zadání názvu léku "ibuprofen" → vyhledání → výběr přípravku → detail → dostupnost → úhrada. Každý krok ověřitelný samostatně.

**Acceptance Scenarios**:

1. **Given** dotaz "ibuprofen", **When** lékař vyhledá lék, **Then** systém vrátí stránkovaný seznam registrovaných přípravků s názvem, SÚKL kódem, ATC kódem, formou a držitelem, s podporou diakritiky i bez ní
2. **Given** platný 7místný SÚKL kód, **When** lékař požádá o detail, **Then** systém vrátí kompletní informace včetně účinných látek, balení, registrace, generické klasifikace a referenčního přípravku
3. **Given** SÚKL kód přípravku, **When** lékař zkontroluje dostupnost, **Then** systém vrátí stav (available/shortage/withdrawn/suspended/unknown), datum posledního dodání a informaci o výpadku
4. **Given** SÚKL kód, **When** lékař požádá o úhradové informace, **Then** systém vrátí cenu výrobce, maximální maloobchodní cenu, výši úhrady pojišťovnou, doplatek pacienta v CZK a úhradovou skupinu
5. **Given** neexistující SÚKL kód, **When** lékař zadá neplatný kód, **Then** systém vrátí srozumitelnou chybovou zprávu

---

### User Story 2 - Lékař hromadně kontroluje dostupnost léků pacienta (Priority: P1)

Praktický lékař reviduje medikaci pacienta (typicky 5-15 léků) a potřebuje zkontrolovat dostupnost všech léků na trhu najednou. Aktuálně musí kontrolovat každý lék zvlášť.

**Why this priority**: Medikační review je denní workflow. Batch operace je předpoklad reálného nasazení pro 4000+ lékařů.

**Independent Test**: Zadání seznamu 5 SÚKL kódů → odpověď do 10 sekund se stavem každého léku.

**Acceptance Scenarios**:

1. **Given** seznam 1-50 platných SÚKL kódů, **When** lékař požádá o hromadnou kontrolu, **Then** systém vrátí stav dostupnosti pro každý lék s celkovým shrnutím (total_checked, available_count, shortage_count, error_count) — paralelní zpracování
2. **Given** seznam obsahující neexistující SÚKL kódy, **When** lékař požádá o kontrolu, **Then** systém vrátí výsledky pro platné kódy a zvýší error_count (partial failure tolerance)
3. **Given** seznam přesahující 50 kódů nebo prázdný, **When** lékař zadá nevalidní vstup, **Then** systém vrátí validační chybu

---

### User Story 3 - Lékař získává kompletní profil léku jedním dotazem (Priority: P1)

Nemocniční specialista potřebuje jedním dotazem získat kompletní profil léku — registrace, dostupnost, úhrada a relevantní PubMed evidence. Workflow orchestrace kombinující české a globální BioMCP zdroje.

**Why this priority**: Hlavní diferenciující funkce CzechMedMCP — propojení českých a globálních dat jedním voláním. Závisí na SÚKL nástrojích (Story 1) a BioMCP article_searcher.

**Independent Test**: Zadání názvu léku → kompletní profil se všemi sekcemi do 10 sekund.

**Acceptance Scenarios**:

1. **Given** název léčiva nebo účinné látky, **When** lékař požádá o kompletní profil, **Then** systém orchestruje: vyhledání přípravku → paralelně (detail + dostupnost + úhrada + PubMed články) → sestaví strukturovaný report
2. **Given** dotaz kde některé zdroje selžou, **When** lékař požádá o profil, **Then** systém vrátí dostupné sekce a u chybějících uvede důvod (graceful degradation)
3. **Given** neexistující přípravek, **When** systém nenajde odpovídající lék, **Then** vrátí informativní zprávu s návrhem alternativního dotazu

---

### User Story 4 - Lékař kóduje diagnózu a hledá evidenci (Priority: P1)

Praktický lékař zadá popis symptomů nebo český název nemoci a systém navrhne odpovídající MKN-10 kódy s hierarchií, inkluzemi/exkluzemi a relevantní PubMed evidencí.

**Why this priority**: MKN-10 nástroje (4 z 23) jsou druhé nejpoužívanější po SÚKL. Kódování diagnóz je povinné pro vykazování. Workflow orchestrace přidává PubMed evidenci.

**Independent Test**: Zadání "akutní zánět hltanu" → MKN-10 kódy s detaily → PubMed články. Offline MKN-10 vyhledávání < 100ms.

**Acceptance Scenarios**:

1. **Given** textový popis symptomů v češtině, **When** lékař vyhledá diagnózu, **Then** systém vrátí odpovídající MKN-10 kódy s českým i anglickým názvem, kapitolou, blokem a skóre shody — vyhledávání podporuje diakritiku i bez ní, trigram matching
2. **Given** MKN-10 kód, **When** lékař požádá o detail, **Then** systém vrátí kompletní hierarchii (parent/children/siblings), inkluze a exkluze
3. **Given** kód nadřazené úrovně nebo None, **When** lékař prochází klasifikaci, **Then** systém vrátí děti dané úrovně (kapitoly → bloky → 3místné → 4místné kódy) s informací o has_children
4. **Given** MKN-10 kód a volitelně rok, **When** lékař požádá o epidemiologické statistiky, **Then** systém vrátí počet případů, rozložení dle pohlaví, věku a krajů z NZIP dat
5. **Given** popis symptomů, **When** lékař použije diagnostickou asistenci (workflow), **Then** systém navrhne MKN-10 kódy s detaily a PubMed evidencí pro top diagnózu, s disclaimerem o podpůrném charakteru nástroje

---

### User Story 5 - Lékař hledá specialistu pro odeslání pacienta (Priority: P2)

Praktický lékař zadá diagnózu a město pacienta. Systém najde relevantní odbornost pro diagnózu a vyhledá poskytovatele v regionu s kontaktními údaji.

**Why this priority**: Kombinuje MKN-10 a NRPZS moduly. NRPZS nástroje (3 z 23) pokrývají vyhledávání poskytovatelů, detaily a číselníky. Workflow orchestrace přidává mapování diagnóza→odbornost.

**Independent Test**: Zadání MKN-10 kódu "I25.1" a města "Brno" → seznam kardiologů v Brně s kontakty.

**Acceptance Scenarios**:

1. **Given** město a volitelně odbornost/forma péče/druh péče, **When** lékař vyhledá poskytovatele, **Then** systém vrátí stránkovaný seznam s IČO, názvem, adresou, odbornostmi, kontakty a GPS souřadnicemi
2. **Given** IČO poskytovatele, **When** lékař požádá o detail, **Then** systém vrátí kompletní profil včetně všech pracovišť, oddělení a ordinačních hodin
3. **Given** typ číselníku (specialties/care_forms/care_types), **When** lékař požádá o číselník, **Then** systém vrátí kompletní seznam položek s kódy a názvy
4. **Given** MKN-10 kód a město, **When** lékař použije asistenta odeslání (workflow), **Then** systém zjistí relevantní odbornost z diagnózy, vyhledá poskytovatele v okolí a vrátí seřazený seznam s kontakty

---

### User Story 6 - Správce kliniky kalkuluje úhrady výkonů (Priority: P2)

Správce kliniky potřebuje vyhledat zdravotní výkon, zjistit jeho bodovou hodnotu a podmínky vykazování, a vypočítat korunovou úhradu s rozlišením podle pojišťovny.

**Why this priority**: SZV nástroje (3 z 23) pokrývají výkony — klíčové pro vykazování a ekonomiku klinik. Offline data (< 100ms latence).

**Independent Test**: Zadání kódu výkonu "09543" → detail s bodovou hodnotou → kalkulace úhrady pro VZP (kód 111).

**Acceptance Scenarios**:

1. **Given** kód výkonu nebo textový popis, **When** správce vyhledá výkon, **Then** systém vrátí seznam výkonů s kódem, názvem, body, odborností, frekvenčním limitem a časem — offline, < 100ms
2. **Given** 5místný kód výkonu, **When** správce požádá o detail, **Then** systém vrátí kompletní podmínky vykazování včetně omezení kombinací, věkových a pohlavních restrikcí, zahrnutého materiálu a historie bodové hodnoty
3. **Given** kód výkonu, kód pojišťovny (default VZP "111") a počet výkonů, **When** správce požádá o kalkulaci, **Then** systém vrátí body, sazbu za bod v CZK, jednotkovou cenu, celkovou úhradu a případný doplatek pacienta

---

### User Story 7 - Lékař porovnává cenové alternativy léku (Priority: P2)

Praktický lékař chce předepsat ekonomicky nejvhodnější variantu léku. Zadá referenční přípravek a systém najde alternativy ve stejné ATC skupině seřazené podle doplatku pacienta.

**Why this priority**: VZP nástroje (2 z 23) pokrývají úhrady a porovnání alternativ. Závisí na SÚKL a VZP datech. Vysoká hodnota pro cenově citlivé pacienty.

**Independent Test**: Zadání SÚKL kódu ibuprofenu → seznam alternativ seřazený dle doplatku s úsporou oproti referenčnímu přípravku.

**Acceptance Scenarios**:

1. **Given** SÚKL kód referenčního přípravku, **When** lékař požádá o VZP úhradové informace, **Then** systém vrátí úhradovou skupinu, maximální cenu, úhradu, doplatek, podmínky preskripce a platnost z VZP ceníků
2. **Given** SÚKL kód referenčního přípravku, **When** lékař požádá o porovnání alternativ, **Then** systém vrátí cross-module výsledek: alternativy ve stejné ATC skupině seřazené dle doplatku s informací o úspoře, generické klasifikaci a dostupnosti
3. **Given** přípravek bez alternativ v dané ATC skupině, **When** lékař požádá o porovnání, **Then** systém vrátí prázdný seznam alternativ s informací

---

### User Story 8 - Lékař přistupuje k příbalové informaci a SPC (Priority: P2)

Lékař potřebuje rychle nahlédnout do příbalové informace (PIL) nebo souhrnu údajů o přípravku (SPC) — celý dokument nebo konkrétní sekci (dávkování, kontraindikace, interakce).

**Why this priority**: PIL a SPC jsou profesionální dokumentace nezbytná pro klinické rozhodování. Doplňuje SÚKL detail o textovou dokumentaci.

**Independent Test**: Zadání SÚKL kódu + sekce "side_effects" → text dané sekce PIL.

**Acceptance Scenarios**:

1. **Given** SÚKL kód a volitelně sekce (dosage/contraindications/side_effects/interactions/pregnancy/storage), **When** lékař požádá o PIL, **Then** systém vrátí text požadované sekce nebo celý dokument se seznamem dostupných sekcí
2. **Given** SÚKL kód a volitelně číslo sekce SPC (4.1-4.9, 5.1-5.3, 6.1-6.6), **When** lékař požádá o SPC, **Then** systém vrátí profesionální text dané sekce se seznamem dostupných sekcí
3. **Given** SÚKL kód přípravku bez dostupného PIL/SPC, **When** lékař požádá o dokument, **Then** systém vrátí chybu s URL pro manuální přístup

---

### User Story 9 - Lékař hledá lékárnu v okolí (Priority: P3)

Praktický lékař potřebuje najít lékárny v okolí pacienta, případně filtrovat pouze nonstop lékárny.

**Why this priority**: Užitečný doplněk, ale lékárny lze najít i jinými cestami. Nejnižší priorita z nových nástrojů.

**Independent Test**: Zadání města "Praha" → seznam lékáren s adresami, telefony a otevírací dobou.

**Acceptance Scenarios**:

1. **Given** město nebo PSČ a volitelně filtr nonstop, **When** lékař hledá lékárny, **Then** systém vrátí stránkovaný seznam s názvem, adresou, telefonem, e-mailem, otevírací dobou a GPS souřadnicemi
2. **Given** alespoň město nebo PSČ musí být vyplněno, **When** lékař nezadá ani jedno, **Then** systém vrátí validační chybu
3. **Given** dotaz s diakritikou i bez, **When** lékař hledá, **Then** systém nalezne shodné výsledky

---

### Edge Cases

- **Česká diakritika**: Vyhledávání funguje s diakritikou i bez ní (unidecode normalizace + trigram matching). "léčivo" = "lecivo", case-insensitive
- **Prázdný vstup**: Prázdný řetězec nebo whitespace → prázdný výsledek, nikdy chyba
- **Nedostupnost API**: Každý nástroj při výpadku → cache fallback nebo bundled data → srozumitelná chybová zpráva, nikdy pád systému
- **Zastaralá data**: Odpovědi obsahují data_freshness datum pro trasparenci
- **Částečný výpadek ve workflow**: Orchestrační nástroje vrátí dostupné sekce i při selhání některých zdrojů (graceful degradation)
- **Neplatný formát kódu**: SÚKL kód musí být 7 číslic, MKN-10 musí odpovídat vzoru `^[A-Z]\d{2}(\.\d{1,2})?$`, kód výkonu 5 číslic, IČO 8 číslic, PSČ 5 číslic — validace přes Pydantic regex
- **Stránkování**: Všechny seznamové výsledky jsou stránkované (total_count, offset, limit, has_more, next_offset)
- **Rate limiting externích API**: SÚKL 5 req/s, NRPZS 3 req/s, VZP 2 req/s — circuit breaker s recovery
- **Změna HTML struktury VZP**: ParseError s URL pro manuální přístup (graceful degradation)

## Requirements *(mandatory)*

### Functional Requirements

**SÚKL — Databáze léčiv (8 nástrojů):**
- **FR-001**: Systém MUSÍ umožnit fulltextové vyhledávání léčiv podle názvu, účinné látky, SÚKL kódu nebo ATC kódu s podporou diakritiky a fuzzy matching
- **FR-002**: Systém MUSÍ vrátit kompletní detail léčivého přípravku podle 7místného SÚKL kódu včetně účinných látek, registrace a generické klasifikace
- **FR-003**: Systém MUSÍ kontrolovat reálnou dostupnost léčiva na trhu z distribučních dat SÚKL
- **FR-004**: Systém MUSÍ umožnit hromadnou kontrolu dostupnosti 1-50 přípravků najednou s paralelním zpracováním
- **FR-005**: Systém MUSÍ poskytovat úhradové informace k léčivu — cena výrobce, maloobchodní cena, úhrada pojišťovnou, doplatek pacienta
- **FR-006**: Systém MUSÍ zpřístupnit příbalovou informaci (PIL) celou nebo po sekcích
- **FR-007**: Systém MUSÍ zpřístupnit souhrn údajů o přípravku (SPC) celý nebo po sekcích
- **FR-008**: Systém MUSÍ vyhledávat lékárny podle města, PSČ nebo filtru nonstop provozu

**MKN-10 — Klasifikace nemocí (4 nástroje):**
- **FR-009**: Systém MUSÍ umožnit fulltextové vyhledávání diagnóz v MKN-10 klasifikaci s trigram matching a unidecode normalizací
- **FR-010**: Systém MUSÍ vrátit kompletní detail diagnózy včetně hierarchie, inkluzí a exkluzí
- **FR-011**: Systém MUSÍ umožnit procházení hierarchie MKN-10 po úrovních (kapitoly → bloky → 3místné → 4místné kódy)
- **FR-012**: Systém MUSÍ poskytovat epidemiologické statistiky diagnózy z NZIP open dat (případy, pohlaví, věk, regiony)

**NRPZS — Registr poskytovatelů (3 nástroje):**
- **FR-013**: Systém MUSÍ vyhledávat poskytovatele zdravotních služeb podle města, PSČ, odbornosti, formy péče a druhu péče
- **FR-014**: Systém MUSÍ vrátit kompletní profil poskytovatele podle IČO včetně všech pracovišť a oddělení
- **FR-015**: Systém MUSÍ poskytovat číselníky NRPZS (odbornosti, formy péče, druhy péče)

**SZV — Seznam zdravotních výkonů (3 nástroje):**
- **FR-016**: Systém MUSÍ vyhledávat zdravotní výkony podle kódu nebo popisu s filtrováním dle odbornosti
- **FR-017**: Systém MUSÍ vrátit kompletní detail výkonu včetně podmínek vykazování, kombinací a historie
- **FR-018**: Systém MUSÍ kalkulovat korunovou úhradu výkonu s rozlišením podle pojišťovny (VZP, VoZP, ČPZP, OZP, ZPŠ, ZPMV, RBP)

**VZP — Úhrady a pojišťovací pravidla (2 nástroje):**
- **FR-019**: Systém MUSÍ poskytovat detailní VZP úhradové informace k léku včetně podmínek preskripce
- **FR-020**: Systém MUSÍ porovnávat cenově dostupné alternativy léku ve stejné ATC skupině seřazené dle doplatku pacienta

**Workflow — Orchestrace (3 nástroje):**
- **FR-021**: Systém MUSÍ orchestrovat kompletní lékový profil: vyhledání → paralelně (detail + dostupnost + úhrada + PubMed evidence) → strukturovaný report s graceful degradation
- **FR-022**: Systém MUSÍ orchestrovat diagnostickou asistenci: vyhledání MKN-10 kódů → detaily top kandidátů → PubMed evidence pro primární diagnózu, s disclaimerem
- **FR-023**: Systém MUSÍ orchestrovat asistenci odeslání: diagnóza → mapování na odbornost → vyhledání poskytovatelů v regionu

**Průřezové požadavky:**
- **FR-024**: Všechny české nástroje MUSÍ sdílet prefix `czechmed_` v názvu
- **FR-025**: Všechny české nástroje MUSÍ vracet dual output — Markdown (content) pro čtení + JSON (structuredContent) pro strojové zpracování
- **FR-026**: Systém MUSÍ podporovat vyhledávání s českou diakritikou i bez ní napříč všemi nástroji
- **FR-027**: Systém MUSÍ cachovat odpovědi externích API s TTL strategií dle typu dat (5 min až 7 dní)
- **FR-028**: Systém MUSÍ zajistit graceful degradation při výpadku externích zdrojů — cache fallback, bundled data nebo srozumitelná chyba

### Key Entities

- **Lék (Medicine)**: SÚKL kód (7 číslic), název, účinné látky, ATC kód, forma, síla, balení, držitel, registrace, výdejnost, generická klasifikace
- **Dostupnost (Availability)**: SÚKL kód, stav (available/shortage/withdrawn/suspended/unknown), datum dodání, informace o výpadku
- **Úhrada (Reimbursement)**: SÚKL kód, cena výrobce, maloobchodní cena, úhrada pojišťovnou, doplatek pacienta, úhradová skupina, platnost
- **Diagnóza (Diagnosis)**: MKN-10 kód, český/anglický název, kapitola, blok, hierarchie (parent/children/siblings), inkluze, exkluze
- **Poskytovatel (Provider)**: IČO (8 číslic), název, adresa, pracoviště, oddělení, odbornosti, forma péče, kontakty, GPS
- **Zdravotní výkon (Procedure)**: Kód (5 číslic), název, bodová hodnota, odbornost, frekvenční limit, čas, podmínky vykazování
- **Lékárna (Pharmacy)**: Název, adresa, město, PSČ, kontakty, otevírací doba, nonstop příznak, GPS
- **Profil léku (Drug Profile)**: Agregace — registrace + dostupnost + úhrada + PubMed evidence (workflow output)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Celkový počet MCP nástrojů po implementaci dosáhne 60 (37 BioMCP + 23 českých včetně 3 workflow)
- **SC-002**: Lékař získá informaci o úhradě a doplatku léku do 2 sekund od dotazu
- **SC-003**: Hromadná kontrola dostupnosti 50 léků se dokončí do 10 sekund (paralelní zpracování)
- **SC-004**: Kompletní profil léku (workflow) je dostupný do 10 sekund včetně PubMed evidence
- **SC-005**: MKN-10 offline vyhledávání a browsing odpovídá do 100ms (in-memory data)
- **SC-006**: SZV offline vyhledávání a kalkulace odpovídá do 100ms (in-memory data)
- **SC-007**: Při výpadku externího zdroje systém vrátí odpověď (cache/bundled/chyba) v 100 % případů — žádný nástroj nezpůsobí pád
- **SC-008**: Vyhledávání funguje identicky s českou diakritikou i bez ní pro 100 % dotazů
- **SC-009**: Všechny nástroje vracejí dual output (Markdown + JSON structuredContent)
- **SC-010**: Systém dodržuje rate limity externích API (SÚKL 5/s, NRPZS 3/s, VZP 2/s) s circuit breakerem
- **SC-011**: Každá instance je bezstavová — horizontální škálování přidáním instancí za load balancer bez koordinace
- **SC-012**: Jedna instance zvládne 50-100 req/s; 3 instance pokryjí peak 200 současných sessions (4000 lékařů × 5% concurrency)

### Assumptions

- SÚKL Open Data API v1 (`opendata.sukl.cz/api/v1`) je primární datový zdroj pro léčiva, úhrady a lékárny; SÚKL web (`sukl.cz`) je fallback pro PIL/SPC (HTML scraping)
- NRPZS REST API (`nrpzs.uzis.cz/api`) je veřejné API dle OAS 2.0 specifikace
- MKN-10 data z ÚZIS ClaML XML + NZIP CSV jsou offline-first (~20 MB v RAM, TTL 7 dní)
- SZV data z MZ ČR CSV jsou offline-first (~5000 výkonů v RAM, TTL 7 dní)
- VZP ceníky jsou dostupné přes web scraping (`vzp.cz/poskytovatele`); HTML struktura se může měnit
- Bodová sazba za bod výkonu se liší podle pojišťovny; výchozí pro VZP (kód "111")
- Epidemiologické statistiky z NZIP Open Data CSV jsou dostupné za roky 2015-2025
- BioMCP article_searcher je plně funkční a využitelný v workflow orchestracích
- Platforma Medevio připojuje MCP server přes standardní MCP protokol; server je bezstavový — in-memory data (MKN-10, SZV) se načítají při startu, disk cache je sdílitelný přes shared volume ale ne vyžadovaný; ~50 MB RAM per instance
- Autentizaci řeší Medevio API gateway — MCP server neimplementuje vlastní auth. Tři režimy: stdio (bez auth), HTTP za gateway (auth/rate limiting/logging řeší gateway), HTTP standalone (volitelný Bearer token z BioMCP auth.py)
- NRPZS data poskytovatelů (adresy, telefony) jsou ze zákona veřejná — žádná PII pacientů serverem neprochází
- Všechny české zdroje jsou veřejné API bez autentizace
