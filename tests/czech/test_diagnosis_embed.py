"""Tests for diagnosis_embed: symptom map and searcher."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from czechmedmcp.czech.diagnosis_embed.searcher import (
    _is_mkn_code,
    _merge_candidates,
    _split_symptoms,
    search_diagnoses,
)
from czechmedmcp.czech.diagnosis_embed.symptom_map import (
    fuzzy_lookup_symptom,
    lookup_symptom,
    normalize_symptom,
)

# ── symptom_map unit tests ─────────────────────────────


class TestNormalizeSymptom:
    """Test normalize_symptom()."""

    def test_strips_diacritics(self):
        assert normalize_symptom("horečka") == "horecka"

    def test_lowercases(self):
        assert normalize_symptom("Bolest") == "bolest"

    def test_strips_whitespace(self):
        assert normalize_symptom("  kašel  ") == "kasel"

    def test_combined(self):
        assert (
            normalize_symptom("  Bolest Hlavy  ")
            == "bolest hlavy"
        )


class TestLookupSymptom:
    """Test exact lookup in symptom map."""

    def test_czech_exact(self):
        codes = lookup_symptom("bolest hlavy")
        assert codes is not None
        assert "R51" in codes

    def test_english_exact(self):
        codes = lookup_symptom("headache")
        assert codes is not None
        assert "R51" in codes

    def test_with_diacritics(self):
        codes = lookup_symptom("horečka")
        assert codes is not None
        assert "R50" in codes

    def test_case_insensitive(self):
        codes = lookup_symptom("BOLEST HLAVY")
        assert codes is not None

    def test_unknown_returns_none(self):
        assert lookup_symptom("xyznonexistent") is None


class TestFuzzyLookup:
    """Test fuzzy/substring lookup."""

    def test_substring_match(self):
        results = fuzzy_lookup_symptom("bolest")
        assert len(results) > 0
        # Should match "bolest hlavy", "bolest zad", etc.
        keys = [k for k, _ in results]
        assert any("bolest" in k for k in keys)

    def test_short_input_returns_empty(self):
        assert fuzzy_lookup_symptom("ab") == []

    def test_no_match(self):
        assert fuzzy_lookup_symptom("xyznonexist") == []


# ── searcher unit tests ─────────────────────────────────


class TestSplitSymptoms:
    """Test _split_symptoms()."""

    def test_comma_split(self):
        tokens = _split_symptoms("bolest hlavy, horečka")
        assert tokens == ["bolest hlavy", "horečka"]

    def test_semicolon_split(self):
        tokens = _split_symptoms("kašel; dušnost")
        assert tokens == ["kašel", "dušnost"]

    def test_mixed_separators(self):
        tokens = _split_symptoms("a, b; c")
        assert len(tokens) == 3

    def test_strips_whitespace(self):
        tokens = _split_symptoms("  a ,  b  ")
        assert tokens == ["a", "b"]

    def test_empty_tokens_removed(self):
        tokens = _split_symptoms(",,,")
        assert tokens == []


class TestIsMknCode:
    """Test _is_mkn_code()."""

    def test_three_char(self):
        assert _is_mkn_code("J06") is True

    def test_dotted(self):
        assert _is_mkn_code("J06.9") is True

    def test_range(self):
        assert _is_mkn_code("A00-B99") is True

    def test_word_is_not_code(self):
        assert _is_mkn_code("bolest") is False

    def test_empty(self):
        assert _is_mkn_code("") is False


class TestMergeCandidates:
    """Test _merge_candidates()."""

    def test_deduplication(self):
        raw = [
            {
                "code": "R51",
                "name_cs": "Bolest hlavy",
                "score": 1.0,
                "match_type": "exact_map",
            },
            {
                "code": "R51",
                "name_cs": "",
                "score": 0.7,
                "match_type": "fuzzy_map",
            },
        ]
        merged = _merge_candidates(raw)
        assert len(merged) == 1
        assert merged[0]["code"] == "R51"
        assert merged[0]["score"] == 1.7

    def test_sorted_by_score(self):
        raw = [
            {
                "code": "A",
                "name_cs": "",
                "score": 0.4,
                "match_type": "text",
            },
            {
                "code": "B",
                "name_cs": "",
                "score": 1.0,
                "match_type": "exact_map",
            },
        ]
        merged = _merge_candidates(raw)
        assert merged[0]["code"] == "B"


# ── search_diagnoses integration-like tests ─────────────

MOCK_MKN_RESULT = json.dumps({
    "results": [
        {"code": "R51", "name_cs": "Bolest hlavy NS"},
    ],
    "total": 1,
})


def _patch_mkn(return_value=MOCK_MKN_RESULT):
    return patch(
        "czechmedmcp.czech.diagnosis_embed.searcher"
        "._mkn_search",
        new_callable=AsyncMock,
        return_value=return_value,
    )


class TestSearchDiagnoses:
    """Test search_diagnoses() with mocked MKN search."""

    async def test_czech_symptoms_return_candidates(self):
        with _patch_mkn():
            results = await search_diagnoses(
                "bolest hlavy"
            )
        assert len(results) > 0
        codes = [r["code"] for r in results]
        assert any(
            c.startswith("G4") or c.startswith("R5")
            for c in codes
        )

    async def test_english_symptoms_return_candidates(
        self,
    ):
        with _patch_mkn():
            results = await search_diagnoses("headache")
        assert len(results) > 0

    async def test_combined_cz_en_symptoms(self):
        with _patch_mkn():
            results = await search_diagnoses(
                "bolest hlavy, fever"
            )
        assert len(results) > 0
        codes = [r["code"] for r in results]
        # Should have both headache and fever codes
        has_headache = any(
            c in ("G43", "G44", "R51") for c in codes
        )
        has_fever = any(c == "R50" for c in codes)
        assert has_headache
        assert has_fever

    async def test_mkn_code_input_raises(self):
        with pytest.raises(ValueError, match="detail"):
            await search_diagnoses("J06.9")

    async def test_empty_input_raises(self):
        with pytest.raises(ValueError, match="Zadejte"):
            await search_diagnoses("")

    async def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="Zadejte"):
            await search_diagnoses("   ")

    async def test_unknown_symptom_falls_back_to_text(
        self,
    ):
        """Unknown symptom should fall back to MKN text search."""
        with _patch_mkn():
            results = await search_diagnoses(
                "neznámý příznak"
            )
        # Should still return something via text fallback
        assert isinstance(results, list)

    async def test_max_results_respected(self):
        with _patch_mkn():
            results = await search_diagnoses(
                "bolest hlavy, horečka, kašel", 2
            )
        assert len(results) <= 2

    async def test_candidates_have_required_keys(self):
        with _patch_mkn():
            results = await search_diagnoses("horečka")
        assert len(results) > 0
        for r in results:
            assert "code" in r
            assert "score" in r
            assert "match_type" in r

    async def test_exact_map_scored_highest(self):
        with _patch_mkn():
            results = await search_diagnoses("horečka")
        # First result should be from exact map
        assert results[0]["match_type"] == "exact_map"
        assert results[0]["score"] >= 1.0
