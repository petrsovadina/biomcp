"""Pydantic v2 models for SZV health procedures data."""

from pydantic import BaseModel, Field


class HealthProcedure(BaseModel):
    """Full health procedure record from SZV/MZCR registry."""

    code: str = Field(description="Procedure code (e.g., '09513')")
    name: str = Field(description="Procedure name")
    category: str | None = Field(
        default=None, description="Category code (e.g., '09')"
    )
    category_name: str | None = Field(
        default=None, description="Category descriptive name"
    )
    point_value: int | None = Field(
        default=None, description="Point value of the procedure"
    )
    time_minutes: int | None = Field(
        default=None, description="Estimated procedure time in minutes"
    )
    frequency_limit: str | None = Field(
        default=None,
        description="Frequency limit (e.g., '1x per year')",
    )
    specialty_codes: list[str] = Field(
        default_factory=list,
        description="Medical specialty codes permitted to perform this",
    )
    material_requirements: str | None = Field(
        default=None, description="Required materials or instruments"
    )
    notes: str | None = Field(
        default=None, description="Additional procedural notes"
    )
    source: str = Field(default="MZCR/SZV")


class ReimbursementCalculation(BaseModel):
    """Reimbursement calculation for a procedure."""

    procedure_code: str
    procedure_name: str
    point_value: int
    insurance_code: str
    insurance_name: str
    rate_per_point: float
    count: int = 1
    unit_price_czk: float = Field(
        description="Points * rate"
    )
    total_czk: float = Field(
        description="unit_price * count"
    )
    patient_copay_czk: float = 0.0
    source: str = "MZCR/SZV"


class ProcedureSearchResult(BaseModel):
    """Paginated health procedure search results."""

    total: int = Field(description="Total number of matches")
    results: list[dict] = Field(
        default_factory=list,
        description=(
            "List of procedure summaries with keys: "
            "code, name, point_value, category"
        ),
    )
