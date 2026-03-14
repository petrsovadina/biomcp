"""Unified search and fetch tools for CzechMedMCP.

This module provides the main MCP tools for searching and fetching biomedical data
across different domains (articles, trials, variants) with integrated sequential
thinking capabilities.
"""

import json
import logging
from typing import Annotated, Literal

from pydantic import Field

from biomcp.constants import (
    DEFAULT_PAGE_NUMBER,
    DEFAULT_PAGE_SIZE,
    DEFAULT_TITLE,
    ERROR_DOMAIN_REQUIRED,
    MAX_RESULTS_PER_DOMAIN_DEFAULT,
    VALID_DOMAINS,
)
from biomcp.core import mcp_app
from biomcp.domain_handlers import get_domain_handler
from biomcp.exceptions import (
    InvalidDomainError,
    InvalidParameterError,
    QueryParsingError,
    SearchExecutionError,
)
from biomcp.fetch_handlers import FETCH_HANDLERS
from biomcp.metrics import track_performance
from biomcp.parameter_parser import ParameterParser
from biomcp.query_parser import QueryParser
from biomcp.query_router import QueryRouter, execute_routing_plan
from biomcp.thinking_tracker import get_thinking_reminder

logger = logging.getLogger(__name__)


def format_results(
    results: list[dict], domain: str, page: int, page_size: int, total: int
) -> dict:
    """Format search results according to OpenAI MCP search semantics.

    Converts domain-specific result formats into a standardized structure with:
    - id: Unique identifier for the result (required)
    - title: Human-readable title (required)
    - text: Brief preview or summary of the content (required)
    - url: Link to the full resource (optional but recommended for citations)

    Note: The OpenAI MCP specification does NOT require metadata in search results.
    Metadata should only be included in fetch results.

    Args:
        results: Raw results from domain-specific search
        domain: Type of results ('article', 'trial', or 'variant')
        page: Current page number (for internal tracking only)
        page_size: Number of results per page (for internal tracking only)
        total: Total number of results available (for internal tracking only)

    Returns:
        Dictionary with results array following OpenAI MCP format:
        {"results": [{"id", "title", "text", "url"}, ...]}

    Raises:
        InvalidDomainError: If domain is not recognized
    """
    logger.debug(f"Formatting {len(results)} results for domain: {domain}")

    formatted_data = []

    # Get the appropriate handler
    try:
        handler_class = get_domain_handler(domain)
    except ValueError:
        raise InvalidDomainError(domain, VALID_DOMAINS) from None

    # Format each result
    for result in results:
        try:
            formatted_result = handler_class.format_result(result)
            # Ensure the result has the required OpenAI MCP fields
            openai_result = {
                "id": formatted_result.get("id", ""),
                "title": formatted_result.get("title", DEFAULT_TITLE),
                "text": formatted_result.get(
                    "snippet", formatted_result.get("text", "")
                ),
                "url": formatted_result.get("url", ""),
            }
            # Note: OpenAI MCP spec doesn't require metadata in search results
            # Only include it if explicitly needed for enhanced functionality
            formatted_data.append(openai_result)
        except Exception as e:
            logger.warning(f"Failed to format result in domain {domain}: {e}")
            # Skip malformed results
            continue

    # Add thinking reminder if needed (as first result)
    reminder = get_thinking_reminder()
    if reminder and formatted_data:
        reminder_result = {
            "id": "thinking-reminder",
            "title": "⚠️ Research Best Practice Reminder",
            "text": reminder,
            "url": "",
        }
        formatted_data.insert(0, reminder_result)

    # Return OpenAI MCP compliant format
    return {"results": formatted_data}


# ────────────────────────────
# Unified SEARCH tool
# ────────────────────────────
@mcp_app.tool()
@track_performance("biomcp.search")
async def search(
    query: Annotated[
        str,
        "Unified search query (e.g., 'gene:BRAF AND trials.condition:melanoma'). If provided, other parameters are ignored.",
    ],
    call_benefit: Annotated[
        str | None,
        Field(
            description="Brief explanation of why this search is being performed and expected benefit. Helps improve search accuracy and provides context for analytics. Highly recommended for better results."
        ),
    ] = None,
    domain: Annotated[
        Literal[
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
        | None,
        Field(
            description="Domain to search: 'article' for papers/literature ABOUT genes/variants/diseases, 'trial' for clinical studies, 'variant' for genetic variant DATABASE RECORDS, 'gene' for gene information from MyGene.info, 'drug' for drug/chemical information from MyChem.info, 'disease' for disease information from MyDisease.info, 'nci_organization' for NCI cancer centers/sponsors, 'nci_intervention' for NCI drugs/devices/procedures, 'nci_biomarker' for NCI trial eligibility biomarkers, 'nci_disease' for NCI cancer vocabulary, 'fda_adverse' for FDA adverse event reports, 'fda_label' for FDA drug labels, 'fda_device' for FDA device events, 'fda_approval' for FDA drug approvals, 'fda_recall' for FDA drug recalls, 'fda_shortage' for FDA drug shortages, 'sukl_drug' for Czech SUKL drug registry, 'mkn_diagnosis' for Czech ICD-10 (MKN-10), 'nrpzs_provider' for Czech healthcare providers, 'szv_procedure' for Czech health procedures, 'vzp_reimbursement' for Czech VZP drug reimbursement"
        ),
    ] = None,
    genes: Annotated[list[str] | str | None, "Gene symbols"] = None,
    diseases: Annotated[list[str] | str | None, "Disease terms"] = None,
    variants: Annotated[list[str] | str | None, "Variant strings"] = None,
    chemicals: Annotated[list[str] | str | None, "Drug/chemical terms"] = None,
    keywords: Annotated[list[str] | str | None, "Free-text keywords"] = None,
    conditions: Annotated[list[str] | str | None, "Trial conditions"] = None,
    interventions: Annotated[
        list[str] | str | None, "Trial interventions"
    ] = None,
    recruiting_status: Annotated[
        str | None, "Trial status filter (OPEN, CLOSED, or ANY)"
    ] = None,
    phase: Annotated[str | None, "Trial phase filter"] = None,
    significance: Annotated[
        str | None, "Variant clinical significance"
    ] = None,
    lat: Annotated[
        float | None,
        "Latitude for trial location search. AI agents should geocode city names (e.g., 'Cleveland' → 41.4993) before using.",
    ] = None,
    long: Annotated[
        float | None,
        "Longitude for trial location search. AI agents should geocode city names (e.g., 'Cleveland' → -81.6944) before using.",
    ] = None,
    distance: Annotated[
        int | None,
        "Distance in miles from lat/long for trial search (default: 50 miles if lat/long provided)",
    ] = None,
    page: Annotated[int, "Page number (minimum: 1)"] = DEFAULT_PAGE_NUMBER,
    page_size: Annotated[int, "Results per page (1-100)"] = DEFAULT_PAGE_SIZE,
    max_results_per_domain: Annotated[
        int | None, "Max results per domain (unified search only)"
    ] = None,
    explain_query: Annotated[
        bool, "Return query explanation (unified search only)"
    ] = False,
    get_schema: Annotated[
        bool, "Return searchable fields schema instead of results"
    ] = False,
    api_key: Annotated[
        str | None,
        Field(
            description="NCI API key for searching NCI domains (nci_organization, nci_intervention, nci_biomarker, nci_disease). Required for NCI searches. Get a free key at: https://clinicaltrialsapi.cancer.gov/"
        ),
    ] = None,
) -> dict:
    """Search biomedical literature, clinical trials, genetic variants, genes, drugs, and diseases.

    ⚠️ IMPORTANT: Have you used the 'think' tool first? If not, STOP and use it NOW!
    The 'think' tool is REQUIRED for proper research planning and should be your FIRST step.

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

    Common fields:
    - Cross-domain: gene, disease, variant, chemical/drug
    - Articles: pmid, title, abstract, journal, author
    - Trials: trials.condition, trials.intervention, trials.phase, trials.status
    - Variants: variants.hgvs, variants.rsid, variants.significance

    Example:
    ```
    await search(
        query="gene:BRAF AND disease:melanoma AND trials.phase:3",
        max_results_per_domain=20
    )
    ```

    ## 2. DOMAIN-SPECIFIC SEARCH
    Use the 'domain' parameter with specific filters for targeted searches.

    Domains:
    - "article": Search PubMed/PubTator3 for research articles and preprints ABOUT genes, variants, diseases, or chemicals
    - "trial": Search ClinicalTrials.gov for clinical studies
    - "variant": Search MyVariant.info for genetic variant DATABASE RECORDS (population frequency, clinical significance, etc.) - NOT for articles about variants!
    - "gene": Search MyGene.info for gene information (symbol, name, function, aliases)
    - "drug": Search MyChem.info for drug/chemical information (names, formulas, indications)
    - "disease": Search MyDisease.info for disease information (names, definitions, synonyms)
    - "nci_organization": Search NCI database for cancer centers, hospitals, and research sponsors (requires API key)
    - "nci_intervention": Search NCI database for drugs, devices, procedures used in cancer trials (requires API key)
    - "nci_biomarker": Search NCI database for biomarkers used in trial eligibility criteria (requires API key)
    - "nci_disease": Search NCI controlled vocabulary for cancer conditions and terms (requires API key)

    Example:
    ```
    await search(
        domain="article",
        genes=["BRAF", "NRAS"],
        diseases=["melanoma"],
        page_size=50
    )
    ```

    ## DOMAIN SELECTION EXAMPLES:
    - To find ARTICLES about BRAF V600E mutation: domain="article", genes=["BRAF"], variants=["V600E"]
    - To find VARIANT DATA for BRAF mutations: domain="variant", gene="BRAF"
    - To find articles about ERBB2 p.D277Y: domain="article", genes=["ERBB2"], variants=["p.D277Y"]
    - Common mistake: Using domain="variant" when you want articles about a variant

    ## IMPORTANT NOTES:
    - For complex research questions, use the separate 'think' tool for systematic analysis
    - The tool returns results in OpenAI MCP format: {"results": [{"id", "title", "text", "url"}, ...]}
    - Search results do NOT include metadata (per OpenAI MCP specification)
    - Use the fetch tool to get detailed metadata for specific records
    - Use get_schema=True to explore available search fields
    - Use explain_query=True to understand query parsing (unified mode)
    - Domain-specific searches use AND logic for multiple values
    - For OR logic, use the unified query language
    - NEW: Article search keywords support OR with pipe separator: "R173|Arg173|p.R173"
    - Remember: domain="article" finds LITERATURE, domain="variant" finds DATABASE RECORDS

    ## RETURN FORMAT:
    All search modes return results in this format:
    ```json
    {
        "results": [
            {
                "id": "unique_identifier",
                "title": "Human-readable title",
                "text": "Summary or snippet of content",
                "url": "Link to full resource"
            }
        ]
    }
    ```
    """
    logger.info(f"Search called with domain={domain}, query={query}")

    # Return schema if requested
    if get_schema:
        parser = QueryParser()
        return parser.get_schema()

    # Determine search mode
    if query and query.strip():
        # Check if this is a unified query (contains field syntax like "gene:" or "AND")
        is_unified_query = any(
            marker in query for marker in [":", " AND ", " OR "]
        )

        # Check if this is an NCI domain
        nci_domains = [
            "nci_biomarker",
            "nci_organization",
            "nci_intervention",
            "nci_disease",
        ]
        is_nci_domain = domain in nci_domains if domain else False

        if not domain or (domain and is_unified_query and not is_nci_domain):
            # Use unified query mode if:
            # 1. No domain specified, OR
            # 2. Domain specified but query has field syntax AND it's not an NCI domain
            logger.info(f"Using unified query mode: {query}")
            return await _unified_search(
                query=query,
                max_results_per_domain=max_results_per_domain
                or MAX_RESULTS_PER_DOMAIN_DEFAULT,
                domains=None,
                explain_query=explain_query,
            )
        elif domain:
            # Domain-specific search with query as keyword
            logger.info(
                f"Domain-specific search with query as keyword: domain={domain}, query={query}"
            )
            # Convert query to keywords parameter for domain-specific search
            keywords = [query]

    # Legacy domain-based search
    if not domain:
        raise InvalidParameterError(
            "query or domain", None, ERROR_DOMAIN_REQUIRED
        )

    # Validate pagination parameters
    try:
        page, page_size = ParameterParser.validate_page_params(page, page_size)
    except InvalidParameterError as e:
        logger.error(f"Invalid pagination parameters: {e}")
        raise

    # Parse parameters using ParameterParser
    genes = ParameterParser.parse_list_param(genes, "genes")
    diseases = ParameterParser.parse_list_param(diseases, "diseases")
    variants = ParameterParser.parse_list_param(variants, "variants")
    chemicals = ParameterParser.parse_list_param(chemicals, "chemicals")
    keywords = ParameterParser.parse_list_param(keywords, "keywords")
    conditions = ParameterParser.parse_list_param(conditions, "conditions")
    interventions = ParameterParser.parse_list_param(
        interventions, "interventions"
    )

    logger.debug(
        f"Parsed parameters for domain {domain}: "
        f"genes={genes}, diseases={diseases}, variants={variants}"
    )

    # Dispatch to domain-specific search handler
    from .router_handlers import SEARCH_HANDLERS

    handler = SEARCH_HANDLERS.get(domain)
    if handler is None:
        raise InvalidDomainError(domain, VALID_DOMAINS)

    result = await handler(
        query=query,
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
        api_key=api_key,
        page=page,
        page_size=page_size,
    )

    # Handlers return either (items, total) tuple
    # or a dict (raw response for FDA/Czech domains)
    if isinstance(result, tuple):
        items, total = result
        return format_results(
            items,
            domain=domain,
            page=page,
            page_size=page_size,
            total=total,
        )

    return result


# ────────────────────────────
# Unified FETCH tool
# ────────────────────────────
@mcp_app.tool()
@track_performance("biomcp.fetch")
async def fetch(
    id: Annotated[  # noqa: A002
        str,
        "PMID / NCT ID / Variant ID / DOI / Gene ID / Drug ID / Disease ID / NCI Organization ID / NCI Intervention ID / NCI Disease ID / FDA Report ID / FDA Set ID / FDA MDR Key / FDA Application Number / FDA Recall Number",
    ],
    domain: Annotated[
        Literal[
            "article",
            "trial",
            "variant",
            "gene",
            "drug",
            "disease",
            "nci_organization",
            "nci_intervention",
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
        | None,
        Field(
            description="Domain of the record (auto-detected if not provided)"
        ),
    ] = None,
    call_benefit: Annotated[
        str | None,
        Field(
            description="Brief explanation of why this fetch is being performed and expected benefit. Helps provide context for analytics and improves result relevance."
        ),
    ] = None,
    detail: Annotated[
        Literal[
            "protocol", "locations", "outcomes", "references", "all", "full"
        ]
        | None,
        "Specific section to retrieve (trials) or 'full' (articles)",
    ] = None,
    api_key: Annotated[
        str | None,
        Field(
            description="NCI API key for fetching NCI records (nci_organization, nci_intervention, nci_disease). Required for NCI fetches. Get a free key at: https://clinicaltrialsapi.cancer.gov/"
        ),
    ] = None,
) -> dict:
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
    - NCI Organizations: NCI organization ID - e.g., "NCI-2011-03337"
    - NCI Interventions: NCI intervention ID - e.g., "INT123456"
    - NCI Diseases: NCI disease ID - e.g., "C4872"

    The domain is automatically detected from the ID format if not provided:
    - NCT* → trial
    - Contains "/" with numeric prefix (DOI) → article
    - Pure numeric → article (PMID)
    - rs* or contains ':' or 'g.' → variant
    - For genes, drugs, diseases: manual specification recommended

    ## DOMAIN-SPECIFIC OPTIONS:

    ### Articles (domain="article"):
    - Returns full article metadata, abstract, and full text when available
    - Supports both PubMed articles (via PMID) and Europe PMC preprints (via DOI)
    - Includes annotations for genes, diseases, chemicals, and variants (PubMed only)
    - detail="full" attempts to retrieve full text content (PubMed only)

    ### Clinical Trials (domain="trial"):
    - detail=None or "protocol": Core study information
    - detail="locations": Study sites and contact information
    - detail="outcomes": Primary/secondary outcomes and results
    - detail="references": Related publications and citations
    - detail="all": Complete trial record with all sections

    ### Variants (domain="variant"):
    - Returns comprehensive variant information including:
      - Clinical significance and interpretations
      - Population frequencies
      - Gene/protein effects
      - External database links
    - detail parameter is ignored (always returns full data)

    ### Genes (domain="gene"):
    - Returns gene information from MyGene.info including:
      - Gene symbol, name, and type
      - Entrez ID and Ensembl IDs
      - Gene summary and aliases
      - RefSeq information
    - detail parameter is ignored (always returns full data)

    ### Drugs (domain="drug"):
    - Returns drug/chemical information from MyChem.info including:
      - Drug name and trade names
      - Chemical formula and structure IDs
      - Clinical indications
      - Mechanism of action
      - External database links (DrugBank, PubChem, ChEMBL)
    - detail parameter is ignored (always returns full data)

    ### Diseases (domain="disease"):
    - Returns disease information from MyDisease.info including:
      - Disease name and definition
      - MONDO ontology ID
      - Disease synonyms
      - Cross-references to other databases
      - Associated phenotypes
    - detail parameter is ignored (always returns full data)

    ### NCI Organizations (domain="nci_organization"):
    - Returns organization information from NCI database including:
      - Organization name and type
      - Full address and contact information
      - Research focus areas
      - Associated clinical trials
    - Requires NCI API key
    - detail parameter is ignored (always returns full data)

    ### NCI Interventions (domain="nci_intervention"):
    - Returns intervention information from NCI database including:
      - Intervention name and type
      - Synonyms and alternative names
      - Mechanism of action (for drugs)
      - FDA approval status
      - Associated clinical trials
    - Requires NCI API key
    - detail parameter is ignored (always returns full data)

    ### NCI Diseases (domain="nci_disease"):
    - Returns disease information from NCI controlled vocabulary including:
      - Preferred disease name
      - Disease category and classification
      - All known synonyms
      - Cross-reference codes (ICD, SNOMED)
    - Requires NCI API key
    - detail parameter is ignored (always returns full data)

    ## RETURN FORMAT:
    All fetch operations return a standardized format:
    ```json
    {
        "id": "unique_identifier",
        "title": "Record title or name",
        "text": "Full content or comprehensive description",
        "url": "Link to original source",
        "metadata": {
            // Domain-specific additional fields
        }
    }
    ```

    ## EXAMPLES:

    Fetch article by PMID (domain auto-detected):
    ```
    await fetch(id="35271234")
    ```

    Fetch article by DOI (domain auto-detected):
    ```
    await fetch(id="10.1101/2024.01.20.23288905")
    ```

    Fetch complete trial information (domain auto-detected):
    ```
    await fetch(
        id="NCT04280705",
        detail="all"
    )
    ```

    Fetch variant with clinical interpretations:
    ```
    await fetch(id="rs121913254")
    ```

    Explicitly specify domain (optional):
    ```
    await fetch(
        domain="variant",
        id="chr7:g.140453136A>T"
    )
    ```
    """
    # Auto-detect domain if not provided
    if domain is None:
        # Try to infer domain from ID format
        if id.upper().startswith("NCT"):
            domain = "trial"
            logger.info(f"Auto-detected domain 'trial' from NCT ID: {id}")
        elif "/" in id and id.split("/")[0].replace(".", "").isdigit():
            # DOI format (e.g., 10.1038/nature12373) - treat as article
            domain = "article"
            logger.info(f"Auto-detected domain 'article' from DOI: {id}")
        elif id.isdigit():
            # Numeric ID - likely PMID
            domain = "article"
            logger.info(
                f"Auto-detected domain 'article' from numeric ID: {id}"
            )
        elif id.startswith("rs") or ":" in id or "g." in id:
            # rsID or HGVS notation
            domain = "variant"
            logger.info(f"Auto-detected domain 'variant' from ID format: {id}")
        else:
            # Default to article if we can't determine
            domain = "article"
            logger.warning(
                f"Could not auto-detect domain for ID '{id}', defaulting to 'article'"
            )

    logger.info(f"Fetch called for {domain} with id={id}, detail={detail}")

    # Dispatch to domain-specific handler
    handler = FETCH_HANDLERS.get(domain)
    if handler is None:
        raise InvalidDomainError(domain, VALID_DOMAINS)

    return await handler(
        id=id,
        detail=detail,
        api_key=api_key,
        call_benefit=call_benefit,
    )


# Internal function for unified search
async def _unified_search(  # noqa: C901
    query: str,
    max_results_per_domain: int = MAX_RESULTS_PER_DOMAIN_DEFAULT,
    domains: list[str] | None = None,
    explain_query: bool = False,
) -> dict:
    """Internal unified search implementation.

    Parses the unified query language and routes to appropriate domain tools.
    Supports field-based syntax like 'gene:BRAF AND trials.phase:3'.

    Args:
        query: Unified query string with field syntax
        max_results_per_domain: Limit results per domain
        domains: Optional list to filter which domains to search
        explain_query: If True, return query parsing explanation

    Returns:
        Dictionary with results organized by domain

    Raises:
        QueryParsingError: If query cannot be parsed
        SearchExecutionError: If search execution fails
    """
    logger.info(f"Unified search with query: {query}")
    # Parse the query
    try:
        parser = QueryParser()
        parsed = parser.parse(query)
    except Exception as e:
        logger.error(f"Failed to parse query: {e}")
        raise QueryParsingError(query, e) from e

    # Route to appropriate tools
    router = QueryRouter()
    plan = router.route(parsed)

    # Filter domains if specified
    if domains:
        filtered_tools = []
        for tool in plan.tools_to_call:
            if (
                ("article" in tool and "articles" in domains)
                or ("trial" in tool and "trials" in domains)
                or ("variant" in tool and "variants" in domains)
            ):
                filtered_tools.append(tool)
        plan.tools_to_call = filtered_tools

    # Return explanation if requested
    if explain_query:
        return {
            "original_query": query,
            "parsed_structure": {
                "cross_domain_fields": parsed.cross_domain_fields,
                "domain_specific_fields": parsed.domain_specific_fields,
                "terms": [
                    {
                        "field": term.field,
                        "operator": term.operator.value,
                        "value": term.value,
                        "domain": term.domain,
                    }
                    for term in parsed.terms
                ],
            },
            "routing_plan": {
                "tools_to_call": plan.tools_to_call,
                "field_mappings": plan.field_mappings,
            },
            "schema": parser.get_schema(),
        }

    # Execute the search plan
    try:
        results = await execute_routing_plan(plan, output_json=True)
    except Exception as e:
        logger.error(f"Failed to execute search plan: {e}")
        raise SearchExecutionError("unified", e) from e

    # Format unified results - collect all results into a single array
    all_results = []

    for domain, result_str in results.items():
        if isinstance(result_str, dict) and "error" in result_str:
            logger.warning(f"Error in domain {domain}: {result_str['error']}")
            continue

        try:
            data = (
                json.loads(result_str)
                if isinstance(result_str, str)
                else result_str
            )

            # Get the appropriate handler for formatting
            handler_class = get_domain_handler(
                domain.removesuffix("s")
            )  # Remove trailing 's'

            # Process and format each result
            # Handle both list format and dict format (for articles with cBioPortal data)
            items_to_process = []
            cbioportal_summary = None

            if isinstance(data, list):
                items_to_process = data[:max_results_per_domain]
            elif isinstance(data, dict):
                # Handle unified search format with cBioPortal data
                if "articles" in data:
                    items_to_process = data["articles"][
                        :max_results_per_domain
                    ]
                    cbioportal_summary = data.get("cbioportal_summary")
                else:
                    # Single item dict
                    items_to_process = [data]

            # Add cBioPortal summary as first result if available
            if cbioportal_summary and domain == "articles":
                try:
                    # Extract gene name from parsed query or summary
                    gene_name = parsed.cross_domain_fields.get("gene", "")
                    if not gene_name and "Summary for " in cbioportal_summary:
                        # Try to extract from summary title
                        import re

                        match = re.search(
                            r"Summary for (\w+)", cbioportal_summary
                        )
                        if match:
                            gene_name = match.group(1)

                    cbio_result = {
                        "id": f"cbioportal_summary_{gene_name or 'gene'}",
                        "title": f"cBioPortal Summary for {gene_name or 'Gene'}",
                        "text": cbioportal_summary[:5000],  # Limit text length
                        "url": f"https://www.cbioportal.org/results?gene_list={gene_name}"
                        if gene_name
                        else "",
                    }
                    all_results.append(cbio_result)
                except Exception as e:
                    logger.warning(f"Failed to format cBioPortal summary: {e}")

            for item in items_to_process:
                try:
                    formatted_result = handler_class.format_result(item)
                    # Ensure OpenAI MCP format
                    openai_result = {
                        "id": formatted_result.get("id", ""),
                        "title": formatted_result.get("title", DEFAULT_TITLE),
                        "text": formatted_result.get(
                            "snippet", formatted_result.get("text", "")
                        ),
                        "url": formatted_result.get("url", ""),
                    }
                    # Note: For unified search, we can optionally include domain in metadata
                    # This helps distinguish between result types
                    all_results.append(openai_result)
                except Exception as e:
                    logger.warning(
                        f"Failed to format result in domain {domain}: {e}"
                    )
                    continue

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning(f"Failed to parse results for domain {domain}: {e}")
            continue

    logger.info(
        f"Unified search completed with {len(all_results)} total results"
    )

    # Return OpenAI MCP compliant format
    return {"results": all_results}
