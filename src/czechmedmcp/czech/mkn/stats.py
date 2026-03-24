"""MKN-10 epidemiological statistics from NZIP open data."""

import csv
import io
import json
import logging
from pathlib import Path

import httpx

from czechmedmcp.constants import (
    CACHE_TTL_DAY,
    CZECH_HTTP_TIMEOUT,
    NZIP_CSV_BASE_URL,
)
from czechmedmcp.czech.mkn.models import (
    AgeGroupStats,
    DiagnosisStats,
    RegionStats,
)
from czechmedmcp.czech.response import format_czech_response
from czechmedmcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)

logger = logging.getLogger(__name__)

_CACHE_TTL = CACHE_TTL_DAY * 7  # 7 days

_LOCAL_DATA_DIR = Path(__file__).parent / "data"


async def _get_diagnosis_stats(code: str, year: int | None = None) -> str:
    """Get epidemiological statistics for a diagnosis.

    Args:
        code: MKN-10 code (e.g. "J06", "J06.9").
        year: Optional year filter (2015-2025).

    Returns:
        JSON string with dual output.
    """
    actual_year = year or 2024
    cache_key = generate_cache_key("NZIP_STATS", f"{code}:{actual_year}", {})
    cached = get_cached_response(cache_key)

    if cached:
        data = json.loads(cached)
    else:
        data = await _fetch_and_aggregate(code, actual_year)
        cache_response(cache_key, json.dumps(data), _CACHE_TTL)

    model = DiagnosisStats(
        code=code,
        name_cs=data.get("name_cs", code),
        year=actual_year,
        total_cases=data.get("total_cases", 0),
        male_count=data.get("male_count"),
        female_count=data.get("female_count"),
        age_distribution=[
            AgeGroupStats(**a) for a in data.get("age_distribution", [])
        ],
        region_distribution=[
            RegionStats(**r) for r in data.get("region_distribution", [])
        ],
        data_available=data.get("data_available", True),
    )

    md = _format_markdown(model)
    return format_czech_response(
        data=model.model_dump(),
        tool_name="get_diagnosis_stats",
        markdown_template=md,
    )


async def _fetch_and_aggregate(code: str, year: int) -> dict:
    """Fetch NZIP CSV and aggregate by diagnosis code."""
    url = f"{NZIP_CSV_BASE_URL}/hospitalizace_{year}.csv"

    try:
        async with httpx.AsyncClient(
            timeout=CZECH_HTTP_TIMEOUT,
        ) as client:
            resp = await client.get(url)
            if not resp.is_success:
                logger.warning(
                    "NZIP CSV unavailable: HTTP %d for year %d",
                    resp.status_code,
                    year,
                )
                return _try_local_fallback(code, year)
            text = resp.text
            if not text.strip():
                logger.warning("NZIP CSV empty for year %d", year)
                return _try_local_fallback(code, year)
    except httpx.HTTPError as exc:
        logger.warning("NZIP fetch failed: %s", exc)
        return _try_local_fallback(code, year)

    return _parse_csv(text, code, year)


def _try_local_fallback(code: str, year: int) -> dict:
    """Try local CSV fallback data."""
    fallback_path = _LOCAL_DATA_DIR / f"hospitalizace_{year}.csv"
    if fallback_path.exists():
        try:
            text = fallback_path.read_text(encoding="utf-8")
            if text.strip():
                logger.info(
                    "Using local NZIP fallback for %d",
                    year,
                )
                return _parse_csv(text, code, year)
        except OSError as exc:
            logger.warning(
                "Local NZIP fallback read error: %s",
                exc,
            )

    return _unavailable_stats(code, year)


def _parse_csv(text: str, code: str, year: int) -> dict:
    """Parse NZIP CSV and aggregate stats for code."""
    # Detect delimiter
    first_line = text.split("\n", 1)[0]
    delimiter = ";" if ";" in first_line else ","

    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

    total = 0
    male = 0
    female = 0
    age_map: dict[str, int] = {}
    region_map: dict[str, int] = {}
    name_cs = code

    for row in reader:
        mkn = row.get("mkn", row.get("diagnoza", ""))
        if not mkn.startswith(code):
            continue

        count = _safe_int(row.get("pocet", row.get("count", "0")))
        total += count

        gender = row.get("pohlavi", "")
        if gender == "M":
            male += count
        elif gender == "Z":
            female += count

        age = row.get("vekova_skupina", "")
        if age:
            age_map[age] = age_map.get(age, 0) + count

        region = row.get("kraj", "")
        if region:
            region_map[region] = region_map.get(region, 0) + count

        if name_cs == code:
            name_cs = row.get(
                "nazev",
                row.get("diagnoza_nazev", code),
            )

    return {
        "name_cs": name_cs,
        "total_cases": total,
        "male_count": male or None,
        "female_count": female or None,
        "age_distribution": [
            {"age_group": k, "count": v} for k, v in sorted(age_map.items())
        ],
        "region_distribution": [
            {"region": k, "count": v}
            for k, v in sorted(
                region_map.items(),
                key=lambda x: -x[1],
            )
        ],
        "data_available": True,
    }


def _safe_int(val: str | int) -> int:
    """Parse int safely, return 0 on failure."""
    try:
        return int(val)
    except (ValueError, TypeError):
        return 0


def _empty_stats(code: str, year: int) -> dict:
    """Return empty stats when data unavailable."""
    return {
        "name_cs": code,
        "total_cases": 0,
        "male_count": None,
        "female_count": None,
        "age_distribution": [],
        "region_distribution": [],
        "data_available": True,
    }


def _unavailable_stats(code: str, year: int) -> dict:
    """Return stats indicating data is unavailable."""
    return {
        "name_cs": code,
        "total_cases": 0,
        "male_count": None,
        "female_count": None,
        "age_distribution": [],
        "region_distribution": [],
        "data_available": False,
    }


def _format_markdown(s: DiagnosisStats) -> str:
    """Format DiagnosisStats as Czech Markdown."""
    lines = [
        f"## Statistika: {s.code} — {s.name_cs}",
        "",
        f"**Rok**: {s.year}",
    ]

    if not s.data_available:
        lines.append(
            "\n**Data nejsou dostupná** pro zadaný "
            "rok. NZIP CSV soubor nebyl nalezen "
            "nebo není přístupný."
        )
        return "\n".join(lines)

    lines.append(f"**Celkem případů**: {s.total_cases:,}")
    if s.male_count is not None:
        lines.append(f"**Muži**: {s.male_count:,}")
    if s.female_count is not None:
        lines.append(f"**Ženy**: {s.female_count:,}")

    if s.age_distribution:
        lines.extend(["", "### Věkové rozložení", ""])
        for a in s.age_distribution:
            lines.append(f"- {a.age_group}: {a.count:,}")

    if s.region_distribution:
        lines.extend(["", "### Regionální rozložení", ""])
        for r in s.region_distribution:
            lines.append(f"- {r.region}: {r.count:,}")

    return "\n".join(lines)
