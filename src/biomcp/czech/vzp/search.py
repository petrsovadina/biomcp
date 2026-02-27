"""VZP insurance codebook search implementation.

Downloads VZP procedure codebook (ZIP with CSV) from
media.vzpstatic.cz and provides in-memory search.

Data source: https://www.vzp.cz/poskytovatele/ciselniky
"""

import csv
import io
import json
import logging
import zipfile

import httpx

from biomcp.constants import (
    CACHE_TTL_DAY,
    DEFAULT_CACHE_TIMEOUT,
)
from biomcp.czech.diacritics import normalize_query
from biomcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)

logger = logging.getLogger(__name__)

# Current VZP codebook version (updated quarterly)
_VZP_VERSION = "01460"
_VZP_ZIP_URL = (
    "https://media.vzpstatic.cz/media/Default/"
    f"dokumenty/ciselniky/vykony_{_VZP_VERSION}.zip"
)

_CODEBOOK_CACHE_TTL = CACHE_TTL_DAY
_ENTRY_CACHE_TTL = DEFAULT_CACHE_TIMEOUT

_VZP_FIELDS = [
    "KOD", "ODB", "OME", "OMO", "NAZ", "VYS",
    "ZUM", "TVY", "CTN", "PMZ", "PMA", "PJP",
    "BOD", "KAT", "UMA", "UBO",
]

# Module-level cache
_ENTRIES: list[dict] | None = None


async def _download_codebook() -> list[dict]:
    """Download and parse VZP codebook ZIP."""
    cache_key = generate_cache_key(
        "PARSED", f"vzp:vykony:{_VZP_VERSION}", {}
    )
    cached = get_cached_response(cache_key)
    if cached:
        return json.loads(cached)

    async with httpx.AsyncClient(
        timeout=60.0,
        follow_redirects=True,
    ) as client:
        resp = await client.get(_VZP_ZIP_URL)
        resp.raise_for_status()
        content = resp.content

    with zipfile.ZipFile(io.BytesIO(content)) as zf:
        filename = zf.namelist()[0]
        raw = zf.read(filename).decode("cp852")

    reader = csv.reader(io.StringIO(raw))
    entries = []
    for row in reader:
        if len(row) >= len(_VZP_FIELDS):
            entry = dict(zip(_VZP_FIELDS, row))
            # Skip empty/header rows
            if entry["KOD"] and entry["KOD"] != "KOD":
                entries.append(entry)

    cache_response(
        cache_key,
        json.dumps(entries, ensure_ascii=False),
        _CODEBOOK_CACHE_TTL,
    )
    return entries


async def _get_entries() -> list[dict]:
    """Return cached or freshly loaded codebook entries."""
    global _ENTRIES
    if _ENTRIES is not None:
        return _ENTRIES

    _ENTRIES = await _download_codebook()
    logger.debug(
        "Loaded %d VZP codebook entries", len(_ENTRIES)
    )
    return _ENTRIES


def _entry_to_summary(
    raw: dict, codebook_type: str,
) -> dict:
    """Return a lightweight summary dict."""
    return {
        "codebook_type": codebook_type,
        "code": raw.get("KOD", "").strip(),
        "name": raw.get("NAZ", "").strip(),
    }


def _normalise_entry(
    raw: dict, codebook_type: str,
) -> dict:
    """Convert raw CSV row to canonical entry dict."""
    return {
        "codebook_type": codebook_type,
        "code": raw.get("KOD", "").strip(),
        "name": raw.get("NAZ", "").strip(),
        "description": raw.get("VYS", "").strip() or None,
        "specialty": raw.get("ODB", "").strip(),
        "location": raw.get("OME", "").strip(),
        "specialty_limits": (
            raw.get("OMO", "").strip() or None
        ),
        "point_value": raw.get("BOD", "").strip() or None,
        "price_czk": raw.get("PMA", "").strip() or None,
        "duration_minutes": (
            raw.get("TVY", "").strip() or None
        ),
        "carrier_time": (
            raw.get("CTN", "").strip() or None
        ),
        "category": raw.get("KAT", "").strip(),
        "material_supplement": raw.get("ZUM", "").strip(),
        "source": "VZP",
    }


def _matches_query(
    raw: dict, normalized_q: str,
) -> bool:
    """Return True if the entry matches the query."""
    code = raw.get("KOD", "").lower()
    name = normalize_query(raw.get("NAZ", ""))
    desc = normalize_query(raw.get("VYS", ""))
    return (
        normalized_q in code
        or normalized_q in name
        or normalized_q in desc
    )


async def _vzp_search(
    query: str,
    codebook_type: str | None = None,
    max_results: int = 10,
) -> str:
    """Search VZP insurance codebooks.

    Args:
        query: Search text (code, name, or description).
        codebook_type: Ignored (kept for API compat).
        max_results: Maximum number of results.

    Returns:
        JSON string with search results.
    """
    ctype = codebook_type or "seznam_vykonu"

    try:
        entries = await _get_entries()
    except Exception as exc:
        logger.error("Failed to load VZP data: %s", exc)
        return json.dumps(
            {
                "total": 0,
                "results": [],
                "error": f"VZP data unavailable: {exc}",
            },
            ensure_ascii=False,
        )

    normalized_q = normalize_query(query)
    matches: list[dict] = []

    for raw in entries:
        if _matches_query(raw, normalized_q):
            matches.append(
                _entry_to_summary(raw, ctype)
            )
            if len(matches) >= max_results:
                break

    return json.dumps(
        {"total": len(matches), "results": matches},
        ensure_ascii=False,
    )


async def _vzp_get(
    codebook_type: str, code: str,
) -> str:
    """Get full codebook entry details.

    Args:
        codebook_type: Codebook type identifier.
        code: Entry code.

    Returns:
        JSON string with full entry details.
    """
    try:
        entries = await _get_entries()
    except Exception as exc:
        logger.error("Failed to load VZP data: %s", exc)
        return json.dumps(
            {"error": f"VZP data unavailable: {exc}"},
            ensure_ascii=False,
        )

    code_lower = code.strip().lower()
    for raw in entries:
        if raw.get("KOD", "").strip().lower() == code_lower:
            return json.dumps(
                _normalise_entry(raw, codebook_type),
                ensure_ascii=False,
            )

    return json.dumps(
        {
            "error": (
                f"Codebook entry not found: "
                f"{codebook_type}/{code}"
            ),
        },
        ensure_ascii=False,
    )
