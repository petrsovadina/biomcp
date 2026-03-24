"""Diagnosis assistant workflow.

Orchestrates hybrid symptom→MKN-10 search + PubMed evidence
lookup.  Uses the symptom mapping dictionary for better
matching of lay symptom descriptions to clinical codes.
"""

import asyncio
import json
import logging

from czechmedmcp.czech.diagnosis_embed.searcher import (
    search_diagnoses,
)
from czechmedmcp.czech.mkn.models import (
    DiagnosisAssistantResult,
)
from czechmedmcp.czech.response import format_czech_response

logger = logging.getLogger(__name__)


async def _diagnosis_assistant(
    symptoms: str, max_candidates: int = 5
) -> str:
    """Suggest MKN-10 codes for symptoms with evidence.

    Args:
        symptoms: Symptom description (CZ or EN).
        max_candidates: Max diagnosis candidates (1-10).

    Returns:
        JSON string with dual output.
    """
    try:
        candidates = await _search_candidates(
            symptoms, max_candidates
        )
    except ValueError as exc:
        # User passed MKN code or empty input
        model = DiagnosisAssistantResult(
            query=symptoms,
            candidates=[],
            evidence=[],
        )
        md = _format_error(symptoms, str(exc))
        return format_czech_response(
            data=model.model_dump(),
            tool_name="diagnosis_assistant",
            markdown_template=md,
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
    """Search for matching diagnoses via hybrid searcher."""
    results = await search_diagnoses(
        symptoms, max_candidates
    )

    return [
        {
            "code": it.get("code", ""),
            "name": it.get("name_cs", ""),
            "score": it.get("score"),
            "match_type": it.get("match_type", ""),
        }
        for it in results[:max_candidates]
    ]


async def _fetch_evidence(
    candidates: list[dict],
) -> list[dict]:
    """Fetch PubMed evidence for top candidates."""
    evidence: list[dict] = []
    if not candidates:
        return evidence

    try:
        from czechmedmcp.articles.search import (
            _article_searcher,
        )
    except ImportError:
        logger.warning(
            "czechmedmcp.articles not available"
            " for evidence"
        )
        return evidence

    tasks = [
        _article_searcher(
            call_benefit=(
                f"Find evidence for diagnosis"
                f" {c['code']}"
            ),
            keywords=[c["name"], "diagnosis"],
        )
        for c in candidates[:3]
        if c.get("name")
    ]

    if not tasks:
        return evidence

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

    if not r.candidates:
        lines.append(
            "_Nebyly nalezeny žádné odpovídající "
            "diagnózy. Zkuste upřesnit popis symptomů._"
        )
    else:
        for i, c in enumerate(r.candidates, 1):
            match_info = ""
            mt = c.get("match_type", "")
            if mt == "exact_map":
                match_info = " ✓"
            elif mt == "fuzzy_map":
                match_info = " ~"
            lines.append(
                f"{i}. **{c.get('code', '?')}** — "
                f"{c.get('name', '?')}{match_info}"
            )

    if r.evidence:
        lines.extend(
            ["", "### Podpůrná literatura", ""]
        )
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


def _format_error(query: str, message: str) -> str:
    """Format an error/guidance message as Markdown."""
    return (
        f'## Diagnostický asistent: "{query}"\n\n'
        f"⚠️ {message}\n\n---\n"
        "*Tento nástroj slouží pouze jako pomůcka. "
        "Konečná diagnóza je vždy na lékaři.*"
    )
