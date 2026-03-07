# task_plan.md — CzechMedMCP Implementation Plan

> Na základě specifikace v2.1 FINAL a gap analýzy z live testingu

## Přehled

| Metriky | Hodnota |
|---------|---------|
| Aktuální nástroje | 51 (37 global + 14 czech) |
| Cílové nástroje | 61 (37 global + 24 czech) |
| Nové nástroje | 10 |
| Kritické bugy | 5 (SUKL, MKN, NRPZS, SZV, VZP) |
| Architektonické změny | 2 (router domény, domain handlery) |

---

## Fáze 0: Stabilizace stávajících nástrojů (NEJVYŠŠÍ PRIORITA)

> Bez funkčních stávajících nástrojů nemá smysl přidávat nové.

### 0.1 SUKL: Oprava sukl_code v search response
- [ ] Analyzovat raw API response z `prehledy.sukl.cz/dlp/api`
- [ ] Zjistit správné pole pro SUKL kód (může být `reg_num`, `sukl_code`, `kod` apod.)
- [ ] Opravit mapping v `czech/sukl/search.py`
- [ ] Ověřit, že getter/SPC/PIL/availability chain funguje end-to-end
- **Soubory:** `src/biomcp/czech/sukl/search.py`, `src/biomcp/czech/sukl/client.py`

### 0.2 MKN-10: Oprava načítání ClaML XML dat
- [ ] Ověřit existenci XML souborů v `data/` adresáři
- [ ] Zjistit proč parser nenačítá data při startu
- [ ] Opravit inicializaci v `czech/mkn/parser.py`
- [ ] Otestovat search + get + browse
- **Soubory:** `src/biomcp/czech/mkn/parser.py`, `src/biomcp/czech/mkn/search.py`, `data/`

### 0.3 NRPZS: Najít funkční API endpoint
- [ ] Ověřit aktuální URL `nrpzs.uzis.cz/api/v1` (vrací 404)
- [ ] Prohledat ÚZIS web pro nový endpoint nebo OpenData portál
- [ ] Implementovat fallback na dostupný zdroj
- [ ] Aktualizovat `constants.py` URL
- **Soubory:** `src/biomcp/czech/nrpzs/search.py`, `src/biomcp/constants.py`

### 0.4 SZV: Ověřit a opravit data loading
- [ ] Zkontrolovat CSV soubory pro SZV v projektu
- [ ] Zjistit proč search vrací 0 výsledků
- [ ] Opravit data loading nebo přidat CSV soubory
- **Soubory:** `src/biomcp/czech/szv/search.py`, `src/biomcp/czech/szv/models.py`

### 0.5 VZP: Ověřit a opravit data loading
- [ ] Zkontrolovat zdroj dat pro VZP codebooks
- [ ] Zjistit proč search vrací 0 výsledků
- [ ] Opravit data loading
- **Soubory:** `src/biomcp/czech/vzp/search.py`, `src/biomcp/czech/vzp/models.py`

---

## Fáze 1: Integrace českých domén do unified routeru

> České nástroje jsou izolované — nemůžou být použity přes `search()` a `fetch()`.

### 1.1 Přidat české domény do `constants.py`
- [ ] Přidat do `VALID_DOMAINS`: `sukl_drug`, `mkn_diagnosis`, `nrpzs_provider`, `szv_procedure`, `vzp_codebook`
- [ ] Přidat do `VALID_DOMAINS_PLURAL`, `DOMAIN_TO_PLURAL`, `PLURAL_TO_DOMAIN`
- **Soubor:** `src/biomcp/constants.py`

### 1.2 Přidat české handlery do `domain_handlers.py`
- [ ] Vytvořit `SUKLDrugHandler`, `MKNDiagnosisHandler`, `NRPZSProviderHandler`, `SZVProcedureHandler`, `VZPCodebookHandler`
- [ ] Každý handler implementuje `format_result()` dle BioMCP patternu
- **Soubor:** `src/biomcp/domain_handlers.py`

### 1.3 Propojit české search/fetch do routeru
- [ ] Přidat české větve do `router.py` search dispatch
- [ ] Přidat české větve do `router.py` fetch dispatch
- **Soubor:** `src/biomcp/router.py`

---

## Fáze 2: Nové české nástroje

> Přidávat až po stabilizaci stávajících (Fáze 0).

### 2.1 SUKL: Batch availability check
- [ ] Implementovat `_sukl_batch_availability()` v `availability.py`
- [ ] Registrovat `sukl_batch_availability_checker` v `czech_tools.py`
- [ ] Využít `asyncio.gather` + semaphore pro paralelní dotazy
- **Soubory:** `czech/sukl/availability.py`, `czech/czech_tools.py`

### 2.2 SUKL: Reimbursement info
- [ ] Implementovat `_sukl_reimbursement()` — cena, úhrada, doplatek
- [ ] Registrovat `sukl_reimbursement_getter`
- [ ] Zdroj: SUKL Open Data API nebo scraping
- **Soubory:** `czech/sukl/getter.py` nebo nový `czech/sukl/reimbursement.py`

### 2.3 SUKL: Find pharmacies
- [ ] Implementovat `_sukl_find_pharmacies()` — lékárny dle města/PSČ
- [ ] Registrovat `sukl_pharmacy_searcher`
- [ ] Zdroj: SUKL registr lékáren
- **Soubory:** nový `czech/sukl/pharmacy.py`, `czech/czech_tools.py`

### 2.4 MKN-10: Diagnosis statistics
- [ ] Implementovat `_mkn_diagnosis_stats()` — epidemiologie z NRHZS/NZIP
- [ ] Registrovat `mkn_diagnosis_stats_getter`
- [ ] Zdroj: NZIP CSV data
- **Soubory:** nový `czech/mkn/stats.py`, `czech/czech_tools.py`

### 2.5 NRPZS: Codebooks
- [ ] Implementovat `_nrpzs_codebooks()` — číselníky oborů, forem péče
- [ ] Registrovat `nrpzs_codebook_getter`
- **Soubory:** `czech/nrpzs/search.py`, `czech/czech_tools.py`

### 2.6 SZV: Calculate reimbursement
- [ ] Implementovat `_szv_calculate_reimbursement()` — kalkulace úhrady výkonu
- [ ] Registrovat `szv_reimbursement_calculator`
- **Soubory:** nový `czech/szv/reimbursement.py`, `czech/czech_tools.py`

### 2.7 VZP: Compare alternatives
- [ ] Implementovat `_vzp_compare_alternatives()` — porovnání v ATC skupině
- [ ] Registrovat `vzp_alternative_comparer`
- **Soubory:** nový `czech/vzp/alternatives.py`, `czech/czech_tools.py`

---

## Fáze 3: Workflow orchestrační nástroje

> Kombinují české + globální moduly — hlavní přidaná hodnota forku.

### 3.1 Drug Profile workflow
- [ ] SUKL detail + dostupnost + úhrada → PubMed studie k účinné látce
- [ ] Registrovat `czechmed_drug_profile`
- **Soubory:** nový `czech/workflows/drug_profile.py`, `czech/czech_tools.py`

### 3.2 Diagnosis Assist workflow
- [ ] MKN-10 search → PubMed evidence
- [ ] Registrovat `czechmed_diagnosis_assist`
- **Soubory:** nový `czech/workflows/diagnosis_assist.py`

### 3.3 Referral Assist workflow
- [ ] MKN-10 validace kódu → NRPZS provider search
- [ ] Registrovat `czechmed_referral_assist`
- **Soubory:** nový `czech/workflows/referral_assist.py`

---

## Fáze 4: Kosmetika a finalizace

### 4.1 Server identity
- [ ] Přejmenovat v `core.py`: `name="CzechMedMCP"` (1 řádek)

### 4.2 Test coverage
- [ ] Unit testy pro všechny nové nástroje
- [ ] Aktualizovat expected tool count v `test_mcp_integration.py`
- [ ] Integration testy s `@pytest.mark.integration`

### 4.3 Dokumentace
- [ ] Aktualizovat CLAUDE.md s novými nástroji
- [ ] Aktualizovat README.md s kompletním katalogem

---

## Rozhodnutí

### R1: Package NEBUDE přejmenován na `czechmedmcp`
**Důvod:** 100+ importů, rozbije upstream sync, rozbije existující integrace. Server identity se změní jen v `core.py:name`.

### R2: Pořadí implementace
```
Fáze 0 (stabilizace) → Fáze 1 (router integrace) → Fáze 2 (nové tools) → Fáze 3 (workflows) → Fáze 4 (finalizace)
```
Důvod: Nové nástroje závisí na funkčních stávajících. Workflow závisí na obojím.

### R3: Cílový počet nástrojů = 61
37 global (stávající) + 24 czech (14 stávajících + 10 nových) = 61
(Spec říká 59, ale nepočítá `get_performance_metrics` a `compare_alternatives`.)
