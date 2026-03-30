"""Arcade wrappers for the unified search and fetch router tools."""

import json
from typing import Annotated, Literal

from czechmedmcp.arcade import arcade_app
from czechmedmcp.router import fetch as _fetch
from czechmedmcp.router import search as _search

# Domain literal shared by both tools
DomainLiteral = Literal[
    "article",
    "trial",
    "variant",
    "gene",
    "drug",
    "disease",
    "nci_organization",
    "nci_intervention",
    "nci_biomarker",
    "nci_disease",
    "fda_adverse",
    "fda_label",
    "fda_device",
    "fda_approval",
    "fda_recall",
    "fda_shortage",
    "sukl_drug",
    "mkn_diagnosis",
    "nrpzs_provider",
    "szv_procedure",
    "vzp_reimbursement",
]

DetailLiteral = Literal[
    "protocol",
    "locations",
    "outcomes",
    "references",
    "all",
    "full",
]


def _clamp(value: int | None, lo: int, hi: int) -> int | None:
    """Clamp an integer between lo and hi, or return None."""
    if value is None:
        return None
    return max(lo, min(hi, value))


def _serialize(result: object) -> str:
    if isinstance(result, str):
        return result
    return json.dumps(result, ensure_ascii=False)


@arcade_app.tool
async def search(
    query: Annotated[
        str,
        "Unified search query (e.g., 'gene:BRAF AND trials.condition:melanoma'). If provided, other parameters are ignored.",
    ],
    call_benefit: Annotated[
        str | None,
        "Brief explanation of why this search is being performed and expected benefit. Helps improve search accuracy and provides context for analytics. Highly recommended for better results.",
    ] = None,
    domain: Annotated[
        DomainLiteral | None,
        "Domain to search: 'article' for papers/literature ABOUT genes/variants/diseases, 'trial' for clinical studies, 'variant' for genetic variant DATABASE RECORDS, 'gene' for gene information from MyGene.info, 'drug' for drug/chemical information from MyChem.info, 'disease' for disease information from MyDisease.info, 'nci_organization' for NCI cancer centers/sponsors, 'nci_intervention' for NCI drugs/devices/procedures, 'nci_biomarker' for NCI trial eligibility biomarkers, 'nci_disease' for NCI cancer vocabulary, 'fda_adverse' for FDA adverse event reports, 'fda_label' for FDA drug labels, 'fda_device' for FDA device events, 'fda_approval' for FDA drug approvals, 'fda_recall' for FDA drug recalls, 'fda_shortage' for FDA drug shortages, 'sukl_drug' for Czech SUKL drug registry, 'mkn_diagnosis' for Czech ICD-10 (MKN-10), 'nrpzs_provider' for Czech healthcare providers, 'szv_procedure' for Czech health procedures, 'vzp_reimbursement' for Czech VZP drug reimbursement",
    ] = None,
    genes: Annotated[str | None, "Gene symbols (comma-separated)"] = None,
    diseases: Annotated[
        str | None, "Disease terms (comma-separated)"
    ] = None,
    variants: Annotated[
        str | None, "Variant strings (comma-separated)"
    ] = None,
    chemicals: Annotated[
        str | None, "Drug/chemical terms (comma-separated)"
    ] = None,
    keywords: Annotated[
        str | None, "Free-text keywords (comma-separated)"
    ] = None,
    conditions: Annotated[
        str | None, "Trial conditions (comma-separated)"
    ] = None,
    interventions: Annotated[
        str | None, "Trial interventions (comma-separated)"
    ] = None,
    recruiting_status: Annotated[
        str | None,
        "Trial status filter (OPEN, CLOSED, or ANY)",
    ] = None,
    phase: Annotated[str | None, "Trial phase filter"] = None,
    significance: Annotated[
        str | None, "Variant clinical significance"
    ] = None,
    lat: Annotated[
        float | None,
        "Latitude for trial location search. AI agents should geocode city names (e.g., 'Cleveland' -> 41.4993) before using.",
    ] = None,
    long: Annotated[
        float | None,
        "Longitude for trial location search. AI agents should geocode city names (e.g., 'Cleveland' -> -81.6944) before using.",
    ] = None,
    distance: Annotated[
        int | None,
        "Distance in miles from lat/long for trial search (default: 50 miles if lat/long provided)",
    ] = None,
    page: Annotated[int, "Page number (minimum: 1)"] = 1,
    page_size: Annotated[int, "Results per page (1-100)"] = 10,
    max_results_per_domain: Annotated[
        int | None,
        "Max results per domain (unified search only)",
    ] = None,
    explain_query: Annotated[
        bool,
        "Return query explanation (unified search only)",
    ] = False,
    get_schema: Annotated[
        bool,
        "Return searchable fields schema instead of results",
    ] = False,
    api_key: Annotated[
        str | None,
        "NCI API key for searching NCI domains (nci_organization, nci_intervention, nci_biomarker, nci_disease). Required for NCI searches. Get a free key at: https://clinicaltrialsapi.cancer.gov/",
    ] = None,
) -> str:
    """Search biomedical literature, clinical trials, genetic variants, genes, drugs, and diseases.

    This tool provides access to biomedical data from PubMed/PubTator3, ClinicalTrials.gov,
    MyVariant.info, and the BioThings suite (MyGene.info, MyChem.info, MyDisease.info).
    It supports two search modes:

    ## 1. UNIFIED QUERY LANGUAGE
    Use the 'query' parameter with field-based syntax for precise cross-domain searches.

    Syntax:
    - Basic: "gene:BRAF"
    - AND logic: "gene:BRAF AND disease:melanoma"
    - OR logic: "gene:PTEN AND (R173 OR Arg173 OR 'position 173')"
    - Domain-specific: "trials.condition:melanoma AND trials.phase:3"

    ## 2. DOMAIN-SPECIFIC SEARCH
    Use the 'domain' parameter with specific filters for targeted searches.

    Domains: article, trial, variant, gene, drug, disease,
    nci_organization, nci_intervention, nci_biomarker, nci_disease,
    fda_adverse, fda_label, fda_device, fda_approval, fda_recall, fda_shortage,
    sukl_drug, mkn_diagnosis, nrpzs_provider, szv_procedure, vzp_reimbursement.
    """
    # Clamp pagination
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    # Pass str|None directly; router's ParameterParser handles CSV splitting
    result = await _search(
        query=query,
        call_benefit=call_benefit,
        domain=domain,
        genes=genes,
        diseases=diseases,
        variants=variants,
        chemicals=chemicals,
        keywords=keywords,
        conditions=conditions,
        interventions=interventions,
        recruiting_status=recruiting_status,
        phase=phase,
        significance=significance,
        lat=lat,
        long=long,
        distance=distance,
        page=page,
        page_size=page_size,
        max_results_per_domain=max_results_per_domain,
        explain_query=explain_query,
        get_schema=get_schema,
        api_key=api_key,
    )
    return _serialize(result)


@arcade_app.tool
async def fetch(
    id: Annotated[
        str,
        "PMID / NCT ID / Variant ID / DOI / Gene ID / Drug ID / Disease ID / NCI Organization ID / NCI Intervention ID / NCI Disease ID / FDA Report ID / FDA Set ID / FDA MDR Key / FDA Application Number / FDA Recall Number",
    ],
    domain: Annotated[
        DomainLiteral | None,
        "Domain of the record (auto-detected if not provided)",
    ] = None,
    call_benefit: Annotated[
        str | None,
        "Brief explanation of why this fetch is being performed and expected benefit. Helps provide context for analytics and improves result relevance.",
    ] = None,
    detail: Annotated[
        DetailLiteral | None,
        "Specific section to retrieve (trials) or 'full' (articles)",
    ] = None,
    api_key: Annotated[
        str | None,
        "NCI API key for fetching NCI records (nci_organization, nci_intervention, nci_disease). Required for NCI fetches. Get a free key at: https://clinicaltrialsapi.cancer.gov/",
    ] = None,
) -> str:
    """Fetch comprehensive details for a specific biomedical record.

    This tool retrieves full information for articles, clinical trials, genetic variants,
    genes, drugs, or diseases using their unique identifiers. It returns data in a
    standardized format suitable for detailed analysis and research.

    ## IDENTIFIER FORMATS:
    - Articles: PMID (PubMed ID) - e.g., "35271234" OR DOI - e.g., "10.1101/2024.01.20.23288905"
    - Trials: NCT ID (ClinicalTrials.gov ID) - e.g., "NCT04280705"
    - Variants: HGVS notation or dbSNP ID - e.g., "chr7:g.140453136A>T" or "rs121913254"
    - Genes: Gene symbol or Entrez ID - e.g., "BRAF" or "673"
    - Drugs: Drug name or ID - e.g., "imatinib" or "DB00619"
    - Diseases: Disease name or ID - e.g., "melanoma" or "MONDO:0005105"

    The domain is automatically detected from the ID format if not provided.
    """
    result = await _fetch(
        id=id,
        domain=domain,
        call_benefit=call_benefit,
        detail=detail,
        api_key=api_key,
    )
    return _serialize(result)
