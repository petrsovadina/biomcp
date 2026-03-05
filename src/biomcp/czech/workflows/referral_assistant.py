"""Referral assistant workflow.

Maps diagnosis → specialty → find providers.
"""

import json
import logging

from biomcp.czech.mkn.search import _mkn_get
from biomcp.czech.nrpzs.search import _nrpzs_search
from biomcp.czech.response import format_czech_response

logger = logging.getLogger(__name__)

# MKN-10 chapter letter → specialty name
_CHAPTER_SPECIALTY: dict[str, str] = {
    "A": "infektologie",
    "B": "infektologie",
    "C": "onkologie",
    "D": "hematologie",
    "E": "endokrinologie",
    "F": "psychiatrie",
    "G": "neurologie",
    "H": "oftalmologie",
    "I": "kardiologie",
    "J": "pneumologie",
    "K": "gastroenterologie",
    "L": "dermatologie",
    "M": "revmatologie",
    "N": "urologie",
    "O": "gynekologie",
    "P": "neonatologie",
    "Q": "genetika",
    "R": "vnitřní lékařství",
    "S": "chirurgie",
    "T": "chirurgie",
}


async def _referral_assistant(
    diagnosis_code: str,
    city: str,
    max_providers: int = 10,
) -> str:
    """Suggest providers for a diagnosis in a city.

    Args:
        diagnosis_code: MKN-10 code (e.g. I25.1).
        city: Patient city for provider search.
        max_providers: Max providers to return.

    Returns:
        Dual output JSON string.
    """
    diag = await _get_diagnosis_info(diagnosis_code)
    specialty = _map_specialty(diagnosis_code)
    providers = await _search_providers(
        city, specialty, max_providers
    )

    data = {
        "diagnosis_code": diagnosis_code,
        "diagnosis_name": diag.get("name", ""),
        "recommended_specialty": specialty,
        "city": city,
        "providers": providers,
    }

    md = _format_markdown(data)
    return format_czech_response(
        data=data,
        tool_name="referral_assistant",
        markdown_template=md,
    )


async def _get_diagnosis_info(
    code: str,
) -> dict:
    """Fetch diagnosis info from MKN-10."""
    try:
        raw = await _mkn_get(code)
        data = json.loads(raw)
        if isinstance(data, dict) and "error" not in data:
            return data
    except Exception:
        logger.warning(
            "Failed to get diagnosis info for %s", code
        )
    return {"code": code, "name": ""}


def _map_specialty(code: str) -> str:
    """Map MKN-10 code to recommended specialty."""
    if not code:
        return "vnitřní lékařství"
    letter = code[0].upper()
    return _CHAPTER_SPECIALTY.get(
        letter, "vnitřní lékařství"
    )


async def _search_providers(
    city: str,
    specialty: str,
    max_providers: int,
) -> list[dict]:
    """Search NRPZS for matching providers."""
    try:
        raw = await _nrpzs_search(
            query=None,
            city=city,
            specialty=specialty,
            page=1,
            page_size=max_providers,
        )
        data = json.loads(raw)
        return data.get("results", [])
    except Exception:
        logger.warning(
            "Failed to search providers for %s/%s",
            city,
            specialty,
        )
        return []


def _format_markdown(data: dict) -> str:
    """Format referral result as Markdown."""
    lines = [
        "## Asistence odeslání",
        "",
        f"**Diagnóza**: {data['diagnosis_code']}"
        f" — {data.get('diagnosis_name', '')}",
        f"**Doporučená odbornost**: "
        f"{data['recommended_specialty']}",
        f"**Město**: {data['city']}",
        "",
    ]

    providers = data.get("providers", [])
    if providers:
        lines.append("### Poskytovatelé\n")
        for i, p in enumerate(providers, 1):
            name = p.get("name", "?")
            city = p.get("city", "")
            lines.append(f"{i}. **{name}** ({city})")
    else:
        lines.append(
            "*Žádní poskytovatelé nalezeni.*"
        )

    return "\n".join(lines)
