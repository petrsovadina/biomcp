# Feature Specification: Oprava selhávajících MCP nástrojů (46% → 80%+)

**Feature Branch**: `012-fix-mcp-tool-bugs`
**Created**: 2026-03-27
**Status**: Draft
**Input**: Komplexní test report z 26. 3. 2026 — 58 nástrojů, 18 identifikovaných bugů (6 P1, 7 P2, 5 P3)

## Clarifications

### Session 2026-03-27

- Q: Strategie opravy NRPZS (5 nástrojů, 0%) a SZV (3 nástroje, 0%) — debug existující implementace vs. přepis na statická data? → A: Debug a opravit existující API/data loading implementaci (endpointy, autorizaci, data parsing). Přepisovat pouze pokud se prokáže nefunkčnost API.
- Q: Zdroj PIL/SmPC dokumentů — scraping, konstruovaná URL, nebo DLP API dokument endpoint? → A: Rozšířit existující SÚKL DLP API integraci o dokument endpoint (`/dlp/v1`). Žádný scraping.
- Q: Dodání oprav — jedna velká PR, fázované commity, nebo separátní PR? → A: 3 fáze na jedné branch (P1 commit, P2 commit, P3 commit), pak jedna PR se 3 logickými celky.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Lékař vyhledá lék podle názvu (Priority: P1)

Lékař potřebuje najít informace o ibuprofenu pro pacienta. Zadá název léku do SearchMedicine a očekává seznam odpovídajících přípravků se SÚKL kódy, silou a lékovou formou.

**Proč tato priorita**: SearchMedicine je hlavní vstupní bod SÚKL sekce. Bez funkčního vyhledávání musí uživatel znát SÚKL kód předem — 90% use cases je nepoužitelných. Opravou SearchMedicine se odemkne celý řetězec SÚKL nástrojů (DrugProfile, CompareAlternatives).

**Nezávislý test**: Zavolat `SearchMedicine(query="ibuprofen")` a ověřit, že vrátí alespoň 1 výsledek s validním SÚKL kódem, názvem a ATC kódem.

**Akceptační scénáře**:

1. **Given** funkční MCP server, **When** uživatel zavolá `SearchMedicine(query="ibuprofen")`, **Then** systém vrátí seznam léčiv obsahujících ibuprofen (minimálně 1 výsledek).
2. **Given** funkční MCP server, **When** uživatel zavolá `SearchMedicine(query="warfarin")`, **Then** systém vrátí seznam warfarinových přípravků.
3. **Given** funkční MCP server, **When** uživatel zavolá `SearchMedicine(query="xyzneexistuje")`, **Then** systém vrátí prázdný výsledek (ne error).

---

### User Story 2 — Lékař vyhledá poskytovatele péče a výkony (Priority: P1)

Lékař v Brně hledá kardiologa pro pacienta s hypertenzí. Potřebuje také zjistit bodové ohodnocení a úhradu EKG výkonu.

**Proč tato priorita**: NRPZS (5 nástrojů, 0%) a SZV (3 nástroje, 0%) jsou kompletně nefunkční. Celkem 8 nástrojů klíčových pro českou ambulantní praxi.

**Nezávislý test**: Zavolat `SearchProviders(city="Brno")` a ověřit, že vrátí seznam zdravotnických zařízení. Zavolat `SearchProcedures(query="EKG")` a ověřit výsledky.

**Akceptační scénáře**:

1. **Given** funkční MCP server, **When** uživatel zavolá `SearchProviders(city="Brno", specialty="kardiologie")`, **Then** systém vrátí seznam kardiologů v Brně.
2. **Given** funkční MCP server, **When** uživatel zavolá `FindPharmacies(city="Praha")`, **Then** systém vrátí seznam lékáren.
3. **Given** funkční MCP server, **When** uživatel zavolá `GetNrpzsCodebooks(codebook_type="specialties")`, **Then** systém vrátí číselník specializací.
4. **Given** funkční MCP server, **When** uživatel zavolá `SearchProcedures(query="EKG")`, **Then** systém vrátí výkon s kódem a body.
5. **Given** funkční MCP server, **When** uživatel zavolá `CalculateReimbursement(procedure_code="09111")`, **Then** systém vrátí kalkulaci úhrady.

---

### User Story 3 — Výzkumník hledá vědecké články (Priority: P1)

Výzkumník hledá články o metforminu a diabetes mellitus 2. typu přes ArticleSearcher.

**Proč tato priorita**: ArticleSearcher je základní nástroj pro biomedicínský výzkum — kompletně nefunkční.

**Nezávislý test**: Zavolat `ArticleSearcher(keywords="warfarin dosing")` a ověřit neprázdné výsledky.

**Akceptační scénáře**:

1. **Given** funkční MCP server, **When** uživatel zavolá `ArticleSearcher(genes="BRCA1")`, **Then** systém vrátí články o BRCA1.
2. **Given** funkční MCP server, **When** uživatel zavolá `ArticleSearcher(chemicals="metformin", diseases="type 2 diabetes")`, **Then** systém vrátí relevantní články.

---

### User Story 4 — Lékař potřebuje PIL/SmPC a profil léku (Priority: P1)

Lékař chce zkontrolovat kontraindikace v SmPC, přečíst příbalový leták a získat kompletní profil léku včetně alternativ.

**Proč tato priorita**: PIL, SmPC, DrugProfile a CompareAlternatives — 4 nástroje, všechny nefunkční. Klíčové klinické dokumenty.

**Nezávislý test**: Zavolat `GetSpc("0124137")` a ověřit neprázdný obsah. Zavolat `DrugProfile(query="ibuprofen")` a ověřit kompletní profil.

**Akceptační scénáře**:

1. **Given** funkční MCP server, **When** uživatel zavolá `GetSpc("0124137")`, **Then** systém vrátí SmPC obsah nebo funkční URL.
2. **Given** funkční MCP server, **When** uživatel zavolá `GetPil("0094113")`, **Then** systém vrátí PIL obsah nebo funkční URL.
3. **Given** funkční MCP server, **When** uživatel zavolá `DrugProfile(query="ibuprofen")`, **Then** systém vrátí kompletní profil.
4. **Given** funkční MCP server, **When** uživatel zavolá `CompareAlternatives(sukl_code="0124137")`, **Then** systém vrátí alternativní léčiva.

---

### User Story 5 — SÚKL kód bez leading zero (Priority: P2)

Lékař dostane 6-místný SÚKL kód z externího systému a zadá jej. Systém automaticky doplní leading zero.

**Proč tato priorita**: Triviální fix, velký dopad na UX.

**Nezávislý test**: `GetMedicineDetail("124137")` vrátí stejný výsledek jako `GetMedicineDetail("0124137")`.

**Akceptační scénáře**:

1. **Given** funkční MCP server, **When** uživatel zadá 6-místný kód "124137", **Then** systém jej normalizuje na "0124137" a vrátí správný výsledek.

---

### User Story 6 — Epidemiologická data a diagnostický asistent (Priority: P2)

Lékař chce statistiky prevalence diagnózy a diferenciální diagnostiku podle symptomů.

**Proč tato priorita**: GetDiagnosisStats vrací 0 případů, DiagnosisAssist vrací prázdné candidates.

**Nezávislý test**: `GetDiagnosisStats(code="E11")` vrátí nenulový total_cases. `DiagnosisAssist(symptoms="bolest na hrudi, dušnost")` vrátí candidates.

**Akceptační scénáře**:

1. **Given** funkční MCP server, **When** uživatel zavolá `GetDiagnosisStats(code="E11", year=2023)`, **Then** `total_cases > 0`.
2. **Given** funkční MCP server, **When** uživatel zavolá `DiagnosisAssist(symptoms="bolest na hrudi, dušnost, levá paže")`, **Then** systém vrátí neprázdné candidates.

---

### User Story 7 — Úhrada léku a konzistentní chybové hlášky (Priority: P2)

Lékař zjišťuje úhradu warfarinu. Jakékoliv chyby přijdou v konzistentním formátu.

**Proč tato priorita**: Úhradová data vrací null, chybové formáty se liší nástroj od nástroje.

**Nezávislý test**: `GetReimbursement("0094113")` vrátí neprázdná data. Chyba z libovolného nástroje má stejný JSON formát.

**Akceptační scénáře**:

1. **Given** funkční MCP server, **When** uživatel zavolá `GetReimbursement("0094113")`, **Then** systém vrátí data s max_price a patient_copay.
2. **Given** libovolný nástroj, **When** nastane chyba, **Then** odpověď má konzistentní formát.

---

### User Story 8 — Drobné opravy kvality (Priority: P3)

Fulltextové vyhledávání diagnóz, metriky, placeholdery v abstrakt, DrugGetter normalizace, GeneGetter verbozita.

**Proč tato priorita**: Nízký dopad, zlepšení kvality.

**Nezávislý test**: `SearchDiagnosis(query="hypertenze")` vrátí relevantní výsledky. `DrugGetter("metformin")` vrátí data.

**Akceptační scénáře**:

1. **Given** funkční MCP server, **When** uživatel zavolá `SearchDiagnosis(query="hypertenze")`, **Then** systém vrátí diagnózy související s hypertenzí (ne lymfomy).
2. **Given** funkční MCP server, **When** uživatel zavolá `DrugGetter("metformin")`, **Then** systém vrátí informace o metforminu.

---

### Edge Cases

- Neexistující SÚKL kód → čitelná chyba, ne server error.
- Vyhledávání s diakritickými znaky (léčiva, kardiológie) → správné výsledky.
- Prázdný query string → prázdný výsledek nebo validační chyba, ne crash.
- Timeout externího API → graceful error s informací o zdroji.
- SÚKL kód s mezerami nebo speciálními znaky → normalizace nebo validační chyba.
- Nefunkční externí API → informativní chyba s názvem zdroje a HTTP kódem (žádný tichý fallback na prázdná data).

## Delivery Strategy

Opravy budou dodány ve 3 fázích na jedné branch `012-fix-mcp-tool-bugs`:

1. **Fáze P1** (commit 1): BUG-001 až BUG-006 — kritické opravy (SearchMedicine, NRPZS, SZV, PIL/SmPC, DrugProfile, ArticleSearcher)
2. **Fáze P2** (commit 2): BUG-007 až BUG-013 — normalizace, DiagnosisStats, DiagnosisAssist, Reimbursement, OpenFDA Recall, substance names, error format
3. **Fáze P3** (commit 3): BUG-014 až BUG-018 — SearchDiagnosis text, metrics, ArticleGetter abstract, DrugGetter, GeneGetter

Poté jedna PR do `main` se 3 logickými celky. Každá fáze je samostatně testovatelná.

## Requirements *(mandatory)*

### Functional Requirements

**P1 — Kritické opravy (BUG-001 až BUG-006)**:

- **FR-001**: SearchMedicine MUSÍ vracet výsledky pro běžné názvy léků (ibuprofen, warfarin, paracetamol, metformin).
- **FR-002**: Všech 5 NRPZS nástrojů (SearchProviders, GetProviderDetail, GetNrpzsCodebooks, ReferralAssist, FindPharmacies) MUSÍ vracet relevantní data místo server error. Přístup: debug existující API/data loading implementace — opravit endpointy, autorizaci a data parsing v current kódu.
- **FR-003**: Všechny 3 SZV nástroje (SearchProcedures, GetProcedureDetail, CalculateReimbursement) MUSÍ vracet relevantní data místo server error. Přístup: debug existující implementace, stejná strategie jako NRPZS.
- **FR-004**: GetPil a GetSpc MUSÍ vracet obsah příbalových letáků a SmPC dokumentů. Zdroj: SÚKL DLP API dokument endpoint (`/dlp/v1`), rozšíření existující integrace.
- **FR-005**: DrugProfile MUSÍ vracet kompletní profil léku.
- **FR-006**: CompareAlternatives MUSÍ vracet alternativní léčiva ve stejné ATC skupině.
- **FR-007**: ArticleSearcher MUSÍ vracet výsledky pro běžné vyhledávací parametry.

**P2 — Středně závažné opravy (BUG-007 až BUG-013)**:

- **FR-008**: Všechny SÚKL nástroje MUSÍ automaticky normalizovat SÚKL kód na 7 číslic (zero-padding).
- **FR-009**: GetDiagnosisStats MUSÍ vracet nenulová epidemiologická data pro běžné diagnózy.
- **FR-010**: DiagnosisAssist MUSÍ vracet neprázdné kandidátní diagnózy pro typické symptomové kombinace.
- **FR-011**: GetReimbursement a GetDrugReimbursement MUSÍ vracet neprázdná úhradová data pro hrazené léky.
- **FR-012**: OpenfdaRecallSearcher MUSÍ vracet výsledky pro léky s dokumentovanou historií recall.
- **FR-013**: GetMedicineDetail MUSÍ vracet lidsky čitelné názvy účinných látek.
- **FR-014**: Všechny nástroje MUSÍ vracet chyby v konzistentním formátu.

**P3 — Nízká priorita (BUG-014 až BUG-018)**:

- **FR-015**: SearchDiagnosis MUSÍ vracet relevantní výsledky pro fulltextové dotazy v češtině.
- **FR-016**: GetPerformanceMetrics MUSÍ vracet metriky po provedení API volání.
- **FR-017**: ArticleGetter MUSÍ vracet reálné abstrakty, ne placeholder text.
- **FR-018**: DrugGetter MUSÍ fungovat pro běžné názvy léků včetně "metformin".
- **FR-019**: GeneGetter by měl nabízet kompaktní výstup bez stovek RefSeq identifikátorů.

### Key Entities

- **SÚKL kód**: 7-místný numerický identifikátor léčivého přípravku v české databázi SÚKL. Musí být zero-padded.
- **MKN-10 kód**: Alfanumerický identifikátor diagnózy dle Mezinárodní klasifikace nemocí (např. E11, I10).
- **NRPZS poskytovatel**: Zdravotnické zařízení registrované v Národním registru poskytovatelů zdravotních služeb.
- **SZV výkon**: Zdravotní výkon s bodovým ohodnocením dle Seznamu zdravotních výkonů.
- **VZP úhrada**: Údaje o úhradě léku zdravotní pojišťovnou (max cena, úhrada, doplatek).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Celkový success rate MCP nástrojů se zvýší z 46% na minimálně 75%.
- **SC-002**: Žádná celá kategorie nástrojů nesmí mít 0% success rate (aktuálně NRPZS a SZV).
- **SC-003**: Všech 6 P1 bugů musí být vyřešeno — postižené nástroje musí vracet relevantní data.
- **SC-004**: SearchMedicine musí vracet výsledky pro 5 z 5 běžných názvů léků.
- **SC-005**: Normalizace SÚKL kódů musí fungovat transparentně — 6-místný i 7-místný kód vrátí identický výsledek.
- **SC-006**: Všechny existující unit testy musí nadále procházet (žádná regrese).
- **SC-007**: Počet registrovaných nástrojů musí zůstat 60.

## Assumptions

- SÚKL DLP API je veřejně dostupné bez autorizačního tokenu.
- NRPZS data jsou dostupná přes existující API implementaci (debug endpointů a autorizace, ne přepis na statická data).
- SZV číselník výkonů je dostupný přes existující implementaci (debug, ne přepis).
- PubTator3 API nevyžaduje API klíč pro základní vyhledávání.
- OpenFDA API funguje bez API klíče (s rate limiting).
- PIL a SmPC dokumenty budou získávány přes SÚKL DLP API dokument endpoint (`/dlp/v1`).
- VZP úhradová data jsou veřejně dostupná.

## Scope Boundaries

**V scope**:
- Oprava všech 18 identifikovaných bugů (BUG-001 až BUG-018)
- Přidání/oprava unit testů pro opravené nástroje
- Aktualizace existujících testů pokud se změní chování

**Mimo scope**:
- Přidávání nových nástrojů
- Změna architektury nebo API rozhraní
- Optimalizace výkonu (kromě opravy timeoutů)
- NCI nástroje (vyžadují externí API klíč)
- AlphaGenome prediktor (vyžaduje externí API klíč)

## Dependencies

- Dostupnost SÚKL DLP API
- Dostupnost NRPZS dat (API nebo statický export)
- Dostupnost SZV číselníku výkonů
- Dostupnost PubTator3 / PubMed API
- Dostupnost OpenFDA API
- Dostupnost VZP úhradových dat
