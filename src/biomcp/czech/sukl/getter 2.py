"""SUKL drug detail, SmPC, and PIL retrieval.

Uses SUKL DLP API v1 for drug details, composition, and
document metadata. Enhanced PIL/SPC with HTML parsing.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

import httpx

from biomcp.constants import DEFAULT_CACHE_TIMEOUT
from biomcp.czech.response import format_czech_response
from biomcp.czech.sukl.client import (
    SUKL_DLP_V1,
    SUKL_HTTP_TIMEOUT,
)
from biomcp.czech.sukl.client import (
    fetch_drug_detail as _fetch_drug_detail,
)
from biomcp.czech.sukl.models import (
    DocumentContent,
    DocumentSection,
)
from biomcp.http_client import (
    cache_response,
    generate_cache_key,
    get_cached_response,
)

if TYPE_CHECKING:
    from lxml.html import HtmlElement

logger = logging.getLogger(__name__)

_CACHE_TTL = DEFAULT_CACHE_TIMEOUT

# PIL section mapping (Czech headings → keys)
_PIL_SECTIONS: dict[str, str] = {
    "dávkování": "dosage",
    "jak se.*přípravek.*užívá": "dosage",
    "jak se.*užívá": "dosage",
    "kontraindikac": "contraindications",
    "neužívejte": "contraindications",
    "nežádoucí účinky": "side_effects",
    "možné nežádoucí": "side_effects",
    "interakc": "interactions",
    "jiné.*léky": "interactions",
    "těhotenstv": "pregnancy",
    "kojení": "pregnancy",
    "uchovávání": "storage",
    "uchováv": "storage",
}

# SPC numbered sections
_SPC_SECTION_RE = re.compile(
    r"^(\d+\.?\d*)\s+(.+)",
)


async def _fetch_composition(sukl_code: str) -> list[dict]:
    """Fetch drug composition (active substances)."""
    url = f"{SUKL_DLP_V1}/slozeni/{sukl_code}"
    cache_key = generate_cache_key("GET", url, {})

    cached = get_cached_response(cache_key)
    if cached:
        return json.loads(cached)

    try:
        async with httpx.AsyncClient(
            timeout=SUKL_HTTP_TIMEOUT
        ) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        logger.warning(
            "Failed to fetch composition for %s",
            sukl_code,
        )
        return []

    cache_response(
        cache_key, json.dumps(data), _CACHE_TTL
    )
    return data if isinstance(data, list) else []


async def _fetch_doc_metadata(
    sukl_code: str, typ: str | None = None
) -> list[dict]:
    """Fetch document metadata for a drug."""
    url = (
        f"{SUKL_DLP_V1}/dokumenty-metadata/{sukl_code}"
    )
    params = {"typ": typ} if typ else {}
    cache_key = generate_cache_key("GET", url, params)

    cached = get_cached_response(cache_key)
    if cached:
        return json.loads(cached)

    try:
        async with httpx.AsyncClient(
            timeout=SUKL_HTTP_TIMEOUT
        ) as client:
            resp = await client.get(url, params=params)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError:
        logger.warning(
            "Failed to fetch doc metadata for %s",
            sukl_code,
        )
        return []

    result = data if isinstance(data, list) else []
    cache_response(
        cache_key, json.dumps(result), _CACHE_TTL
    )
    return result


def _build_doc_url(
    sukl_code: str, doc_type: str
) -> str:
    """Build document download URL."""
    return (
        f"{SUKL_DLP_V1}/dokumenty/{sukl_code}"
        f"/{doc_type}"
    )


def _composition_to_substances(
    composition: list[dict],
) -> list[dict]:
    """Convert API composition to active substances."""
    substances = []
    seen: set[int] = set()
    for item in composition:
        code = item.get("kodLatky", 0)
        if code in seen:
            continue
        seen.add(code)
        amount = item.get("mnozstvi", "")
        unit = item.get("jednotkaKod", "")
        strength = (
            f"{amount} {unit}".strip() if amount else None
        )
        substances.append(
            {"substance_code": code, "strength": strength}
        )
    return substances


async def _sukl_drug_details(sukl_code: str) -> str:
    """Get full drug details by SUKL code."""
    detail = await _fetch_drug_detail(sukl_code)
    if not detail:
        return json.dumps(
            {"error": f"Drug not found: {sukl_code}"},
            ensure_ascii=False,
        )

    composition = await _fetch_composition(sukl_code)
    doc_meta = await _fetch_doc_metadata(sukl_code)

    spc_docs = [
        d for d in doc_meta if d.get("typ") == "spc"
    ]
    pil_docs = [
        d for d in doc_meta if d.get("typ") == "pil"
    ]

    spc_url = (
        _build_doc_url(sukl_code, "spc")
        if spc_docs
        else None
    )
    pil_url = (
        _build_doc_url(sukl_code, "pil")
        if pil_docs
        else None
    )

    result = {
        "sukl_code": detail.get("kodSUKL", sukl_code),
        "name": detail.get("nazev", ""),
        "strength": detail.get("sila"),
        "active_substances": _composition_to_substances(
            composition
        ),
        "pharmaceutical_form": detail.get(
            "lekovaFormaKod"
        ),
        "atc_code": detail.get("ATCkod"),
        "registration_number": detail.get(
            "registracniCislo"
        ),
        "mah_code": detail.get("drzitelKod"),
        "registration_valid_to": detail.get(
            "registracePlatDo"
        ),
        "is_delivered": detail.get("jeDodavka"),
        "spc_url": spc_url,
        "pil_url": pil_url,
        "source": "SUKL",
    }

    return json.dumps(result, ensure_ascii=False)


# -------------------------------------------------------
# HTML document scraping
# -------------------------------------------------------


async def _fetch_doc_html(doc_url: str) -> str | None:
    """Fetch document HTML from SUKL."""
    cache_key = generate_cache_key(
        "GET", doc_url, {}
    )
    cached = get_cached_response(cache_key)
    if cached:
        return cached

    try:
        async with httpx.AsyncClient(
            timeout=SUKL_HTTP_TIMEOUT
        ) as client:
            resp = await client.get(doc_url)
            if not resp.is_success:
                return None
            html = resp.text
    except httpx.HTTPError:
        logger.warning(
            "Failed to fetch document from %s", doc_url
        )
        return None

    cache_response(cache_key, html, _CACHE_TTL)
    return html


def _parse_html_to_tree(
    html: str,
) -> HtmlElement | None:
    """Parse HTML string to lxml tree."""
    try:
        from lxml import html as lxml_html

        return lxml_html.fromstring(html)
    except Exception:
        logger.warning("Failed to parse document HTML")
        return None


def _extract_text_blocks(
    tree: HtmlElement,
) -> list[tuple[str, str]]:
    """Extract (heading, text) blocks from HTML."""
    blocks: list[tuple[str, str]] = []
    heading_tags = {"h1", "h2", "h3", "h4", "h5", "h6"}

    body = tree.find(".//body")
    root = body if body is not None else tree

    current_heading = ""
    current_text: list[str] = []

    for el in root.iter():
        tag = el.tag if isinstance(el.tag, str) else ""
        if tag in heading_tags:
            if current_heading or current_text:
                blocks.append((
                    current_heading,
                    "\n".join(current_text).strip(),
                ))
            current_heading = (
                el.text_content().strip()
            )
            current_text = []
        elif tag in ("p", "div", "li", "td"):
            txt = el.text_content().strip()
            if txt:
                current_text.append(txt)

    if current_heading or current_text:
        blocks.append((
            current_heading,
            "\n".join(current_text).strip(),
        ))

    return blocks


def _classify_pil_section(heading: str) -> str:
    """Map PIL heading to section key."""
    lower = heading.lower()
    for pattern, key in _PIL_SECTIONS.items():
        if re.search(pattern, lower):
            return key
    return heading.lower().replace(" ", "_")[:30]


def _parse_pil_sections(
    blocks: list[tuple[str, str]],
) -> list[DocumentSection]:
    """Parse PIL blocks into DocumentSection list."""
    sections: list[DocumentSection] = []
    for heading, text in blocks:
        if not text:
            continue
        section_id = _classify_pil_section(heading)
        sections.append(DocumentSection(
            section_id=section_id,
            title=heading,
            content=text,
        ))
    return sections


def _parse_spc_sections(
    blocks: list[tuple[str, str]],
) -> list[DocumentSection]:
    """Parse SPC blocks into DocumentSection list."""
    sections: list[DocumentSection] = []
    for heading, text in blocks:
        if not text:
            continue
        m = _SPC_SECTION_RE.match(heading)
        if m:
            section_id = m.group(1)
            title = m.group(2).strip()
        else:
            section_id = heading[:10]
            title = heading
        sections.append(DocumentSection(
            section_id=section_id,
            title=title,
            content=text,
        ))
    return sections


def _filter_sections(
    sections: list[DocumentSection],
    section_filter: str | None,
) -> list[DocumentSection]:
    """Filter sections by ID prefix match."""
    if not section_filter:
        return sections
    return [
        s
        for s in sections
        if s.section_id.startswith(section_filter)
    ]


# -------------------------------------------------------
# Enhanced PIL/SPC getters
# -------------------------------------------------------


async def _sukl_document_getter(
    sukl_code: str,
    doc_type: str,
    section: str | None = None,
) -> str:
    """Get a SUKL document (SmPC or PIL).

    Args:
        sukl_code: SUKL drug code.
        doc_type: ``"spc"`` or ``"pil"``.
        section: Optional section filter.

    Returns dual output JSON.
    """
    label = "SPC" if doc_type == "spc" else "PIL"

    detail = await _fetch_drug_detail(sukl_code)
    if not detail:
        return json.dumps(
            {"error": f"Drug not found: {sukl_code}"},
            ensure_ascii=False,
        )

    doc_meta = await _fetch_doc_metadata(
        sukl_code, typ=doc_type
    )
    name = detail.get("nazev", "")

    if not doc_meta:
        return json.dumps(
            {
                "error": (
                    f"{label} not available "
                    f"for {sukl_code}"
                ),
                "sukl_code": sukl_code,
                "name": name,
                "source": "SUKL",
            },
            ensure_ascii=False,
        )

    doc_url = _build_doc_url(sukl_code, doc_type)
    sections = await _scrape_document(
        doc_url, doc_type
    )
    sections = _filter_sections(sections, section)

    full_text = "\n\n".join(
        f"## {s.title}\n{s.content}" for s in sections
    ) if sections else None

    model = DocumentContent(
        sukl_code=sukl_code,
        document_type=label,
        title=name,
        sections=sections,
        full_text=full_text,
        url=doc_url,
    )

    md = _format_doc_markdown(model, section)
    return format_czech_response(
        data=model.model_dump(),
        tool_name=f"get_{doc_type}",
        markdown_template=md,
    )


async def _scrape_document(
    doc_url: str, doc_type: str
) -> list[DocumentSection]:
    """Scrape and parse a SUKL document."""
    html = await _fetch_doc_html(doc_url)
    if not html:
        return []

    tree = _parse_html_to_tree(html)
    if tree is None:
        return []

    blocks = _extract_text_blocks(tree)
    if doc_type == "pil":
        return _parse_pil_sections(blocks)
    return _parse_spc_sections(blocks)


def _format_doc_markdown(
    doc: DocumentContent,
    section_filter: str | None,
) -> str:
    """Format document as Markdown."""
    lines = [
        f"## {doc.document_type}: {doc.title}",
        "",
    ]
    if section_filter:
        lines.append(
            f"*Filtr sekce: {section_filter}*\n"
        )

    if doc.sections:
        for s in doc.sections:
            lines.extend([
                f"### {s.title}",
                "",
                s.content,
                "",
            ])
    else:
        lines.append(
            f"Dokument dostupný na: {doc.url}"
        )

    lines.extend([
        "---",
        f"*Zdroj: {doc.source} | Kód: "
        f"{doc.sukl_code}*",
    ])
    return "\n".join(lines)


async def _sukl_spc_getter(
    sukl_code: str, section: str | None = None
) -> str:
    """Get Summary of Product Characteristics."""
    return await _sukl_document_getter(
        sukl_code, "spc", section
    )


async def _sukl_pil_getter(
    sukl_code: str, section: str | None = None
) -> str:
    """Get Patient Information Leaflet (PIL)."""
    return await _sukl_document_getter(
        sukl_code, "pil", section
    )
