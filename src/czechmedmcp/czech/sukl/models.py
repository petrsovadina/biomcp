"""Pydantic v2 models for SUKL drug registry data."""

from pydantic import BaseModel, Field


class ActiveSubstance(BaseModel):
    """Active substance in a drug."""

    name: str = Field(description="Substance name")
    strength: str | None = Field(
        default=None, description="Strength (e.g., '400 mg')"
    )


class AvailabilityStatus(BaseModel):
    """Drug market availability status."""

    status: str = Field(description="'available', 'limited', or 'unavailable'")
    last_checked: str | None = Field(
        default=None, description="ISO 8601 datetime"
    )
    note: str | None = Field(
        default=None, description="Additional availability note"
    )


class Drug(BaseModel):
    """Full drug record from SUKL registry."""

    sukl_code: str = Field(description="7-digit SUKL identifier")
    name: str = Field(description="Trade name")
    active_substances: list[ActiveSubstance] = Field(default_factory=list)
    pharmaceutical_form: str | None = Field(
        default=None, description="Dosage form"
    )
    atc_code: str | None = Field(
        default=None, description="ATC classification code"
    )
    registration_number: str | None = Field(
        default=None, description="Marketing authorization number"
    )
    mah: str | None = Field(
        default=None, description="Marketing Authorization Holder"
    )
    registration_valid_to: str | None = Field(
        default=None, description="Validity date (ISO 8601)"
    )
    availability: AvailabilityStatus | None = Field(default=None)
    spc_url: str | None = Field(
        default=None, description="URL to SmPC document"
    )
    pil_url: str | None = Field(
        default=None, description="URL to PIL document"
    )
    source: str = Field(default="SUKL")


class DrugSummary(BaseModel):
    """Summary drug info for search results."""

    sukl_code: str
    name: str
    active_substance: str | None = Field(
        default=None, description="Primary active substance"
    )
    atc_code: str | None = None
    pharmaceutical_form: str | None = None


class DrugSearchResult(BaseModel):
    """Paginated drug search results."""

    total: int = Field(description="Total number of matches")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Results per page")
    results: list[DrugSummary] = Field(default_factory=list)


class Reimbursement(BaseModel):
    """Drug reimbursement details from SUKL."""

    sukl_code: str
    name: str
    manufacturer_price: float | None = Field(
        None, description="Cena výrobce CZK"
    )
    max_retail_price: float | None = Field(
        None, description="Max. maloobchodní cena CZK"
    )
    reimbursement_amount: float | None = Field(
        None, description="Úhrada pojišťovnou CZK"
    )
    patient_copay: float | None = Field(
        None, description="Doplatek pacienta CZK"
    )
    reimbursement_group: str | None = None
    conditions: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    source: str = "SUKL"


class DocumentSection(BaseModel):
    """Single section of a PIL or SPC document."""

    section_id: str = Field(description="Section key")
    title: str = Field(description="Section heading")
    content: str = Field(description="Section text")


class DocumentContent(BaseModel):
    """Full PIL or SPC document with parsed sections."""

    sukl_code: str
    document_type: str = Field(
        description="PIL or SPC"
    )
    title: str = ""
    sections: list[DocumentSection] = Field(
        default_factory=list
    )
    full_text: str | None = None
    url: str = ""
    source: str = "SUKL"


class DrugProfileSection(BaseModel):
    """Single section of a drug profile."""

    section: str = Field(
        description=(
            "registration, availability, "
            "reimbursement, or evidence"
        )
    )
    status: str = Field(
        description="ok or error"
    )
    data: dict | None = None
    error: str | None = None


class DrugProfile(BaseModel):
    """Complete drug profile from multiple sources."""

    query: str
    sukl_code: str = ""
    sections: list[DrugProfileSection] = Field(
        default_factory=list
    )
    source: str = "SUKL+PubMed"


class Pharmacy(BaseModel):
    """Pharmacy from SUKL registry."""

    pharmacy_id: str = ""
    name: str = ""
    city: str = ""
    postal_code: str = ""
    address: str = ""
    phone: str | None = None
    nonstop: bool = False
    source: str = "SUKL"


class PharmacySearchResult(BaseModel):
    """Paginated pharmacy search results."""

    total: int = 0
    page: int = 1
    page_size: int = 10
    results: list[Pharmacy] = Field(
        default_factory=list
    )


class BatchAvailabilityItem(BaseModel):
    """Single drug availability in a batch check."""

    sukl_code: str = Field(description="7-digit SUKL code")
    name: str | None = None
    status: str = Field(
        description=(
            "available|shortage|withdrawn|"
            "suspended|unknown"
        )
    )
    last_delivery: str | None = None
    error: str | None = None


class BatchAvailabilityResult(BaseModel):
    """Aggregated batch availability check result."""

    total_checked: int
    available_count: int
    shortage_count: int
    error_count: int
    items: list[BatchAvailabilityItem]
    checked_at: str  # ISO 8601
    source: str = "SUKL"
