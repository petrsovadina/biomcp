"""Shared SUKL DLP API client utilities.

Provides the base URL constant and a single _fetch_drug_detail
implementation used by search, getter, and availability modules.
"""

import json
import logging

import httpx

from biomcp.constants import (
    CZECH_HTTP_TIMEOUT,
    DEFAULT_CACHE_TIMEOUT,
    SUKL_API_URL,
)
from biomcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)

logger = logging.getLogger(__name__)

SUKL_DLP_V1 = f"{SUKL_API_URL.removesuffix('/api')}/v1"
SUKL_HTTP_TIMEOUT = CZECH_HTTP_TIMEOUT
_DEFAULT_CACHE_TTL = DEFAULT_CACHE_TIMEOUT


async def fetch_drug_detail(
    sukl_code: str,
    use_cache: bool = True,
    cache_ttl: int = _DEFAULT_CACHE_TTL,
) -> dict | None:
    """Fetch drug detail from DLP API by SUKL code.

    Args:
        sukl_code: The SUKL drug code.
        use_cache: Whether to check/store in cache.
        cache_ttl: Cache TTL in seconds (default 1 week).
    """
    url = f"{SUKL_DLP_V1}/lecive-pripravky/{sukl_code}"
    cache_key = generate_cache_key("GET", url, {})

    if use_cache:
        cached = get_cached_response(cache_key)
        if cached:
            return json.loads(cached)

    try:
        async with httpx.AsyncClient(
            timeout=SUKL_HTTP_TIMEOUT
        ) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        logger.warning(
            "Failed to fetch drug detail for %s", sukl_code
        )
        return None

    if use_cache:
        cache_response(cache_key, json.dumps(data), cache_ttl)
    return data
