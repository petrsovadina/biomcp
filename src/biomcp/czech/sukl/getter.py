"""SUKL drug detail, SmPC, and PIL retrieval.

Uses SUKL DLP API v1 for drug details, composition, and
document metadata.
"""

import json
import logging

import httpx

from biomcp.constants import DEFAULT_CACHE_TIMEOUT
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

_CACHE_TTL = DEFAULT_CACHE_TIMEOUT


async def _fetch_composition(sukl_code: str) -> list[dict]:
    """Fetch drug composition (active substances)."""
    url = f"{SUKL_DLP_V1}/slozeni/{sukl_code}"
    cache_key = generate_cache_key("GET", url, {})

    cached = get_cached_response(cache_key)
    if cached:
        return json.loads(cached)

    try:
        async with httpx.AsyncClient(timeout=SUKL_HTTP_TIMEOUT) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        logger.warning("Failed to fetch composition for %s", sukl_code)
        return []

    cache_response(cache_key, json.dumps(data), _CACHE_TTL)
    return data if isinstance(data, list) else []


async def _fetch_doc_metadata(
    sukl_code: str, typ: str | None = None
) -> list[dict]:
    """Fetch document metadata for a drug."""
    url = f"{SUKL_DLP_V1}/dokumenty-metadata/{sukl_code}"
    params = {"typ": typ} if typ else {}
    cache_key = generate_cache_key("GET", url, params)

    cached = get_cached_response(cache_key)
    if cached:
        return json.loads(cached)

    try:
        async with httpx.AsyncClient(timeout=SUKL_HTTP_TIMEOUT) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        logger.warning("Failed to fetch doc metadata for %s", sukl_code)
        return []

    result = data if isinstance(data, list) else []
    cache_response(cache_key, json.dumps(result), _CACHE_TTL)
    return result


def _build_doc_url(sukl_code: str, doc_type: str) -> str:
    """Build document download URL."""
    return f"{SUKL_DLP_V1}/dokumenty/{sukl_code}/{doc_type}"


def _composition_to_substances(
    composition: list[dict],
) -> list[dict]:
    """Convert API composition to active substances list."""
    substances = []
    for item in composition:
        name = item.get("nazevLatky", "")
        amount = item.get("mnozstvi", "")
        unit = item.get("jednotka", "")
        strength = f"{amount} {unit}".strip() if amount else None
        substances.append({"name": name, "strength": strength})
    return substances


async def _sukl_drug_details(sukl_code: str) -> str:
    """Get full drug details by SUKL code.

    Returns JSON with full Drug entity fields.
    """
    detail = await _fetch_drug_detail(sukl_code)
    if not detail:
        return json.dumps(
            {"error": f"Drug not found: {sukl_code}"},
            ensure_ascii=False,
        )

    composition = await _fetch_composition(sukl_code)
    doc_meta = await _fetch_doc_metadata(sukl_code)

    spc_docs = [d for d in doc_meta if d.get("typ") == "spc"]
    pil_docs = [d for d in doc_meta if d.get("typ") == "pil"]

    spc_url = _build_doc_url(sukl_code, "spc") if spc_docs else None
    pil_url = _build_doc_url(sukl_code, "pil") if pil_docs else None

    result = {
        "sukl_code": detail.get("kodSukl", sukl_code),
        "name": detail.get("nazev", ""),
        "active_substances": _composition_to_substances(composition),
        "pharmaceutical_form": detail.get("nazevFormy"),
        "atc_code": detail.get("kodAtc"),
        "registration_number": detail.get("registracniCislo"),
        "mah": detail.get("nazevDrzitele"),
        "registration_valid_to": detail.get("platnostRegistrace"),
        "spc_url": spc_url,
        "pil_url": pil_url,
        "source": "SUKL",
    }

    return json.dumps(result, ensure_ascii=False)


async def _sukl_document_getter(
    sukl_code: str, doc_type: str
) -> str:
    """Get a SUKL document (SmPC or PIL) by type.

    Args:
        sukl_code: SUKL drug code.
        doc_type: Document type — ``"spc"`` or ``"pil"``.

    Returns JSON with sukl_code, name, text, url, source.
    """
    label = "SmPC" if doc_type == "spc" else "PIL"
    text_key = f"{doc_type}_text"
    url_key = f"{doc_type}_url"

    detail = await _fetch_drug_detail(sukl_code)
    if not detail:
        return json.dumps(
            {"error": f"Drug not found: {sukl_code}"},
            ensure_ascii=False,
        )

    doc_meta = await _fetch_doc_metadata(sukl_code, typ=doc_type)
    name = detail.get("nazev", "")

    if not doc_meta:
        return json.dumps(
            {
                "error": f"{label} not available for {sukl_code}",
                "sukl_code": sukl_code,
                "name": name,
                text_key: None,
                url_key: None,
                "source": "SUKL",
            },
            ensure_ascii=False,
        )

    doc_url = _build_doc_url(sukl_code, doc_type)
    return json.dumps(
        {
            "sukl_code": sukl_code,
            "name": name,
            text_key: f"{label} document available at: {doc_url}",
            url_key: doc_url,
            "source": "SUKL",
        },
        ensure_ascii=False,
    )


async def _sukl_spc_getter(sukl_code: str) -> str:
    """Get Summary of Product Characteristics (SmPC)."""
    return await _sukl_document_getter(sukl_code, "spc")


async def _sukl_pil_getter(sukl_code: str) -> str:
    """Get Patient Information Leaflet (PIL)."""
    return await _sukl_document_getter(sukl_code, "pil")
