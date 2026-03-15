"""SUKL drug availability check.

Uses SUKL DLP API v1 to check distribution status.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from czechmedmcp.czech.sukl.models import BatchAvailabilityResult

import httpx

from czechmedmcp.constants import CACHE_TTL_HOUR
from czechmedmcp.czech.sukl.client import (
    SUKL_DLP_V1,
    SUKL_HTTP_TIMEOUT,
)
from czechmedmcp.czech.sukl.client import (
    fetch_drug_detail as _fetch_drug_detail,
)
from czechmedmcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)

logger = logging.getLogger(__name__)

_CACHE_TTL = CACHE_TTL_HOUR


async def _check_distribution(sukl_code: str) -> str:
    """Check if drug is in active distribution.

    Checks VPOIS endpoint for holder info, which indicates
    the drug is actively distributed.

    Returns: 'available', 'limited', or 'unavailable'
    """
    url = f"{SUKL_DLP_V1}/vpois/{sukl_code}"
    cache_key = generate_cache_key("GET", url, {})

    cached = get_cached_response(cache_key)
    if cached:
        data = json.loads(cached)
        if data.get("_status"):
            return data["_status"]

    try:
        async with httpx.AsyncClient(timeout=SUKL_HTTP_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                status = "unavailable"
            elif resp.is_success:
                status = "available"
            else:
                status = "unavailable"
    except httpx.HTTPError:
        status = "unavailable"

    cache_response(
        cache_key,
        json.dumps({"_status": status}),
        _CACHE_TTL,
    )
    return status


async def _sukl_availability_check(sukl_code: str) -> str:
    """Check current drug market availability.

    Args:
        sukl_code: SUKL drug identifier

    Returns:
        JSON with sukl_code, name, status, last_checked, note,
        source
    """
    detail = await _fetch_drug_detail(sukl_code)
    if not detail:
        return json.dumps(
            {"error": f"Drug not found: {sukl_code}"},
            ensure_ascii=False,
        )

    status = await _check_distribution(sukl_code)
    now = datetime.now(timezone.utc).isoformat()

    return json.dumps(
        {
            "sukl_code": detail.get("kodSUKL", sukl_code),
            "name": detail.get("nazev", ""),
            "status": status,
            "last_checked": now,
            "note": None,
            "source": "SUKL",
        },
        ensure_ascii=False,
    )


async def _batch_availability(sukl_codes: list[str]) -> str:
    """Check availability for multiple drugs in parallel.

    Args:
        sukl_codes: List of 7-digit SUKL codes (1-50).

    Returns:
        JSON string with dual output via format_czech_response().
    """
    from czechmedmcp.czech.response import format_czech_response
    from czechmedmcp.czech.sukl.models import (
        BatchAvailabilityItem,
        BatchAvailabilityResult,
    )

    now = datetime.now(timezone.utc).isoformat()

    async def _check_one(code: str) -> BatchAvailabilityItem:
        try:
            detail = await _fetch_drug_detail(code)
            name = (
                detail.get("nazev") if detail else None
            )
            status = await _check_distribution(code)
            return BatchAvailabilityItem(
                sukl_code=code,
                name=name,
                status=status,
            )
        except Exception as e:
            return BatchAvailabilityItem(
                sukl_code=code,
                status="unknown",
                error=str(e),
            )

    results = await asyncio.gather(
        *[_check_one(code) for code in sukl_codes],
        return_exceptions=True,
    )

    items: list[BatchAvailabilityItem] = []
    for i, r in enumerate(results):
        if isinstance(r, BaseException):
            items.append(
                BatchAvailabilityItem(
                    sukl_code=sukl_codes[i],
                    status="unknown",
                    error=str(r),
                )
            )
        else:
            items.append(r)

    available = sum(
        1 for it in items if it.status == "available"
    )
    shortage = sum(
        1 for it in items if it.status == "shortage"
    )
    errors = sum(
        1 for it in items if it.error is not None
    )

    batch = BatchAvailabilityResult(
        total_checked=len(items),
        available_count=available,
        shortage_count=shortage,
        error_count=errors,
        items=items,
        checked_at=now,
    )

    md = _format_batch_markdown(batch)
    return format_czech_response(
        data=batch.model_dump(),
        tool_name="batch_check_availability",
        markdown_template=md,
    )


def _format_batch_markdown(b: BatchAvailabilityResult) -> str:
    """Format batch result as Czech Markdown."""
    lines = [
        "## Hromadná kontrola dostupnosti",
        "",
        f"**Zkontrolováno**: {b.total_checked} léků",
        f"**Dostupné**: {b.available_count}",
        f"**Výpadek**: {b.shortage_count}",
        f"**Chyby**: {b.error_count}",
        "",
        "| SÚKL kód | Název | Status |",
        "|----------|-------|--------|",
    ]
    for it in b.items:
        name = it.name or "—"
        status = it.error or it.status
        lines.append(f"| {it.sukl_code} | {name} | {status} |")
    return "\n".join(lines)
