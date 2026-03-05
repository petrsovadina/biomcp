# Data Model: CzechMedMCP

**Branch**: `001-czechmedmcp-implementation` | **Date**: 2026-03-02

## Entity Overview

```
Lék (Drug) ──1:N──▶ Dostupnost (Availability)
     │               ▲ (batch: N drugs)
     │──1:1──▶ Úhrada (Reimbursement)
     │──1:N──▶ Alternativa (DrugAlternative)
     │──1:1──▶ PIL / SPC (DocumentContent)
     │
Diagnóza (Diagnosis) ──1:N──▶ Statistika (DiagnosisStats)
     │──N:M──▶ Poskytovatel (Provider)  [via workflow]
     │
Poskytovatel (Provider) ──1:N──▶ Pracoviště (Workplace)
     │
Výkon (Procedure) ──1:1──▶ Kalkulace (ReimbursementCalc)
     │
Lékárna (Pharmacy) [standalone entity]
     │
Číselník (Codebook) [reference data]
```

## New Pydantic Models

### BatchAvailabilityResult (SÚKL)

```python
class BatchAvailabilityItem(BaseModel):
    sukl_code: str = Field(description="7-digit SUKL code")
    name: str | None = None
    status: str = Field(description="available|shortage|withdrawn|suspended|unknown")
    last_delivery: str | None = None
    error: str | None = None

class BatchAvailabilityResult(BaseModel):
    total_checked: int
    available_count: int
    shortage_count: int
    error_count: int
    items: list[BatchAvailabilityItem]
    checked_at: str  # ISO 8601
    source: str = "SUKL"
```

### Reimbursement (SÚKL)

```python
class Reimbursement(BaseModel):
    sukl_code: str
    name: str
    manufacturer_price: float | None = Field(None, description="Cena výrobce CZK")
    max_retail_price: float | None = Field(None, description="Max. maloobchodní cena CZK")
    reimbursement_amount: float | None = Field(None, description="Úhrada pojišťovnou CZK")
    patient_copay: float | None = Field(None, description="Doplatek pacienta CZK")
    reimbursement_group: str | None = None
    conditions: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    source: str = "SUKL"
```

### Pharmacy (SÚKL)

```python
class Pharmacy(BaseModel):
    name: str
    address: str
    city: str
    postal_code: str | None = None
    phone: str | None = None
    email: str | None = None
    opening_hours: str | None = None
    is_nonstop: bool = False
    latitude: float | None = None
    longitude: float | None = None
    source: str = "SUKL"

class PharmacySearchResult(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[Pharmacy]
```

### DocumentContent (SÚKL PIL/SPC)

```python
class DocumentSection(BaseModel):
    section_id: str
    title: str
    content: str

class DocumentContent(BaseModel):
    sukl_code: str
    document_type: str  # "PIL" | "SPC"
    title: str
    sections: list[DocumentSection]
    full_text: str | None = None
    url: str
    source: str = "SUKL"
```

### DiagnosisStats (MKN-10)

```python
class AgeGroupStats(BaseModel):
    age_group: str  # "0-14", "15-24", "25-34", ...
    count: int

class RegionStats(BaseModel):
    region: str
    count: int

class DiagnosisStats(BaseModel):
    code: str
    name_cs: str
    year: int
    total_cases: int
    male_count: int | None = None
    female_count: int | None = None
    age_distribution: list[AgeGroupStats] = Field(default_factory=list)
    region_distribution: list[RegionStats] = Field(default_factory=list)
    source: str = "NZIP"
```

### Codebook (NRPZS)

```python
class CodebookItem(BaseModel):
    code: str
    name: str

class Codebook(BaseModel):
    codebook_type: str  # "specialties" | "care_forms" | "care_types"
    items: list[CodebookItem]
    total: int
    source: str = "NRPZS"
```

### ReimbursementCalculation (SZV)

```python
class ReimbursementCalculation(BaseModel):
    procedure_code: str
    procedure_name: str
    point_value: int
    insurance_code: str  # "111" (VZP), "201" (VoZP), etc.
    insurance_name: str
    rate_per_point: float  # CZK za bod
    count: int = 1
    unit_price_czk: float
    total_czk: float
    patient_copay_czk: float = 0.0
    source: str = "SZV/MZ_CR"
```

### DrugReimbursement (VZP)

```python
class DrugReimbursement(BaseModel):
    sukl_code: str
    name: str
    reimbursement_group: str | None = None
    max_price: float | None = None
    reimbursement_amount: float | None = None
    patient_copay: float | None = None
    prescription_conditions: str | None = None
    valid_from: str | None = None
    source: str = "VZP"
```

### DrugAlternative (VZP cross-module)

```python
class DrugAlternative(BaseModel):
    sukl_code: str
    name: str
    atc_code: str
    patient_copay: float | None = None
    savings_vs_reference: float | None = None
    is_generic: bool = False
    availability_status: str | None = None
    source: str = "SUKL+VZP"

class AlternativeComparison(BaseModel):
    reference_sukl_code: str
    reference_name: str
    reference_copay: float | None = None
    atc_code: str
    alternatives: list[DrugAlternative]
    total_alternatives: int
    source: str = "SUKL+VZP"
```

### Workflow Output Models

```python
class DrugProfileSection(BaseModel):
    section: str  # "registration", "availability", "reimbursement", "evidence"
    status: str   # "ok", "error", "unavailable"
    data: dict | None = None
    error: str | None = None

class DrugProfile(BaseModel):
    query: str
    sukl_code: str | None = None
    sections: list[DrugProfileSection]
    completed_at: str  # ISO 8601
    source: str = "CzechMedMCP"

class DiagnosisAssistantResult(BaseModel):
    query: str
    candidates: list[dict]  # MKN-10 codes with details
    evidence: list[dict]    # PubMed articles
    disclaimer: str = "Tento nástroj je pouze podpůrný. Konečná diagnóza je vždy na lékaři."
    source: str = "CzechMedMCP"

class ReferralResult(BaseModel):
    diagnosis_code: str
    diagnosis_name: str
    recommended_specialty: str | None = None
    providers: list[dict]
    city: str
    source: str = "CzechMedMCP"
```

## Existing Models (unchanged)

Stávající modely v `models.py` každého modulu zůstávají beze změny:
- **SÚKL**: `Drug`, `DrugSummary`, `DrugSearchResult`, `ActiveSubstance`, `AvailabilityStatus`
- **MKN-10**: `Diagnosis`, `DiagnosisHierarchy`, `DiagnosisCategory`, `Modifier`
- **NRPZS**: `HealthcareProvider`, `ProviderSummary`, `ProviderSearchResult`, `Address`, `Contact`, `Workplace`
- **SZV**: `HealthProcedure`, `ProcedureSearchResult`
- **VZP**: `CodebookEntry`, `CodebookSearchResult`

## Validation Rules

| Entity | Field | Rule |
|--------|-------|------|
| Lék | `sukl_code` | `^\\d{7}$` (7 číslic) |
| Diagnóza | `code` | `^[A-Z]\\d{2}(\\.\\d{1,2})?$` |
| Poskytovatel | `ico` | `^\\d{8}$` (8 číslic) |
| Výkon | `code` | `^\\d{5}$` (5 číslic) |
| Lékárna | `postal_code` | `^\\d{5}$` (5 číslic) |
| Batch | `sukl_codes` | `len(codes) >= 1 and len(codes) <= 50` |
| Pojišťovna | `insurance_code` | `^\\d{3}$` (111, 201, 205, 207, 209, 211, 213) |

## State Transitions

Žádné entity nemají formální state machine. Jedinou relevantní stavovou informací je `AvailabilityStatus.status`:

```
available ──▶ shortage ──▶ withdrawn
    ▲              │              │
    └──────────────┘              │
    ▲                             │
    └── suspended ◀───────────────┘
```

Stavy jsou read-only (z SÚKL API), systém je nezapisuje.
