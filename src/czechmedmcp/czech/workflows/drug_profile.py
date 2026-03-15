"""Drug profile workflow.

Orchestrates SUKL detail + availability + reimbursement
+ PubMed evidence in one call.
"""

import asyncio
import json
import logging

from czechmedmcp.czech.response import format_czech_response
from czechmedmcp.czech.sukl.models import (
    DrugProfile,
    DrugProfileSection,
)

logger = logging.getLogger(__name__)


async def _drug_profile(query: str) -> str:
    """Complete drug profile in one call.

    Args:
        query: Drug name, substance, or SUKL code.

    Returns:
        Dual output JSON string.
    """
    sukl_code = await _resolve_sukl_code(query)
    if not sukl_code:
        return json.dumps(
            {"error": f"Drug not found: {query}"},
            ensure_ascii=False,
        )

    sections = await _fetch_all_sections(sukl_code)

    model = DrugProfile(
        query=query,
        sukl_code=sukl_code,
        sections=sections,
    )

    md = _format_markdown(model)
    return format_czech_response(
        data=model.model_dump(),
        tool_name="drug_profile",
        markdown_template=md,
    )


async def _resolve_sukl_code(query: str) -> str | None:
    """Search SUKL to resolve query to sukl_code."""
    try:
        from czechmedmcp.czech.sukl.search import (
            _sukl_drug_search,
        )

        raw = await _sukl_drug_search(
            query, page=1, page_size=1
        )
        data = json.loads(raw)
        results = data.get("results", [])
        if results:
            return results[0].get("sukl_code")
    except Exception:
        logger.warning(
            "Failed to resolve SUKL code for %s", query
        )
    return None


async def _fetch_all_sections(
    sukl_code: str,
) -> list[DrugProfileSection]:
    """Fetch all profile sections in parallel."""
    results = await asyncio.gather(
        _fetch_detail(sukl_code),
        _fetch_availability(sukl_code),
        _fetch_reimbursement(sukl_code),
        _fetch_evidence(sukl_code),
        return_exceptions=True,
    )

    names = [
        "registration",
        "availability",
        "reimbursement",
        "evidence",
    ]
    sections: list[DrugProfileSection] = []
    for name, result in zip(names, results, strict=False):
        if isinstance(result, BaseException):
            sections.append(DrugProfileSection(
                section=name,
                status="error",
                error=str(result),
            ))
        elif result is None:
            sections.append(DrugProfileSection(
                section=name,
                status="error",
                error="No data available",
            ))
        else:
            sections.append(DrugProfileSection(
                section=name,
                status="ok",
                data=result,
            ))

    return sections


async def _fetch_detail(sukl_code: str) -> dict | None:
    """Fetch drug detail section."""
    from czechmedmcp.czech.sukl.getter import (
        _sukl_drug_details,
    )

    raw = await _sukl_drug_details(sukl_code)
    data = json.loads(raw)
    if "error" in data:
        return None
    return data


async def _fetch_availability(
    sukl_code: str,
) -> dict | None:
    """Fetch availability section."""
    from czechmedmcp.czech.sukl.availability import (
        _sukl_availability_check,
    )

    raw = await _sukl_availability_check(sukl_code)
    data = json.loads(raw)
    if "error" in data:
        return None
    return data


async def _fetch_reimbursement(
    sukl_code: str,
) -> dict | None:
    """Fetch reimbursement section."""
    from czechmedmcp.czech.sukl.reimbursement import (
        _get_reimbursement,
    )

    raw = await _get_reimbursement(sukl_code)
    data = json.loads(raw)
    sc = data.get("structuredContent", data)
    if "error" in sc:
        return None
    return sc


async def _fetch_evidence(
    sukl_code: str,
) -> dict | None:
    """Fetch PubMed evidence section."""
    try:
        from czechmedmcp.articles.search import (
            _article_searcher,
        )

        raw = await _article_searcher(
            call_benefit=(
                f"Find evidence for drug {sukl_code}"
            ),
            keywords=[sukl_code],
        )
        data = json.loads(raw)
        if isinstance(data, list):
            return {"articles": data[:3]}
        return data
    except ImportError:
        logger.warning("PubMed module not available")
        return None


def _format_markdown(p: DrugProfile) -> str:
    """Format drug profile as Markdown."""
    lines = [
        f"## Profil léku: {p.query}",
        f"*SUKL kód: {p.sukl_code}*",
        "",
    ]

    for s in p.sections:
        title = {
            "registration": "Registrace",
            "availability": "Dostupnost",
            "reimbursement": "Úhrada",
            "evidence": "Evidence (PubMed)",
        }.get(s.section, s.section)

        lines.append(f"### {title}")
        if s.status == "error":
            lines.append(f"*Chyba: {s.error}*")
        elif s.data:
            for k, v in s.data.items():
                if v is not None and k != "source":
                    lines.append(f"- **{k}**: {v}")
        lines.append("")

    return "\n".join(lines)
