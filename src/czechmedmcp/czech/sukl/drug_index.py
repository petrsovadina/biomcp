"""In-memory searchable drug index for SUKL registry.

Builds a lazy-loaded index from cached drug details (~14 MB),
refreshed daily (CACHE_TTL_DAY). Follows the same on-demand
initialization pattern as MKN-10 and SZV modules.

Persistent disk cache: after a successful build the serialised
index is written to diskcache so that subsequent process starts
load in ~1 s instead of re-fetching ~68 K drug details (~10 min).
"""

import asyncio
import json
import logging
import time
from dataclasses import asdict, dataclass

import httpx

from czechmedmcp.constants import (
    BULK_DOWNLOAD_TIMEOUT,
    CACHE_TTL_DAY,
    compute_skip,
)
from czechmedmcp.czech.diacritics import normalize_query
from czechmedmcp.czech.sukl.client import (
    SUKL_DLP_V1,
    fetch_drug_detail,
)
from czechmedmcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)
from czechmedmcp.utils.retry import async_retry

logger = logging.getLogger(__name__)

_INDEX_CACHE_TTL = CACHE_TTL_DAY
_INDEX_DISK_KEY = "sukl_drug_index_v1"
_MIN_SUCCESS_RATIO = 0.50  # build succeeds if >= 50% fetched


@dataclass(frozen=True, slots=True)
class DrugIndexEntry:
    """Single drug entry in the searchable index."""

    sukl_code: str
    name: str
    name_normalized: str
    strength: str
    atc_code: str
    atc_normalized: str
    form: str
    supplement: str
    supplement_normalized: str
    holder_code: str


class DrugIndex:
    """In-memory searchable drug index singleton."""

    def __init__(self) -> None:
        self._entries: list[DrugIndexEntry] = []
        self._built_at: float = 0.0
        self._lock = asyncio.Lock()
        self._rebuilding = False
        self._rebuild_task: asyncio.Task | None = None

    @property
    def is_expired(self) -> bool:
        if not self._entries:
            return True
        return (time.time() - self._built_at) > _INDEX_CACHE_TTL

    @property
    def size(self) -> int:
        return len(self._entries)

    async def ensure_built(self) -> None:
        """Build or rebuild the index if needed."""
        if not self.is_expired:
            return
        # Stale entries exist — serve them, rebuild bg
        if self._entries:
            self._schedule_background_rebuild()
            return
        # No entries at all — must block
        async with self._lock:
            # Double-check after acquiring lock
            if not self.is_expired:
                return
            await self._build()

    def _schedule_background_rebuild(self) -> None:
        """Trigger non-blocking background rebuild."""
        if self._rebuilding:
            return
        self._rebuilding = True
        self._rebuild_task = asyncio.create_task(
            self._background_rebuild()
        )

    async def _background_rebuild(self) -> None:
        """Rebuild index in background."""
        try:
            async with self._lock:
                if not self.is_expired:
                    return
                await self._build()
        except Exception:
            logger.error(
                "Background SUKL index rebuild failed",
                exc_info=True,
            )
        finally:
            self._rebuilding = False

    async def _build(self) -> None:
        """Fetch all drug codes and build index.

        Tries to load from persistent disk cache first.
        Falls back to live API fetch with partial-build tolerance.
        """
        # 1. Try persistent disk cache
        cached_json = get_cached_response(_INDEX_DISK_KEY)
        if cached_json:
            try:
                raw = json.loads(cached_json)
                self._entries = [
                    DrugIndexEntry(**e) for e in raw
                ]
                self._built_at = time.time()
                logger.info(
                    "SUKL drug index loaded from cache: "
                    "%d entries",
                    len(self._entries),
                )
                return
            except Exception:
                logger.warning(
                    "Corrupt disk cache — rebuilding index"
                )

        # 2. Live fetch
        logger.info("Building SUKL drug index from API...")
        start = time.time()

        try:
            codes = await async_retry(
                _fetch_drug_list, max_retries=3
            )
        except Exception:
            logger.error("Failed to fetch drug list after retries")
            return

        if not codes:
            logger.error("Drug list is empty")
            return

        entries = await _fetch_all_details(codes)

        ratio = len(entries) / len(codes) if codes else 0
        if ratio < _MIN_SUCCESS_RATIO:
            logger.error(
                "Drug index build too incomplete: "
                "%d/%d (%.0f%%) — below %.0f%% threshold",
                len(entries),
                len(codes),
                ratio * 100,
                _MIN_SUCCESS_RATIO * 100,
            )
            # Still use partial entries if we have any
            if not entries:
                return

        self._entries = entries
        self._built_at = time.time()

        # 3. Persist to disk cache
        serialised = json.dumps(
            [asdict(e) for e in entries],
            ensure_ascii=False,
        )
        cache_response(
            _INDEX_DISK_KEY, serialised, _INDEX_CACHE_TTL
        )

        elapsed = time.time() - start
        logger.info(
            "SUKL drug index built: %d entries in %.1fs",
            len(entries),
            elapsed,
        )


# Module-level singleton
_index: DrugIndex | None = None


async def get_drug_index() -> DrugIndex:
    """Get or create the drug index singleton."""
    global _index
    if _index is None:
        _index = DrugIndex()
    await _index.ensure_built()
    return _index


def reset_drug_index() -> None:
    """Reset the singleton (for testing)."""
    global _index
    _index = None


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
        timeout=BULK_DOWNLOAD_TIMEOUT
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

    cache_response(
        cache_key, json.dumps(codes), _INDEX_CACHE_TTL
    )
    return codes


async def _fetch_all_details(
    codes: list[str],
) -> list[DrugIndexEntry]:
    """Fetch details for all codes with bounded concurrency."""
    sem = asyncio.Semaphore(20)
    entries: list[DrugIndexEntry] = []
    errors = 0

    async def _fetch_one(code: str) -> DrugIndexEntry | None:
        nonlocal errors
        async with sem:
            detail = await fetch_drug_detail(code)
            if not detail:
                errors += 1
                return None
            return _detail_to_entry(detail)

    results = await asyncio.gather(
        *(_fetch_one(c) for c in codes),
        return_exceptions=True,
    )

    for r in results:
        if isinstance(r, DrugIndexEntry):
            entries.append(r)

    if errors:
        logger.warning(
            "Drug index: %d/%d codes failed to fetch",
            errors,
            len(codes),
        )

    return entries


def _detail_to_entry(detail: dict) -> DrugIndexEntry:
    """Convert raw API detail to index entry."""
    name = detail.get("nazev", "")
    supplement = detail.get("doplnek", "")
    atc = detail.get("ATCkod") or ""
    holder = (detail.get("drzitelKod") or "").lower()

    return DrugIndexEntry(
        sukl_code=detail.get("kodSUKL", ""),
        name=name,
        name_normalized=normalize_query(name),
        strength=detail.get("sila") or "",
        atc_code=atc,
        atc_normalized=atc.lower(),
        form=detail.get("lekovaFormaKod") or "",
        supplement=supplement,
        supplement_normalized=normalize_query(supplement),
        holder_code=holder,
    )


def search_index(
    index: DrugIndex,
    query: str,
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[DrugIndexEntry], int]:
    """Search the drug index by name, ATC, or supplement.

    Args:
        index: The built drug index.
        query: Search query (name, ATC code, substance).
        page: Page number (1-based).
        page_size: Results per page.

    Returns:
        Tuple of (page_results, total_matches).
    """
    normalized_q = normalize_query(query)
    if not normalized_q:
        return [], 0

    matches: list[DrugIndexEntry] = []
    for entry in index._entries:
        if (
            normalized_q in entry.name_normalized
            or normalized_q == entry.atc_normalized
            or normalized_q in entry.supplement_normalized
            or normalized_q in entry.holder_code
        ):
            matches.append(entry)

    total = len(matches)
    start = compute_skip(page, page_size)
    end = start + page_size
    return matches[start:end], total
