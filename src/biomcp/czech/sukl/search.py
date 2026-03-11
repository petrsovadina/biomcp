"""SUKL drug search implementation.

Uses an in-memory DrugIndex (lazy-loaded, refreshed daily)
for fast sub-second search instead of fetching all 68K drug
details on every query.
"""

import json
import logging

import httpx

from biomcp.constants import CACHE_TTL_DAY, compute_skip
from biomcp.czech.sukl.client import (
    SUKL_DLP_V1,
    SUKL_HTTP_TIMEOUT,
)
from biomcp.czech.sukl.drug_index import (
    get_drug_index,
    search_index,
)
from biomcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)

logger = logging.getLogger(__name__)

_DRUG_LIST_CACHE_TTL = CACHE_TTL_DAY


def _entry_to_summary(entry) -> dict:
    """Convert DrugIndexEntry to DrugSummary dict."""
    return {
        "sukl_code": entry.sukl_code,
        "name": entry.name,
        "strength": entry.strength,
        "atc_code": entry.atc_code,
        "pharmaceutical_form": entry.form,
    }


async def _sukl_drug_search(
    query: str,
    page: int = 1,
    page_size: int = 10,
) -> str:
    """Search Czech drug registry by name, substance, or ATC code.

    Uses an in-memory drug index for fast search. The index is
    built on first query and refreshed daily (CACHE_TTL_DAY).

    Args:
        query: Drug name, active substance, or ATC code
        page: Page number (1-based)
        page_size: Results per page (1-100)

    Returns:
        JSON string with search results
    """
    try:
        index = await get_drug_index()
    except Exception as e:
        logger.error("Failed to build drug index: %s", e)
        return json.dumps(
            {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "results": [],
                "error": f"SUKL API unavailable: {e}",
            },
            ensure_ascii=False,
        )

    results, total = search_index(
        index, query, page, page_size
    )

    return json.dumps(
        {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": [
                _entry_to_summary(e) for e in results
            ],
        },
        ensure_ascii=False,
    )


# -------------------------------------------------------
# Pharmacy search
# -------------------------------------------------------

_PHARMACY_URL = f"{SUKL_DLP_V1}/lecebna-zarizeni"


async def _find_pharmacies(
    city: str | None = None,
    postal_code: str | None = None,
    nonstop_only: bool = False,
    page: int = 1,
    page_size: int = 10,
) -> str:
    """Search pharmacies by city/postal code.

    At least ``city`` or ``postal_code`` required.

    Returns:
        Dual output JSON string.
    """
    from biomcp.czech.response import format_czech_response

    if not city and not postal_code:
        return json.dumps(
            {
                "error": (
                    "At least city or postal_code "
                    "is required"
                ),
            },
            ensure_ascii=False,
        )

    pharmacies = await _fetch_pharmacies(
        city, postal_code
    )

    if nonstop_only:
        pharmacies = [
            p for p in pharmacies if p.get("nonstop")
        ]

    total = len(pharmacies)
    start = compute_skip(page, page_size)
    end = start + page_size
    page_results = pharmacies[start:end]

    data = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": page_results,
    }

    md = _format_pharmacy_markdown(data)
    return format_czech_response(
        data=data,
        tool_name="find_pharmacies",
        markdown_template=md,
    )


async def _fetch_pharmacies(
    city: str | None,
    postal_code: str | None,
) -> list[dict]:
    """Fetch pharmacy list from SUKL API."""
    params: dict[str, str] = {}
    if city:
        params["mesto"] = city
    if postal_code:
        params["psc"] = postal_code

    cache_key = generate_cache_key(
        "GET", _PHARMACY_URL, params
    )
    cached = get_cached_response(cache_key)
    if cached:
        return json.loads(cached)

    try:
        async with httpx.AsyncClient(
            timeout=SUKL_HTTP_TIMEOUT
        ) as client:
            resp = await client.get(
                _PHARMACY_URL, params=params
            )
            if resp.status_code == 504:
                logger.warning(
                    "SUKL pharmacy API returned 504"
                )
                return []
            if not resp.is_success:
                return []
            data = resp.json()
    except httpx.HTTPError:
        logger.warning("Failed to fetch pharmacies")
        return []

    result = _parse_pharmacies(
        data if isinstance(data, list) else []
    )
    cache_response(
        cache_key,
        json.dumps(result, ensure_ascii=False),
        _DRUG_LIST_CACHE_TTL,
    )
    return result


def _parse_pharmacies(raw_list: list) -> list[dict]:
    """Parse SUKL pharmacy API response."""
    pharmacies = []
    for item in raw_list:
        pharmacies.append({
            "pharmacy_id": str(
                item.get("id", "")
            ),
            "name": item.get("nazev", ""),
            "city": item.get("mesto", ""),
            "postal_code": str(
                item.get("psc", "")
            ),
            "address": item.get("ulice", ""),
            "phone": item.get("telefon"),
            "nonstop": bool(
                item.get("nepretrzity")
            ),
        })
    return pharmacies


def _format_pharmacy_markdown(data: dict) -> str:
    """Format pharmacy search as Markdown."""
    lines = [
        f"## Lékárny ({data['total']} nalezeno)",
        "",
    ]
    results = data.get("results", [])
    if results:
        for i, p in enumerate(results, 1):
            name = p.get("name", "?")
            city = p.get("city", "")
            addr = p.get("address", "")
            nonstop = " [24/7]" if p.get("nonstop") else ""
            lines.append(
                f"{i}. **{name}**{nonstop} — "
                f"{addr}, {city}"
            )
    else:
        lines.append("*Žádné lékárny nalezeny.*")

    return "\n".join(lines)
