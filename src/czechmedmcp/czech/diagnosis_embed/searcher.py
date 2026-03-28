"""Hybrid diagnosis searcher.

Combines four search strategies for symptom→MKN-10 matching:
1. Symptom cluster matching (multi-keyword patterns)
2. Exact lookup in the symptom mapping dictionary
3. Fuzzy/substring lookup in the symptom mapping dictionary
4. Fallback to MKN-10 full-text search (existing _mkn_search)

Scores: cluster = boost (0.80-0.95), exact map = 1.0,
fuzzy = 0.7, text search = 0.4.
Results are merged, deduplicated by code, and ranked.
Oncology codes are demoted when context is metabolic.
"""

import json
import logging
import re

from czechmedmcp.czech.diacritics import normalize_query
from czechmedmcp.czech.diagnosis_embed.symptom_map import (
    fuzzy_lookup_symptom,
    lookup_symptom,
)
from czechmedmcp.czech.mkn.search import _mkn_search
from czechmedmcp.czech.mkn.synonyms import (
    has_metabolic_context,
    is_oncology_code,
    match_symptom_clusters,
)

logger = logging.getLogger(__name__)

# MKN-10 code pattern (e.g. J06, J06.9, A00-B99)
_CODE_RE = re.compile(
    r"^[A-Z]\d{2}(?:\.\d{1,2})?$"
    r"|^[A-Z]\d{2}-[A-Z]\d{2}$",
    re.IGNORECASE,
)

_SCORE_EXACT = 1.0
_SCORE_FUZZY = 0.7
_SCORE_TEXT = 0.4

# Separator pattern for splitting multi-symptom input
_SEP_RE = re.compile(r"[,;]+")


def _is_mkn_code(text: str) -> bool:
    """Check if text looks like an MKN-10 code."""
    return bool(_CODE_RE.match(text.strip()))


def _split_symptoms(symptoms: str) -> list[str]:
    """Split symptom string by commas/semicolons.

    Returns non-empty stripped tokens.
    """
    tokens = _SEP_RE.split(symptoms)
    return [t.strip() for t in tokens if t.strip()]


def _merge_candidates(
    raw: list[dict],
) -> list[dict]:
    """Merge candidates by code, summing scores.

    Keeps the highest match_type priority and best name.
    """
    by_code: dict[str, dict] = {}
    type_priority = {
        "cluster": 4,
        "exact_map": 3,
        "fuzzy_map": 2,
        "text": 1,
    }

    for c in raw:
        code = c["code"]
        if code in by_code:
            existing = by_code[code]
            existing["score"] += c["score"]
            ep = type_priority.get(existing["match_type"], 0)
            cp = type_priority.get(c["match_type"], 0)
            if cp > ep:
                existing["match_type"] = c["match_type"]
            if not existing.get("name_cs") and c.get("name_cs"):
                existing["name_cs"] = c["name_cs"]
        else:
            by_code[code] = dict(c)

    merged = list(by_code.values())
    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged


async def _enrich_with_names(
    candidates: list[dict],
) -> list[dict]:
    """Fill in name_cs for candidates that lack it.

    Uses MKN-10 code search to look up names.
    """
    for c in candidates:
        if c.get("name_cs"):
            continue
        code = c["code"]
        try:
            raw = await _mkn_search(code, 1)
            data = json.loads(raw)
            results = data.get("results", [])
            if results:
                c["name_cs"] = results[0].get(
                    "name_cs", ""
                )
        except Exception:
            logger.debug(
                "Failed to enrich name for %s", code
            )
    return candidates


def _match_exact(token: str) -> list[dict]:
    """Try exact symptom-map lookup for a token."""
    codes = lookup_symptom(token)
    if not codes:
        return []
    return [
        {
            "code": c,
            "name_cs": "",
            "score": _SCORE_EXACT,
            "match_type": "exact_map",
        }
        for c in codes
    ]


def _match_fuzzy(token: str) -> list[dict]:
    """Try fuzzy/substring symptom-map lookup."""
    fuzzy = fuzzy_lookup_symptom(token)
    if not fuzzy:
        return []
    results: list[dict] = []
    for _key, codes_f in fuzzy:
        for code in codes_f:
            results.append({
                "code": code,
                "name_cs": "",
                "score": _SCORE_FUZZY,
                "match_type": "fuzzy_map",
            })
    return results


async def _match_text(token: str) -> list[dict]:
    """Fallback: MKN-10 full-text search."""
    try:
        mkn_raw = await _mkn_search(token, 5)
        mkn_data = json.loads(mkn_raw)
        results = mkn_data.get("results", [])
        return [
            {
                "code": r.get("code", ""),
                "name_cs": r.get("name_cs", ""),
                "score": _SCORE_TEXT,
                "match_type": "text",
            }
            for r in results
        ]
    except Exception:
        logger.warning(
            "MKN search failed for token: %s", token
        )
        return []


def _validate_input(symptoms: str) -> list[str]:
    """Validate and tokenize symptom input.

    Raises ValueError for empty or MKN-code input.
    """
    stripped = symptoms.strip()
    if not stripped:
        raise ValueError(
            "Zadejte popis symptomů (např. "
            "'bolest hlavy, horečka')."
        )

    if _is_mkn_code(stripped):
        raise ValueError(
            "Pro detail diagnózy použijte nástroj "
            "GetDiagnosisDetail s kódem "
            f"'{stripped}'."
        )

    tokens = _split_symptoms(stripped)
    if not tokens:
        raise ValueError(
            "Zadejte popis symptomů (např. "
            "'bolest hlavy, horečka')."
        )
    return tokens


def _match_clusters(
    symptoms: str,
) -> list[dict]:
    """Match symptom clusters on full query string."""
    norm = normalize_query(symptoms)
    hits = match_symptom_clusters(norm)
    return [
        {
            "code": code,
            "name_cs": "",
            "score": score,
            "match_type": "cluster",
        }
        for code, score in hits
    ]


def _demote_oncology(
    candidates: list[dict],
    symptoms: str,
) -> list[dict]:
    """Demote oncology codes when context is metabolic.

    If the query contains metabolic keywords, any C/D0-D4
    codes are pushed to the bottom with halved scores.
    """
    norm = normalize_query(symptoms)
    if not has_metabolic_context(norm):
        return candidates

    keep: list[dict] = []
    demoted: list[dict] = []
    for c in candidates:
        if is_oncology_code(c.get("code", "")):
            c = dict(c)
            c["score"] = c["score"] * 0.5
            demoted.append(c)
        else:
            keep.append(c)

    return keep + demoted


async def search_diagnoses(
    symptoms: str,
    max_results: int = 5,
) -> list[dict]:
    """Search for MKN-10 diagnoses matching symptoms.

    Combines symptom cluster matching, dictionary lookup,
    and MKN-10 full-text search for best coverage.

    Args:
        symptoms: Comma/semicolon-separated symptom text.
        max_results: Maximum candidates to return.

    Returns:
        List of dicts with code, name_cs, score,
        match_type keys.

    Raises:
        ValueError: If symptoms is empty or is an MKN-10
            code (user should use GetDiagnosisDetail).
    """
    tokens = _validate_input(symptoms)
    raw_candidates: list[dict] = []

    # Phase 1: cluster matching on full query
    cluster_hits = _match_clusters(symptoms)
    raw_candidates.extend(cluster_hits)

    # Phase 2: per-token exact/fuzzy/text search
    for token in tokens:
        hits = _match_exact(token)
        if not hits:
            hits = _match_fuzzy(token)
        if not hits:
            hits = await _match_text(token)
        raw_candidates.extend(hits)

    merged = _merge_candidates(raw_candidates)

    # Phase 3: demote oncology codes for metabolic queries
    merged = _demote_oncology(merged, symptoms)

    top = merged[:max_results]

    # Enrich names from MKN-10 for map-sourced entries
    top = await _enrich_with_names(top)

    return top
