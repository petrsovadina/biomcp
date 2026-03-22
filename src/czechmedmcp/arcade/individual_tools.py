"""Arcade tool wrappers for individual biomedical tools."""

import asyncio
import json
import logging
from typing import Annotated

from czechmedmcp.arcade import arcade_app
from czechmedmcp.articles.fetch import _article_details
from czechmedmcp.articles.search import _article_searcher
from czechmedmcp.cbioportal_helper import (
    get_cbioportal_summary_for_genes,
    get_variant_cbioportal_summary,
)
from czechmedmcp.constants import compute_skip
from czechmedmcp.core import ensure_list
from czechmedmcp.diseases.getter import _disease_details
from czechmedmcp.drugs.getter import _drug_details
from czechmedmcp.enrichr import EnrichrClient
from czechmedmcp.genes.getter import _gene_details
from czechmedmcp.oncokb_helper import get_oncokb_summary_for_genes
from czechmedmcp.trials.getter import (
    _trial_locations,
    _trial_outcomes,
    _trial_protocol,
    _trial_references,
)
from czechmedmcp.trials.search import _trial_searcher
from czechmedmcp.variants.getter import _variant_details
from czechmedmcp.variants.search import _variant_searcher

logger = logging.getLogger(__name__)


def _handle_cts_bucket_error(
    error: Exception, suggestions: str
) -> str | None:
    """Handle NCI CTS API bucket limit errors."""
    error_msg = str(error)
    if (
        "too_many_buckets_exception" in error_msg
        or "75000" in error_msg
    ):
        return (
            "\u26a0\ufe0f **Search Too Broad**\n\n"
            "The NCI API cannot process this search "
            "because it returns too many results.\n\n"
            f"{suggestions}"
        )
    return None


# Article Tools


@arcade_app.tool
async def article_searcher(
    chemicals: Annotated[
        str | None,
        "Chemical/drug names to search for",
    ] = None,
    diseases: Annotated[
        str | None,
        "Disease names to search for",
    ] = None,
    genes: Annotated[
        str | None,
        "Gene symbols to search for",
    ] = None,
    keywords: Annotated[
        str | None,
        "Free-text keywords to search for",
    ] = None,
    variants: Annotated[
        str | None,
        "Variant strings to search for (e.g., 'V600E', 'p.D277Y')",
    ] = None,
    include_preprints: Annotated[
        bool,
        "Include preprints from bioRxiv/medRxiv",
    ] = True,
    include_cbioportal: Annotated[
        bool,
        "Include cBioPortal cancer genomics summary when searching by gene",
    ] = True,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    page_size: Annotated[
        int,
        "Results per page",
    ] = 10,
) -> str:
    """Search PubMed/PubTator3 for research articles and preprints.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to plan your research strategy!

    Use this tool to find scientific literature ABOUT genes, variants, diseases, or chemicals.
    Results include articles from PubMed and optionally preprints from bioRxiv/medRxiv.

    Important: This searches for ARTICLES ABOUT these topics, not database records.
    For genetic variant database records, use variant_searcher instead.

    Example usage:
    - Find articles about BRAF mutations in melanoma
    - Search for papers on a specific drug's effects
    - Locate research on gene-disease associations
    """
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    chemicals_list = (
        ensure_list(chemicals, split_strings=True)
        if chemicals
        else None
    )
    diseases_list = (
        ensure_list(diseases, split_strings=True)
        if diseases
        else None
    )
    genes_list = (
        ensure_list(genes, split_strings=True)
        if genes
        else None
    )
    keywords_list = (
        ensure_list(keywords, split_strings=True)
        if keywords
        else None
    )
    variants_list = (
        ensure_list(variants, split_strings=True)
        if variants
        else None
    )

    result = await _article_searcher(
        call_benefit="Direct article search for specific biomedical topics",
        chemicals=chemicals_list,
        diseases=diseases_list,
        genes=genes_list,
        keywords=keywords_list,
        variants=variants_list,
        include_preprints=include_preprints,
        include_cbioportal=include_cbioportal,
    )

    # Add cBioPortal summary if searching by gene
    if include_cbioportal and genes_list:
        request_params = {
            "keywords": keywords_list,
            "diseases": diseases_list,
            "chemicals": chemicals_list,
            "variants": variants_list,
        }
        cbioportal_summary = await get_cbioportal_summary_for_genes(
            genes_list, request_params
        )
        if cbioportal_summary:
            result = cbioportal_summary + "\n\n---\n\n" + result

    return result


@arcade_app.tool
async def article_getter(
    pmid: Annotated[
        str,
        "Article identifier - either a PubMed ID (e.g., '38768446' or 'PMC11193658') or DOI (e.g., '10.1101/2024.01.20.23288905')",
    ],
) -> str:
    """Fetch detailed information for a specific article.

    Retrieves the full abstract and available text for an article by its identifier.
    Supports:
    - PubMed IDs (PMID) for published articles
    - PMC IDs for articles in PubMed Central
    - DOIs for preprints from Europe PMC

    Returns formatted text including:
    - Title
    - Abstract
    - Full text (when available from PMC for published articles)
    - Source information (PubMed or Europe PMC)
    """
    return await _article_details(
        call_benefit="Fetch detailed article information for analysis",
        pmid=pmid,
    )


# Trial Tools


@arcade_app.tool
async def trial_searcher(
    conditions: Annotated[
        str | None,
        "Medical conditions to search for",
    ] = None,
    interventions: Annotated[
        str | None,
        "Treatment interventions to search for",
    ] = None,
    other_terms: Annotated[
        str | None,
        "Additional search terms",
    ] = None,
    recruiting_status: Annotated[
        str | None,
        "Filter by recruiting status: OPEN, CLOSED, or ANY",
    ] = None,
    phase: Annotated[
        str | None,
        "Filter by clinical trial phase: EARLY_PHASE1, PHASE1, PHASE2, PHASE3, PHASE4, NOT_APPLICABLE",
    ] = None,
    location: Annotated[
        str | None,
        "Location term for geographic filtering",
    ] = None,
    lat: Annotated[
        float | None,
        "Latitude for location-based search. AI agents should geocode city names before using.",
    ] = None,
    long: Annotated[
        float | None,
        "Longitude for location-based search. AI agents should geocode city names before using.",
    ] = None,
    distance: Annotated[
        int | None,
        "Distance in miles from lat/long coordinates",
    ] = None,
    age_group: Annotated[
        str | None,
        "Filter by age group: CHILD, ADULT, or OLDER_ADULT",
    ] = None,
    sex: Annotated[
        str | None,
        "Filter by biological sex: FEMALE, MALE, or ALL",
    ] = None,
    healthy_volunteers: Annotated[
        str | None,
        "Filter by healthy volunteer eligibility: YES or NO",
    ] = None,
    study_type: Annotated[
        str | None,
        "Filter by study type: INTERVENTIONAL, OBSERVATIONAL, or EXPANDED_ACCESS",
    ] = None,
    funder_type: Annotated[
        str | None,
        "Filter by funding source: NIH, OTHER_GOV, INDUSTRY, or OTHER",
    ] = None,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    page_size: Annotated[
        int,
        "Results per page",
    ] = 10,
) -> str:
    """Search ClinicalTrials.gov for clinical studies.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to plan your research strategy!

    Comprehensive search tool for finding clinical trials based on multiple criteria.
    Supports filtering by conditions, interventions, location, phase, and eligibility.

    Location search notes:
    - Use either location term OR lat/long coordinates, not both
    - For city-based searches, AI agents should geocode to lat/long first
    - Distance parameter only works with lat/long coordinates

    Returns a formatted list of matching trials with key details.
    """
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    if lat is not None:
        lat = max(-90.0, min(90.0, lat))
    if long is not None:
        long = max(-180.0, min(180.0, long))
    if distance is not None:
        distance = max(1, distance)

    # Validate location parameters
    if location and (lat is not None or long is not None):
        raise ValueError(
            "Use either location term OR lat/long coordinates, not both"
        )

    if (lat is not None and long is None) or (
        lat is None and long is not None
    ):
        raise ValueError(
            "Both latitude and longitude must be provided together"
        )

    if distance is not None and (lat is None or long is None):
        raise ValueError(
            "Distance parameter requires both latitude and longitude"
        )

    conditions_list = (
        ensure_list(conditions, split_strings=True)
        if conditions
        else None
    )
    interventions_list = (
        ensure_list(interventions, split_strings=True)
        if interventions
        else None
    )
    other_terms_list = (
        ensure_list(other_terms, split_strings=True)
        if other_terms
        else None
    )

    return await _trial_searcher(
        call_benefit="Direct clinical trial search for specific criteria",
        conditions=conditions_list,
        interventions=interventions_list,
        terms=other_terms_list,
        recruiting_status=recruiting_status,
        phase=phase,
        lat=lat,
        long=long,
        distance=distance,
        age_group=age_group,
        study_type=study_type,
        page_size=page_size,
    )


@arcade_app.tool
async def trial_getter(
    nct_id: Annotated[
        str,
        "NCT ID (e.g., 'NCT06524388')",
    ],
) -> str:
    """Fetch comprehensive details for a specific clinical trial.

    Retrieves all available information for a clinical trial by its NCT ID.
    This includes protocol details, locations, outcomes, and references.

    For specific sections only, use the specialized getter tools:
    - trial_protocol_getter: Core protocol information
    - trial_locations_getter: Site locations and contacts
    - trial_outcomes_getter: Primary/secondary outcomes and results
    - trial_references_getter: Publications and references
    """
    benefit = "Fetch comprehensive trial details for analysis"
    protocol, locations, outcomes, references = await asyncio.gather(
        _trial_protocol(call_benefit=benefit, nct_id=nct_id),
        _trial_locations(call_benefit=benefit, nct_id=nct_id),
        _trial_outcomes(call_benefit=benefit, nct_id=nct_id),
        _trial_references(call_benefit=benefit, nct_id=nct_id),
    )

    results = [
        r for r in [protocol, locations, outcomes, references] if r
    ]
    return (
        "\n\n".join(results)
        if results
        else f"No data found for trial {nct_id}"
    )


@arcade_app.tool
async def trial_protocol_getter(
    nct_id: Annotated[
        str,
        "NCT ID (e.g., 'NCT06524388')",
    ],
) -> str:
    """Fetch core protocol information for a clinical trial.

    Retrieves essential protocol details including:
    - Official title and brief summary
    - Study status and sponsor information
    - Study design (type, phase, allocation, masking)
    - Eligibility criteria
    - Primary completion date
    """
    return await _trial_protocol(
        call_benefit="Fetch trial protocol information for eligibility assessment",
        nct_id=nct_id,
    )


@arcade_app.tool
async def trial_references_getter(
    nct_id: Annotated[
        str,
        "NCT ID (e.g., 'NCT06524388')",
    ],
) -> str:
    """Fetch publications and references for a clinical trial.

    Retrieves all linked publications including:
    - Published results papers
    - Background literature
    - Protocol publications
    - Related analyses

    Includes PubMed IDs when available for easy cross-referencing.
    """
    return await _trial_references(
        call_benefit="Fetch trial publications and references for evidence review",
        nct_id=nct_id,
    )


@arcade_app.tool
async def trial_outcomes_getter(
    nct_id: Annotated[
        str,
        "NCT ID (e.g., 'NCT06524388')",
    ],
) -> str:
    """Fetch outcome measures and results for a clinical trial.

    Retrieves detailed outcome information including:
    - Primary outcome measures
    - Secondary outcome measures
    - Results data (if available)
    - Adverse events (if reported)

    Note: Results are only available for completed trials that have posted data.
    """
    return await _trial_outcomes(
        call_benefit="Fetch trial outcome measures and results for efficacy assessment",
        nct_id=nct_id,
    )


@arcade_app.tool
async def trial_locations_getter(
    nct_id: Annotated[
        str,
        "NCT ID (e.g., 'NCT06524388')",
    ],
) -> str:
    """Fetch contact and location details for a clinical trial.

    Retrieves all study locations including:
    - Facility names and addresses
    - Principal investigator information
    - Contact details (when recruiting)
    - Recruitment status by site

    Useful for finding trials near specific locations or contacting study teams.
    """
    return await _trial_locations(
        call_benefit="Fetch trial locations and contacts for enrollment information",
        nct_id=nct_id,
    )


# Variant Tools


@arcade_app.tool
async def variant_searcher(  # noqa: C901
    gene: Annotated[
        str | None,
        "Gene symbol (e.g., 'BRAF', 'TP53')",
    ] = None,
    hgvs: Annotated[
        str | None,
        "HGVS notation (genomic, coding, or protein)",
    ] = None,
    hgvsp: Annotated[
        str | None,
        "Protein change in HGVS format (e.g., 'p.V600E')",
    ] = None,
    hgvsc: Annotated[
        str | None,
        "Coding sequence change (e.g., 'c.1799T>A')",
    ] = None,
    rsid: Annotated[
        str | None,
        "dbSNP rsID (e.g., 'rs113488022')",
    ] = None,
    region: Annotated[
        str | None,
        "Genomic region (e.g., 'chr7:140753336-140753337')",
    ] = None,
    significance: Annotated[
        str | None,
        "Clinical significance filter: pathogenic, likely_pathogenic, uncertain_significance, likely_benign, benign, conflicting",
    ] = None,
    frequency_min: Annotated[
        float | None,
        "Minimum allele frequency (0-1)",
    ] = None,
    frequency_max: Annotated[
        float | None,
        "Maximum allele frequency (0-1)",
    ] = None,
    consequence: Annotated[
        str | None,
        "Variant consequence (e.g., 'missense_variant')",
    ] = None,
    cadd_score_min: Annotated[
        float | None,
        "Minimum CADD score for pathogenicity",
    ] = None,
    sift_prediction: Annotated[
        str | None,
        "SIFT functional prediction: deleterious or tolerated",
    ] = None,
    polyphen_prediction: Annotated[
        str | None,
        "PolyPhen-2 functional prediction: probably_damaging, possibly_damaging, or benign",
    ] = None,
    include_cbioportal: Annotated[
        bool,
        "Include cBioPortal cancer genomics summary when searching by gene",
    ] = True,
    include_oncokb: Annotated[
        bool,
        "Include OncoKB precision oncology summary when searching by gene",
    ] = True,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    page_size: Annotated[
        int,
        "Results per page",
    ] = 10,
) -> str:
    """Search MyVariant.info for genetic variant DATABASE RECORDS.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to plan your research strategy!

    Important: This searches for variant DATABASE RECORDS (frequency, significance, etc.),
    NOT articles about variants. For articles about variants, use article_searcher.

    Searches the comprehensive variant database including:
    - Population frequencies (gnomAD, 1000 Genomes, etc.)
    - Clinical significance (ClinVar)
    - Functional predictions (SIFT, PolyPhen, CADD)
    - Gene and protein consequences

    Search by various identifiers or filter by clinical/functional criteria.
    """
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    if frequency_min is not None:
        frequency_min = max(0.0, min(1.0, frequency_min))
    if frequency_max is not None:
        frequency_max = max(0.0, min(1.0, frequency_max))

    # Map generic hgvs to hgvsp/hgvsc based on notation format
    effective_hgvsp = hgvsp
    effective_hgvsc = hgvsc
    if hgvs:
        if hgvs.startswith("p.") or "p." in hgvs:
            effective_hgvsp = effective_hgvsp or hgvs
        elif hgvs.startswith("c.") or "c." in hgvs:
            effective_hgvsc = effective_hgvsc or hgvs
        else:
            # Genomic HGVS — use as rsid-style direct query
            rsid = rsid or hgvs

    result = await _variant_searcher(
        call_benefit="Direct variant database search for genetic analysis",
        gene=gene,
        hgvsp=effective_hgvsp,
        hgvsc=effective_hgvsc,
        rsid=rsid,
        region=region,
        significance=significance,
        min_frequency=frequency_min,
        max_frequency=frequency_max,
        cadd=cadd_score_min,
        sift=sift_prediction,
        polyphen=polyphen_prediction,
        size=page_size,
        offset=compute_skip(page, page_size) if page > 1 else 0,
    )

    # Fetch cBioPortal + OncoKB summaries in parallel
    if gene and (include_cbioportal or include_oncokb):
        tasks = {}
        if include_cbioportal:
            tasks["cbio"] = get_variant_cbioportal_summary(gene)
        if include_oncokb:
            tasks["oncokb"] = get_oncokb_summary_for_genes([gene])

        summaries = await asyncio.gather(*tasks.values())
        summary_map = dict(
            zip(tasks.keys(), summaries, strict=False)
        )

        if cbio := summary_map.get("cbio"):
            result = cbio + "\n\n" + result
        if oncokb := summary_map.get("oncokb"):
            result = oncokb + "\n\n" + result

    return result


@arcade_app.tool
async def variant_getter(
    variant_id: Annotated[
        str,
        "Variant ID (HGVS, rsID, or MyVariant ID like 'chr7:g.140753336A>T')",
    ],
    include_external: Annotated[
        bool,
        "Include external annotations (TCGA, 1000 Genomes, functional predictions)",
    ] = True,
) -> str:
    """Fetch comprehensive details for a specific genetic variant.

    Retrieves all available information for a variant including:
    - Gene location and consequences
    - Population frequencies across databases
    - Clinical significance from ClinVar
    - Functional predictions
    - External annotations (TCGA cancer data, conservation scores)

    Accepts various ID formats:
    - HGVS: NM_004333.4:c.1799T>A
    - rsID: rs113488022
    - MyVariant ID: chr7:g.140753336A>T
    """
    return await _variant_details(
        call_benefit="Fetch comprehensive variant annotations for interpretation",
        variant_id=variant_id,
        include_external=include_external,
    )


@arcade_app.tool
async def alphagenome_predictor(
    chromosome: Annotated[
        str,
        "Chromosome (e.g., 'chr7', 'chrX')",
    ],
    position: Annotated[
        int,
        "1-based genomic position of the variant",
    ],
    reference: Annotated[
        str,
        "Reference allele(s) (e.g., 'A', 'ATG')",
    ],
    alternate: Annotated[
        str,
        "Alternate allele(s) (e.g., 'T', 'A')",
    ],
    interval_size: Annotated[
        int,
        "Size of genomic interval to analyze in bp (max 1,000,000)",
    ] = 131072,
    tissue_types: Annotated[
        str | None,
        "UBERON ontology terms for tissue-specific predictions (e.g., 'UBERON:0002367' for external ear)",
    ] = None,
    significance_threshold: Annotated[
        float,
        "Threshold for significant log2 fold changes (default: 0.5)",
    ] = 0.5,
    api_key: Annotated[
        str | None,
        "AlphaGenome API key. Check if user mentioned 'my AlphaGenome API key is...' in their message. If not provided here and no env var is set, user will be prompted to provide one.",
    ] = None,
) -> str:
    """Predict variant effects on gene regulation using Google DeepMind's AlphaGenome.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to plan your analysis strategy!

    AlphaGenome provides state-of-the-art predictions for how genetic variants
    affect gene regulation, including:
    - Gene expression changes (RNA-seq)
    - Chromatin accessibility impacts (ATAC-seq, DNase-seq)
    - Splicing alterations
    - Promoter activity changes (CAGE)

    This tool requires:
    1. AlphaGenome to be installed (see error message for instructions)
    2. An API key from https://deepmind.google.com/science/alphagenome

    API Key Options:
    - Provide directly via the api_key parameter
    - Or set ALPHAGENOME_API_KEY environment variable

    Example usage:
    - Predict regulatory effects of BRAF V600E mutation: chr7:140753336 A>T
    - Assess non-coding variant impact on gene expression
    - Evaluate promoter variants in specific tissues

    Note: This is an optional tool that enhances variant interpretation
    with AI predictions. Standard annotations remain available via variant_getter.
    """
    from czechmedmcp.variants.alphagenome import (
        predict_variant_effects,
    )

    interval_size = max(2000, min(1000000, interval_size))
    significance_threshold = max(0.0, min(5.0, significance_threshold))

    tissue_types_list = (
        ensure_list(tissue_types, split_strings=True)
        if tissue_types
        else None
    )

    return await predict_variant_effects(
        chromosome=chromosome,
        position=position,
        reference=reference,
        alternate=alternate,
        interval_size=interval_size,
        tissue_types=tissue_types_list,
        significance_threshold=significance_threshold,
        api_key=api_key,
    )


# Gene Tools


@arcade_app.tool
async def gene_getter(
    gene_id_or_symbol: Annotated[
        str,
        "Gene symbol (e.g., 'TP53', 'BRAF') or Entrez ID (e.g., '7157')",
    ],
) -> str:
    """Get detailed gene information from MyGene.info.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to understand your research goal!

    Provides real-time gene annotations including:
    - Official gene name and symbol
    - Gene summary/description
    - Aliases and alternative names
    - Gene type (protein-coding, etc.)
    - Links to external databases

    This tool fetches CURRENT gene information from MyGene.info, ensuring
    you always have the latest annotations and nomenclature.

    Example usage:
    - Get information about TP53 tumor suppressor
    - Look up BRAF kinase gene details
    - Find the official name for a gene by its alias

    Note: For genetic variants, use variant_searcher. For articles about genes, use article_searcher.
    """
    return await _gene_details(
        call_benefit="Get up-to-date gene annotations and information",
        gene_id_or_symbol=gene_id_or_symbol,
    )


@arcade_app.tool
async def enrichr_analyzer(
    genes: Annotated[
        str,
        "Gene symbols to analyze (e.g., 'TP53,BRCA1' or 'TP53')",
    ],
    database: Annotated[
        str,
        "Enrichment database category: pathway, kegg, reactome, wikipathways, ontology, go_process, go_molecular, go_cellular, celltypes, tissues, diseases, gwas, transcription_factors, tf",
    ] = "pathway",
    species: Annotated[
        str,
        "Species (currently only 'human' supported)",
    ] = "human",
) -> str:
    """Perform functional enrichment analysis on a gene list.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to plan your enrichment analysis strategy!

    Inspired by gget enrichr (Luebbert & Pachter, 2023).
    Uses Enrichr API: https://maayanlab.cloud/Enrichr/

    Analyzes a list of genes to identify enriched:
    - Biological pathways (KEGG, Reactome, WikiPathways)
    - Gene Ontology terms (biological process, molecular function, cellular component)
    - Cell types and tissue expression patterns
    - Disease associations (GWAS Catalog)
    - Transcription factor targets (ChEA)

    Returns enrichment results with p-values, z-scores, and combined scores
    for each significantly enriched term.

    Example usage:
    - Analyze differentially expressed genes for pathway enrichment
    - Identify cell types associated with a gene signature
    - Find diseases associated with a gene list
    - Discover transcription factors regulating a set of genes

    Database categories:
    - pathway, kegg, reactome, wikipathways: Biological pathways
    - ontology, go_process, go_molecular, go_cellular: Gene Ontology terms
    - celltypes, tissues: Cell type and tissue expression
    - diseases, gwas: Disease associations
    - transcription_factors, tf: Transcription factor targets

    Note: This tool submits gene lists to the public Enrichr API. For single gene
    enrichment, consider using gene_getter with --enrich flag via CLI.
    """
    gene_list = (
        ensure_list(genes, split_strings=True) if genes else []
    )

    if not gene_list:
        return json.dumps({
            "error": "No genes provided for enrichment analysis",
            "genes": [],
        })

    if species.lower() != "human":
        return json.dumps({
            "error": f"Species '{species}' not supported. Only 'human' is currently available.",
            "genes": gene_list,
        })

    try:
        client = EnrichrClient()
        terms = await client.enrich(
            genes=gene_list,
            database=database,
        )

        if terms is None:
            return json.dumps({
                "error": "Failed to retrieve enrichment results from Enrichr API",
                "genes": gene_list,
                "database": database,
            })

        enrichment_terms = [
            {
                "rank": term.rank,
                "path_name": term.path_name,
                "p_val": term.p_val,
                "z_score": term.z_score,
                "combined_score": term.combined_score,
                "overlapping_genes": term.overlapping_genes,
                "adj_p_val": term.adj_p_val,
                "database": term.database,
            }
            for term in terms
        ]

        return json.dumps(
            {
                "genes": gene_list,
                "database": (
                    terms[0].database if terms else database
                ),
                "enrichment_terms": enrichment_terms,
                "total_terms": len(enrichment_terms),
            },
            indent=2,
        )

    except Exception as e:
        logger.error(f"Enrichment analysis failed: {e}")
        return json.dumps({
            "error": f"Enrichment analysis failed: {e!s}",
            "genes": gene_list,
            "database": database,
        })


# Disease Tools


@arcade_app.tool
async def disease_getter(
    disease_id_or_name: Annotated[
        str,
        "Disease name (e.g., 'melanoma', 'lung cancer') or ontology ID (e.g., 'MONDO:0016575', 'DOID:1909')",
    ],
) -> str:
    """Get detailed disease information from MyDisease.info.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to understand your research goal!

    Provides real-time disease annotations including:
    - Official disease name and definition
    - Disease synonyms and alternative names
    - Ontology mappings (MONDO, DOID, OMIM, etc.)
    - Associated phenotypes
    - Links to disease databases

    This tool fetches CURRENT disease information from MyDisease.info, ensuring
    you always have the latest ontology mappings and definitions.

    Example usage:
    - Get the definition of GIST (Gastrointestinal Stromal Tumor)
    - Look up synonyms for melanoma
    - Find the MONDO ID for a disease by name

    Note: For clinical trials about diseases, use trial_searcher. For articles about diseases, use article_searcher.
    """
    return await _disease_details(
        call_benefit="Get up-to-date disease definitions and ontology information",
        disease_id_or_name=disease_id_or_name,
    )


@arcade_app.tool
async def drug_getter(
    drug_id_or_name: Annotated[
        str,
        "Drug name (e.g., 'aspirin', 'imatinib') or ID (e.g., 'DB00945', 'CHEMBL941')",
    ],
) -> str:
    """Get detailed drug/chemical information from MyChem.info.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to understand your research goal!

    This tool provides comprehensive drug information including:
    - Chemical properties (formula, InChIKey)
    - Drug identifiers (DrugBank, ChEMBL, PubChem)
    - Trade names and brand names
    - Clinical indications
    - Mechanism of action
    - Pharmacology details
    - Links to drug databases

    This tool fetches CURRENT drug information from MyChem.info, part of the
    BioThings suite, ensuring you always have the latest drug data.

    Example usage:
    - Get information about imatinib (Gleevec)
    - Look up details for DrugBank ID DB00619
    - Find the mechanism of action for pembrolizumab

    Note: For clinical trials about drugs, use trial_searcher. For articles about drugs, use article_searcher.
    """
    return await _drug_details(drug_id_or_name)


# NCI-Specific Tools


@arcade_app.tool
async def nci_organization_searcher(
    name: Annotated[
        str | None,
        "Organization name to search for (partial match supported)",
    ] = None,
    organization_type: Annotated[
        str | None,
        "Type of organization (e.g., 'Academic', 'Industry', 'Government')",
    ] = None,
    city: Annotated[
        str | None,
        "City where organization is located. IMPORTANT: Always use with state to avoid API errors",
    ] = None,
    state: Annotated[
        str | None,
        "State/province code (e.g., 'CA', 'NY'). IMPORTANT: Always use with city to avoid API errors",
    ] = None,
    api_key: Annotated[
        str | None,
        "NCI API key. Check if user mentioned 'my NCI API key is...' in their message. If not provided here and no env var is set, user will be prompted to provide one.",
    ] = None,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    page_size: Annotated[
        int,
        "Results per page",
    ] = 20,
) -> str:
    """Search for organizations in the NCI Clinical Trials database.

    Searches the National Cancer Institute's curated database of organizations
    involved in cancer clinical trials. This includes:
    - Academic medical centers
    - Community hospitals
    - Industry sponsors
    - Government facilities
    - Research networks

    Requires NCI API key from: https://clinicaltrialsapi.cancer.gov/

    IMPORTANT: To avoid API errors, always use city AND state together when searching by location.
    The NCI API has limitations on broad searches.

    Example usage:
    - Find cancer centers in Boston, MA (city AND state)
    - Search for "MD Anderson" in Houston, TX
    - List academic organizations in Cleveland, OH
    - Search by organization name alone (without location)
    """
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    from czechmedmcp.integrations.cts_api import CTSAPIError
    from czechmedmcp.organizations import search_organizations
    from czechmedmcp.organizations.search import (
        format_organization_results,
    )

    try:
        results = await search_organizations(
            name=name,
            org_type=organization_type,
            city=city,
            state=state,
            page_size=page_size,
            page=page,
            api_key=api_key,
        )
        return format_organization_results(results)
    except CTSAPIError as e:
        msg = _handle_cts_bucket_error(
            e,
            "**To fix this, try:**\n"
            "1. **Always use city AND state together** for location searches\n"
            "2. Add an organization name (even partial) to narrow results\n"
            "3. Use multiple filters together (name + location, or name + type)\n\n"
            "**Examples that work:**\n"
            "- `nci_organization_searcher(city='Cleveland', state='OH')`\n"
            "- `nci_organization_searcher(name='Cleveland Clinic')`\n"
            "- `nci_organization_searcher(name='cancer', city='Boston', state='MA')`\n"
            "- `nci_organization_searcher(organization_type='Academic', city='Houston', state='TX')`",
        )
        if msg:
            return msg
        raise


@arcade_app.tool
async def nci_organization_getter(
    organization_id: Annotated[
        str,
        "NCI organization ID (e.g., 'NCI-2011-03337')",
    ],
    api_key: Annotated[
        str | None,
        "NCI API key. Check if user mentioned 'my NCI API key is...' in their message. If not provided here and no env var is set, user will be prompted to provide one.",
    ] = None,
) -> str:
    """Get detailed information about a specific organization from NCI.

    Retrieves comprehensive details about an organization including:
    - Full name and aliases
    - Address and contact information
    - Organization type and role
    - Associated clinical trials
    - Research focus areas

    Requires NCI API key from: https://clinicaltrialsapi.cancer.gov/

    Example usage:
    - Get details about a specific cancer center
    - Find contact information for trial sponsors
    - View organization's trial portfolio
    """
    from czechmedmcp.organizations import get_organization
    from czechmedmcp.organizations.getter import (
        format_organization_details,
    )

    org_data = await get_organization(
        org_id=organization_id,
        api_key=api_key,
    )

    return format_organization_details(org_data)


@arcade_app.tool
async def nci_intervention_searcher(
    name: Annotated[
        str | None,
        "Intervention name to search for (e.g., 'pembrolizumab')",
    ] = None,
    intervention_type: Annotated[
        str | None,
        "Type of intervention: 'Drug', 'Device', 'Biological', 'Procedure', 'Radiation', 'Behavioral', 'Genetic', 'Dietary', 'Other'",
    ] = None,
    synonyms: Annotated[
        bool,
        "Include synonym matches in search",
    ] = True,
    api_key: Annotated[
        str | None,
        "NCI API key. Check if user mentioned 'my NCI API key is...' in their message. If not provided here and no env var is set, user will be prompted to provide one.",
    ] = None,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    page_size: Annotated[
        int | None,
        "Results per page. If not specified, returns all matching results.",
    ] = None,
) -> str:
    """Search for interventions in the NCI Clinical Trials database.

    Searches the National Cancer Institute's curated database of interventions
    used in cancer clinical trials. This includes:
    - FDA-approved drugs
    - Investigational agents
    - Medical devices
    - Surgical procedures
    - Radiation therapies
    - Behavioral interventions

    Requires NCI API key from: https://clinicaltrialsapi.cancer.gov/

    Example usage:
    - Find all trials using pembrolizumab
    - Search for CAR-T cell therapies
    - List radiation therapy protocols
    - Find dietary interventions
    """
    page = max(1, page)
    if page_size is not None:
        page_size = max(1, min(100, page_size))

    from czechmedmcp.integrations.cts_api import CTSAPIError
    from czechmedmcp.interventions import search_interventions
    from czechmedmcp.interventions.search import (
        format_intervention_results,
    )

    try:
        results = await search_interventions(
            name=name,
            intervention_type=intervention_type,
            synonyms=synonyms,
            page_size=page_size,
            page=page,
            api_key=api_key,
        )
        return format_intervention_results(results)
    except CTSAPIError as e:
        msg = _handle_cts_bucket_error(
            e,
            "**Try adding more specific filters:**\n"
            "- Add an intervention name (even partial)\n"
            "- Specify an intervention type (e.g., 'Drug', 'Device')\n"
            "- Search for a specific drug or therapy name\n\n"
            "**Example searches that work better:**\n"
            "- Search for 'pembrolizumab' instead of all drugs\n"
            "- Search for 'CAR-T' to find CAR-T cell therapies\n"
            "- Filter by type: Drug, Device, Procedure, etc.",
        )
        if msg:
            return msg
        raise


@arcade_app.tool
async def nci_intervention_getter(
    intervention_id: Annotated[
        str,
        "NCI intervention ID (e.g., 'INT123456')",
    ],
    api_key: Annotated[
        str | None,
        "NCI API key. Check if user mentioned 'my NCI API key is...' in their message. If not provided here and no env var is set, user will be prompted to provide one.",
    ] = None,
) -> str:
    """Get detailed information about a specific intervention from NCI.

    Retrieves comprehensive details about an intervention including:
    - Full name and synonyms
    - Intervention type and category
    - Mechanism of action (for drugs)
    - FDA approval status
    - Associated clinical trials
    - Combination therapies

    Requires NCI API key from: https://clinicaltrialsapi.cancer.gov/

    Example usage:
    - Get details about a specific drug
    - Find all trials using a device
    - View combination therapy protocols
    """
    from czechmedmcp.interventions import get_intervention
    from czechmedmcp.interventions.getter import (
        format_intervention_details,
    )

    intervention_data = await get_intervention(
        intervention_id=intervention_id,
        api_key=api_key,
    )

    return format_intervention_details(intervention_data)


# Biomarker Tools


@arcade_app.tool
async def nci_biomarker_searcher(
    name: Annotated[
        str | None,
        "Biomarker name to search for (e.g., 'PD-L1', 'EGFR mutation')",
    ] = None,
    biomarker_type: Annotated[
        str | None,
        "Type of biomarker ('reference_gene' or 'branch')",
    ] = None,
    api_key: Annotated[
        str | None,
        "NCI API key. Check if user mentioned 'my NCI API key is...' in their message. If not provided here and no env var is set, user will be prompted to provide one.",
    ] = None,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    page_size: Annotated[
        int,
        "Results per page",
    ] = 20,
) -> str:
    """Search for biomarkers in the NCI Clinical Trials database.

    Searches for biomarkers used in clinical trial eligibility criteria.
    This is essential for precision medicine trials that select patients
    based on specific biomarker characteristics.

    Biomarker examples:
    - Gene mutations (e.g., BRAF V600E, EGFR T790M)
    - Protein expression (e.g., PD-L1 \u2265 50%, HER2 positive)
    - Gene fusions (e.g., ALK fusion, ROS1 fusion)
    - Other molecular markers (e.g., MSI-H, TMB-high)

    Requires NCI API key from: https://clinicaltrialsapi.cancer.gov/

    Note: Biomarker data availability may be limited in CTRP.
    Results focus on biomarkers used in trial eligibility criteria.

    Example usage:
    - Search for PD-L1 expression biomarkers
    - Find trials requiring EGFR mutations
    - Look up biomarkers tested by NGS
    - Search for HER2 expression markers
    """
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    from czechmedmcp.biomarkers import search_biomarkers
    from czechmedmcp.biomarkers.search import (
        format_biomarker_results,
    )
    from czechmedmcp.integrations.cts_api import CTSAPIError

    try:
        results = await search_biomarkers(
            name=name,
            biomarker_type=biomarker_type,
            page_size=page_size,
            page=page,
            api_key=api_key,
        )
        return format_biomarker_results(results)
    except CTSAPIError as e:
        msg = _handle_cts_bucket_error(
            e,
            "**Try adding more specific filters:**\n"
            "- Add a biomarker name (even partial)\n"
            "- Specify a gene symbol\n"
            "- Add an assay type (e.g., 'IHC', 'NGS')\n\n"
            "**Example searches that work:**\n"
            "- `nci_biomarker_searcher(name='PD-L1')`\n"
            "- `nci_biomarker_searcher(gene='EGFR', biomarker_type='mutation')`\n"
            "- `nci_biomarker_searcher(assay_type='IHC')`",
        )
        if msg:
            return msg
        raise


# NCI Disease Tools


@arcade_app.tool
async def nci_disease_searcher(
    name: Annotated[
        str | None,
        "Disease name to search for (partial match)",
    ] = None,
    include_synonyms: Annotated[
        bool,
        "Include synonym matches in search",
    ] = True,
    category: Annotated[
        str | None,
        "Disease category/type filter",
    ] = None,
    api_key: Annotated[
        str | None,
        "NCI API key. Check if user mentioned 'my NCI API key is...' in their message. If not provided here and no env var is set, user will be prompted to provide one.",
    ] = None,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    page_size: Annotated[
        int,
        "Results per page",
    ] = 20,
) -> str:
    """Search NCI's controlled vocabulary of cancer conditions.

    Searches the National Cancer Institute's curated database of cancer
    conditions and diseases used in clinical trials. This is different from
    the general disease_getter tool which uses MyDisease.info.

    NCI's disease vocabulary provides:
    - Official cancer terminology used in trials
    - Disease synonyms and alternative names
    - Hierarchical disease classifications
    - Standardized disease codes for trial matching

    Requires NCI API key from: https://clinicaltrialsapi.cancer.gov/

    Example usage:
    - Search for specific cancer types (e.g., "melanoma")
    - Find all lung cancer subtypes
    - Look up official names for disease synonyms
    - Get standardized disease terms for trial searches

    Note: This is specifically for NCI's cancer disease vocabulary.
    For general disease information, use the disease_getter tool.
    """
    page = max(1, page)
    page_size = max(1, min(100, page_size))

    from czechmedmcp.diseases import search_diseases
    from czechmedmcp.diseases.search import format_disease_results
    from czechmedmcp.integrations.cts_api import CTSAPIError

    try:
        results = await search_diseases(
            name=name,
            include_synonyms=include_synonyms,
            category=category,
            page_size=page_size,
            page=page,
            api_key=api_key,
        )
        return format_disease_results(results)
    except CTSAPIError as e:
        msg = _handle_cts_bucket_error(
            e,
            "**Try adding more specific filters:**\n"
            "- Add a disease name (even partial)\n"
            "- Specify a disease category\n"
            "- Use more specific search terms\n\n"
            "**Example searches that work:**\n"
            "- `nci_disease_searcher(name='melanoma')`\n"
            "- `nci_disease_searcher(name='lung', category='maintype')`\n"
            "- `nci_disease_searcher(name='NSCLC')`",
        )
        if msg:
            return msg
        raise


# OpenFDA Tools


@arcade_app.tool
async def openfda_adverse_searcher(
    drug: Annotated[
        str | None,
        "Drug name to search for adverse events",
    ] = None,
    reaction: Annotated[
        str | None,
        "Adverse reaction term to search for",
    ] = None,
    serious: Annotated[
        bool | None,
        "Filter for serious events only",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of results",
    ] = 25,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Search FDA adverse event reports (FAERS) for drug safety information.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to plan your research strategy!

    Searches FDA's Adverse Event Reporting System for:
    - Drug side effects and adverse reactions
    - Serious event reports (death, hospitalization, disability)
    - Safety signal patterns across patient populations

    Note: These reports do not establish causation - they are voluntary reports
    that may contain incomplete or unverified information.
    """
    limit = max(1, min(100, limit))
    page = max(1, page)

    from czechmedmcp.openfda import search_adverse_events

    skip = compute_skip(page, limit)
    return await search_adverse_events(
        drug=drug,
        reaction=reaction,
        serious=serious,
        limit=limit,
        skip=skip,
        api_key=api_key,
    )


@arcade_app.tool
async def openfda_adverse_getter(
    report_id: Annotated[
        str,
        "Safety report ID",
    ],
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Get detailed information for a specific FDA adverse event report.

    Retrieves complete details including:
    - Patient demographics and medical history
    - All drugs involved and dosages
    - Complete list of adverse reactions
    - Event narrative and outcomes
    - Reporter information
    """
    from czechmedmcp.openfda import get_adverse_event

    return await get_adverse_event(report_id, api_key=api_key)


@arcade_app.tool
async def openfda_label_searcher(
    name: Annotated[
        str | None,
        "Drug name to search for",
    ] = None,
    indication: Annotated[
        str | None,
        "Search for drugs indicated for this condition",
    ] = None,
    boxed_warning: Annotated[
        bool,
        "Filter for drugs with boxed warnings",
    ] = False,
    section: Annotated[
        str | None,
        "Specific label section (e.g., 'contraindications', 'warnings')",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of results",
    ] = 25,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Search FDA drug product labels (SPL) for prescribing information.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to plan your research strategy!

    Searches official FDA drug labels for:
    - Approved indications and usage
    - Dosage and administration guidelines
    - Contraindications and warnings
    - Drug interactions and adverse reactions
    - Special population considerations

    Label sections include: indications, dosage, contraindications, warnings,
    adverse, interactions, pregnancy, pediatric, geriatric, overdose
    """
    limit = max(1, min(100, limit))
    page = max(1, page)

    from czechmedmcp.openfda import search_drug_labels

    skip = compute_skip(page, limit)
    return await search_drug_labels(
        name=name,
        indication=indication,
        boxed_warning=boxed_warning,
        section=section,
        limit=limit,
        skip=skip,
        api_key=api_key,
    )


@arcade_app.tool
async def openfda_label_getter(
    set_id: Annotated[
        str,
        "Label set ID",
    ],
    sections: Annotated[
        str | None,
        "Specific sections to retrieve, comma-separated (default: key sections)",
    ] = None,
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Get complete FDA drug label information by set ID.

    Retrieves the full prescribing information including:
    - Complete indications and usage text
    - Detailed dosing instructions
    - All warnings and precautions
    - Clinical pharmacology and studies
    - Manufacturing and storage information

    Specify sections to retrieve specific parts, or leave empty for default key sections.
    """
    from czechmedmcp.openfda import get_drug_label

    sections_list = (
        ensure_list(sections, split_strings=True)
        if sections
        else None
    )
    return await get_drug_label(
        set_id, sections_list, api_key=api_key
    )


@arcade_app.tool
async def openfda_device_searcher(
    device: Annotated[
        str | None,
        "Device name to search for",
    ] = None,
    manufacturer: Annotated[
        str | None,
        "Manufacturer name",
    ] = None,
    problem: Annotated[
        str | None,
        "Device problem description",
    ] = None,
    product_code: Annotated[
        str | None,
        "FDA product code",
    ] = None,
    genomics_only: Annotated[
        bool,
        "Filter to genomic/diagnostic devices only",
    ] = True,
    limit: Annotated[
        int,
        "Maximum number of results",
    ] = 25,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Search FDA device adverse event reports (MAUDE) for medical device issues.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to plan your research strategy!

    Searches FDA's device adverse event database for:
    - Device malfunctions and failures
    - Patient injuries related to devices
    - Genomic test and diagnostic device issues

    By default, filters to genomic/diagnostic devices relevant to precision medicine.
    Set genomics_only=False to search all medical devices.
    """
    limit = max(1, min(100, limit))
    page = max(1, page)

    from czechmedmcp.openfda import search_device_events

    skip = compute_skip(page, limit)
    return await search_device_events(
        device=device,
        manufacturer=manufacturer,
        problem=problem,
        product_code=product_code,
        genomics_only=genomics_only,
        limit=limit,
        skip=skip,
        api_key=api_key,
    )


@arcade_app.tool
async def openfda_device_getter(
    mdr_report_key: Annotated[
        str,
        "MDR report key",
    ],
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Get detailed information for a specific FDA device event report.

    Retrieves complete device event details including:
    - Device identification and specifications
    - Complete event narrative
    - Patient outcomes and impacts
    - Manufacturer analysis and actions
    - Remedial actions taken
    """
    from czechmedmcp.openfda import get_device_event

    return await get_device_event(mdr_report_key, api_key=api_key)


@arcade_app.tool
async def openfda_approval_searcher(
    drug: Annotated[
        str | None,
        "Drug name (brand or generic) to search for",
    ] = None,
    application_number: Annotated[
        str | None,
        "NDA or BLA application number",
    ] = None,
    approval_year: Annotated[
        str | None,
        "Year of approval (YYYY format)",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of results",
    ] = 25,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Search FDA drug approval records from Drugs@FDA database.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to plan your research strategy!

    Returns information about:
    - Application numbers and sponsors
    - Brand and generic names
    - Product formulations and strengths
    - Marketing status and approval dates
    - Submission history

    Useful for verifying if a drug is FDA-approved and when.
    """
    limit = max(1, min(100, limit))
    page = max(1, page)

    from czechmedmcp.openfda import search_drug_approvals

    skip = compute_skip(page, limit)
    return await search_drug_approvals(
        drug=drug,
        application_number=application_number,
        approval_year=approval_year,
        limit=limit,
        skip=skip,
        api_key=api_key,
    )


@arcade_app.tool
async def openfda_approval_getter(
    application_number: Annotated[
        str,
        "NDA or BLA application number",
    ],
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Get detailed FDA drug approval information for a specific application.

    Returns comprehensive approval details including:
    - Full product list with dosage forms and strengths
    - Complete submission history
    - Marketing status timeline
    - Therapeutic equivalence codes
    - Pharmacologic class information
    """
    from czechmedmcp.openfda import get_drug_approval

    return await get_drug_approval(
        application_number, api_key=api_key
    )


@arcade_app.tool
async def openfda_recall_searcher(
    drug: Annotated[
        str | None,
        "Drug name to search for recalls",
    ] = None,
    recall_class: Annotated[
        str | None,
        "Recall classification (1=most serious, 2=moderate, 3=least serious)",
    ] = None,
    status: Annotated[
        str | None,
        "Recall status (ongoing, completed, terminated)",
    ] = None,
    reason: Annotated[
        str | None,
        "Search text in recall reason",
    ] = None,
    since_date: Annotated[
        str | None,
        "Show recalls after this date (YYYYMMDD format)",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of results",
    ] = 25,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Search FDA drug recall records from the Enforcement database.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to plan your research strategy!

    Returns recall information including:
    - Classification (Class I, II, or III)
    - Recall reason and description
    - Product identification
    - Distribution information
    - Recalling firm details
    - Current status

    Class I = most serious (death/serious harm)
    Class II = moderate (temporary/reversible harm)
    Class III = least serious (unlikely to cause harm)
    """
    limit = max(1, min(100, limit))
    page = max(1, page)

    from czechmedmcp.openfda import search_drug_recalls

    skip = compute_skip(page, limit)
    return await search_drug_recalls(
        drug=drug,
        recall_class=recall_class,
        status=status,
        reason=reason,
        since_date=since_date,
        limit=limit,
        skip=skip,
        api_key=api_key,
    )


@arcade_app.tool
async def openfda_recall_getter(
    recall_number: Annotated[
        str,
        "FDA recall number",
    ],
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Get detailed FDA drug recall information for a specific recall.

    Returns complete recall details including:
    - Full product description and code information
    - Complete reason for recall
    - Distribution pattern and locations
    - Quantity of product recalled
    - Firm information and actions taken
    - Timeline of recall events
    """
    from czechmedmcp.openfda import get_drug_recall

    return await get_drug_recall(recall_number, api_key=api_key)


@arcade_app.tool
async def openfda_shortage_searcher(
    drug: Annotated[
        str | None,
        "Drug name (generic or brand) to search",
    ] = None,
    status: Annotated[
        str | None,
        "Shortage status (current or resolved)",
    ] = None,
    therapeutic_category: Annotated[
        str | None,
        "Therapeutic category (e.g., Oncology, Anti-infective)",
    ] = None,
    limit: Annotated[
        int,
        "Maximum number of results",
    ] = 25,
    page: Annotated[
        int,
        "Page number (1-based)",
    ] = 1,
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Search FDA drug shortage records.

    \u26a0\ufe0f PREREQUISITE: Use the 'think' tool FIRST to plan your research strategy!

    Returns shortage information including:
    - Current shortage status
    - Shortage start and resolution dates
    - Reason for shortage
    - Therapeutic category
    - Manufacturer information
    - Estimated resolution timeline

    Note: Shortage data is cached and updated periodically.
    Check FDA.gov for most current information.
    """
    limit = max(1, min(100, limit))
    page = max(1, page)

    from czechmedmcp.openfda import search_drug_shortages

    skip = compute_skip(page, limit)
    return await search_drug_shortages(
        drug=drug,
        status=status,
        therapeutic_category=therapeutic_category,
        limit=limit,
        skip=skip,
        api_key=api_key,
    )


@arcade_app.tool
async def openfda_shortage_getter(
    drug: Annotated[
        str,
        "Drug name (generic or brand)",
    ],
    api_key: Annotated[
        str | None,
        "Optional OpenFDA API key (overrides OPENFDA_API_KEY env var)",
    ] = None,
) -> str:
    """Get detailed FDA drug shortage information for a specific drug.

    Returns comprehensive shortage details including:
    - Complete timeline of shortage
    - Detailed reason for shortage
    - All affected manufacturers
    - Alternative products if available
    - Resolution status and estimates
    - Additional notes and recommendations

    Data is updated periodically from FDA shortage database.
    """
    from czechmedmcp.openfda import get_drug_shortage

    return await get_drug_shortage(drug, api_key=api_key)
