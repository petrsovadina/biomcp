"""Diagnosis assistant workflow.

Orchestrates MKN-10 search + PubMed evidence lookup.
"""

import asyncio
import json
import logging

from czechmedmcp.czech.mkn.models import DiagnosisAssistantResult
from czechmedmcp.czech.mkn.search import _mkn_search
from czechmedmcp.czech.response import format_czech_response

logger = logging.getLogger(__name__)


async def _diagnosis_assistant(
    symptoms: str, max_candidates: int = 5
) -> str:
    """Suggest MKN-10 codes for symptoms with evidence.

    Args:
        symptoms: Symptom description in Czech.
        max_candidates: Max diagnosis candidates (1-10).

    Returns:
        JSON string with dual output.
    """
    candidates = await _search_candidates(
        symptoms, max_candidates
    )
    evidence = await _fetch_evidence(candidates)

    model = DiagnosisAssistantResult(
        query=symptoms,
        candidates=candidates,
        evidence=evidence,
    )

    md = _format_markdown(model)
    return format_czech_response(
        data=model.model_dump(),
        tool_name="diagnosis_assistant",
        markdown_template=md,
    )


async def _search_candidates(
    symptoms: str, max_candidates: int
) -> list[dict]:
    """Search MKN-10 for matching diagnoses."""
    mkn_raw = await _mkn_search(symptoms, max_candidates)
    mkn_data = json.loads(mkn_raw)

    if isinstance(mkn_data, dict):
        results = mkn_data.get("results", [])
    elif isinstance(mkn_data, list):
        results = mkn_data
    else:
        results = []

    return [
        {
            "code": it.get("code", ""),
            "name": it.get("name", it.get("name_cs", "")),
            "score": it.get("score"),
        }
        for it in results[:max_candidates]
    ]


async def _fetch_evidence(
    candidates: list[dict],
) -> list[dict]:
    """Fetch PubMed evidence for top candidates."""
    evidence: list[dict] = []
    try:
        from czechmedmcp.articles.search import _article_searcher
    except ImportError:
        logger.warning(
            "czechmedmcp.articles not available for evidence"
        )
        return evidence

    tasks = [
        _article_searcher(
            call_benefit=(
                f"Find evidence for diagnosis {c['code']}"
            ),
            keywords=[c["name"], "diagnosis"],
        )
        for c in candidates[:3]
    ]

    results_raw = await asyncio.gather(
        *tasks, return_exceptions=True
    )

    for i, raw in enumerate(results_raw):
        if isinstance(raw, BaseException):
            logger.warning(
                "PubMed failed for %s: %s",
                candidates[i]["code"],
                raw,
            )
            continue
        evidence.extend(
            _parse_articles(raw, candidates[i]["code"])
        )

    return evidence


def _parse_articles(
    raw: str, diagnosis_code: str
) -> list[dict]:
    """Parse PubMed article results."""
    try:
        articles = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(articles, list):
        return []
    return [
        {
            "pmid": a.get("pmid", ""),
            "title": a.get("title", ""),
            "diagnosis_code": diagnosis_code,
        }
        for a in articles[:2]
    ]


def _format_markdown(r: DiagnosisAssistantResult) -> str:
    """Format diagnosis assistant result as Markdown."""
    lines = [
        f'## Diagnostický asistent: "{r.query}"',
        "",
        "### Navrhované diagnózy",
        "",
    ]
    for i, c in enumerate(r.candidates, 1):
        lines.append(
            f"{i}. **{c.get('code', '?')}** — "
            f"{c.get('name', '?')}"
        )

    if r.evidence:
        lines.extend(["", "### Podpůrná literatura", ""])
        for e in r.evidence:
            lines.append(
                f"- [{e.get('title', '?')}]"
                f"(https://pubmed.ncbi.nlm.nih.gov/"
                f"{e.get('pmid', '')}/) "
                f"({e.get('diagnosis_code', '')})"
            )

    lines.extend([
        "",
        "---",
        f"*{r.disclaimer}*",
    ])
    return "\n".join(lines)
