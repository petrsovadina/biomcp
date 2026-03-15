"""SUKL drug reimbursement lookup.

Fetches reimbursement data from SUKL opendata API.
"""

import json
import logging

import httpx

from czechmedmcp.constants import (
    CACHE_TTL_DAY,
    CZECH_HTTP_TIMEOUT,
    SUKL_REIMBURSEMENT_URL,
)
from czechmedmcp.czech.response import format_czech_response
from czechmedmcp.czech.sukl.client import (
    fetch_drug_detail as _fetch_drug_detail,
)
from czechmedmcp.czech.sukl.models import Reimbursement
from czechmedmcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)

logger = logging.getLogger(__name__)


async def _get_reimbursement(sukl_code: str) -> str:
    """Get reimbursement details for a drug.

    Args:
        sukl_code: 7-digit SUKL drug identifier.

    Returns:
        JSON string with dual output (content + structuredContent).
    """
    # Get drug name from detail
    detail = await _fetch_drug_detail(sukl_code)
    name = detail.get("nazev", sukl_code) if detail else sukl_code

    # Check cache
    url = f"{SUKL_REIMBURSEMENT_URL}/{sukl_code}"
    cache_key = generate_cache_key("GET", url, {})
    cached = get_cached_response(cache_key)

    if cached:
        data = json.loads(cached)
    else:
        try:
            async with httpx.AsyncClient(
                timeout=CZECH_HTTP_TIMEOUT,
            ) as client:
                resp = await client.get(url)
                if resp.status_code == 404:
                    return format_czech_response(
                        data={
                            "sukl_code": sukl_code,
                            "name": name,
                            "error": "Reimbursement data not found",
                        },
                        tool_name="get_reimbursement",
                    )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            logger.warning(
                "Reimbursement fetch failed for %s: %s",
                sukl_code,
                e,
            )
            return format_czech_response(
                data={
                    "sukl_code": sukl_code,
                    "name": name,
                    "error": f"API error: {e}",
                },
                tool_name="get_reimbursement",
            )

        cache_response(cache_key, json.dumps(data), CACHE_TTL_DAY)

    model = Reimbursement(
        sukl_code=sukl_code,
        name=name,
        manufacturer_price=data.get("cenaVyrobce"),
        max_retail_price=data.get("maxMaloobchodniCena"),
        reimbursement_amount=data.get("uhrada"),
        patient_copay=data.get("doplatek"),
        reimbursement_group=data.get("uhradovaSkupina"),
        conditions=data.get("podminky"),
        valid_from=data.get("platnostOd"),
        valid_to=data.get("platnostDo"),
    )

    md = _format_markdown(model)
    return format_czech_response(
        data=model.model_dump(),
        tool_name="get_reimbursement",
        markdown_template=md,
    )


def _format_markdown(r: Reimbursement) -> str:
    """Format Reimbursement as Czech Markdown."""
    lines = [
        f"## Úhrada: {r.name}",
        "",
        f"**SÚKL kód**: {r.sukl_code}",
    ]
    if r.manufacturer_price is not None:
        lines.append(
            f"**Cena výrobce**: {r.manufacturer_price:.2f} CZK"
        )
    if r.max_retail_price is not None:
        lines.append(
            f"**Max. maloobchodní cena**: "
            f"{r.max_retail_price:.2f} CZK"
        )
    if r.reimbursement_amount is not None:
        lines.append(
            f"**Úhrada pojišťovnou**: "
            f"{r.reimbursement_amount:.2f} CZK"
        )
    if r.patient_copay is not None:
        lines.append(
            f"**Doplatek pacienta**: "
            f"{r.patient_copay:.2f} CZK"
        )
    if r.reimbursement_group:
        lines.append(
            f"**Úhradová skupina**: {r.reimbursement_group}"
        )
    if r.conditions:
        lines.append(f"**Podmínky**: {r.conditions}")
    return "\n".join(lines)
