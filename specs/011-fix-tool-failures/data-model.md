# Data Model: Fix Tool Failures

## Nové entity

### DiagnosisEmbeddingIndex

Vektorizovaný MKN-10 katalog pro DiagnosisAssist.

| Field | Type | Description |
| ----- | ---- | ----------- |
| code | str | MKN-10 kód (e.g., "J45.0") |
| name_cs | str | Český název diagnózy |
| text_blob | str | Konkatenace: name_cs + synonyms + includes + excludes |
| embedding | vector[384] | Embedding z embed-multilingual-light-v3.0 (384-dim) |

**Storage**: SQLite-vec nebo FAISS in-memory index
**Lifecycle**: Build při prvním DiagnosisAssist volání, cache na disk (TTL = CACHE_TTL_MONTH)
**Scale**: ~14,000 MKN-10 kódů × 384-dim = ~21 MB

### VZPReimbursementRecord

Statický záznam z VZP úhradového seznamu.

| Field | Type | Description |
| ----- | ---- | ----------- |
| sukl_code | str | 7-místný SÚKL kód |
| atc_code | str | ATC kód |
| drug_name | str | Název léčivého přípravku |
| reimbursement_group | str | Úhradová skupina |
| max_price | float | Maximální cena (CZK) |
| reimbursement_amount | float | Výše úhrady (CZK) |
| patient_copay | float | Doplatek pacienta (CZK) |
| valid_from | str | Datum platnosti |

**Storage**: CSV soubor v `czech/vzp/data/`, in-memory dict po načtení
**Lifecycle**: Statický, aktualizace manuální
**Scale**: ~8,000-10,000 záznamů

### NZIPHospitalizationRecord

Statický záznam z NZIP hospitalizační statistiky.

| Field | Type | Description |
| ----- | ---- | ----------- |
| mkn_code | str | MKN-10 kód |
| year | int | Rok |
| total_cases | int | Celkový počet případů |
| male_count | int | Mužů |
| female_count | int | Žen |
| age_groups | dict[str, int] | Věková distribuce |

**Storage**: CSV soubor v `czech/mkn/data/`, in-memory dict po načtení
**Scale**: ~5,000 kódů × roky

## Modifikované entity

### ArticleGetter — rozšířená detekce identifikátorů

Stávající flow `is_pmid() / is_doi()` rozšířen o `is_pmc_id()`:
- PMID: `^\d+$` → PubTator3 API
- DOI: `^10\.\d{4,9}/` → Europe PMC API
- PMC ID: `^PMC\d{7,8}$` → NCBI ID Converter → PMID → PubTator3

### VariantQuery — nová validace

Pydantic `@model_validator` rozšířen:
- gene-only (bez hgvsp/rsid/region) → `InvalidParameterError`
- gene + significance-only → `InvalidParameterError`

### DrugProfileSection — status field

Existující model rozšířen o explicitní status:
- `status: "ok" | "unavailable" | "error"`
- `error_message: str | None` — vysvětlení nedostupnosti

### SUKLSubstance — substance_name

Rozšíření:
- `substance_name: str | None` — textový název (lookup přes SUKL API `/latky/`)
