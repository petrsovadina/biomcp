"""Domain-specific search handlers for the router module."""

import json
import logging
from typing import Any

from .constants import (
    ESTIMATED_ADDITIONAL_RESULTS,
    compute_skip,
)
from .exceptions import (
    InvalidParameterError,
    ResultParsingError,
    SearchExecutionError,
)
from .parameter_parser import ParameterParser

logger = logging.getLogger(__name__)

# Type alias for handler return values.
# Structured handlers return (items, total) for format_results().
# Raw handlers return a dict directly.
SearchResult = tuple[list[dict], int] | dict


async def handle_article_search(
    genes: list[str] | None = None,
    diseases: list[str] | None = None,
    variants: list[str] | None = None,
    chemicals: list[str] | None = None,
    keywords: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> tuple[list[dict], int]:
    """Handle article domain search."""
    logger.info("Executing article search")
    try:
        from biomcp.articles.search import PubmedRequest
        from biomcp.articles.unified import search_articles_unified

        request = PubmedRequest(
            chemicals=chemicals or [],
            diseases=diseases or [],
            genes=genes or [],
            keywords=keywords or [],
            variants=variants or [],
        )
        result_str = await search_articles_unified(
            request,
            include_pubmed=True,
            include_preprints=True,
            output_json=True,
        )
    except Exception as e:
        logger.error(f"Article search failed: {e}")
        raise SearchExecutionError("article", e) from e

    # Parse the JSON results
    try:
        parsed_result = json.loads(result_str)
        # Handle unified search format (may include cBioPortal data)
        if (
            isinstance(parsed_result, dict)
            and "articles" in parsed_result
        ):
            all_results = parsed_result["articles"]
            # Log if cBioPortal data was included
            if "cbioportal_summary" in parsed_result:
                logger.info(
                    "Article search included cBioPortal"
                    " summary data"
                )
        elif isinstance(parsed_result, list):
            all_results = parsed_result
        else:
            # Handle unexpected format
            logger.warning(
                "Unexpected article result format:"
                f" {type(parsed_result)}"
            )
            all_results = []
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse article results: {e}")
        raise ResultParsingError("article", e) from e

    # Manual pagination
    start = compute_skip(page, page_size)
    end = start + page_size
    items = all_results[start:end]
    total = len(all_results)

    logger.info(
        f"Article search returned {total} total results,"
        f" showing {len(items)}"
    )

    return items, total


async def handle_trial_search(  # noqa: C901
    conditions: list[str] | None = None,
    interventions: list[str] | None = None,
    keywords: list[str] | None = None,
    recruiting_status: str | None = None,
    phase: str | None = None,
    genes: list[str] | None = None,
    lat: float | None = None,
    long: float | None = None,
    distance: int | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> tuple[list[dict], int]:
    """Handle trial domain search."""
    logger.info("Executing trial search")

    # Build the trial search parameters
    search_params: dict[str, Any] = {}
    if conditions:
        search_params["conditions"] = conditions
    if interventions:
        search_params["interventions"] = interventions
    if recruiting_status:
        search_params["recruiting_status"] = recruiting_status
    if phase:
        try:
            search_params["phase"] = (
                ParameterParser.normalize_phase(phase)
            )
        except InvalidParameterError:
            raise
    if keywords:
        search_params["keywords"] = keywords
    if lat is not None:
        search_params["lat"] = lat
    if long is not None:
        search_params["long"] = long
    if distance is not None:
        search_params["distance"] = distance

    # Add gene support for trials
    if genes:
        if "keywords" in search_params:
            search_params["keywords"].extend(genes)
        else:
            search_params["keywords"] = list(genes)

    try:
        from biomcp.trials.search import (
            TrialQuery,
            search_trials,
        )

        trial_query = TrialQuery(
            **search_params, page_size=page_size
        )
        result_str = await search_trials(
            trial_query, output_json=True
        )
    except Exception as e:
        logger.error(f"Trial search failed: {e}")
        raise SearchExecutionError("trial", e) from e

    # Parse the JSON results
    try:
        results = json.loads(result_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse trial results: {e}")
        raise ResultParsingError("trial", e) from e

    # Handle different response formats
    if isinstance(results, dict):
        if "studies" in results:
            items = results["studies"]
            total = len(items)
        elif "error" in results:
            logger.warning(
                "Trial API returned error:"
                f" {results.get('error')}"
            )
            return [], 0
        else:
            items = [results]
            total = 1
    elif isinstance(results, list):
        items = results
        total = len(items)
    else:
        items = []
        total = 0

    logger.info(
        f"Trial search returned {total} total results"
    )

    return items, total


async def handle_variant_search(
    genes: list[str] | None = None,
    significance: str | None = None,
    keywords: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> tuple[list[dict], int]:
    """Handle variant domain search."""
    logger.info("Executing variant search")

    gene = genes[0] if genes else None

    try:
        from biomcp.variants.search import (
            VariantQuery,
            search_variants,
        )

        variant_query = VariantQuery(
            gene=gene,
            significance=significance,
            size=page_size,
            offset=compute_skip(page, page_size),
        )
        result_str = await search_variants(
            variant_query, output_json=True
        )
    except Exception as e:
        logger.error(f"Variant search failed: {e}")
        raise SearchExecutionError("variant", e) from e

    # Parse the JSON results
    try:
        all_results = json.loads(result_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse variant results: {e}")
        raise ResultParsingError("variant", e) from e

    items = (
        all_results if isinstance(all_results, list) else []
    )
    total = len(items) + (
        ESTIMATED_ADDITIONAL_RESULTS
        if len(items) == page_size
        else 0
    )

    logger.info(
        f"Variant search returned {len(items)} results"
    )

    return items, total


async def handle_gene_search(
    genes: list[str] | None = None,
    keywords: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> tuple[list[dict], int]:
    """Handle gene domain search."""
    logger.info("Executing gene search")

    query_str = (
        keywords[0]
        if keywords
        else genes[0] if genes else ""
    )

    if not query_str:
        raise InvalidParameterError(
            "keywords or genes",
            None,
            "a gene symbol or search term",
        )

    try:
        from biomcp.integrations.biothings_client import (
            BioThingsClient,
        )

        client = BioThingsClient()
        results = await client._query_gene(query_str)

        if not results:
            items: list[dict[str, Any]] = []
            total = 0
        else:
            items = []
            for result in results[:page_size]:
                gene_id = result.get("_id")
                if gene_id:
                    full_gene = await client._get_gene_by_id(
                        gene_id
                    )
                    if full_gene:
                        items.append(full_gene.model_dump())

            total = len(results)

    except Exception as e:
        logger.error(f"Gene search failed: {e}")
        raise SearchExecutionError("gene", e) from e

    logger.info(
        f"Gene search returned {len(items)} results"
    )

    return items, total


async def handle_drug_search(
    chemicals: list[str] | None = None,
    keywords: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> tuple[list[dict], int]:
    """Handle drug domain search."""
    logger.info("Executing drug search")

    query_str = (
        keywords[0]
        if keywords
        else chemicals[0] if chemicals else ""
    )

    if not query_str:
        raise InvalidParameterError(
            "keywords or chemicals",
            None,
            "a drug name or search term",
        )

    try:
        from biomcp.integrations.biothings_client import (
            BioThingsClient,
        )

        client = BioThingsClient()
        results = await client._query_drug(query_str)

        if not results:
            items: list[dict[str, Any]] = []
            total = 0
        else:
            items = []
            for result in results[:page_size]:
                drug_id = result.get("_id")
                if drug_id:
                    full_drug = (
                        await client._get_drug_by_id(
                            drug_id
                        )
                    )
                    if full_drug:
                        items.append(
                            full_drug.model_dump(
                                by_alias=True
                            )
                        )

            total = len(results)

    except Exception as e:
        logger.error(f"Drug search failed: {e}")
        raise SearchExecutionError("drug", e) from e

    logger.info(
        f"Drug search returned {len(items)} results"
    )

    return items, total


async def handle_disease_search(
    diseases: list[str] | None = None,
    keywords: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> tuple[list[dict], int]:
    """Handle disease domain search."""
    logger.info("Executing disease search")

    query_str = (
        keywords[0]
        if keywords
        else diseases[0] if diseases else ""
    )

    if not query_str:
        raise InvalidParameterError(
            "keywords or diseases",
            None,
            "a disease name or search term",
        )

    try:
        from biomcp.integrations.biothings_client import (
            BioThingsClient,
        )

        client = BioThingsClient()
        results = await client._query_disease(query_str)

        if not results:
            items: list[dict[str, Any]] = []
            total = 0
        else:
            items = []
            for result in results[:page_size]:
                disease_id = result.get("_id")
                if disease_id:
                    full_disease = (
                        await client._get_disease_by_id(
                            disease_id
                        )
                    )
                    if full_disease:
                        items.append(
                            full_disease.model_dump(
                                by_alias=True
                            )
                        )

            total = len(results)

    except Exception as e:
        logger.error(f"Disease search failed: {e}")
        raise SearchExecutionError("disease", e) from e

    logger.info(
        f"Disease search returned {len(items)} results"
    )

    return items, total


async def handle_nci_organization_search(
    name: str | None = None,
    organization_type: str | None = None,
    city: str | None = None,
    state: str | None = None,
    api_key: str | None = None,
    keywords: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> tuple[list[dict], int]:
    """Handle NCI organization domain search."""
    logger.info("Executing NCI organization search")

    # Extract NCI-specific parameters from keywords
    if name is None and keywords:
        organization_type = keywords[0]
        name = keywords[0]

        if len(keywords) >= 2:
            city = keywords[-2]
            state = keywords[-1]
            if len(state) == 2 and state.isupper():
                name = (
                    " ".join(keywords[:-2])
                    if len(keywords) > 2
                    else None
                )
            else:
                city = None
                state = None
                name = " ".join(keywords)

    try:
        from biomcp.organizations import (
            search_organizations,
            search_organizations_with_or,
        )

        # Check if name contains OR query
        if name and (" OR " in name or " or " in name):
            results = await search_organizations_with_or(
                name_query=name,
                org_type=organization_type,
                city=city,
                state=state,
                page_size=page_size,
                page=page,
                api_key=api_key,
            )
        else:
            results = await search_organizations(
                name=name,
                org_type=organization_type,
                city=city,
                state=state,
                page_size=page_size,
                page=page,
                api_key=api_key,
            )

        items = results.get("organizations", [])
        total = results.get("total", len(items))

    except Exception as e:
        logger.error(
            f"NCI organization search failed: {e}"
        )
        raise SearchExecutionError(
            "nci_organization", e
        ) from e

    logger.info(
        f"NCI organization search returned"
        f" {total} results"
    )
    return items, total


async def handle_nci_intervention_search(
    name: str | None = None,
    intervention_type: str | None = None,
    synonyms: bool = True,
    api_key: str | None = None,
    keywords: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> tuple[list[dict], int]:
    """Handle NCI intervention domain search."""
    logger.info("Executing NCI intervention search")

    # Extract name from keywords if not provided
    if name is None and keywords:
        name = keywords[0]

    try:
        from biomcp.interventions import (
            search_interventions,
            search_interventions_with_or,
        )

        # Check if name contains OR query
        if name and (" OR " in name or " or " in name):
            results = await search_interventions_with_or(
                name_query=name,
                intervention_type=intervention_type,
                synonyms=synonyms,
                page_size=page_size,
                page=page,
                api_key=api_key,
            )
        else:
            results = await search_interventions(
                name=name,
                intervention_type=intervention_type,
                synonyms=synonyms,
                page_size=page_size,
                page=page,
                api_key=api_key,
            )

        items = results.get("interventions", [])
        total = results.get("total", len(items))

    except Exception as e:
        logger.error(
            f"NCI intervention search failed: {e}"
        )
        raise SearchExecutionError(
            "nci_intervention", e
        ) from e

    logger.info(
        f"NCI intervention search returned"
        f" {total} results"
    )
    return items, total


async def handle_nci_biomarker_search(
    name: str | None = None,
    gene: str | None = None,
    biomarker_type: str | None = None,
    assay_type: str | None = None,
    api_key: str | None = None,
    genes: list[str] | None = None,
    keywords: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> tuple[list[dict], int]:
    """Handle NCI biomarker domain search."""
    logger.info("Executing NCI biomarker search")

    # Extract from keywords/genes if not provided
    if name is None and keywords:
        name = keywords[0]
    if gene is None and genes:
        gene = genes[0]

    try:
        from biomcp.biomarkers import (
            search_biomarkers,
            search_biomarkers_with_or,
        )

        # Check if name contains OR query
        if name and (" OR " in name or " or " in name):
            results = await search_biomarkers_with_or(
                name_query=name,
                eligibility_criterion=gene,
                biomarker_type=biomarker_type,
                assay_purpose=assay_type,
                page_size=page_size,
                page=page,
                api_key=api_key,
            )
        else:
            results = await search_biomarkers(
                name=name,
                eligibility_criterion=gene,
                biomarker_type=biomarker_type,
                assay_purpose=assay_type,
                page_size=page_size,
                page=page,
                api_key=api_key,
            )

        items = results.get("biomarkers", [])
        total = results.get("total", len(items))

    except Exception as e:
        logger.error(
            f"NCI biomarker search failed: {e}"
        )
        raise SearchExecutionError(
            "nci_biomarker", e
        ) from e

    logger.info(
        f"NCI biomarker search returned {total} results"
    )
    return items, total


async def handle_nci_disease_search(
    name: str | None = None,
    include_synonyms: bool = True,
    category: str | None = None,
    api_key: str | None = None,
    diseases: list[str] | None = None,
    keywords: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> tuple[list[dict], int]:
    """Handle NCI disease domain search."""
    logger.info("Executing NCI disease search")

    # Extract name from diseases/keywords if not provided
    if name is None:
        if diseases:
            name = diseases[0]
        elif keywords:
            name = keywords[0]

    try:
        from biomcp.diseases import (
            search_diseases,
            search_diseases_with_or,
        )

        # Check if name contains OR query
        if name and (" OR " in name or " or " in name):
            results = await search_diseases_with_or(
                name_query=name,
                include_synonyms=include_synonyms,
                category=category,
                page_size=page_size,
                page=page,
                api_key=api_key,
            )
        else:
            results = await search_diseases(
                name=name,
                include_synonyms=include_synonyms,
                category=category,
                page_size=page_size,
                page=page,
                api_key=api_key,
            )

        items = results.get("diseases", [])
        total = results.get("total", len(items))

    except Exception as e:
        logger.error(f"NCI disease search failed: {e}")
        raise SearchExecutionError(
            "nci_disease", e
        ) from e

    logger.info(
        f"NCI disease search returned {total} results"
    )
    return items, total


# ────────────────────────────
# OpenFDA search handlers
# ────────────────────────────


async def handle_fda_adverse_search(
    chemicals: list[str] | None = None,
    keywords: list[str] | None = None,
    api_key: str | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> dict:
    """Handle FDA adverse event domain search."""
    from biomcp.openfda import search_adverse_events

    drug_name = (
        chemicals[0]
        if chemicals
        else keywords[0] if keywords else None
    )
    skip = compute_skip(page, page_size)
    fda_result = await search_adverse_events(
        drug=drug_name,
        limit=page_size,
        skip=skip,
        api_key=api_key,
    )
    return {"results": [{"content": fda_result}]}


async def handle_fda_label_search(
    chemicals: list[str] | None = None,
    keywords: list[str] | None = None,
    api_key: str | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> dict:
    """Handle FDA drug label domain search."""
    from biomcp.openfda import search_drug_labels

    drug_name = (
        chemicals[0]
        if chemicals
        else keywords[0] if keywords else None
    )
    skip = compute_skip(page, page_size)
    fda_result = await search_drug_labels(
        name=drug_name,
        limit=page_size,
        skip=skip,
        api_key=api_key,
    )
    return {"results": [{"content": fda_result}]}


async def handle_fda_device_search(
    keywords: list[str] | None = None,
    api_key: str | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> dict:
    """Handle FDA device event domain search."""
    from biomcp.openfda import search_device_events

    device_name = keywords[0] if keywords else None
    skip = compute_skip(page, page_size)
    fda_result = await search_device_events(
        device=device_name,
        limit=page_size,
        skip=skip,
        api_key=api_key,
    )
    return {"results": [{"content": fda_result}]}


async def handle_fda_approval_search(
    chemicals: list[str] | None = None,
    keywords: list[str] | None = None,
    api_key: str | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> dict:
    """Handle FDA drug approval domain search."""
    from biomcp.openfda import search_drug_approvals

    drug_name = (
        chemicals[0]
        if chemicals
        else keywords[0] if keywords else None
    )
    skip = compute_skip(page, page_size)
    fda_result = await search_drug_approvals(
        drug=drug_name,
        limit=page_size,
        skip=skip,
        api_key=api_key,
    )
    return {"results": [{"content": fda_result}]}


async def handle_fda_recall_search(
    chemicals: list[str] | None = None,
    keywords: list[str] | None = None,
    api_key: str | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> dict:
    """Handle FDA drug recall domain search."""
    from biomcp.openfda import search_drug_recalls

    drug_name = (
        chemicals[0]
        if chemicals
        else keywords[0] if keywords else None
    )
    skip = compute_skip(page, page_size)
    fda_result = await search_drug_recalls(
        drug=drug_name,
        limit=page_size,
        skip=skip,
        api_key=api_key,
    )
    return {"results": [{"content": fda_result}]}


async def handle_fda_shortage_search(
    chemicals: list[str] | None = None,
    keywords: list[str] | None = None,
    api_key: str | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> dict:
    """Handle FDA drug shortage domain search."""
    from biomcp.openfda import search_drug_shortages

    drug_name = (
        chemicals[0]
        if chemicals
        else keywords[0] if keywords else None
    )
    skip = compute_skip(page, page_size)
    fda_result = await search_drug_shortages(
        drug=drug_name,
        limit=page_size,
        skip=skip,
        api_key=api_key,
    )
    return {"results": [{"content": fda_result}]}


# ────────────────────────────
# Czech healthcare search handlers
# ────────────────────────────


async def handle_sukl_drug_search(
    query: str = "",
    keywords: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> dict:
    """Handle SUKL drug domain search."""
    from biomcp.czech.sukl.search import (
        _sukl_drug_search,
    )

    query_str = keywords[0] if keywords else query
    czech_result: str = await _sukl_drug_search(
        query_str, page, page_size
    )
    return {"results": [{"content": czech_result}]}


async def handle_mkn_diagnosis_search(
    query: str = "",
    keywords: list[str] | None = None,
    page_size: int = 10,
    **_: Any,
) -> dict:
    """Handle MKN diagnosis domain search."""
    from biomcp.czech.mkn.search import _mkn_search

    query_str = keywords[0] if keywords else query
    czech_result = await _mkn_search(
        query_str, page_size
    )
    return {"results": [{"content": czech_result}]}


async def handle_nrpzs_provider_search(
    query: str = "",
    keywords: list[str] | None = None,
    page: int = 1,
    page_size: int = 10,
    **_: Any,
) -> dict:
    """Handle NRPZS provider domain search."""
    from biomcp.czech.nrpzs.search import _nrpzs_search

    query_str = keywords[0] if keywords else query
    city = None
    specialty = None
    czech_result = await _nrpzs_search(
        query_str, city, specialty, page, page_size
    )
    return {"results": [{"content": czech_result}]}


async def handle_szv_procedure_search(
    query: str = "",
    keywords: list[str] | None = None,
    page_size: int = 10,
    **_: Any,
) -> dict:
    """Handle SZV procedure domain search."""
    from biomcp.czech.szv.search import _szv_search

    query_str = keywords[0] if keywords else query
    czech_result = await _szv_search(
        query_str, page_size
    )
    return {"results": [{"content": czech_result}]}


async def handle_vzp_reimbursement_search(
    query: str = "",
    keywords: list[str] | None = None,
    **_: Any,
) -> dict:
    """Handle VZP reimbursement domain search."""
    from biomcp.czech.vzp.drug_reimbursement import (
        _get_vzp_drug_reimbursement,
    )

    query_str = keywords[0] if keywords else query
    czech_result = await _get_vzp_drug_reimbursement(
        query_str
    )
    return {"results": [{"content": czech_result}]}


# Dispatch table mapping domain → handler function
SEARCH_HANDLERS: dict[str, Any] = {
    "article": handle_article_search,
    "trial": handle_trial_search,
    "variant": handle_variant_search,
    "gene": handle_gene_search,
    "drug": handle_drug_search,
    "disease": handle_disease_search,
    "nci_organization": handle_nci_organization_search,
    "nci_intervention": handle_nci_intervention_search,
    "nci_biomarker": handle_nci_biomarker_search,
    "nci_disease": handle_nci_disease_search,
    "fda_adverse": handle_fda_adverse_search,
    "fda_label": handle_fda_label_search,
    "fda_device": handle_fda_device_search,
    "fda_approval": handle_fda_approval_search,
    "fda_recall": handle_fda_recall_search,
    "fda_shortage": handle_fda_shortage_search,
    "sukl_drug": handle_sukl_drug_search,
    "mkn_diagnosis": handle_mkn_diagnosis_search,
    "nrpzs_provider": handle_nrpzs_provider_search,
    "szv_procedure": handle_szv_procedure_search,
    "vzp_reimbursement": handle_vzp_reimbursement_search,
}
