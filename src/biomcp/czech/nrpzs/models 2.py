"""Pydantic v2 models for NRPZS healthcare provider registry data."""

from pydantic import BaseModel, Field


class Address(BaseModel):
    """Physical address of a provider or workplace."""

    street: str | None = None
    city: str | None = None
    postal_code: str | None = None
    region: str | None = None


class Contact(BaseModel):
    """Contact information for a provider or workplace."""

    phone: str | None = None
    email: str | None = None
    website: str | None = None


class Workplace(BaseModel):
    """A single workplace (misto poskytovani) for a provider."""

    workplace_id: str
    name: str
    address: Address | None = None
    specialties: list[str] = Field(default_factory=list)
    contact: Contact | None = None


class HealthcareProvider(BaseModel):
    """Full healthcare provider record from NRPZS registry."""

    provider_id: str = Field(description="NRPZS provider identifier")
    name: str = Field(description="Provider or facility name")
    legal_form: str | None = Field(
        default=None, description="Legal form (e.g., 'fyzická osoba')"
    )
    ico: str | None = Field(
        default=None, description="Company registration number (IČO)"
    )
    address: Address | None = Field(default=None, description="Main address")
    specialties: list[str] = Field(
        default_factory=list,
        description="Medical specialties provided",
    )
    care_types: list[str] = Field(
        default_factory=list,
        description="Types of care (e.g., 'ambulantní', 'lůžková')",
    )
    workplaces: list[Workplace] = Field(
        default_factory=list,
        description="Individual workplaces",
    )
    registration_number: str | None = Field(
        default=None, description="Registry registration number"
    )
    source: str = Field(default="NRPZS")


class CodebookItem(BaseModel):
    """Single item in an NRPZS codebook."""

    code: str
    name: str


class Codebook(BaseModel):
    """NRPZS reference codebook."""

    codebook_type: str
    items: list[CodebookItem] = Field(
        default_factory=list
    )
    total: int = 0
    source: str = "NRPZS"


class ReferralResult(BaseModel):
    """Referral assistant result."""

    diagnosis_code: str
    diagnosis_name: str = ""
    recommended_specialty: str = ""
    city: str = ""
    providers: list[dict] = Field(
        default_factory=list
    )
    source: str = "NRPZS"


class ProviderSummary(BaseModel):
    """Summary provider info for search results."""

    provider_id: str
    name: str
    city: str | None = None
    specialties: list[str] = Field(default_factory=list)


class ProviderSearchResult(BaseModel):
    """Paginated healthcare provider search results."""

    total: int = Field(description="Total number of matches")
    page: int = Field(description="Current page number")
    page_size: int = Field(default=10, description="Results per page")
    results: list[ProviderSummary] = Field(default_factory=list)
