"""SZV health procedures search implementation.

Downloads Excel export from szv.mzcr.cz and provides
in-memory search with diskcache for the raw data.

Data source: https://szv.mzcr.cz/Vykon/Export/
"""

import io
import json
import logging

import httpx
import openpyxl

from czechmedmcp.constants import (
    BULK_DOWNLOAD_TIMEOUT,
    CACHE_TTL_DAY,
    DEFAULT_CACHE_TIMEOUT,
)
from czechmedmcp.czech.diacritics import normalize_query
from czechmedmcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)
from czechmedmcp.utils.retry import async_retry

logger = logging.getLogger(__name__)

_SZV_EXPORT_URL = "https://szv.mzcr.cz/Vykon/Export/"
_LIST_CACHE_TTL = CACHE_TTL_DAY
_DETAIL_CACHE_TTL = DEFAULT_CACHE_TIMEOUT

# Module-level cache
_PROCEDURES: list[dict] | None = None


async def _download_excel() -> list[dict]:  # noqa: C901
    """Download SZV Excel export and parse procedures.

    Raises:
        RuntimeError: When download or parse fails,
            with a descriptive message for the caller.
    """
    cache_key = generate_cache_key(
        "PARSED", "szv:procedures", {}
    )
    cached = get_cached_response(cache_key)
    if cached:
        return json.loads(cached)

    async def _do_download() -> bytes:
        async with httpx.AsyncClient(
            timeout=BULK_DOWNLOAD_TIMEOUT,
            follow_redirects=True,
        ) as client:
            resp = await client.get(_SZV_EXPORT_URL)
            resp.raise_for_status()
            return resp.content

    try:
        content = await async_retry(
            _do_download, max_retries=3, initial_delay=2.0
        )
    except httpx.TimeoutException:
        logger.error(
            "SZV Excel download timed out: %s",
            _SZV_EXPORT_URL,
        )
        raise RuntimeError(
            "SZV server timeout — try again later"
        ) from None
    except httpx.HTTPStatusError as exc:
        logger.error(
            "SZV Excel HTTP %s: %s",
            exc.response.status_code,
            _SZV_EXPORT_URL,
        )
        raise RuntimeError(
            f"SZV server HTTP "
            f"{exc.response.status_code}"
        ) from None
    except httpx.ConnectError:
        logger.error(
            "SZV connection failed: %s",
            _SZV_EXPORT_URL,
        )
        raise RuntimeError(
            "SZV server unreachable"
        ) from None
    except httpx.HTTPError as exc:
        logger.error("SZV HTTP error: %s", exc)
        raise RuntimeError(
            f"SZV download failed: {exc}"
        ) from None

    try:
        wb = openpyxl.load_workbook(
            io.BytesIO(content), read_only=True
        )
        ws = wb["Export"]
        rows = list(ws.iter_rows(values_only=True))
        wb.close()
    except Exception as exc:
        logger.error(
            "SZV Excel parse error: %s", exc
        )
        raise RuntimeError(
            f"SZV Excel parse failed: {exc}"
        ) from None

    if not rows:
        return []

    headers = [str(h or "").strip() for h in rows[0]]
    procedures = []
    for row in rows[1:]:
        entry = dict(zip(headers, row, strict=False))
        if entry.get("Kód"):
            procedures.append(entry)

    cache_response(
        cache_key,
        json.dumps(
            procedures,
            ensure_ascii=False,
            default=str,
        ),
        _LIST_CACHE_TTL,
    )
    return procedures


async def _get_procedures() -> list[dict]:
    """Return cached or freshly loaded procedure list."""
    global _PROCEDURES
    if _PROCEDURES is not None:
        return _PROCEDURES

    _PROCEDURES = await _download_excel()
    logger.debug(
        "Loaded %d SZV procedures", len(_PROCEDURES)
    )
    return _PROCEDURES


def _raw_to_summary(raw: dict) -> dict:
    """Convert an Excel row to a procedure summary."""
    return {
        "code": str(raw.get("Kód", "")).strip(),
        "name": str(raw.get("Název", "")).strip(),
        "point_value": raw.get("Celkové"),
        "category": raw.get("Kategorie"),
    }


def _raw_to_full(raw: dict) -> dict:
    """Convert an Excel row to full procedure detail."""
    return {
        "code": str(raw.get("Kód", "")).strip(),
        "name": str(raw.get("Název", "")).strip(),
        "description": raw.get("Popis výkonu"),
        "category": raw.get("Kategorie"),
        "specialty": raw.get("Odbornost"),
        "other_specialties": raw.get(
            "Další odbornosti"
        ),
        "point_value": raw.get("Celkové"),
        "direct_costs": raw.get("Přímé náklady"),
        "personnel_costs": raw.get("Osobní"),
        "overhead_costs": raw.get("Režijní"),
        "time_minutes": raw.get("Trvání"),
        "carrier_time": raw.get("Čas nositele"),
        "carrier_level": raw.get("Nositel"),
        "frequency_limit": raw.get("OF"),
        "location": raw.get("OM"),
        "conditions": raw.get("Podmínky výkonu"),
        "notes": raw.get("Poznámka výkonu"),
        "zulp": raw.get("ZULP"),
        "zum": raw.get("ZUM"),
        "source": "MZCR/SZV",
    }


def _matches_query(raw: dict, normalized_q: str) -> bool:
    """Return True if the procedure matches the query."""
    code = str(raw.get("Kód", "")).lower()
    name = normalize_query(str(raw.get("Název", "")))
    spec = normalize_query(
        str(raw.get("Odbornost", ""))
    )
    return (
        normalized_q in code
        or normalized_q in name
        or normalized_q in spec
    )


async def _szv_search(
    query: str,
    max_results: int = 10,
) -> str:
    """Search health procedures by code or name.

    Args:
        query: Procedure code or name fragment.
        max_results: Maximum number of results.

    Returns:
        JSON string with search results.
    """
    try:
        procedures = await _get_procedures()
    except Exception as exc:
        logger.error(
            "Failed to load SZV data: %s", exc
        )
        return json.dumps(
            {
                "total": 0,
                "results": [],
                "error": f"SZV data unavailable: {exc}",
            },
            ensure_ascii=False,
        )

    normalized_q = normalize_query(query)
    matches: list[dict] = []

    for raw in procedures:
        if _matches_query(raw, normalized_q):
            matches.append(_raw_to_summary(raw))
            if len(matches) >= max_results:
                break

    return json.dumps(
        {"total": len(matches), "results": matches},
        ensure_ascii=False,
    )


async def _szv_get(code: str) -> str:
    """Get full procedure details by code.

    Args:
        code: Procedure code (e.g. "09513").

    Returns:
        JSON string with full procedure fields.
    """
    try:
        procedures = await _get_procedures()
    except Exception as exc:
        logger.error(
            "Failed to load SZV data: %s", exc
        )
        return json.dumps(
            {"error": f"SZV data unavailable: {exc}"},
            ensure_ascii=False,
        )

    code_lower = code.strip().lower()
    for raw in procedures:
        raw_code = str(
            raw.get("Kód", "")
        ).strip().lower()
        if raw_code == code_lower:
            return json.dumps(
                _raw_to_full(raw), ensure_ascii=False
            )

    return json.dumps(
        {"error": f"Procedure not found: {code}"},
        ensure_ascii=False,
    )
