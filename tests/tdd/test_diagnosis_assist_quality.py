"""Quality tests for diagnosis assistant (BUG-6).

Verifies that symptom cluster matching produces correct
diagnoses for common clinical presentations:
- Diabetes symptoms -> E11/E10 in top results
- Chest pain + dyspnea -> I21/I20 in top results
- Oncology codes demoted for metabolic queries

Also tests the match_symptom_clusters function directly.
"""

import json
from unittest.mock import AsyncMock, patch

from czechmedmcp.czech.diacritics import normalize_query
from czechmedmcp.czech.mkn.synonyms import (
    has_metabolic_context,
    is_oncology_code,
    match_symptom_clusters,
)
from czechmedmcp.czech.workflows.diagnosis_assistant import (
    _diagnosis_assistant,
)

MOCK_MKN = json.dumps({
    "results": [
        {"code": "R53", "name_cs": "Nevolnost a unava"},
    ],
    "total": 1,
})

MOCK_MKN_E11 = json.dumps({
    "results": [
        {
            "code": "E11",
            "name_cs": "Diabetes mellitus 2. typu",
        },
    ],
    "total": 1,
})

MOCK_PUBMED = json.dumps([
    {"pmid": "12345", "title": "Test article"},
])


def _pm():
    return patch(
        "czechmedmcp.czech.diagnosis_embed.searcher"
        "._mkn_search",
        new_callable=AsyncMock,
        return_value=MOCK_MKN,
    )


def _pp():
    return patch(
        "czechmedmcp.articles.search._article_searcher",
        new_callable=AsyncMock,
        return_value=MOCK_PUBMED,
    )


class TestMatchSymptomClusters:
    """Unit tests for match_symptom_clusters."""

    def test_diabetes_cz_keywords(self):
        q = normalize_query(
            "zizen, caste moceni, unava, "
            "vysoky krevni cukr"
        )
        hits = match_symptom_clusters(q)
        codes = [c for c, _ in hits]
        assert "E11" in codes
        assert "E10" in codes

    def test_diabetes_en_keywords(self):
        q = normalize_query(
            "thirst, frequent urination, fatigue"
        )
        hits = match_symptom_clusters(q)
        codes = [c for c, _ in hits]
        assert "E11" in codes

    def test_chest_pain_cz(self):
        q = normalize_query("bolest na hrudi, dusnost")
        hits = match_symptom_clusters(q)
        codes = [c for c, _ in hits]
        assert "I21" in codes or "I20" in codes

    def test_no_match_single_keyword(self):
        q = normalize_query("zizen")
        hits = match_symptom_clusters(q)
        assert len(hits) == 0

    def test_no_match_unrelated(self):
        q = normalize_query("bolest zubu")
        hits = match_symptom_clusters(q)
        assert len(hits) == 0

    def test_scores_sorted_descending(self):
        q = normalize_query(
            "zizen, moceni, cukr, unava"
        )
        hits = match_symptom_clusters(q)
        scores = [s for _, s in hits]
        assert scores == sorted(scores, reverse=True)

    def test_stroke_keywords(self):
        q = normalize_query(
            "znecitliveni, slabost, porucha reci"
        )
        hits = match_symptom_clusters(q)
        codes = [c for c, _ in hits]
        assert "I63" in codes

    def test_respiratory_cluster(self):
        q = normalize_query("kasel, horecka, dusnost")
        hits = match_symptom_clusters(q)
        codes = [c for c, _ in hits]
        assert "J18" in codes


class TestOncologyDemotion:
    """Tests for oncology code demotion helpers."""

    def test_is_oncology_c_code(self):
        assert is_oncology_code("C84") is True
        assert is_oncology_code("C50") is True

    def test_is_oncology_d_code(self):
        assert is_oncology_code("D05") is True
        assert is_oncology_code("D49") is True

    def test_is_not_oncology_d50_plus(self):
        assert is_oncology_code("D50") is False
        assert is_oncology_code("D64") is False

    def test_is_not_oncology(self):
        assert is_oncology_code("E11") is False
        assert is_oncology_code("I21") is False
        assert is_oncology_code("R53") is False

    def test_metabolic_context_detected(self):
        q = normalize_query(
            "zizen, moceni, vysoky krevni cukr"
        )
        assert has_metabolic_context(q) is True

    def test_metabolic_context_absent(self):
        q = normalize_query("bolest hlavy, horecka")
        assert has_metabolic_context(q) is False


class TestDiagnosisQualityDiabetes:
    """E2E: diabetes symptoms produce E11 in top-5."""

    async def test_diabetes_cz_top5(self):
        with _pm(), _pp():
            raw = await _diagnosis_assistant(
                "zizen, caste moceni, unava, "
                "vysoky krevni cukr"
            )
        sc = json.loads(raw)["structuredContent"]
        codes = [c["code"] for c in sc["candidates"]]
        assert "E11" in codes, (
            f"E11 not in top candidates: {codes}"
        )

    async def test_diabetes_en_top5(self):
        with _pm(), _pp():
            raw = await _diagnosis_assistant(
                "thirst, frequent urination, fatigue"
            )
        sc = json.loads(raw)["structuredContent"]
        codes = [c["code"] for c in sc["candidates"]]
        assert "E11" in codes, (
            f"E11 not in top candidates: {codes}"
        )


class TestDiagnosisQualityCardiac:
    """E2E: chest pain symptoms produce I21/I20 in top-5."""

    async def test_chest_pain_cz_top5(self):
        with _pm(), _pp():
            raw = await _diagnosis_assistant(
                "bolest na hrudi, dusnost"
            )
        sc = json.loads(raw)["structuredContent"]
        codes = [c["code"] for c in sc["candidates"]]
        assert any(
            c in ("I21", "I20") for c in codes
        ), f"I21/I20 not in candidates: {codes}"

    async def test_chest_pain_en_top5(self):
        with _pm(), _pp():
            raw = await _diagnosis_assistant(
                "chest pain, shortness of breath"
            )
        sc = json.loads(raw)["structuredContent"]
        codes = [c["code"] for c in sc["candidates"]]
        assert any(
            c in ("R07", "I20", "I21") for c in codes
        ), f"Cardiac codes not in candidates: {codes}"
