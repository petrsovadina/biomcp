"""MCP tool registrations for Czech healthcare modules.

Tools are registered here using @mcp_app.tool() decorator.
This module is imported by czech/__init__.py to auto-register
all Czech tools when the package is loaded.

All tools use ``czechmed_`` prefix per FR-024.
"""

import logging
from typing import Annotated

from pydantic import Field

from czechmedmcp.core import mcp_app
from czechmedmcp.czech.mkn.search import (
    _mkn_browse,
    _mkn_get,
    _mkn_search,
)
from czechmedmcp.czech.mkn.stats import _get_diagnosis_stats
from czechmedmcp.czech.nrpzs.search import (
    _get_codebooks,
    _nrpzs_get,
    _nrpzs_search,
)
from czechmedmcp.czech.sukl.availability import (
    _batch_availability,
    _sukl_availability_check,
)
from czechmedmcp.czech.sukl.getter import (
    _sukl_drug_details,
    _sukl_pil_getter,
    _sukl_spc_getter,
)
from czechmedmcp.czech.sukl.reimbursement import (
    _get_reimbursement,
)
from czechmedmcp.czech.sukl.search import (
    _find_pharmacies,
    _sukl_drug_search,
)
from czechmedmcp.czech.szv.reimbursement import (
    _calculate_reimbursement,
)
from czechmedmcp.czech.szv.search import _szv_get, _szv_search
from czechmedmcp.czech.vzp.drug_reimbursement import (
    _compare_alternatives,
    _get_vzp_drug_reimbursement,
)
from czechmedmcp.czech.workflows.diagnosis_assistant import (
    _diagnosis_assistant,
)
from czechmedmcp.czech.workflows.drug_profile import (
    _drug_profile,
)
from czechmedmcp.czech.workflows.referral_assistant import (
    _referral_assistant,
)
from czechmedmcp.metrics import track_performance

logger = logging.getLogger(__name__)

# -------------------------------------------------------------------
# SUKL Drug Registry Tools (5 tools)
# -------------------------------------------------------------------


@mcp_app.tool()
@track_performance("czechmedmcp.search_medicine")
async def czechmed_search_medicine(
    query: Annotated[
        str,
        Field(
            description=(
                "Drug name, active substance, "
                "SUKL code, or ATC code"
            )
        ),
    ],
    page: Annotated[
        int,
        Field(description="Page number (1-based)", ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Field(
            description="Results per page (1-100)",
            ge=1,
            le=100,
        ),
    ] = 10,
) -> str:
    """Search Czech drug registry (SUKL).

    Supports diacritics-insensitive search.
    """
    return await _sukl_drug_search(query, page, page_size)


@mcp_app.tool()
@track_performance("czechmedmcp.get_medicine_detail")
async def czechmed_get_medicine_detail(
    sukl_code: Annotated[
        str,
        Field(description="SUKL drug identifier (7-digit code)"),
    ],
) -> str:
    """Get full drug details from Czech SUKL registry."""
    return await _sukl_drug_details(sukl_code)


@mcp_app.tool()
@track_performance("czechmedmcp.get_spc")
async def czechmed_get_spc(
    sukl_code: Annotated[
        str,
        Field(description="SUKL drug identifier"),
    ],
    section: Annotated[
        str | None,
        Field(
            description=(
                "Optional SPC section number "
                "(e.g., 4.1-4.9, 5.1-5.3, 6.1-6.6)"
            )
        ),
    ] = None,
) -> str:
    """Get SmPC (Summary of Product Characteristics) for a drug."""
    return await _sukl_spc_getter(sukl_code, section)


@mcp_app.tool()
@track_performance("czechmedmcp.get_pil")
async def czechmed_get_pil(
    sukl_code: Annotated[
        str,
        Field(description="SUKL drug identifier"),
    ],
    section: Annotated[
        str | None,
        Field(
            description=(
                "Optional section: dosage, "
                "contraindications, side_effects, "
                "interactions, pregnancy, storage"
            )
        ),
    ] = None,
) -> str:
    """Get PIL (Patient Information Leaflet) for a drug."""
    return await _sukl_pil_getter(sukl_code, section)


@mcp_app.tool()
@track_performance("czechmedmcp.check_availability")
async def czechmed_check_availability(
    sukl_code: Annotated[
        str,
        Field(description="SUKL drug identifier"),
    ],
) -> str:
    """Check current market availability of a Czech drug."""
    return await _sukl_availability_check(sukl_code)


@mcp_app.tool()
@track_performance("czechmedmcp.get_reimbursement")
async def czechmed_get_reimbursement(
    sukl_code: Annotated[
        str,
        Field(description="7-digit SUKL code"),
    ],
) -> str:
    """Get reimbursement details — price, insurance coverage, copay."""
    return await _get_reimbursement(sukl_code)


@mcp_app.tool()
@track_performance("czechmedmcp.batch_check_availability")
async def czechmed_batch_check_availability(
    sukl_codes: Annotated[
        list[str],
        Field(
            description="List of 7-digit SUKL codes (1-50)",
            min_length=1,
            max_length=50,
        ),
    ],
) -> str:
    """Batch check market availability for multiple drugs."""
    return await _batch_availability(sukl_codes)


@mcp_app.tool()
@track_performance("czechmedmcp.find_pharmacies")
async def czechmed_find_pharmacies(
    city: Annotated[
        str | None,
        Field(description="City name"),
    ] = None,
    postal_code: Annotated[
        str | None,
        Field(description="5-digit postal code"),
    ] = None,
    nonstop_only: Annotated[
        bool,
        Field(
            description="Filter 24/7 pharmacies only"
        ),
    ] = False,
    page: Annotated[
        int,
        Field(description="Page number", ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Field(
            description="Results per page",
            ge=1,
            le=100,
        ),
    ] = 10,
) -> str:
    """Find pharmacies by city, postal code, or 24/7 filter."""
    return await _find_pharmacies(
        city, postal_code, nonstop_only, page, page_size
    )


# -------------------------------------------------------------------
# MKN-10 Diagnosis Code Tools (3 tools)
# -------------------------------------------------------------------


@mcp_app.tool()
@track_performance("czechmedmcp.search_diagnosis")
async def czechmed_search_diagnosis(
    query: Annotated[
        str,
        Field(description="MKN-10 code or free text in Czech"),
    ],
    max_results: Annotated[
        int,
        Field(description="Maximum results", ge=1, le=100),
    ] = 10,
) -> str:
    """Search Czech ICD-10 (MKN-10) diagnoses."""
    return await _mkn_search(query, max_results)


@mcp_app.tool()
@track_performance("czechmedmcp.get_diagnosis_detail")
async def czechmed_get_diagnosis_detail(
    code: Annotated[
        str,
        Field(description='MKN-10 code (e.g., "J06.9")'),
    ],
) -> str:
    """Get full diagnosis details including hierarchy."""
    return await _mkn_get(code)


@mcp_app.tool()
@track_performance("czechmedmcp.browse_diagnosis")
async def czechmed_browse_diagnosis(
    code: Annotated[
        str | None,
        Field(
            description=(
                "Category code to browse "
                "(omit for root/chapters)"
            )
        ),
    ] = None,
) -> str:
    """Browse MKN-10 category hierarchy."""
    return await _mkn_browse(code)


@mcp_app.tool()
@track_performance("czechmedmcp.get_diagnosis_stats")
async def czechmed_get_diagnosis_stats(
    code: Annotated[
        str,
        Field(description="MKN-10 code (e.g. J06)"),
    ],
    year: Annotated[
        int | None,
        Field(
            description="Year (2015-2025)",
            ge=2015,
            le=2025,
        ),
    ] = None,
) -> str:
    """Get epidemiological statistics for a diagnosis."""
    return await _get_diagnosis_stats(code, year)


@mcp_app.tool()
@track_performance("czechmedmcp.diagnosis_assist")
async def czechmed_diagnosis_assist(
    symptoms: Annotated[
        str,
        Field(description="Symptom description in Czech"),
    ],
    max_candidates: Annotated[
        int,
        Field(
            description="Max diagnosis candidates",
            ge=1,
            le=10,
        ),
    ] = 5,
) -> str:
    """Suggest MKN-10 codes for symptoms with PubMed evidence."""
    return await _diagnosis_assistant(
        symptoms, max_candidates
    )


@mcp_app.tool()
@track_performance("czechmedmcp.drug_profile")
async def czechmed_drug_profile(
    query: Annotated[
        str,
        Field(
            description=(
                "Drug name, active substance, "
                "or SUKL code"
            )
        ),
    ],
) -> str:
    """Complete drug profile: registration + availability + reimbursement + evidence."""
    return await _drug_profile(query)


# -------------------------------------------------------------------
# NRPZS Provider Registry Tools (4 tools)
# -------------------------------------------------------------------


@mcp_app.tool()
@track_performance("czechmedmcp.search_providers")
async def czechmed_search_providers(
    query: Annotated[
        str | None,
        Field(description="Provider name or keyword"),
    ] = None,
    city: Annotated[
        str | None,
        Field(description="City name"),
    ] = None,
    specialty: Annotated[
        str | None,
        Field(description="Medical specialty"),
    ] = None,
    page: Annotated[
        int,
        Field(description="Page number", ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Field(description="Results per page", ge=1, le=100),
    ] = 10,
) -> str:
    """Search Czech healthcare providers (NRPZS)."""
    return await _nrpzs_search(
        query, city, specialty, page, page_size
    )


@mcp_app.tool()
@track_performance("czechmedmcp.get_provider_detail")
async def czechmed_get_provider_detail(
    provider_id: Annotated[
        str,
        Field(description="NRPZS provider identifier"),
    ],
) -> str:
    """Get full provider details including workplaces."""
    return await _nrpzs_get(provider_id)


@mcp_app.tool()
@track_performance("czechmedmcp.get_nrpzs_codebooks")
async def czechmed_get_nrpzs_codebooks(
    codebook_type: Annotated[
        str,
        Field(
            description=(
                "Codebook type: specialties, "
                "care_forms, or care_types"
            )
        ),
    ],
) -> str:
    """Get NRPZS reference codebook — specialties, care forms, or care types."""
    return await _get_codebooks(codebook_type)


@mcp_app.tool()
@track_performance("czechmedmcp.referral_assist")
async def czechmed_referral_assist(
    diagnosis_code: Annotated[
        str,
        Field(description="MKN-10 code (e.g. I25.1)"),
    ],
    city: Annotated[
        str,
        Field(description="Patient city"),
    ],
    max_providers: Annotated[
        int,
        Field(
            description="Max providers to return",
            ge=1,
            le=20,
        ),
    ] = 10,
) -> str:
    """Referral assistant: diagnosis to specialty to providers."""
    return await _referral_assistant(
        diagnosis_code, city, max_providers
    )


# -------------------------------------------------------------------
# SZV + VZP Tools (5 tools)
# -------------------------------------------------------------------


@mcp_app.tool()
@track_performance("czechmedmcp.search_procedures")
async def czechmed_search_procedures(
    query: Annotated[
        str,
        Field(description="Procedure code or name"),
    ],
    max_results: Annotated[
        int,
        Field(description="Maximum results", ge=1, le=100),
    ] = 10,
) -> str:
    """Search Czech health procedures (SZV)."""
    return await _szv_search(query, max_results)


@mcp_app.tool()
@track_performance("czechmedmcp.get_procedure_detail")
async def czechmed_get_procedure_detail(
    code: Annotated[
        str,
        Field(description='Procedure code (e.g., "09513")'),
    ],
) -> str:
    """Get full procedure details with point value."""
    return await _szv_get(code)


@mcp_app.tool()
@track_performance("czechmedmcp.calculate_reimbursement")
async def czechmed_calculate_reimbursement(
    procedure_code: Annotated[
        str,
        Field(description="5-digit procedure code"),
    ],
    insurance_code: Annotated[
        str,
        Field(
            description=(
                "Insurance code: 111 (VZP), "
                "201 (VoZP), 205 (ČPZP), "
                "207 (OZP), 209 (ZPŠ), "
                "211 (ZPMV), 213 (RBP)"
            )
        ),
    ] = "111",
    count: Annotated[
        int,
        Field(
            description="Number of procedures",
            ge=1,
        ),
    ] = 1,
) -> str:
    """Calculate CZK reimbursement for a procedure."""
    return await _calculate_reimbursement(
        procedure_code, insurance_code, count
    )


@mcp_app.tool()
@track_performance("czechmedmcp.get_drug_reimbursement")
async def czechmed_get_drug_reimbursement(
    sukl_code: Annotated[
        str,
        Field(description="7-digit SUKL code"),
    ],
) -> str:
    """Get VZP drug reimbursement — group, max price, coverage, copay."""
    return await _get_vzp_drug_reimbursement(sukl_code)


@mcp_app.tool()
@track_performance("czechmedmcp.compare_alternatives")
async def czechmed_compare_alternatives(
    sukl_code: Annotated[
        str,
        Field(
            description="7-digit SUKL code of reference drug"
        ),
    ],
) -> str:
    """Compare drug price alternatives in same ATC group."""
    return await _compare_alternatives(sukl_code)
