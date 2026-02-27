"""MKN-10 search, lookup, and hierarchy browsing.

Provides three public async functions:
- _mkn_search: free-text or code-based search
- _mkn_get: full diagnosis detail by code
- _mkn_browse: hierarchy navigation

All functions return a JSON string. Data is auto-loaded from
MZ ČR open data CSV on first use.
"""

import json
import logging
import re

from biomcp.czech.diacritics import normalize_query
from biomcp.czech.mkn.parser import CodeIndex, TextIndex, load_mkn10

logger = logging.getLogger(__name__)

# MKN-10 codes: "J06", "J06.9", "A00-B99" etc.
_CODE_RE = re.compile(
    r"^[A-Z]\d{2}(?:\.\d{1,2})?$"
    r"|^[A-Z]\d{2}-[A-Z]\d{2}$",
    re.IGNORECASE,
)

# Module-level cache for parsed indices (reset per process).
_INDEX_CACHE: tuple[CodeIndex, TextIndex] | None = None


async def _get_index() -> tuple[CodeIndex, TextIndex]:
    """Return cached or freshly loaded (code_index, text_index)."""
    global _INDEX_CACHE
    if _INDEX_CACHE is None:
        _INDEX_CACHE = await load_mkn10()
    return _INDEX_CACHE


def _resolve_hierarchy(
    code: str,
    code_index: CodeIndex,
) -> dict | None:
    """Walk up parent links to resolve chapter/block/category."""
    node = code_index.get(code)
    if node is None:
        return None

    chapter_code = ""
    chapter_name = ""
    block_code = ""
    block_name = ""
    category_code = ""

    current = node
    chain: list[dict] = [current]
    while current.get("parent_code"):
        parent = code_index.get(current["parent_code"])
        if parent is None:
            break
        chain.append(parent)
        current = parent

    for ancestor in reversed(chain):
        kind = ancestor.get("kind", "")
        if kind == "chapter":
            chapter_code = ancestor["code"]
            chapter_name = ancestor.get("name_cs", "")
        elif kind == "block":
            block_code = ancestor["code"]
            block_name = ancestor.get("name_cs", "")
        elif kind == "category":
            category_code = ancestor["code"]

    if node.get("kind") == "category" and not category_code:
        category_code = node["code"]

    if not chapter_code:
        return None

    return {
        "chapter": chapter_code,
        "chapter_name": chapter_name,
        "block": block_code,
        "block_name": block_name,
        "category": category_code or code,
    }


def _node_to_diagnosis(
    code: str,
    code_index: CodeIndex,
) -> dict | None:
    """Build a Diagnosis-shaped dict from the code index."""
    node = code_index.get(code)
    if node is None:
        return None

    hierarchy = _resolve_hierarchy(code, code_index)

    return {
        "code": node["code"],
        "name_cs": node.get("name_cs", ""),
        "name_en": None,
        "definition": None,
        "hierarchy": hierarchy,
        "includes": [],
        "excludes": [],
        "modifiers": [],
        "source": "UZIS/MKN-10",
    }


def _search_by_code(
    query: str,
    code_index: CodeIndex,
    max_results: int,
) -> list[dict]:
    """Return nodes whose code starts with the query prefix."""
    upper_q = query.upper()
    results = []
    for code, node in code_index.items():
        if code.upper().startswith(upper_q):
            results.append(node)
            if len(results) >= max_results:
                break
    return results


def _search_by_text(
    query: str,
    code_index: CodeIndex,
    text_index: TextIndex,
    max_results: int,
) -> list[dict]:
    """Full-text search using the inverted text index."""
    normalized = normalize_query(query)
    words = [w for w in normalized.split() if len(w) >= 2]

    if not words:
        return []

    candidate_sets: list[set[str]] = []
    for word in words:
        matching: set[str] = set()
        for indexed_word, codes in text_index.items():
            if word in indexed_word or indexed_word in word:
                matching.update(codes)
        candidate_sets.append(matching)

    if not candidate_sets:
        return []

    candidates = candidate_sets[0]
    for s in candidate_sets[1:]:
        candidates = candidates & s

    results = []
    for code in candidates:
        node = code_index.get(code)
        if node:
            results.append(node)

    results.sort(key=lambda n: n["code"])
    return results[:max_results]


async def _mkn_search(
    query: str,
    max_results: int = 10,
) -> str:
    """Search MKN-10 by code prefix or free text.

    Args:
        query: Code or free-text search string.
        max_results: Maximum number of results to return.

    Returns:
        JSON string: {"results": [...], "total": N, "query": str}
    """
    try:
        code_index, text_index = await _get_index()
    except Exception as exc:
        logger.error("Failed to load MKN-10 data: %s", exc)
        return json.dumps(
            {"error": f"MKN-10 data unavailable: {exc}",
             "results": []},
            ensure_ascii=False,
        )

    stripped = query.strip()
    if _CODE_RE.match(stripped):
        nodes = _search_by_code(
            stripped, code_index, max_results
        )
    else:
        nodes = _search_by_text(
            stripped, code_index, text_index, max_results
        )

    results = [
        {
            "code": n["code"],
            "name_cs": n.get("name_cs", ""),
            "kind": n.get("kind", ""),
        }
        for n in nodes
    ]

    return json.dumps(
        {
            "query": stripped,
            "total": len(results),
            "results": results,
        },
        ensure_ascii=False,
    )


async def _mkn_get(
    code: str,
) -> str:
    """Get full diagnosis details for a single MKN-10 code.

    Args:
        code: Exact MKN-10 code (e.g., "J06.9").

    Returns:
        JSON string with Diagnosis fields, or {"error": ...}.
    """
    try:
        code_index, _ = await _get_index()
    except Exception as exc:
        logger.error("Failed to load MKN-10 data: %s", exc)
        return json.dumps(
            {"error": f"MKN-10 data unavailable: {exc}"},
            ensure_ascii=False,
        )

    diagnosis = _node_to_diagnosis(code.strip(), code_index)
    if diagnosis is None:
        return json.dumps(
            {"error": f"Code not found: {code}"},
            ensure_ascii=False,
        )

    return json.dumps(diagnosis, ensure_ascii=False)


async def _mkn_browse(
    code: str | None = None,
) -> str:
    """Browse the MKN-10 category hierarchy.

    If code is None, returns all root-level chapters.
    If code is provided, returns that node with its immediate
    children expanded.

    Args:
        code: MKN-10 code to browse, or None for root chapters.

    Returns:
        JSON string with hierarchy node(s).
    """
    try:
        code_index, _ = await _get_index()
    except Exception as exc:
        logger.error("Failed to load MKN-10 data: %s", exc)
        return json.dumps(
            {"error": f"MKN-10 data unavailable: {exc}"},
            ensure_ascii=False,
        )

    if code is None:
        chapters = [
            {
                "code": node["code"],
                "name_cs": node.get("name_cs", ""),
                "kind": node.get("kind", ""),
                "children_count": len(node.get("children", [])),
            }
            for node in code_index.values()
            if node.get("kind") == "chapter"
        ]
        chapters.sort(key=lambda n: n["code"])
        return json.dumps(
            {"type": "chapters", "items": chapters},
            ensure_ascii=False,
        )

    node = code_index.get(code.strip())
    if node is None:
        return json.dumps(
            {"error": f"Code not found: {code}"},
            ensure_ascii=False,
        )

    child_nodes = []
    for child_code in node.get("children", []):
        child = code_index.get(child_code)
        if child:
            child_nodes.append({
                "code": child["code"],
                "name_cs": child.get("name_cs", ""),
                "kind": child.get("kind", ""),
                "children_count": len(
                    child.get("children", [])
                ),
            })

    result = {
        "code": node["code"],
        "name_cs": node.get("name_cs", ""),
        "kind": node.get("kind", ""),
        "parent_code": node.get("parent_code"),
        "children": child_nodes,
    }
    return json.dumps(result, ensure_ascii=False)
