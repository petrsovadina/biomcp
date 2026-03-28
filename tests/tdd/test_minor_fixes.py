"""Tests for US7 minor fixes (BUG-24, BUG-25).

Covers:
- Czech synonym dictionary lookup
- Synonym integration in MKN search
- Prevalence-based relevance ranking
"""

import json
from unittest.mock import AsyncMock, patch

from czechmedmcp.czech.mkn.synonyms import (
    CZ_MEDICAL_SYNONYMS,
    PREVALENCE_BOOST,
    get_prevalence_boost,
    lookup_synonym,
)

# ---- T049: lookup_synonym tests ----


class TestLookupSynonym:
    """Test the synonym lookup function."""

    def test_cukrovka_returns_diabetes_codes(self):
        result = lookup_synonym("cukrovka")
        assert result == ["E11", "E10"]

    def test_unknown_term_returns_none(self):
        result = lookup_synonym("unknown_term")
        assert result is None

    def test_case_insensitive(self):
        result = lookup_synonym("Cukrovka")
        assert result == ["E11", "E10"]

    def test_diacritics_stripped(self):
        """Query with diacritics should still match."""
        result = lookup_synonym("Astma")
        assert result == ["J45"]

    def test_vysoky_tlak(self):
        result = lookup_synonym("vysoky tlak")
        assert result == ["I10"]

    def test_infarkt(self):
        result = lookup_synonym("infarkt")
        assert result == ["I21"]

    def test_rakovina(self):
        result = lookup_synonym("rakovina")
        assert result == ["C80"]

    def test_zapal_plic(self):
        result = lookup_synonym("zapal plic")
        assert result == ["J18"]

    def test_alergie(self):
        result = lookup_synonym("alergie")
        assert result == ["T78.4"]

    def test_returns_new_list_not_reference(self):
        """Returned list should be a copy."""
        r1 = lookup_synonym("cukrovka")
        r2 = lookup_synonym("cukrovka")
        assert r1 is not r2

    def test_at_least_50_entries(self):
        assert len(CZ_MEDICAL_SYNONYMS) >= 50


# ---- T046: prevalence boost tests ----


class TestPrevalenceBoost:
    """Test prevalence-based ranking."""

    def test_e11_higher_than_e10(self):
        assert get_prevalence_boost("E11") > (
            get_prevalence_boost("E10")
        )

    def test_unknown_code_returns_default(self):
        assert get_prevalence_boost("Z99.9") == 1.0

    def test_dotted_code_uses_prefix(self):
        assert get_prevalence_boost("E11.9") == (
            get_prevalence_boost("E11")
        )

    def test_prevalence_boost_has_entries(self):
        assert len(PREVALENCE_BOOST) > 10


# ---- T045/T049: MKN search synonym integration ----


def _make_code_index():
    """Build a minimal code index for testing."""
    return {
        "E11": {
            "code": "E11",
            "name_cs": "Diabetes mellitus 2. typu",
            "kind": "category",
            "parent_code": "E10-E14",
            "children": [],
        },
        "E10": {
            "code": "E10",
            "name_cs": "Diabetes mellitus 1. typu",
            "kind": "category",
            "parent_code": "E10-E14",
            "children": [],
        },
        "I10": {
            "code": "I10",
            "name_cs": "Esenciální hypertenze",
            "kind": "category",
            "parent_code": "I10-I15",
            "children": [],
        },
        "J45": {
            "code": "J45",
            "name_cs": "Astma",
            "kind": "category",
            "parent_code": "J40-J47",
            "children": [],
        },
    }


def _make_text_index():
    """Build a minimal text index for testing."""
    return {
        "diabetes": ["E10", "E11"],
        "mellitus": ["E10", "E11"],
        "hypertenze": ["I10"],
        "astma": ["J45"],
    }


class TestMknSearchSynonymIntegration:
    """Test that _mkn_search uses synonym lookup."""

    async def test_synonym_results_come_first(self):
        """Synonym codes should appear before text hits."""
        from czechmedmcp.czech.mkn.search import _mkn_search

        ci = _make_code_index()
        ti = _make_text_index()

        with patch(
            "czechmedmcp.czech.mkn.search._get_index",
            new_callable=AsyncMock,
            return_value=(ci, ti),
        ):
            raw = await _mkn_search("cukrovka")
            data = json.loads(raw)

        codes = [r["code"] for r in data["results"]]
        # E11 and E10 from synonyms should be present
        assert "E11" in codes
        assert "E10" in codes
        # E11 must come before E10 (synonym order)
        assert codes.index("E11") < codes.index("E10")

    async def test_unknown_query_falls_through(self):
        """Query with no synonym match uses text search."""
        from czechmedmcp.czech.mkn.search import _mkn_search

        ci = _make_code_index()
        ti = _make_text_index()

        with patch(
            "czechmedmcp.czech.mkn.search._get_index",
            new_callable=AsyncMock,
            return_value=(ci, ti),
        ):
            raw = await _mkn_search("astma")
            data = json.loads(raw)

        codes = [r["code"] for r in data["results"]]
        assert "J45" in codes

    async def test_prevalence_ranking_diabetes(self):
        """For 'diabetes' text search, E11 should rank
        before E10 due to prevalence boost."""
        from czechmedmcp.czech.mkn.search import _mkn_search

        ci = _make_code_index()
        ti = _make_text_index()

        with patch(
            "czechmedmcp.czech.mkn.search._get_index",
            new_callable=AsyncMock,
            return_value=(ci, ti),
        ):
            raw = await _mkn_search("diabetes")
            data = json.loads(raw)

        codes = [r["code"] for r in data["results"]]
        assert "E11" in codes
        assert "E10" in codes
        # E11 (T2DM) should rank before E10 (T1DM)
        assert codes.index("E11") < codes.index("E10")
