"""MKN-10 CSV data loader for Czech ICD-10 classification.

Downloads the official MZ ČR open data CSV and builds two
in-memory indices:
- code_index: maps code -> node dict (code, name_cs, kind,
  parent_code, children)
- text_index: maps normalized word -> list of codes

Results are cached using diskcache to avoid re-downloading.

Data source: https://data.mzcr.cz (CC BY 4.0)
"""

import csv
import io
import json
import logging

import httpx

from biomcp.constants import CACHE_TTL_MONTH, CZECH_HTTP_TIMEOUT
from biomcp.czech.diacritics import normalize_query
from biomcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)

logger = logging.getLogger(__name__)

_MKN10_CSV_URL = (
    "https://data.mzcr.cz/data/distribuce/463/"
    "Otevrena-data-OIS-12-03-ciselnik-mkn-10-cz.csv"
)
_CACHE_TTL = CACHE_TTL_MONTH

# Type aliases for the two index types
CodeIndex = dict[str, dict]
TextIndex = dict[str, list[str]]


def _build_text_index(
    code: str,
    name_cs: str,
    text_index: TextIndex,
) -> None:
    """Index all words of a Czech name into the text index."""
    normalized = normalize_query(name_cs)
    for word in normalized.split():
        if len(word) < 2:
            continue
        if word not in text_index:
            text_index[word] = []
        if code not in text_index[word]:
            text_index[word].append(code)


async def _download_csv() -> str:
    """Download the MKN-10 CSV from MZ ČR open data."""
    cache_key = generate_cache_key("GET", _MKN10_CSV_URL, {})
    cached = get_cached_response(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient(timeout=CZECH_HTTP_TIMEOUT) as client:
        resp = await client.get(_MKN10_CSV_URL)
        resp.raise_for_status()
        content = resp.text

    cache_response(cache_key, content, _CACHE_TTL)
    return content


def _parse_csv(csv_text: str) -> tuple[CodeIndex, TextIndex]:
    """Parse CSV text and return (code_index, text_index).

    Builds chapter nodes from unique (kod_kapitola_rozsah,
    kod_kapitola_cislo, nazev_kapitola) tuples, category nodes
    from 3-char codes, and subcategory nodes from dotted codes.
    """
    code_index: CodeIndex = {}
    text_index: TextIndex = {}

    # Track chapters and categories for hierarchy
    chapters: dict[str, dict] = {}
    category_to_chapter: dict[str, str] = {}

    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        kod_tecka = (row.get("kod_tecka") or "").strip()
        nazev = (row.get("nazev") or "").strip()
        platnost_do = (row.get("platnost_do") or "").strip()

        if not kod_tecka or not nazev:
            continue
        # Skip expired codes
        if platnost_do:
            continue

        chap_range = (row.get("kod_kapitola_rozsah") or "").strip()
        chap_num = (row.get("kod_kapitola_cislo") or "").strip()
        chap_name = (row.get("nazev_kapitola") or "").strip()

        # Register chapter if new
        if chap_range and chap_range not in chapters:
            chapters[chap_range] = {
                "code": chap_range,
                "name_cs": chap_name,
                "kind": "chapter",
                "parent_code": None,
                "children": [],
                "chapter_num": chap_num,
            }

        # Determine kind and parent
        if "." in kod_tecka:
            kind = "category"
            parent_code = kod_tecka.split(".")[0]
        else:
            kind = "block"
            parent_code = chap_range

        # Track category → chapter mapping
        if kind == "block":
            category_to_chapter[kod_tecka] = chap_range

        code_index[kod_tecka] = {
            "code": kod_tecka,
            "name_cs": nazev,
            "kind": kind,
            "parent_code": parent_code,
            "children": [],
        }

        if nazev:
            _build_text_index(kod_tecka, nazev, text_index)

    # Add chapter nodes to code_index
    for chap_code, chap_node in chapters.items():
        code_index[chap_code] = chap_node
        if chap_node["name_cs"]:
            _build_text_index(
                chap_code, chap_node["name_cs"], text_index
            )

    # Build children lists
    for code, node in code_index.items():
        parent = node.get("parent_code")
        if parent and parent in code_index:
            parent_node = code_index[parent]
            if code not in parent_node["children"]:
                parent_node["children"].append(code)

    # Sort children for consistent ordering
    for node in code_index.values():
        node["children"].sort()

    logger.debug(
        "Parsed %d MKN-10 entries, %d text tokens",
        len(code_index),
        len(text_index),
    )
    return code_index, text_index


async def load_mkn10() -> tuple[CodeIndex, TextIndex]:
    """Download and parse MKN-10 data, with caching.

    Returns (code_index, text_index). Results are cached in
    diskcache for one month.
    """
    index_cache_key = generate_cache_key(
        "PARSED", "mkn10:index", {}
    )
    cached = get_cached_response(index_cache_key)
    if cached:
        payload = json.loads(cached)
        return payload["code_index"], payload["text_index"]

    csv_text = await _download_csv()
    code_index, text_index = _parse_csv(csv_text)

    payload = json.dumps(
        {"code_index": code_index, "text_index": text_index},
        ensure_ascii=False,
    )
    cache_response(index_cache_key, payload, _CACHE_TTL)

    return code_index, text_index
