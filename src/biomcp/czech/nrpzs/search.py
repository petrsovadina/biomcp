"""NRPZS healthcare provider search and detail retrieval.

Downloads CSV open data from ÚZIS (datanzis.uzis.gov.cz) and
provides in-memory search with diskcache for the raw CSV.

Data source: https://datanzis.uzis.gov.cz (CC BY 4.0)
"""

import csv
import io
import json
import logging

import httpx

from biomcp.constants import (
    CACHE_TTL_DAY,
    CZECH_HTTP_TIMEOUT,
)
from biomcp.czech.diacritics import normalize_query
from biomcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)

logger = logging.getLogger(__name__)

_NRPZS_CSV_URL = (
    "https://datanzis.uzis.gov.cz/data/NR-01-NRPZS/NR-01-06/"
    "Otevrena-data-NR-01-06-nrpzs-mista-poskytovani-"
    "zdravotnich-sluzeb.csv"
)
_CSV_CACHE_TTL = CACHE_TTL_DAY

# Module-level cache
_PROVIDERS: list[dict] | None = None


async def _download_csv() -> str:
    """Download the NRPZS CSV from ÚZIS open data."""
    cache_key = generate_cache_key("GET", _NRPZS_CSV_URL, {})
    cached = get_cached_response(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient(
        timeout=CZECH_HTTP_TIMEOUT,
        follow_redirects=True,
    ) as client:
        resp = await client.get(_NRPZS_CSV_URL)
        resp.raise_for_status()
        content = resp.text

    cache_response(cache_key, content, _CSV_CACHE_TTL)
    return content


def _parse_csv(csv_text: str) -> list[dict]:
    """Parse NRPZS CSV into a list of provider dicts."""
    reader = csv.DictReader(io.StringIO(csv_text))
    providers = []
    for row in reader:
        providers.append(row)
    return providers


async def _get_providers() -> list[dict]:
    """Return cached or freshly loaded provider list."""
    global _PROVIDERS
    if _PROVIDERS is not None:
        return _PROVIDERS

    csv_text = await _download_csv()
    _PROVIDERS = _parse_csv(csv_text)
    logger.debug("Loaded %d NRPZS providers", len(_PROVIDERS))
    return _PROVIDERS


def _csv_to_summary(row: dict) -> dict:
    """Convert a CSV row to ProviderSummary dict."""
    specialties_str = row.get("ZZ_obor_pece", "")
    specialties = (
        [s.strip() for s in specialties_str.split(",")
         if s.strip()]
        if specialties_str
        else []
    )

    return {
        "provider_id": row.get("ZZ_misto_poskytovani_ID", ""),
        "name": row.get("ZZ_nazev", ""),
        "city": row.get("ZZ_obec"),
        "specialties": specialties,
    }


def _csv_to_provider(row: dict) -> dict:
    """Convert a CSV row to full HealthcareProvider dict."""
    specialties_str = row.get("ZZ_obor_pece", "")
    specialties = (
        [s.strip() for s in specialties_str.split(",")
         if s.strip()]
        if specialties_str
        else []
    )

    care_types_str = row.get("ZZ_druh_pece", "")
    care_types = (
        [s.strip() for s in care_types_str.split(",")
         if s.strip()]
        if care_types_str
        else []
    )

    address: dict | None = None
    if any(
        row.get(k)
        for k in (
            "ZZ_ulice", "ZZ_obec", "ZZ_PSC", "ZZ_kraj_nazev"
        )
    ):
        address = {
            "street": row.get("ZZ_ulice"),
            "city": row.get("ZZ_obec"),
            "postal_code": row.get("ZZ_PSC"),
            "region": row.get("ZZ_kraj_nazev"),
        }

    contact: dict | None = None
    phone = row.get("poskytovatel_telefon")
    email = row.get("poskytovatel_email")
    web = row.get("poskytovatel_web")
    if any((phone, email, web)):
        contact = {
            "phone": phone or None,
            "email": email or None,
            "website": web or None,
        }

    return {
        "provider_id": row.get(
            "ZZ_misto_poskytovani_ID", ""
        ),
        "name": row.get("ZZ_nazev", ""),
        "legal_form": row.get(
            "poskytovatel_pravni_forma_nazev"
        ),
        "ico": row.get("poskytovatel_ICO"),
        "address": address,
        "specialties": specialties,
        "care_types": care_types,
        "care_form": row.get("ZZ_forma_pece"),
        "contact": contact,
        "facility_type": row.get("ZZ_druh_nazev"),
        "region": row.get("ZZ_kraj_nazev"),
        "district": row.get("ZZ_okres_nazev"),
        "source": "NRPZS",
    }


def _matches_query(
    row: dict,
    query_n: str | None,
    city_n: str | None,
    specialty_n: str | None,
) -> bool:
    """Check if a CSV row matches the search criteria."""
    if query_n:
        name_n = normalize_query(
            row.get("ZZ_nazev", "")
        )
        prov_n = normalize_query(
            row.get("poskytovatel_nazev", "")
        )
        if query_n not in name_n and query_n not in prov_n:
            return False

    if city_n:
        row_city = normalize_query(
            row.get("ZZ_obec", "")
        )
        if city_n not in row_city:
            return False

    if specialty_n:
        spec_n = normalize_query(
            row.get("ZZ_obor_pece", "")
        )
        if specialty_n not in spec_n:
            return False

    return True


async def _nrpzs_search(
    query: str | None = None,
    city: str | None = None,
    specialty: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> str:
    """Search Czech healthcare providers in NRPZS.

    Args:
        query: Provider or facility name.
        city: Filter by municipality name.
        specialty: Filter by medical specialty.
        page: Page number (1-based).
        page_size: Results per page (1-100).

    Returns:
        JSON string with search results.
    """
    try:
        providers = await _get_providers()
    except Exception as exc:
        logger.error("Failed to load NRPZS data: %s", exc)
        return json.dumps(
            {
                "total": 0,
                "page": page,
                "page_size": page_size,
                "results": [],
                "error": f"NRPZS data unavailable: {exc}",
            },
            ensure_ascii=False,
        )

    query_n = normalize_query(query) if query else None
    city_n = normalize_query(city) if city else None
    specialty_n = (
        normalize_query(specialty) if specialty else None
    )

    # Paginate: skip to correct page
    skip = (page - 1) * page_size
    matches: list[dict] = []
    total = 0

    for row in providers:
        if _matches_query(row, query_n, city_n, specialty_n):
            total += 1
            if total > skip and len(matches) < page_size:
                matches.append(_csv_to_summary(row))

    result = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "results": matches,
    }

    return json.dumps(result, ensure_ascii=False)


async def _nrpzs_get(provider_id: str) -> str:
    """Get full provider details by facility ID.

    Args:
        provider_id: ZZ_misto_poskytovani_ID value.

    Returns:
        JSON string with HealthcareProvider fields.
    """
    try:
        providers = await _get_providers()
    except Exception as exc:
        logger.error("Failed to load NRPZS data: %s", exc)
        return json.dumps(
            {"error": f"NRPZS data unavailable: {exc}"},
            ensure_ascii=False,
        )

    for row in providers:
        row_id = row.get("ZZ_misto_poskytovani_ID", "")
        if str(row_id) == str(provider_id):
            result = _csv_to_provider(row)
            return json.dumps(result, ensure_ascii=False)

    return json.dumps(
        {"error": f"Provider not found: {provider_id}"},
        ensure_ascii=False,
    )
