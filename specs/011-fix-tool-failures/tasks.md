# Tasks: Fix Tool Failures (011)

**Input**: Design documents from `/specs/011-fix-tool-failures/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/behavior-contracts.md

**Tests**: Unit testy POVINNÉ pro každý opravený nástroj (FR-018).

**Organization**: Tasky seskupeny po user stories pro nezávislou implementaci a testování.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Lze spustit paralelně (různé soubory, žádné závislosti)
- **[Story]**: User story (US1–US9)
- Cesty relativní k repository root

---

## Phase 1: Setup

**Purpose**: Příprava prostředí a nových závislostí

- [x] T001 Přidat `sentence-transformers` + `numpy` dependency do pyproject.toml `[project.optional-dependencies]` jako `embeddings` extra
- [x] T002 [P] Přidat konstantu `NCBI_PMC_CONVERTER_URL` do src/czechmedmcp/constants.py
- [x] T003 [P] Změnit `BIOMCP_METRICS_ENABLED` default na `true` v src/czechmedmcp/metrics.py
- [x] T004 [P] Vytvořit adresářovou strukturu src/czechmedmcp/czech/diagnosis_embed/__init__.py + data adresáře

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Sdílená infrastruktura nutná před user stories

**⚠️ CRITICAL**: Žádný user story nemůže začít před dokončením Phase 2

- [ ] T005 Stáhnout a uložit VZP úhradový seznam CSV do src/czechmedmcp/czech/vzp/data/vzp_reimbursement.csv
- [ ] T006 [P] Vytvořit VZP data loader v src/czechmedmcp/czech/vzp/data_loader.py — načtení CSV do in-memory dict (sukl_code → VZPReimbursementRecord)
- [ ] T007 [P] Ověřit NZIP hospitalizační CSV URL (https://reporting.uzis.cz/cr/data/hospitalizace_{year}.csv) a stáhnout fallback dataset do src/czechmedmcp/czech/mkn/data/
- [ ] T008 [P] Vytvořit NZIP data loader v src/czechmedmcp/czech/mkn/data_loader.py — načtení CSV do in-memory dict (mkn_code+year → NZIPHospitalizationRecord)
- [ ] T009 Napsat unit testy pro VZP/NZIP data loadery v tests/czech/test_data_loaders.py

**Checkpoint**: Statické datasety ready — user stories mohou začít

---

## Phase 3: User Story 1 — ArticleGetter (Priority: P1) 🎯 MVP

**Goal**: ArticleGetter vrací plné abstrakty pro PMID, DOI i PMC ID

**Independent Test**: `ArticleGetter(pmid="38768446")` vrátí metadata s neprázdným abstraktem; `ArticleGetter(pmid="PMC11193658")` vrátí metadata přes PMC→PMID konverzi

### Testy pro US1

- [x] T010 [P] [US1] Unit test pro `is_pmc_id()` detekci v tests/tdd/test_article_getter.py
- [x] T011 [P] [US1] Unit test pro `convert_pmc_to_pmid()` (mockovaný NCBI API) v tests/tdd/test_article_getter.py
- [x] T012 [P] [US1] Unit test pro ArticleGetter s PMID/DOI/PMC ID routing v tests/tdd/test_article_getter.py
- [x] T013 [P] [US1] Unit test pro error handling (neexistující PMID, nedostupné API) v tests/tdd/test_article_getter.py

### Implementace US1

- [x] T014 [US1] Přidat `is_pmc_id()` funkci do src/czechmedmcp/articles/fetch.py (regex `^PMC\d{7,8}$`)
- [x] T015 [US1] Implementovat `convert_pmc_to_pmid()` v src/czechmedmcp/articles/fetch.py — NCBI ID Converter API s cache
- [x] T016 [US1] Aktualizovat `_article_details()` routing v src/czechmedmcp/articles/fetch.py — přidat PMC ID větev
- [x] T017 [US1] Přidat robustní error handling — fallback na Europe PMC při PubTator3 selhání v src/czechmedmcp/articles/fetch.py
- [x] T018 [US1] Aktualizovat test v tests/tdd/test_europe_pmc_fetch.py — PMC ID již není "invalid identifier"

**Checkpoint**: ArticleGetter funguje s PMID, DOI i PMC ID

---

## Phase 4: User Story 2 — SZV výkony (Priority: P1)

**Goal**: SearchProcedures a GetProcedureDetail vrací výsledky bez server errorů

**Independent Test**: `SearchProcedures(query="09513")` vrátí výsledky; `GetProcedureDetail(code="09513")` vrátí bodovou hodnotu

### Testy pro US2

- [x] T019 [P] [US2] Unit test pro SZV Excel download + parsing v tests/czech/test_szv.py (mockovaný httpx)
- [x] T020 [P] [US2] Unit test pro SZV search matching v tests/czech/test_szv.py
- [x] T021 [P] [US2] Unit test pro SZV error handling (timeout, 504, malformed Excel) v tests/czech/test_szv.py

### Implementace US2

- [x] T022 [US2] Debug SZV Excel download v src/czechmedmcp/czech/szv/search.py — ověřit URL, timeout, response handling
- [x] T023 [US2] Přidat graceful error handling pro download selhání v src/czechmedmcp/czech/szv/search.py — vrátit `{"error": "SZV data unavailable: ..."}` místo raise
- [x] T024 [US2] Ověřit Arcade wrapper pro SearchProcedures/GetProcedureDetail v src/czechmedmcp/arcade/czech_tools.py

**Checkpoint**: SZV blok funkční — SearchProcedures, GetProcedureDetail, CalculateReimbursement

---

## Phase 5: User Story 3 — DiagnosisAssist (Priority: P1)

**Goal**: DiagnosisAssist vrací neprázdné MKN-10 kandidáty pro CZ i EN příznaky

**Independent Test**: `DiagnosisAssist(symptoms="bolest hlavy, horečka")` vrátí alespoň 2 kandidáty

### Testy pro US3

- [ ] T025 [P] [US3] Unit test pro MKN-10 embedding indexer v tests/czech/test_diagnosis_embed.py (mockovaný embedding)
- [ ] T026 [P] [US3] Unit test pro hybrid search (cosine + keyword) v tests/czech/test_diagnosis_embed.py
- [ ] T027 [P] [US3] Unit test pro DiagnosisAssist end-to-end flow v tests/tdd/test_diagnosis_assist.py

### Implementace US3

- [ ] T028 [US3] Vytvořit MKN-10 indexer v src/czechmedmcp/czech/diagnosis_embed/indexer.py — build embedding index z MKN-10 dat
- [ ] T029 [US3] Vytvořit hybrid searcher v src/czechmedmcp/czech/diagnosis_embed/searcher.py — cosine similarity + keyword match scoring
- [ ] T030 [US3] Přepojit DiagnosisAssist workflow na embedding pipeline v src/czechmedmcp/czech/workflows/diagnosis_assistant.py
- [ ] T031 [US3] Přidat keyword-match fallback pokud embedding model nedostupný v src/czechmedmcp/czech/diagnosis_embed/searcher.py
- [ ] T032 [US3] Aktualizovat Arcade wrapper pro DiagnosisAssist v src/czechmedmcp/arcade/czech_tools.py

**Checkpoint**: DiagnosisAssist vrací smysluplné kandidáty pro CZ i EN vstupy

---

## Phase 6: User Story 4 — OpenFDA Recall (Priority: P2)

**Goal**: RecallSearcher vrací výsledky, RecallGetter vrací detail

**Independent Test**: `RecallSearcher(drug="metformin")` vrátí recall záznamy

### Testy pro US4

- [x] T033 [P] [US4] Unit test pro RecallSearcher query builder v tests/tdd/test_recall.py (mockovaný OpenFDA response)
- [x] T034 [P] [US4] Unit test pro RecallGetter s platným recall number v tests/tdd/test_recall.py

### Implementace US4

- [x] T035 [US4] Debug RecallSearcher v src/czechmedmcp/openfda/drug_recalls.py — safe request wrapper + error handling
- [x] T036 [US4] Debug RecallGetter v src/czechmedmcp/openfda/drug_recalls.py — safe request wrapper
- [x] T037 [US4] Přidat logging pro diagnostiku NOT_FOUND vs server error v src/czechmedmcp/openfda/drug_recalls.py
- [x] T038 [US4] Aktualizovat Arcade wrappery pro Recall nástroje v src/czechmedmcp/arcade/individual_tools.py

**Checkpoint**: OpenFDA Recall pipeline funkční

---

## Phase 7: User Story 5 — DrugsProfile + CompareAlternatives (Priority: P2)

**Goal**: DrugsProfile vrací částečná data, CompareAlternatives vrací alternativy

**Independent Test**: `DrugsProfile(query="ibuprofen")` vrátí profil s indikátory dostupnosti per sekce

### Testy pro US5

- [x] T039 [P] [US5] Unit test pro DrugsProfile partial return v tests/tdd/test_drug_profile.py
- [x] T040 [P] [US5] Unit test pro CompareAlternatives s mockovaným SÚKL v tests/tdd/test_drug_profile.py

### Implementace US5

- [x] T041 [US5] Implementovat graceful partial return v src/czechmedmcp/czech/workflows/drug_profile.py — každá sekce s status ok/unavailable/error
- [x] T042 [US5] Opravit CompareAlternatives v src/czechmedmcp/czech/vzp/drug_reimbursement.py — vrátit alternativy i bez reimbursement dat
- [x] T043 [US5] Napojit VZP statický dataset (T006) do DrugsProfile reimbursement sekce v src/czechmedmcp/czech/workflows/drug_profile.py
- [x] T044 [US5] Aktualizovat Arcade wrappery v src/czechmedmcp/arcade/czech_tools.py

**Checkpoint**: DrugsProfile a CompareAlternatives funkční

---

## Phase 8: User Story 6 — VariantSearcher validace (Priority: P2)

**Goal**: Gene-only dotazy vrací chybu s návodem místo timeoutu

**Independent Test**: `VariantSearcher(gene="TP53")` vrátí chybovou zprávu; `VariantSearcher(gene="TP53", hgvsp="p.R175H")` vrátí výsledky

### Testy pro US6

- [x] T045 [P] [US6] Unit test pro gene-only validaci v tests/tdd/test_variant_search_validation.py

### Implementace US6

- [x] T046 [US6] Přidat @model_validator do VariantQuery v src/czechmedmcp/variants/search.py — gene-only bez hgvsp/rsid/region → ValueError
- [x] T047 [US6] Aktualizovat Arcade wrapper pro VariantSearcher v src/czechmedmcp/arcade/individual_tools.py

**Checkpoint**: VariantSearcher odmítá gene-only dotazy s návodem

---

## Phase 9: User Story 7 — GetMedicineDetail (Priority: P2)

**Goal**: Substance names v textu, SPC/PIL URL kde dostupné

**Independent Test**: `GetMedicineDetail(sukl_code="0124137")` vrátí `substance_name` v active_substances

### Testy pro US7

- [x] T048 [P] [US7] Unit test pro substance name lookup v tests/tdd/test_medicine_detail.py
- [x] T049 [P] [US7] Unit test pro SPC/PIL URL construction v tests/tdd/test_medicine_detail.py

### Implementace US7

- [x] T050 [US7] Implementovat substance name lookup v src/czechmedmcp/czech/sukl/getter.py — SUKL DLP API `/latky/{kodLatky}` s cache
- [x] T051 [US7] Opravit SPC/PIL URL handling v src/czechmedmcp/czech/sukl/getter.py — validace metadata existence, null s vysvětlením
- [ ] T052 [US7] Aktualizovat Arcade wrapper v src/czechmedmcp/arcade/czech_tools.py

**Checkpoint**: GetMedicineDetail vrací substance names a SPC/PIL URL

---

## Phase 10: User Story 8 — DeviceGetter + VZP + NZIP (Priority: P2)

**Goal**: DeviceGetter funguje s MDR keys, VZP/NZIP vrací data nebo vysvětlení

**Independent Test**: GetDrugReimbursement vrací data z VZP datasetu; GetDiagnosisStats vrací nenulové statistiky

### Testy pro US8

- [ ] T053 [P] [US8] Unit test pro DeviceGetter MDR key format v tests/tdd/test_device.py
- [ ] T054 [P] [US8] Unit test pro GetDrugReimbursement z VZP datasetu v tests/czech/test_vzp_reimbursement.py
- [ ] T055 [P] [US8] Unit test pro GetDiagnosisStats z NZIP datasetu v tests/czech/test_nzip_stats.py

### Implementace US8

- [ ] T056 [US8] Debug DeviceGetter MDR key v src/czechmedmcp/openfda/device_events.py — ověřit formát mezi Searcher a Getter
- [ ] T057 [US8] Napojit VZP statický dataset do GetDrugReimbursement v src/czechmedmcp/czech/vzp/drug_reimbursement.py
- [ ] T058 [US8] Napojit NZIP dataset/fallback do GetDiagnosisStats v src/czechmedmcp/czech/mkn/stats.py
- [ ] T059 [US8] Napojit VZP dataset do GetReimbursement v src/czechmedmcp/czech/sukl/reimbursement.py
- [ ] T060 [US8] Aktualizovat Arcade wrappery v src/czechmedmcp/arcade/czech_tools.py a arcade/individual_tools.py

**Checkpoint**: VZP, NZIP a DeviceGetter funkční

---

## Phase 11: User Story 9 — NRPZS + Metrics (Priority: P3)

**Goal**: GetProviderDetail funguje s IČO, GetPerformanceMetrics sbírá metriky

**Independent Test**: GetProviderDetail vrací data; GetPerformanceMetrics vrací nenulové metriky

### Testy pro US9

- [x] T061 [P] [US9] Unit test pro NRPZS multi-field lookup (IČO, facility ID) v tests/czech/test_nrpzs.py
- [x] T062 [P] [US9] Unit test pro GetPerformanceMetrics s enabled metriky v tests/tdd/test_metrics_enabled.py

### Implementace US9

- [x] T063 [US9] Rozšířit `_nrpzs_get()` o kaskádový lookup (IČO → facility ID → name) v src/czechmedmcp/czech/nrpzs/search.py
- [x] T064 [US9] Změnit `BIOMCP_METRICS_ENABLED` default na `true` v src/czechmedmcp/metrics.py
- [x] T065 [US9] Aktualizovat Arcade wrappery v src/czechmedmcp/arcade/czech_tools.py

**Checkpoint**: NRPZS a metrics funkční

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Regresní validace, Arcade sync, dokumentace

- [x] T066 Spustit `uv run python -m pytest -x --ff -n auto` — ověřit žádné regrese v 1020+ testech
- [x] T067 [P] Spustit `uv run python -m pytest tests/tdd/test_mcp_integration.py` — ověřit 60 nástrojů
- [ ] T068 [P] Spustit `uv run python -m pytest tests/tdd/test_arcade_integration.py` — ověřit 60 Arcade nástrojů
- [ ] T069 Spustit `make check` — ruff, mypy, pre-commit, deptry bez chyb
- [ ] T070 [P] Aktualizovat CLAUDE.md Known Issues — odebrat opravené, přidat nové omezení
- [ ] T071 [P] Aktualizovat test count v CLAUDE.md (z 1020 na nový počet)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Žádné závislosti — start okamžitě
- **Foundational (Phase 2)**: Závisí na Phase 1 — BLOKUJE US5, US8 (VZP/NZIP datasety)
- **US1 (Phase 3)**: Závisí na Phase 1 (T002 konstanta)
- **US2 (Phase 4)**: Závisí na Phase 1
- **US3 (Phase 5)**: Závisí na Phase 1 (T001 sqlite-vec, T004 adresář)
- **US4 (Phase 6)**: Nezávisí na Phase 2
- **US5 (Phase 7)**: Závisí na Phase 2 (T006 VZP data loader)
- **US6 (Phase 8)**: Nezávisí na Phase 2
- **US7 (Phase 9)**: Nezávisí na Phase 2
- **US8 (Phase 10)**: Závisí na Phase 2 (T006, T008 datasety)
- **US9 (Phase 11)**: Nezávisí na Phase 2
- **Polish (Phase 12)**: Závisí na všechny předchozí fáze

### User Story Dependencies

- **US1** (ArticleGetter): Nezávislý — start po Phase 1
- **US2** (SZV): Nezávislý — start po Phase 1
- **US3** (DiagnosisAssist): Nezávislý — start po Phase 1
- **US4** (Recall): Nezávislý — start po Phase 1
- **US5** (DrugsProfile): Závisí na Phase 2 (VZP dataset)
- **US6** (VariantSearcher): Nezávislý — start po Phase 1
- **US7** (GetMedicineDetail): Nezávislý — start po Phase 1
- **US8** (DeviceGetter+VZP+NZIP): Závisí na Phase 2
- **US9** (NRPZS+Metrics): Nezávislý — start po Phase 1

### Parallel Opportunities

US1, US2, US3, US4, US6, US7, US9 mohou běžet PARALELNĚ po Phase 1.
US5, US8 mohou běžet PARALELNĚ po Phase 2.

---

## Implementation Strategy

### MVP First (US1 + US2 + US3 = P1 stories)

1. Phase 1: Setup (T001-T004)
2. Phase 2: Foundational datasets (T005-T009)
3. Phase 3: US1 ArticleGetter (T010-T018) — paralelně s US2, US3
4. Phase 4: US2 SZV (T019-T024)
5. Phase 5: US3 DiagnosisAssist (T025-T032)
6. **STOP a VALIDATE**: 3 P1 stories funkční

### Incremental Delivery

7. Phase 6-9: P2 stories (US4-US8) — paralelizovatelné
8. Phase 11: P3 stories (US9)
9. Phase 12: Polish, regresní testy, dokumentace

---

## Notes

- [P] tasky = různé soubory, žádné závislosti
- [Story] label mapuje task na user story
- Po každém checkpointu spustit regresní testy
- Commit po každém logickém celku
- Celkem: **71 tasků** (4 setup + 5 foundational + 53 story + 6 polish + 3 test tasks)
