"""Pydantic v2 models for MKN-10 (Czech ICD-10) classification."""

from pydantic import BaseModel, Field


class DiagnosisHierarchy(BaseModel):
    """Hierarchical position of a diagnosis in MKN-10."""

    chapter: str = Field(description="Chapter code, e.g., 'X'")
    chapter_name: str = Field(
        description="Chapter name in Czech, e.g., 'Nemoci dýchací soustavy'"
    )
    block: str = Field(description="Block code, e.g., 'J00-J06'")
    block_name: str = Field(description="Block name in Czech")
    category: str = Field(description="Category code, e.g., 'J06'")


class Modifier(BaseModel):
    """Diagnostic modifier code."""

    code: str = Field(description="Modifier code")
    name: str = Field(description="Modifier name in Czech")


class Diagnosis(BaseModel):
    """Full diagnosis record from MKN-10."""

    code: str = Field(description="Diagnosis code, e.g., 'J06.9'")
    name_cs: str = Field(description="Diagnosis name in Czech")
    name_en: str | None = Field(
        default=None, description="Diagnosis name in English"
    )
    definition: str | None = Field(
        default=None, description="Textual definition"
    )
    hierarchy: DiagnosisHierarchy | None = Field(
        default=None, description="Hierarchical position in MKN-10"
    )
    includes: list[str] = Field(
        default_factory=list,
        description="Included conditions",
    )
    excludes: list[str] = Field(
        default_factory=list,
        description="Excluded conditions",
    )
    modifiers: list[Modifier] = Field(
        default_factory=list,
        description="Diagnostic modifiers",
    )
    source: str = Field(default="UZIS/MKN-10")


class DiagnosisCategory(BaseModel):
    """Node in the MKN-10 classification hierarchy."""

    code: str = Field(description="Class code")
    name: str = Field(description="Class name in Czech")
    type: str = Field(description="One of: 'chapter', 'block', 'category'")
    children: list["DiagnosisCategory"] = Field(
        default_factory=list,
        description="Direct child nodes",
    )
    parent_code: str | None = Field(
        default=None, description="Parent class code"
    )


class AgeGroupStats(BaseModel):
    """Epidemiological stats for an age group."""

    age_group: str = Field(
        description="e.g. '0-14', '15-24', '25-34'"
    )
    count: int


class RegionStats(BaseModel):
    """Epidemiological stats for a region."""

    region: str
    count: int


class DiagnosisStats(BaseModel):
    """Epidemiological statistics for a diagnosis."""

    code: str
    name_cs: str
    year: int
    total_cases: int
    male_count: int | None = None
    female_count: int | None = None
    age_distribution: list[AgeGroupStats] = Field(
        default_factory=list
    )
    region_distribution: list[RegionStats] = Field(
        default_factory=list
    )
    source: str = "NZIP"


class DiagnosisAssistantResult(BaseModel):
    """Result from diagnosis assistant workflow."""

    query: str
    candidates: list[dict] = Field(default_factory=list)
    evidence: list[dict] = Field(default_factory=list)
    disclaimer: str = (
        "Tento nástroj slouží pouze jako pomůcka. "
        "Konečná diagnóza je vždy na lékaři."
    )
