# Feature Specification: Oprava selhávajících MCP nástrojů dle testovací zprávy v2

**Feature Branch**: `011-fix-tool-failures`
**Created**: 2026-03-24
**Status**: Draft
**Input**: Kompletní testovací zpráva v2 (90 testů, 3 kola) — 8 FAIL, 7 PARTIAL nástrojů k opravě

## User Scenarios & Testing *(mandatory)*

### User Story 1 — ArticleGetter vrací plné abstrakty článků (Priority: P1)

Výzkumník zadá PMID, DOI nebo PMC ID a obdrží kompletní metadata článku včetně abstraktu. Aktuálně tool selhává s server errorem (regrese v kole 3 testování).

**Why this priority**: ArticleGetter je jediný způsob, jak získat detail konkrétního článku. Bez něj je literární pipeline omezena jen na vyhledávání (ArticleSearcher).

**Independent Test**: Zavolat `ArticleGetter(pmid="38768446")` — musí vrátit title, abstract, journal, DOI. Zavolat s DOI a PMC ID — oba formáty musí fungovat.

**Acceptance Scenarios**:

1. **Given** PMID "38768446", **When** ArticleGetter volán, **Then** vrátí strukturovaná metadata s neprázdným abstraktem
2. **Given** DOI "10.1038/s41586-024-07386-0", **When** ArticleGetter volán, **Then** vrátí metadata z Europe PMC
3. **Given** PMC ID "PMC11193658", **When** ArticleGetter volán, **Then** vrátí metadata (ne "Invalid identifier format")
4. **Given** neexistující PMID, **When** ArticleGetter volán, **Then** vrátí srozumitelnou chybovou zprávu (ne server error)

---

### User Story 2 — SZV výkony: vyhledávání a detail fungují (Priority: P1)

Lékař nebo pojišťovací analytik hledá zdravotní výkony (kód nebo název) a získává detaily výkonu včetně bodové hodnoty. Aktuálně SearchProcedures i GetProcedureDetail selhávají s server errorem.

**Why this priority**: SZV blok je kompletně nefunkční — 0 ze 3 nástrojů funguje. Blokuje vyhledávání výkonů a výpočet úhrad (CalculateReimbursement).

**Independent Test**: Zavolat `SearchProcedures(query="09513")` — musí vrátit výsledky. Zavolat `GetProcedureDetail(code="09513")` — musí vrátit bodovou hodnotu a popis výkonu.

**Acceptance Scenarios**:

1. **Given** kód výkonu "09513", **When** SearchProcedures volán, **Then** vrátí alespoň 1 výsledek s názvem a kódem
2. **Given** textový dotaz "vyšetření", **When** SearchProcedures volán, **Then** vrátí relevantní výkony
3. **Given** kód "09513", **When** GetProcedureDetail volán, **Then** vrátí název, bodovou hodnotu a čas výkonu
4. **Given** SZV export nedostupný (504 timeout), **When** SearchProcedures volán, **Then** vrátí srozumitelnou chybu místo server erroru

---

### User Story 3 — DiagnosisAssist navrhuje MKN-10 kódy pro příznaky (Priority: P1)

Lékař zadá příznaky pacienta (česky nebo anglicky) a obdrží seznam navrhovaných MKN-10 diagnóz s relevancí. Aktuálně vrací prázdné candidates (CZ) nebo server error (EN).

**Why this priority**: Klíčová funkce pro klinické rozhodování — mapování příznaků na diagnózy.

**Independent Test**: Zavolat `DiagnosisAssist(symptoms="bolest hlavy, horečka, kašel")` — musí vrátit alespoň 2 MKN-10 kandidáty.

**Acceptance Scenarios**:

1. **Given** české příznaky "bolest hlavy, horečka", **When** DiagnosisAssist volán, **Then** vrátí neprázdný seznam MKN-10 kandidátů
2. **Given** anglické příznaky "headache, fever, cough", **When** DiagnosisAssist volán, **Then** vrátí neprázdný seznam MKN-10 kandidátů (ne server error)
3. **Given** MKN-10 kód jako vstup "J45", **When** DiagnosisAssist volán, **Then** vrátí srozumitelnou chybu s návodem k použití správného nástroje

---

### User Story 4 — OpenFDA Recall nástroje fungují (Priority: P2)

Farmaceut vyhledává FDA recally léků podle názvu, klasifikace nebo statusu. Aktuálně RecallSearcher vrací NOT_FOUND a RecallGetter server error.

**Why this priority**: FDA recall pipeline je důležitá bezpečnostní funkce — 2/12 OpenFDA nástrojů.

**Independent Test**: Zavolat `RecallSearcher(drug="metformin")` — musí vrátit výsledky. Zavolat `RecallGetter` s recall number z výsledků — musí vrátit detail.

**Acceptance Scenarios**:

1. **Given** léčivo "metformin", **When** RecallSearcher volán, **Then** vrátí alespoň 1 recall záznam
2. **Given** recall_class="1", **When** RecallSearcher volán, **Then** vrátí Class I recally
3. **Given** platné recall number z RecallSearcher, **When** RecallGetter volán, **Then** vrátí kompletní detail

---

### User Story 5 — SÚKL DrugsProfile a CompareAlternatives fungují (Priority: P2)

Lékař zadá název léku nebo SÚKL kód a obdrží kompletní profil nebo srovnání alternativ ve stejné ATC skupině. Aktuálně oba selhávají s server errorem.

**Why this priority**: DrugsProfile je agregační nástroj. CompareAlternatives umožňuje porovnat cenové alternativy.

**Independent Test**: Zavolat `DrugsProfile(query="ibuprofen")` — musí vrátit profil. Zavolat `CompareAlternatives(sukl_code="0124137")` — musí vrátit alternativy.

**Acceptance Scenarios**:

1. **Given** text "ibuprofen", **When** DrugsProfile volán, **Then** vrátí registrační údaje + dostupnost (ne server error)
2. **Given** SÚKL kód "0124137", **When** DrugsProfile volán, **Then** vrátí profil pro IBUPROFEN GALMED
3. **Given** SÚKL kód s platným ATC, **When** CompareAlternatives volán, **Then** vrátí seznam alternativ

---

### User Story 6 — VariantSearcher validuje gene-only dotazy (Priority: P2)

Genomický analytik hledá varianty podle genu. Gene-only dotaz (gene="TP53") způsobí timeout. Systém musí vynutit specifičtější filtr.

**Why this priority**: Zlepšení UX — místo timeoutu srozumitelná chybová zpráva s návodem.

**Independent Test**: Zavolat `VariantSearcher(gene="TP53")` — musí vrátit chybovou zprávu s návodem, ne timeout.

**Acceptance Scenarios**:

1. **Given** gene="TP53" bez dalšího filtru, **When** VariantSearcher volán, **Then** vrátí chybovou zprávu vyžadující hgvsp, rsid nebo region
2. **Given** gene="TP53" + hgvsp="p.R175H", **When** VariantSearcher volán, **Then** vrátí výsledky (zachovaná funkčnost)

---

### User Story 7 — GetMedicineDetail obohacen o názvy látek a SPC/PIL URL (Priority: P2)

Lékárník získá detail léku s textovými názvy účinných látek a funkčními URL na SPC/PIL dokumenty.

**Why this priority**: Substance_code bez názvu je nepoužitelný. SPC/PIL URL blokují GetPil/GetSpc.

**Independent Test**: Zavolat `GetMedicineDetail(sukl_code="0124137")` — active_substances musí obsahovat textový název.

**Acceptance Scenarios**:

1. **Given** SÚKL kód "0124137", **When** GetMedicineDetail volán, **Then** active_substances obsahuje "substance_name"
2. **Given** lék s dostupným SPC, **When** GetMedicineDetail volán, **Then** spc_url je neprázdné URL
3. **Given** lék bez SPC, **When** GetMedicineDetail volán, **Then** odpověď obsahuje vysvětlení nedostupnosti

---

### User Story 8 — OpenFDA DeviceGetter, VZP úhrady, NZIP statistiky (Priority: P2)

DeviceGetter akceptuje MDR keys z DeviceSearcher. VZP vrací data nebo vysvětlení. NZIP vrací statistiky nebo vysvětlení.

**Why this priority**: Konzistence Searcher→Getter pipeline a české datové zdroje.

**Independent Test**: MDR key z DeviceSearcher funguje v DeviceGetter. GetDrugReimbursement nevrací prázdná null pole.

**Acceptance Scenarios**:

1. **Given** mdr_report_key z DeviceSearcher, **When** DeviceGetter volán, **Then** vrátí detail události
2. **Given** SÚKL kód léku, **When** GetDrugReimbursement volán, **Then** vrátí data nebo srozumitelnou zprávu o nedostupnosti
3. **Given** MKN-10 kód a rok, **When** GetDiagnosisStats volán, **Then** vrátí statistiky nebo zprávu o nedostupnosti

---

### User Story 9 — NRPZS poskytovatelé a performance metriky (Priority: P3)

GetProviderDetail funguje s platnými NRPZS ID. GetPerformanceMetrics sbírá metriky z tool volání.

**Why this priority**: Nižší priorita — závisí na kvalitě externích zdrojů a je enhancement.

**Independent Test**: GetProviderDetail vrací data nebo srozumitelnou chybu. GetPerformanceMetrics vrací nenulové metriky po sérii volání.

**Acceptance Scenarios**:

1. **Given** platné NRPZS ID, **When** GetProviderDetail volán, **Then** vrátí údaje poskytovatele nebo srozumitelnou chybu
2. **Given** server zpracoval 10+ volání, **When** GetPerformanceMetrics volán, **Then** vrátí request_count > 0

---

### Edge Cases

- SÚKL API změní strukturu odpovědí → graceful degradace s logováním, ne server error
- SZV export timeout (504) → srozumitelná chybová zpráva s doporučením opakovat později
- VZP/NZIP databáze trvale nedostupné → zdokumentovat omezení, vrátit vysvětlení uživateli
- ArticleGetter: rozlišení PMID vs DOI vs PMC ID → automatická detekce formátu identifikátoru
- VariantSearcher gene-only s 50K+ výsledky → input validace PŘED API voláním
- OpenFDA Enforcement API prázdné výsledky vs server error → odlišit NOT_FOUND od chyby query

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: ArticleGetter MUSÍ podporovat PMID, DOI a PMC ID formáty a vracet metadata s abstraktem
- **FR-002**: ArticleGetter MUSÍ vracet srozumitelné chybové zprávy místo server errorů
- **FR-003**: SearchProcedures MUSÍ vracet výsledky pro textové dotazy i kódy výkonů
- **FR-004**: GetProcedureDetail MUSÍ vracet název, bodovou hodnotu a čas výkonu
- **FR-005**: DiagnosisAssist MUSÍ vracet neprázdné MKN-10 kandidáty pro české i anglické příznaky
- **FR-006**: RecallSearcher MUSÍ správně konstruovat dotazy na FDA Enforcement API
- **FR-007**: RecallGetter MUSÍ akceptovat recall numbers ve formátu vraceném RecallSearcherem
- **FR-008**: DrugsProfile MUSÍ orchestrovat SÚKL detail + dostupnost + úhrada a při selhání sub-komponenty vrátit částečná data s indikátorem "nedostupné" u selhavších sekcí (graceful partial return)
- **FR-009**: CompareAlternatives MUSÍ vracet seznam alternativ v ATC skupině
- **FR-010**: VariantSearcher MUSÍ validovat gene-only dotazy a vracet chybu s návodem
- **FR-011**: GetMedicineDetail MUSÍ vracet textové názvy účinných látek
- **FR-012**: GetMedicineDetail MUSÍ vracet SPC/PIL URL kde jsou dostupné
- **FR-013**: DeviceGetter MUSÍ akceptovat MDR key formát konzistentní s DeviceSearcher
- **FR-014**: GetDrugReimbursement MUSÍ vracet data nebo srozumitelnou zprávu o nedostupnosti
- **FR-015**: GetDiagnosisStats MUSÍ vracet data nebo srozumitelnou zprávu o nedostupnosti
- **FR-016**: GetProviderDetail MUSÍ vracet data pro platná NRPZS ID nebo srozumitelnou chybu
- **FR-017**: GetPerformanceMetrics MUSÍ sbírat metriky z tool volání
- **FR-018**: Všechny opravené nástroje MUSÍ mít unit testy s mockovanými API odpověďmi
- **FR-019**: Existující testy (1020) NESMÍ být rozbity opravami
- **FR-020**: Počet registrovaných nástrojů MUSÍ zůstat 60
- **FR-021**: Arcade wrappery MUSÍ být synchronizovány s opravami hlavních nástrojů; test_arcade_integration.py MUSÍ nadále ověřovat 60 Arcade nástrojů

### Key Entities

- **MCP Tool**: Funkční jednotka serveru registrovaná přes `@mcp_app.tool()`, vrací `str`
- **API Endpoint**: Externí datový zdroj (SÚKL, VZP, NZIP, OpenFDA, PubMed, MyVariant.info)
- **Error Response**: Srozumitelná chybová zpráva ve formátu markdown místo raw stack trace

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Celkový PASS rate nástrojů vzroste z 62% na alespoň 85% (z 34/55 na 47/55 testovatelných)
- **SC-002**: Všech 8 aktuálně FAILujících nástrojů buď vrací správná data nebo srozumitelnou chybovou zprávu
- **SC-003**: Všech 7 PARTIAL nástrojů zlepšeno — vrací kompletní data nebo zdokumentovaný důvod nekompletnosti
- **SC-004**: Žádný nástroj nevykazuje regresi oproti aktuálnímu stavu
- **SC-005**: Nárůst z 1020 na alespoň 1050 testů pokrývajících opravy
- **SC-006**: `make check` (ruff + mypy + pre-commit + deptry) prochází bez chyb
- **SC-007**: Regresní test v `test_mcp_integration.py` nadále ověřuje přesně 60 nástrojů

## Clarifications

### Session 2026-03-24

- Q: DiagnosisAssist — přístup k mapování příznaků na diagnózy? → A: Hybridní Symbolic + Embedding pipeline — symptomy → vektory (embed-multilingual-light-v3.0), MKN-10 katalog vektorizován (název + synonyms + includes/excludes), FAISS/SQLite-vec storage, hybridní scoring (cosine similarity + keyword/phrase match). Multilingvní, kontextová pravidla (věk, pohlaví) rozšiřitelné.
- Q: VZP/NZIP trvale nedostupné — strategie? → A: Statický dataset z veřejných VZP/NZIP exportů (CSV/Excel), periodicky aktualizovaný. VZP úhradový seznam je veřejně dostupný. Umožní funkční tools i bez live API.
- Q: DrugsProfile — chování při částečném selhání sub-komponent? → A: Graceful partial return — vrátit úspěšné sekce + "nedostupné" značka u selhavších sub-zdrojů. Neúplný profil je v klinickém kontextu stále cenný.
- Q: Arcade wrappery — synchronizace oprav v scope? → A: Ano, Arcade wrappery v scope. Sdílené implementace se promítnou automaticky; explicitně zkontrolovat konzistenci a opravit Arcade-specifický kód kde potřeba. test_arcade_integration.py musí nadále procházet.

## Assumptions

- SÚKL DLP API je dostupné a vrací konzistentní strukturu pro registrační data
- SZV export (Excel z MZČR) je stáhnutelný; pokud ne, implementujeme fallback s vysvětlením
- VZP úhradový seznam a NZIP epidemiologická data: pokud live API nedostupné, implementovat statický dataset z veřejně dostupných exportů (CSV/Excel) s periodickou aktualizací. VZP úhradový seznam je veřejný na webu VZP.
- OpenFDA Enforcement API má stabilní query formát — ověříme aktuální dokumentaci
- PubTator3 API pro ArticleGetter může být nestabilní — implementujeme fallback na Europe PMC
- DiagnosisAssist bude implementován jako hybridní Symbolic + Embedding pipeline: symptomy vektorizovány přes embed-multilingual-light-v3.0, MKN-10 katalog (název + synonyms + includes/excludes) uložen ve FAISS/SQLite-vec, scoring kombinuje cosine similarity + keyword match. Žádná závislost na externím LLM, multilingvní podpora nativně.
