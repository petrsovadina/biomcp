"""Arcade tool wrappers for Czech healthcare tools."""

import json
from typing import Annotated

from czechmedmcp.arcade import arcade_app
from czechmedmcp.core import ensure_list
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

# -------------------------------------------------------------------
# SUKL Drug Registry Tools (5 tools)
# -------------------------------------------------------------------


@arcade_app.tool
async def czechmed_search_medicine(
    query: Annotated[
        str,
        "Drug name, active substance, SUKL code, or ATC code",
    ],
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    page_size: Annotated[
        int,
        "Results per page (1-100)",
    ] = 10,
) -> str:
    """Search Czech drug registry (SUKL).

    Supports diacritics-insensitive search.
    """
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    return await _sukl_drug_search(query, page, page_size)


@arcade_app.tool
async def czechmed_get_medicine_detail(
    sukl_code: Annotated[
        str,
        "SUKL drug identifier (7-digit code)",
    ],
) -> str:
    """Get full drug details from Czech SUKL registry."""
    return await _sukl_drug_details(sukl_code)


@arcade_app.tool
async def czechmed_get_spc(
    sukl_code: Annotated[
        str,
        "SUKL drug identifier",
    ],
    section: Annotated[
        str | None,
        "Optional SPC section number "
        "(e.g., 4.1-4.9, 5.1-5.3, 6.1-6.6)",
    ] = None,
) -> str:
    """Get SmPC (Summary of Product Characteristics) for a drug."""
    return await _sukl_spc_getter(sukl_code, section)


@arcade_app.tool
async def czechmed_get_pil(
    sukl_code: Annotated[
        str,
        "SUKL drug identifier",
    ],
    section: Annotated[
        str | None,
        "Optional section: dosage, "
        "contraindications, side_effects, "
        "interactions, pregnancy, storage",
    ] = None,
) -> str:
    """Get PIL (Patient Information Leaflet) for a drug."""
    return await _sukl_pil_getter(sukl_code, section)


@arcade_app.tool
async def czechmed_check_availability(
    sukl_code: Annotated[
        str,
        "SUKL drug identifier",
    ],
) -> str:
    """Check current market availability of a Czech drug."""
    return await _sukl_availability_check(sukl_code)


@arcade_app.tool
async def czechmed_get_reimbursement(
    sukl_code: Annotated[
        str,
        "7-digit SUKL code",
    ],
) -> str:
    """Get reimbursement details -- price, insurance coverage, copay."""
    return await _get_reimbursement(sukl_code)


@arcade_app.tool
async def czechmed_batch_check_availability(
    sukl_codes: Annotated[
        str | None,
        "Comma-separated list of 7-digit SUKL codes (1-50)",
    ] = None,
) -> str:
    """Batch check market availability for multiple drugs."""
    codes: list[str] = ensure_list(
        sukl_codes, split_strings=True
    )
    codes = codes[:50]
    if not codes:
        return json.dumps(
            {"error": "At least one SUKL code is required"},
            ensure_ascii=False,
        )
    return await _batch_availability(codes)


@arcade_app.tool
async def czechmed_find_pharmacies(
    city: Annotated[
        str | None,
        "City name",
    ] = None,
    postal_code: Annotated[
        str | None,
        "5-digit postal code",
    ] = None,
    nonstop_only: Annotated[
        bool,
        "Filter 24/7 pharmacies only",
    ] = False,
    page: Annotated[
        int,
        "Page number",
    ] = 1,
    page_size: Annotated[
        int,
        "Results per page",
    ] = 10,
) -> str:
    """Find pharmacies by city, postal code, or 24/7 filter."""
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    return await _find_pharmacies(
        city, postal_code, nonstop_only, page, page_size
    )


# -------------------------------------------------------------------
# MKN-10 Diagnosis Code Tools (3 tools)
# -------------------------------------------------------------------


@arcade_app.tool
async def czechmed_search_diagnosis(
    query: Annotated[
        str,
        "MKN-10 code or free text in Czech",
    ],
    max_results: Annotated[
        int,
        "Maximum results",
    ] = 10,
) -> str:
    """Search Czech ICD-10 (MKN-10) diagnoses."""
    max_results = max(1, min(100, max_results))
    return await _mkn_search(query, max_results)


@arcade_app.tool
async def czechmed_get_diagnosis_detail(
    code: Annotated[
        str,
        'MKN-10 code (e.g., "J06.9")',
    ],
) -> str:
    """Get full diagnosis details including hierarchy."""
    return await _mkn_get(code)


@arcade_app.tool
async def czechmed_browse_diagnosis(
    code: Annotated[
        str | None,
        "Category code to browse (omit for root/chapters)",
    ] = None,
) -> str:
    """Browse MKN-10 category hierarchy."""
    return await _mkn_browse(code)


@arcade_app.tool
async def czechmed_get_diagnosis_stats(
    code: Annotated[
        str,
        "MKN-10 code (e.g. J06)",
    ],
    year: Annotated[
        int | None,
        "Year (2015-2025)",
    ] = None,
) -> str:
    """Get epidemiological statistics for a diagnosis."""
    if year is not None:
        year = max(2015, min(2025, year))
    return await _get_diagnosis_stats(code, year)


@arcade_app.tool
async def czechmed_diagnosis_assist(
    symptoms: Annotated[
        str,
        "Symptom description in Czech",
    ],
    max_candidates: Annotated[
        int,
        "Max diagnosis candidates",
    ] = 5,
) -> str:
    """Suggest MKN-10 codes for symptoms with PubMed evidence."""
    max_candidates = max(1, min(10, max_candidates))
    return await _diagnosis_assistant(
        symptoms, max_candidates
    )


@arcade_app.tool
async def czechmed_drug_profile(
    query: Annotated[
        str,
        "Drug name, active substance, or SUKL code",
    ],
) -> str:
    """Complete drug profile: registration + availability + reimbursement + evidence."""
    return await _drug_profile(query)


# -------------------------------------------------------------------
# NRPZS Provider Registry Tools (4 tools)
# -------------------------------------------------------------------


@arcade_app.tool
async def czechmed_search_providers(
    query: Annotated[
        str | None,
        "Provider name or keyword",
    ] = None,
    city: Annotated[
        str | None,
        "City name",
    ] = None,
    specialty: Annotated[
        str | None,
        "Medical specialty",
    ] = None,
    page: Annotated[
        int,
        "Page number",
    ] = 1,
    page_size: Annotated[
        int,
        "Results per page",
    ] = 10,
) -> str:
    """Search Czech healthcare providers (NRPZS)."""
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    return await _nrpzs_search(
        query, city, specialty, page, page_size
    )


@arcade_app.tool
async def czechmed_get_provider_detail(
    provider_id: Annotated[
        str,
        "NRPZS provider identifier",
    ],
) -> str:
    """Get full provider details including workplaces."""
    return await _nrpzs_get(provider_id)


@arcade_app.tool
async def czechmed_get_nrpzs_codebooks(
    codebook_type: Annotated[
        str,
        "Codebook type: specialties, care_forms, or care_types",
    ],
) -> str:
    """Get NRPZS reference codebook -- specialties, care forms, or care types."""
    return await _get_codebooks(codebook_type)


@arcade_app.tool
async def czechmed_referral_assist(
    diagnosis_code: Annotated[
        str,
        "MKN-10 code (e.g. I25.1)",
    ],
    city: Annotated[
        str,
        "Patient city",
    ],
    max_providers: Annotated[
        int,
        "Max providers to return",
    ] = 10,
) -> str:
    """Referral assistant: diagnosis to specialty to providers."""
    max_providers = max(1, min(20, max_providers))
    return await _referral_assistant(
        diagnosis_code, city, max_providers
    )


# -------------------------------------------------------------------
# SZV + VZP Tools (5 tools)
# -------------------------------------------------------------------


@arcade_app.tool
async def czechmed_search_procedures(
    query: Annotated[
        str,
        "Procedure code or name",
    ],
    max_results: Annotated[
        int,
        "Maximum results",
    ] = 10,
) -> str:
    """Search Czech health procedures (SZV)."""
    max_results = max(1, min(100, max_results))
    return await _szv_search(query, max_results)


@arcade_app.tool
async def czechmed_get_procedure_detail(
    code: Annotated[
        str,
        'Procedure code (e.g., "09513")',
    ],
) -> str:
    """Get full procedure details with point value."""
    return await _szv_get(code)


@arcade_app.tool
async def czechmed_calculate_reimbursement(
    procedure_code: Annotated[
        str,
        "5-digit procedure code",
    ],
    insurance_code: Annotated[
        str,
        "Insurance code: 111 (VZP), "
        "201 (VoZP), 205 (CPZP), "
        "207 (OZP), 209 (ZPS), "
        "211 (ZPMV), 213 (RBP)",
    ] = "111",
    count: Annotated[
        int,
        "Number of procedures",
    ] = 1,
) -> str:
    """Calculate CZK reimbursement for a procedure."""
    count = max(1, count)
    return await _calculate_reimbursement(
        procedure_code, insurance_code, count
    )


@arcade_app.tool
async def czechmed_get_drug_reimbursement(
    sukl_code: Annotated[
        str,
        "7-digit SUKL code",
    ],
) -> str:
    """Get VZP drug reimbursement -- group, max price, coverage, copay."""
    return await _get_vzp_drug_reimbursement(sukl_code)


@arcade_app.tool
async def czechmed_compare_alternatives(
    sukl_code: Annotated[
        str,
        "7-digit SUKL code of reference drug",
    ],
) -> str:
    """Compare drug price alternatives in same ATC group."""
    return await _compare_alternatives(sukl_code)
