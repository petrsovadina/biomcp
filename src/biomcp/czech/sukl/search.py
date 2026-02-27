"""SUKL drug search implementation.

Uses SUKL DLP API v1 (prehledy.sukl.cz) with diskcache for
response caching and offline fallback.
"""

import asyncio
import json
import logging

import httpx

from biomcp.constants import CACHE_TTL_DAY, compute_skip
from biomcp.czech.diacritics import normalize_query
from biomcp.czech.sukl.client import (
    SUKL_DLP_V1,
    SUKL_HTTP_TIMEOUT,
)
from biomcp.czech.sukl.client import (
    fetch_drug_detail as _fetch_drug_detail,
)
from biomcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)

logger = logging.getLogger(__name__)

_DRUG_LIST_CACHE_TTL = CACHE_TTL_DAY


async def _fetch_drug_list(
    typ_seznamu: str = "dlpo",
) -> list[str]:
    """Fetch list of SUKL codes from DLP API."""
    cache_key = generate_cache_key(
        "GET",
        f"{SUKL_DLP_V1}/lecive-pripravky",
        {"typSeznamu": typ_seznamu, "uvedeneCeny": "false"},
    )
    cached = get_cached_response(cache_key)
    if cached:
        return json.loads(cached)

    async with httpx.AsyncClient(
        timeout=SUKL_HTTP_TIMEOUT
    ) as client:
        resp = await client.get(
            f"{SUKL_DLP_V1}/lecive-pripravky",
            params={
                "typSeznamu": typ_seznamu,
                "uvedeneCeny": "false",
            },
        )
        resp.raise_for_status()
        codes = resp.json()

    cache_response(cache_key, json.dumps(codes), _DRUG_LIST_CACHE_TTL)
    return codes


def _matches_query(detail: dict, normalized_q: str) -> bool:
    """Check if a drug detail matches the search query."""
    if not detail:
        return False

    name = normalize_query(detail.get("nazev", ""))
    supplement = normalize_query(detail.get("doplnek", ""))
    atc = (detail.get("ATCkod") or "").lower()
    holder = (detail.get("drzitelKod") or "").lower()

    return (
        normalized_q in name
        or normalized_q in supplement
        or normalized_q == atc
        or normalized_q in holder
    )


def _detail_to_summary(detail: dict) -> dict:
    """Convert API drug detail to DrugSummary dict."""
    return {
        "sukl_code": detail.get("kodSUKL", ""),
        "name": detail.get("nazev", ""),
        "strength": detail.get("sila"),
        "atc_code": detail.get("ATCkod"),
        "pharmaceutical_form": detail.get("lekovaFormaKod"),
    }


async def _sukl_drug_search(
    query: str,
    page: int = 1,
    page_size: int = 10,
) -> str:
    """Search Czech drug registry by name, substance, or ATC code.

    Args:
        query: Drug name, active substance, or ATC code
        page: Page number (1-based)
        page_size: Results per page (1-100)

    Returns:
        JSON string with search results
    """
    try:
        codes = await _fetch_drug_list()
    except Exception as e:
        logger.error("Failed to fetch drug list: %s", e)
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

    normalized_q = normalize_query(query)

    # Fetch details concurrently with bounded parallelism
    sem = asyncio.Semaphore(10)

    async def _fetch_one(code: str):
        async with sem:
            return await _fetch_drug_detail(code)

    details = await asyncio.gather(
        *(_fetch_one(c) for c in codes)
    )
    matches = [
        _detail_to_summary(d)
        for d in details
        if d and _matches_query(d, normalized_q)
    ]

    total = len(matches)
    start = compute_skip(page, page_size)
    end = start + page_size
    page_results = matches[start:end]

    return json.dumps(
        {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": page_results,
        },
        ensure_ascii=False,
    )
