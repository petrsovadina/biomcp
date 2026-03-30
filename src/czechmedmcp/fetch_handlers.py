"""Domain-specific fetch handlers for the router module."""

import json
import logging
from typing import Any

from .constants import (
    DEFAULT_TITLE,
    TRIAL_DETAIL_SECTIONS,
)
from .exceptions import (
    InvalidParameterError,
    ResultParsingError,
    SearchExecutionError,
)

logger = logging.getLogger(__name__)


async def handle_article_fetch(
    identifier: str,
    call_benefit: str | None = None,
    **_: Any,
) -> dict:
    """Handle article domain fetch."""
    logger.debug("Fetching article details")
    try:
        from czechmedmcp.articles.fetch import _article_details

        result_str = await _article_details(
            call_benefit=call_benefit
            or "Fetching article details via MCP tool",
            pmid=identifier,
        )
    except Exception as e:
        logger.error(f"Article fetch failed: {e}")
        raise SearchExecutionError("article", e) from e

    try:
        articles = (
            json.loads(result_str)
            if isinstance(result_str, str)
            else result_str
        )
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse article fetch results: {e}")
        raise ResultParsingError("article", e) from e

    if not articles:
        return {"error": "Article not found"}

    article = articles[0]

    if "error" in article:
        return {"error": article["error"]}

    full_text = article.get("full_text", "")
    abstract = article.get("abstract", "")
    text_content = full_text if full_text else abstract

    return {
        "id": str(article.get("pmid", identifier)),
        "title": article.get("title", DEFAULT_TITLE),
        "text": text_content,
        "url": article.get(
            "url",
            f"https://pubmed.ncbi.nlm.nih.gov/{identifier}/",
        ),
        "metadata": {
            "pmid": article.get("pmid"),
            "journal": article.get("journal"),
            "authors": article.get("authors"),
            "year": article.get("year"),
            "doi": article.get("doi"),
            "annotations": article.get("annotations", {}),
            "is_preprint": article.get("is_preprint", False),
            "preprint_source": article.get("preprint_source"),
        },
    }


async def handle_trial_fetch(  # noqa: C901
    identifier: str,
    detail: str | None = None,
    **_: Any,
) -> dict:
    """Handle trial domain fetch."""
    logger.debug(f"Fetching trial details for section: {detail}")

    from czechmedmcp.trials import getter as trial_getter

    if detail is not None and detail not in TRIAL_DETAIL_SECTIONS:
        raise InvalidParameterError(
            "detail",
            detail,
            f"one of: {', '.join(TRIAL_DETAIL_SECTIONS)} or None",
        )

    try:
        protocol_json = await trial_getter.get_trial(
            nct_id=identifier,
            module=trial_getter.Module.PROTOCOL,
            output_json=True,
        )

        try:
            protocol_data = json.loads(protocol_json)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse protocol JSON"
                f" for {identifier}: {e}"
            )
            return {
                "id": identifier,
                "title": f"Clinical Trial {identifier}",
                "text": f"Error parsing trial data: {e}",
                "url": (
                    "https://clinicaltrials.gov"
                    f"/study/{identifier}"
                ),
                "metadata": {
                    "nct_id": identifier,
                    "error": f"JSON parse error: {e}",
                },
            }

        if "error" in protocol_data:
            return {
                "id": identifier,
                "title": f"Clinical Trial {identifier}",
                "text": protocol_data.get(
                    "details",
                    protocol_data.get("error", "Trial not found"),
                ),
                "url": (
                    "https://clinicaltrials.gov"
                    f"/study/{identifier}"
                ),
                "metadata": {
                    "nct_id": identifier,
                    "error": protocol_data.get("error"),
                },
            }

        text_parts = []
        protocol_section = protocol_data.get("protocolSection", {})

        id_module = protocol_section.get("identificationModule", {})
        status_module = protocol_section.get("statusModule", {})
        desc_module = protocol_section.get("descriptionModule", {})
        conditions_module = protocol_section.get("conditionsModule", {})
        design_module = protocol_section.get("designModule", {})
        arms_module = protocol_section.get("armsInterventionsModule", {})

        title = id_module.get(
            "briefTitle", f"Clinical Trial {identifier}"
        )
        text_parts.append(f"Study Title: {title}")

        conditions = conditions_module.get("conditions", [])
        if conditions:
            text_parts.append(f"\nConditions: {', '.join(conditions)}")

        interventions = []
        for intervention in arms_module.get("interventions", []):
            interventions.append(intervention.get("name", ""))
        if interventions:
            text_parts.append(f"Interventions: {', '.join(interventions)}")

        phases = design_module.get("phases", [])
        if phases:
            text_parts.append(f"Phase: {', '.join(phases)}")

        overall_status = status_module.get("overallStatus", "N/A")
        text_parts.append(f"Status: {overall_status}")

        brief_summary = desc_module.get("briefSummary", "No summary available")
        text_parts.append(f"\nSummary: {brief_summary}")

        metadata: dict[str, Any] = {
            "nct_id": identifier,
            "protocol": protocol_data,
        }

        if detail in (
            "all",
            "locations",
            "outcomes",
            "references",
        ):
            if detail in ("all", "locations"):
                try:
                    locations_json = await trial_getter.get_trial(
                        nct_id=identifier,
                        module=trial_getter.Module.LOCATIONS,
                        output_json=True,
                    )
                    locations_data = json.loads(locations_json)
                    if "error" not in locations_data:
                        locations_module = locations_data.get(
                            "protocolSection", {}
                        ).get(
                            "contactsLocationsModule",
                            {},
                        )
                        locations_list = locations_module.get("locations", [])
                        metadata["locations"] = locations_list
                        if locations_list:
                            text_parts.append(
                                f"\n\nLocations:"
                                f" {len(locations_list)}"
                                " study sites"
                            )
                except Exception as e:
                    logger.warning(
                        "Failed to fetch locations"
                        f" for {identifier}: {e}"
                    )
                    metadata["locations"] = []

            if detail in ("all", "outcomes"):
                try:
                    outcomes_json = await trial_getter.get_trial(
                        nct_id=identifier,
                        module=trial_getter.Module.OUTCOMES,
                        output_json=True,
                    )
                    outcomes_data = json.loads(outcomes_json)
                    if "error" not in outcomes_data:
                        outcomes_module = outcomes_data.get(
                            "protocolSection", {}
                        ).get("outcomesModule", {})
                        primary = outcomes_module.get("primaryOutcomes", [])
                        secondary = outcomes_module.get(
                            "secondaryOutcomes", []
                        )
                        metadata["outcomes"] = {
                            "primary_outcomes": primary,
                            "secondary_outcomes": (secondary),
                        }
                        if primary:
                            text_parts.append(
                                "\n\nPrimary Outcomes:"
                                f" {len(primary)}"
                                " measures"
                            )
                except Exception as e:
                    logger.warning(
                        "Failed to fetch outcomes"
                        f" for {identifier}: {e}"
                    )
                    metadata["outcomes"] = {}

            if detail in ("all", "references"):
                try:
                    references_json = await trial_getter.get_trial(
                        nct_id=identifier,
                        module=(trial_getter.Module.REFERENCES),
                        output_json=True,
                    )
                    references_data = json.loads(references_json)
                    if "error" not in references_data:
                        references_module = references_data.get(
                            "protocolSection", {}
                        ).get("referencesModule", {})
                        references_list = references_module.get(
                            "references", []
                        )
                        metadata["references"] = references_list
                        if references_list:
                            text_parts.append(
                                "\n\nReferences:"
                                f" {len(references_list)}"
                                " publications"
                            )
                except Exception as e:
                    logger.warning(
                        "Failed to fetch references"
                        f" for {identifier}: {e}"
                    )
                    metadata["references"] = []

        return {
            "id": identifier,
            "title": title,
            "text": "\n".join(text_parts),
            "url": (
                "https://clinicaltrials.gov"
                f"/study/{identifier}"
            ),
            "metadata": metadata,
        }

    except Exception as e:
        logger.error(f"Trial fetch failed: {e}")
        raise SearchExecutionError("trial", e) from e


async def handle_variant_fetch(  # noqa: C901
    identifier: str,
    **_: Any,
) -> dict:
    """Handle variant domain fetch."""
    logger.debug("Fetching variant details")
    try:
        from czechmedmcp.variants.getter import get_variant

        result_str = await get_variant(
            variant_id=identifier,
            output_json=True,
            include_external=True,
        )
    except Exception as e:
        logger.error(f"Variant fetch failed: {e}")
        raise SearchExecutionError("variant", e) from e

    try:
        variant_response = (
            json.loads(result_str)
            if isinstance(result_str, str)
            else result_str
        )
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse variant fetch results: {e}")
        raise ResultParsingError("variant", e) from e

    if isinstance(variant_response, list) and variant_response:
        variant_data = variant_response[0]
    elif isinstance(variant_response, dict):
        variant_data = variant_response
    else:
        return {"error": "Variant not found"}

    text_parts = []
    text_parts.append(
        f"Variant: {variant_data.get('_id', identifier)}"
    )

    if variant_data.get("gene"):
        gene_info = variant_data["gene"]
        text_parts.append(
            f"\nGene: {gene_info.get('symbol', 'Unknown')}"
            f" ({gene_info.get('name', '')})"
        )

    if variant_data.get("clinvar"):
        clinvar = variant_data["clinvar"]
        if clinvar.get("clinical_significance"):
            text_parts.append(
                f"\nClinical Significance: {clinvar['clinical_significance']}"
            )
        if clinvar.get("review_status"):
            text_parts.append(f"Review Status: {clinvar['review_status']}")

    if variant_data.get("dbsnp"):
        dbsnp = variant_data["dbsnp"]
        if dbsnp.get("rsid"):
            text_parts.append(f"\ndbSNP: {dbsnp['rsid']}")

    if variant_data.get("cadd"):
        cadd = variant_data["cadd"]
        if cadd.get("phred"):
            text_parts.append(f"\nCADD Score: {cadd['phred']}")

    if variant_data.get("gnomad_exome"):
        gnomad = variant_data["gnomad_exome"]
        if gnomad.get("af", {}).get("af"):
            text_parts.append(
                f"\nGnomAD Allele Frequency: {gnomad['af']['af']:.6f}"
            )

    if variant_data.get("external_links"):
        links = variant_data["external_links"]
        text_parts.append(
            f"\n\nExternal Resources: {len(links)} database links available"
        )

    if variant_data.get("tcga"):
        text_parts.append("\n\nTCGA Data: Available")
    if variant_data.get("1000genomes"):
        text_parts.append("\n1000 Genomes Data: Available")

    url = variant_data.get("url", "")
    if not url and variant_data.get("dbsnp", {}).get("rsid"):
        url = (
            f"https://www.ncbi.nlm.nih.gov/snp/{variant_data['dbsnp']['rsid']}"
        )
    elif not url:
        url = (
            "https://myvariant.info/v1"
            f"/variant/{identifier}"
        )

    return {
        "id": variant_data.get("_id", identifier),
        "title": (
            f"Variant {variant_data.get('_id', identifier)}"
        ),
        "text": "\n".join(text_parts),
        "url": url,
        "metadata": variant_data,
    }


async def handle_gene_fetch(
    identifier: str,
    **_: Any,
) -> dict:
    """Handle gene domain fetch."""
    logger.debug("Fetching gene details")
    try:
        from czechmedmcp.integrations.biothings_client import (
            BioThingsClient,
        )

        client = BioThingsClient()
        gene_info = await client.get_gene_info(identifier)

        if not gene_info:
            return {"error": f"Gene {identifier} not found"}

        text_parts = []
        text_parts.append(f"Gene: {gene_info.symbol} ({gene_info.name})")

        if gene_info.entrezgene:
            text_parts.append(f"\nEntrez ID: {gene_info.entrezgene}")

        if gene_info.type_of_gene:
            text_parts.append(f"Type: {gene_info.type_of_gene}")

        if gene_info.summary:
            text_parts.append(f"\nSummary: {gene_info.summary}")

        if gene_info.alias:
            text_parts.append(f"\nAliases: {', '.join(gene_info.alias)}")

        url = (
            "https://www.genenames.org/data/"
            "gene-symbol-report"
            f"/#!/symbol/{gene_info.symbol}"
            if gene_info.symbol
            else ""
        )

        return {
            "id": str(gene_info.gene_id),
            "title": (
                f"{gene_info.symbol}: {gene_info.name}"
                if gene_info.symbol and gene_info.name
                else gene_info.symbol or gene_info.name or DEFAULT_TITLE
            ),
            "text": "\n".join(text_parts),
            "url": url,
            "metadata": gene_info.model_dump(),
        }

    except Exception as e:
        logger.error(f"Gene fetch failed: {e}")
        raise SearchExecutionError("gene", e) from e


async def handle_drug_fetch(  # noqa: C901
    identifier: str,
    **_: Any,
) -> dict:
    """Handle drug domain fetch."""
    logger.debug("Fetching drug details")
    try:
        from czechmedmcp.integrations.biothings_client import (
            BioThingsClient,
        )

        client = BioThingsClient()
        drug_info = await client.get_drug_info(identifier)

        if not drug_info:
            return {"error": f"Drug {identifier} not found"}

        text_parts = []
        text_parts.append(f"Drug: {drug_info.name}")

        if drug_info.drugbank_id:
            text_parts.append(f"\nDrugBank ID: {drug_info.drugbank_id}")

        if drug_info.formula:
            text_parts.append(f"Formula: {drug_info.formula}")

        if drug_info.tradename:
            text_parts.append(
                f"\nTrade Names: {', '.join(drug_info.tradename)}"
            )

        if drug_info.description:
            text_parts.append(f"\nDescription: {drug_info.description}")

        if drug_info.indication:
            text_parts.append(f"\nIndication: {drug_info.indication}")

        if drug_info.mechanism_of_action:
            text_parts.append(
                f"\nMechanism of Action: {drug_info.mechanism_of_action}"
            )

        url = ""
        if drug_info.drugbank_id:
            url = f"https://www.drugbank.ca/drugs/{drug_info.drugbank_id}"
        elif drug_info.pubchem_cid:
            url = (
                "https://pubchem.ncbi.nlm.nih.gov"
                f"/compound/{drug_info.pubchem_cid}"
            )

        return {
            "id": drug_info.drug_id,
            "title": (drug_info.name or drug_info.drug_id or DEFAULT_TITLE),
            "text": "\n".join(text_parts),
            "url": url,
            "metadata": drug_info.model_dump(),
        }

    except Exception as e:
        logger.error(f"Drug fetch failed: {e}")
        raise SearchExecutionError("drug", e) from e


async def handle_disease_fetch(  # noqa: C901
    identifier: str,
    **_: Any,
) -> dict:
    """Handle disease domain fetch."""
    logger.debug("Fetching disease details")
    try:
        from czechmedmcp.integrations.biothings_client import (
            BioThingsClient,
        )

        client = BioThingsClient()
        disease_info = await client.get_disease_info(identifier)

        if not disease_info:
            return {
                "error": f"Disease {identifier} not found"
            }

        text_parts = []
        text_parts.append(f"Disease: {disease_info.name}")

        if disease_info.mondo and isinstance(disease_info.mondo, dict):
            mondo_id = disease_info.mondo.get("id")
            if mondo_id:
                text_parts.append(f"\nMONDO ID: {mondo_id}")

        if disease_info.definition:
            text_parts.append(f"\nDefinition: {disease_info.definition}")

        if disease_info.synonyms:
            text_parts.append(
                f"\nSynonyms: {', '.join(disease_info.synonyms[:5])}"
            )
            if len(disease_info.synonyms) > 5:
                text_parts.append(
                    f"  ... and {len(disease_info.synonyms) - 5} more"
                )

        if disease_info.phenotypes:
            text_parts.append(
                f"\nAssociated Phenotypes: {len(disease_info.phenotypes)}"
            )

        url = ""
        if disease_info.mondo and isinstance(disease_info.mondo, dict):
            mondo_id = disease_info.mondo.get("id")
            if mondo_id:
                url = f"https://monarchinitiative.org/disease/{mondo_id}"

        return {
            "id": disease_info.disease_id,
            "title": (
                disease_info.name or disease_info.disease_id or DEFAULT_TITLE
            ),
            "text": "\n".join(text_parts),
            "url": url,
            "metadata": disease_info.model_dump(),
        }

    except Exception as e:
        logger.error(f"Disease fetch failed: {e}")
        raise SearchExecutionError("disease", e) from e


async def handle_nci_organization_fetch(
    identifier: str,
    api_key: str | None = None,
    **_: Any,
) -> dict:
    """Handle NCI organization domain fetch."""
    logger.debug("Fetching NCI organization details")
    try:
        from czechmedmcp.organizations import get_organization
        from czechmedmcp.organizations.getter import (
            format_organization_details,
        )

        org_data = await get_organization(
            org_id=identifier,
            api_key=api_key,
        )

        formatted_text = format_organization_details(org_data)

        return {
            "id": identifier,
            "title": org_data.get(
                "name", "Unknown Organization"
            ),
            "text": formatted_text,
            "url": "",
            "metadata": org_data,
        }

    except Exception as e:
        logger.error(f"NCI organization fetch failed: {e}")
        raise SearchExecutionError("nci_organization", e) from e


async def handle_nci_intervention_fetch(
    identifier: str,
    api_key: str | None = None,
    **_: Any,
) -> dict:
    """Handle NCI intervention domain fetch."""
    logger.debug("Fetching NCI intervention details")
    try:
        from czechmedmcp.interventions import get_intervention
        from czechmedmcp.interventions.getter import (
            format_intervention_details,
        )

        intervention_data = await get_intervention(
            intervention_id=identifier,
            api_key=api_key,
        )

        formatted_text = format_intervention_details(intervention_data)

        return {
            "id": identifier,
            "title": intervention_data.get(
                "name", "Unknown Intervention"
            ),
            "text": formatted_text,
            "url": "",
            "metadata": intervention_data,
        }

    except Exception as e:
        logger.error(f"NCI intervention fetch failed: {e}")
        raise SearchExecutionError("nci_intervention", e) from e


async def handle_nci_disease_fetch(
    identifier: str,
    api_key: str | None = None,
    **_: Any,
) -> dict:
    """Handle NCI disease domain fetch."""
    logger.debug("Fetching NCI disease details")
    try:
        from czechmedmcp.diseases import get_disease_by_id

        disease_data = await get_disease_by_id(
            disease_id=identifier,
            api_key=api_key,
        )

        text_parts = []
        text_parts.append(
            f"Disease: {disease_data.get('name', 'Unknown Disease')}"
        )

        if disease_data.get("category"):
            text_parts.append(f"\nCategory: {disease_data['category']}")

        if disease_data.get("synonyms"):
            synonyms = disease_data["synonyms"]
            if isinstance(synonyms, list) and synonyms:
                text_parts.append(f"\nSynonyms: {', '.join(synonyms[:5])}")
                if len(synonyms) > 5:
                    text_parts.append(f"  ... and {len(synonyms) - 5} more")

        if disease_data.get("codes"):
            codes = disease_data["codes"]
            if isinstance(codes, dict):
                code_items = [
                    f"{system}: {code}" for system, code in codes.items()
                ]
                if code_items:
                    text_parts.append(f"\nCodes: {', '.join(code_items)}")

        return {
            "id": identifier,
            "title": disease_data.get(
                "name",
                disease_data.get(
                    "preferred_name",
                    "Unknown Disease",
                ),
            ),
            "text": "\n".join(text_parts),
            "url": "",
            "metadata": disease_data,
        }

    except Exception as e:
        logger.error(f"NCI disease fetch failed: {e}")
        raise SearchExecutionError("nci_disease", e) from e


async def handle_fda_adverse_fetch(
    identifier: str,
    api_key: str | None = None,
    **_: Any,
) -> dict:
    """Handle FDA adverse event domain fetch."""
    from czechmedmcp.openfda import get_adverse_event

    result = await get_adverse_event(
        identifier, api_key=api_key
    )
    return {
        "title": f"FDA Adverse Event Report {identifier}",
        "text": result,
        "url": "",
        "metadata": {
            "report_id": identifier,
            "domain": "fda_adverse",
        },
    }


async def handle_fda_label_fetch(
    identifier: str,
    api_key: str | None = None,
    **_: Any,
) -> dict:
    """Handle FDA drug label domain fetch."""
    from czechmedmcp.openfda import get_drug_label

    result = await get_drug_label(
        identifier, api_key=api_key
    )
    return {
        "title": f"FDA Drug Label {identifier}",
        "text": result,
        "url": "",
        "metadata": {
            "set_id": identifier,
            "domain": "fda_label",
        },
    }


async def handle_fda_device_fetch(
    identifier: str,
    api_key: str | None = None,
    **_: Any,
) -> dict:
    """Handle FDA device event domain fetch."""
    from czechmedmcp.openfda import get_device_event

    result = await get_device_event(
        identifier, api_key=api_key
    )
    return {
        "title": f"FDA Device Event {identifier}",
        "text": result,
        "url": "",
        "metadata": {
            "mdr_report_key": identifier,
            "domain": "fda_device",
        },
    }


async def handle_fda_approval_fetch(
    identifier: str,
    api_key: str | None = None,
    **_: Any,
) -> dict:
    """Handle FDA drug approval domain fetch."""
    from czechmedmcp.openfda import get_drug_approval

    result = await get_drug_approval(
        identifier, api_key=api_key
    )
    return {
        "title": f"FDA Drug Approval {identifier}",
        "text": result,
        "url": "",
        "metadata": {
            "application_number": identifier,
            "domain": "fda_approval",
        },
    }


async def handle_fda_recall_fetch(
    identifier: str,
    api_key: str | None = None,
    **_: Any,
) -> dict:
    """Handle FDA drug recall domain fetch."""
    from czechmedmcp.openfda import get_drug_recall

    result = await get_drug_recall(
        identifier, api_key=api_key
    )
    return {
        "title": f"FDA Drug Recall {identifier}",
        "text": result,
        "url": "",
        "metadata": {
            "recall_number": identifier,
            "domain": "fda_recall",
        },
    }


async def handle_fda_shortage_fetch(
    identifier: str,
    api_key: str | None = None,
    **_: Any,
) -> dict:
    """Handle FDA drug shortage domain fetch."""
    from czechmedmcp.openfda import get_drug_shortage

    result = await get_drug_shortage(
        identifier, api_key=api_key
    )
    return {
        "title": f"FDA Drug Shortage - {identifier}",
        "text": result,
        "url": "",
        "metadata": {
            "drug": identifier,
            "domain": "fda_shortage",
        },
    }


async def handle_sukl_drug_fetch(
    identifier: str,
    **_: Any,
) -> dict:
    """Handle SUKL drug domain fetch."""
    from czechmedmcp.czech.sukl.getter import (
        _sukl_drug_details,
    )

    result = await _sukl_drug_details(identifier)
    return {
        "id": identifier,
        "title": f"SUKL Drug - {identifier}",
        "text": result,
        "url": (
            "https://www.sukl.cz/modules"
            "/medication/detail.php"
            f"?code={identifier}"
        ),
        "metadata": {
            "sukl_code": identifier,
            "domain": "sukl_drug",
        },
    }


async def handle_mkn_diagnosis_fetch(
    identifier: str,
    **_: Any,
) -> dict:
    """Handle MKN diagnosis domain fetch."""
    from czechmedmcp.czech.mkn.search import _mkn_get

    result = await _mkn_get(identifier)
    return {
        "id": identifier,
        "title": f"MKN-10 Diagnosis - {identifier}",
        "text": result,
        "url": "",
        "metadata": {
            "code": identifier,
            "domain": "mkn_diagnosis",
        },
    }


async def handle_nrpzs_provider_fetch(
    identifier: str,
    **_: Any,
) -> dict:
    """Handle NRPZS provider domain fetch."""
    from czechmedmcp.czech.nrpzs.search import _nrpzs_get

    result = await _nrpzs_get(identifier)
    return {
        "id": identifier,
        "title": f"NRPZS Provider - {identifier}",
        "text": result,
        "url": "",
        "metadata": {
            "provider_id": identifier,
            "domain": "nrpzs_provider",
        },
    }


async def handle_szv_procedure_fetch(
    identifier: str,
    **_: Any,
) -> dict:
    """Handle SZV procedure domain fetch."""
    from czechmedmcp.czech.szv.search import _szv_get

    result = await _szv_get(identifier)
    return {
        "id": identifier,
        "title": f"SZV Procedure - {identifier}",
        "text": result,
        "url": "",
        "metadata": {
            "code": identifier,
            "domain": "szv_procedure",
        },
    }


async def handle_vzp_reimbursement_fetch(
    identifier: str,
    **_: Any,
) -> dict:
    """Handle VZP reimbursement domain fetch."""
    from czechmedmcp.czech.vzp.drug_reimbursement import (
        _get_vzp_drug_reimbursement,
    )

    result = await _get_vzp_drug_reimbursement(identifier)
    return {
        "id": identifier,
        "title": f"VZP Reimbursement - {identifier}",
        "text": result,
        "url": "",
        "metadata": {
            "sukl_code": identifier,
            "domain": "vzp_reimbursement",
        },
    }


# Dispatch table mapping domain → handler function
FETCH_HANDLERS: dict[str, Any] = {
    "article": handle_article_fetch,
    "trial": handle_trial_fetch,
    "variant": handle_variant_fetch,
    "gene": handle_gene_fetch,
    "drug": handle_drug_fetch,
    "disease": handle_disease_fetch,
    "nci_organization": handle_nci_organization_fetch,
    "nci_intervention": handle_nci_intervention_fetch,
    "nci_disease": handle_nci_disease_fetch,
    "fda_adverse": handle_fda_adverse_fetch,
    "fda_label": handle_fda_label_fetch,
    "fda_device": handle_fda_device_fetch,
    "fda_approval": handle_fda_approval_fetch,
    "fda_recall": handle_fda_recall_fetch,
    "fda_shortage": handle_fda_shortage_fetch,
    "sukl_drug": handle_sukl_drug_fetch,
    "mkn_diagnosis": handle_mkn_diagnosis_fetch,
    "nrpzs_provider": handle_nrpzs_provider_fetch,
    "szv_procedure": handle_szv_procedure_fetch,
    "vzp_reimbursement": handle_vzp_reimbursement_fetch,
}
