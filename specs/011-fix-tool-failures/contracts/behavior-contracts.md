# API Behavior Contracts: Fix Tool Failures

Tento soubor definuje očekávané chování opravených nástrojů (input → output kontrakty).

## ArticleGetter

### Contract: PMID input
- **Input**: `pmid="38768446"`
- **Output**: Markdown s title, authors, journal, date, abstract (neprázdný), DOI, PMID
- **Error**: `"Article not found: {pmid}"` (ne server error)

### Contract: DOI input
- **Input**: `pmid="10.1038/s41586-024-07386-0"`
- **Output**: Markdown s metadata z Europe PMC
- **Error**: `"Article not found for DOI: {doi}"`

### Contract: PMC ID input (NEW)
- **Input**: `pmid="PMC11193658"`
- **Output**: Interní konverze PMC→PMID, pak PubTator3 fetch → stejný formát jako PMID
- **Error**: `"Cannot convert PMC ID: {pmc_id}"`

---

## SearchProcedures / GetProcedureDetail

### Contract: Search by code
- **Input**: `query="09513"`
- **Output**: JSON list s `{code, name, category, specialty, point_value, time_minutes}`
- **Error**: `{"error": "SZV data unavailable: {reason}"}` (ne server error)

### Contract: Get detail
- **Input**: `code="09513"`
- **Output**: JSON s kompletním detailem výkonu
- **Error**: `{"error": "Procedure not found: {code}"}`

---

## DiagnosisAssist

### Contract: Czech symptoms
- **Input**: `symptoms="bolest hlavy, horečka, kašel"`
- **Output**: JSON s `candidates: [{code, name_cs, score, evidence: [...]}]`, min 1 kandidát
- **Scoring**: Hybridní (cosine similarity + keyword match), seřazeno desc

### Contract: English symptoms
- **Input**: `symptoms="headache, fever, cough"`
- **Output**: Stejný formát jako CZ (multilingvní embedding)

---

## RecallSearcher / RecallGetter

### Contract: Search by drug
- **Input**: `drug="metformin"`
- **Query**: `openfda.brand_name:"metformin" OR openfda.generic_name:"metformin" OR product_description:"metformin"`
- **Output**: Markdown s recall záznamy

### Contract: Get by recall number
- **Input**: `recall_number="D-0325-2021"`
- **Output**: Markdown s kompletním detailem

---

## DrugsProfile

### Contract: Partial return
- **Input**: `query="ibuprofen"`
- **Output**: JSON/Markdown se sekcemi:
  - `registration: {status: "ok", data: {...}}`
  - `availability: {status: "ok", data: {...}}`
  - `reimbursement: {status: "unavailable", message: "VZP data nedostupná pro tento lék"}`
  - `evidence: {status: "ok", data: [...]}`

---

## VariantSearcher

### Contract: Gene-only rejection
- **Input**: `gene="TP53"` (bez dalších filtrů)
- **Output**: `InvalidParameterError`: "Gene-only query může vrátit příliš mnoho výsledků. Specifikujte alespoň jeden z: hgvsp, rsid, region, nebo frequency_max."

---

## GetMedicineDetail

### Contract: Substance names
- **Input**: `sukl_code="0124137"`
- **Output**: `active_substances: [{substance_code: 1593, substance_name: "IBUPROFENUM", strength: "400 MG"}]`

### Contract: SPC/PIL URL
- **Output**: `spc_url: "https://..." | null`, `pil_url: "https://..." | null`
- Pokud null: `spc_note: "SPC dokument není dostupný v SÚKL databázi"`

---

## GetDrugReimbursement

### Contract: Data available
- **Input**: `sukl_code="0020621"`
- **Output**: Nenulová pole z VZP statického datasetu

### Contract: Data unavailable
- **Output**: `{"message": "Úhradová data nejsou dostupná pro tento SÚKL kód", "source": "VZP", "note": "Lék nemusí být v úhradovém seznamu"}`

---

## GetPerformanceMetrics

### Contract: Metrics enabled (default)
- **Output**: `{request_count: N, avg_duration_ms: X, error_rate: Y, cache_hit_rate: Z, ...}`
- **Podmínka**: `BIOMCP_METRICS_ENABLED` default změněn na `true`
