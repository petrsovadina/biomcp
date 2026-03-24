"""VZP reimbursement static data loader.

Downloads VZP reimbursement CSV from official source,
falls back to local CSV template. Provides in-memory
cache keyed by SUKL code.
"""

import csv
import io
import logging
import time
from pathlib import Path

import httpx

from czechmedmcp.constants import (
    CACHE_TTL_DAY,
    CZECH_HTTP_TIMEOUT,
)

logger = logging.getLogger(__name__)

# VZP publishes reimbursement CSVs here (semicolon-sep)
_VZP_CSV_URL = (
    "https://media.vzpstatic.cz/media/Default/"
    "dokumenty/ciselniky/uhrada-leciva.csv"
)

_LOCAL_CSV = Path(__file__).parent / "data" / "vzp_reimbursement.csv"

# In-memory cache
_cache: dict[str, dict] = {}
_cache_ts: float = 0.0


def _is_cache_valid() -> bool:
    return bool(_cache) and (time.time() - _cache_ts < CACHE_TTL_DAY)


async def load_vzp_reimbursement_data() -> dict[str, dict]:
    """Load VZP reimbursement data into memory.

    Tries remote CSV first, then local fallback.

    Returns:
        Dict mapping sukl_code to reimbursement info.
    """
    global _cache, _cache_ts

    if _is_cache_valid():
        return _cache

    text = await _download_csv()
    if not text:
        text = _read_local_csv()

    if text:
        _cache = _parse_reimbursement_csv(text)
        _cache_ts = time.time()
        logger.info(
            "VZP reimbursement data loaded: %d entries",
            len(_cache),
        )
    else:
        logger.warning("No VZP reimbursement data available")

    return _cache


async def _download_csv() -> str | None:
    """Download VZP reimbursement CSV."""
    try:
        async with httpx.AsyncClient(
            timeout=CZECH_HTTP_TIMEOUT,
        ) as client:
            resp = await client.get(_VZP_CSV_URL)
            if resp.is_success and resp.text.strip():
                logger.info(
                    "Downloaded VZP CSV (%d bytes)",
                    len(resp.text),
                )
                return resp.text
            logger.warning(
                "VZP CSV download failed: HTTP %d",
                resp.status_code,
            )
    except httpx.HTTPError as exc:
        logger.warning("VZP CSV download error: %s", exc)
    return None


def _read_local_csv() -> str | None:
    """Read local fallback CSV file."""
    try:
        if _LOCAL_CSV.exists():
            text = _LOCAL_CSV.read_text(encoding="utf-8")
            if text.strip():
                return text
    except OSError as exc:
        logger.warning("Local VZP CSV read error: %s", exc)
    return None


def _parse_reimbursement_csv(
    text: str,
) -> dict[str, dict]:
    """Parse VZP reimbursement CSV into lookup dict.

    Handles both comma and semicolon delimiters.
    Expected columns: sukl_code, reimbursement_group,
    max_price, reimbursement_amount, patient_copay.
    """
    result: dict[str, dict] = {}

    # Detect delimiter
    first_line = text.split("\n", 1)[0]
    delimiter = ";" if ";" in first_line else ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    for row in reader:
        code = row.get("sukl_code", row.get("kod_sukl", "")).strip()
        if not code:
            continue

        result[code] = {
            "reimbursement_group": (
                row.get("reimbursement_group")
                or row.get("skupina_uhrady")
                or None
            ),
            "max_price": _safe_float(
                row.get("max_price") or row.get("max_cena")
            ),
            "reimbursement_amount": _safe_float(
                row.get("reimbursement_amount") or row.get("uhrada")
            ),
            "patient_copay": _safe_float(
                row.get("patient_copay") or row.get("doplatek")
            ),
        }

    return result


def _safe_float(val: str | None) -> float | None:
    """Parse float, return None on failure."""
    if not val:
        return None
    try:
        return float(val.replace(",", ".").strip())
    except (ValueError, AttributeError):
        return None


def get_vzp_reimbursement_for_code(
    sukl_code: str,
) -> dict | None:
    """Look up reimbursement for a SUKL code.

    Must call load_vzp_reimbursement_data() first.
    """
    return _cache.get(sukl_code.strip())


def clear_cache() -> None:
    """Clear in-memory VZP reimbursement cache."""
    global _cache, _cache_ts
    _cache = {}
    _cache_ts = 0.0
