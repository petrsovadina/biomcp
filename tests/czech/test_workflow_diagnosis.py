"""Tests for diagnosis assistant workflow."""

import json
from unittest.mock import patch

from czechmedmcp.czech.workflows.diagnosis_assistant import (
    _diagnosis_assistant,
)

MOCK_MKN_RESULT = json.dumps({
    "results": [
        {"code": "J06.9", "name": "Akutní infekce NS"},
        {"code": "J06.0", "name": "Akutní laryngitis"},
    ]
})

MOCK_PUBMED_RESULT = json.dumps([
    {"pmid": "12345", "title": "Acute respiratory infection"},
])


def _patch_mkn():
    return patch(
        "czechmedmcp.czech.workflows."
        "diagnosis_assistant._mkn_search",
        return_value=MOCK_MKN_RESULT,
    )


def _patch_pubmed(side_effect=None):
    kw = {"return_value": MOCK_PUBMED_RESULT}
    if side_effect is not None:
        kw = {"side_effect": side_effect}
    return patch(
        "czechmedmcp.articles.search._article_searcher",
        **kw,
    )


class TestDiagnosisAssistant:
    """Test _diagnosis_assistant() workflow."""

    async def test_returns_dual_output(self):
        """Result must have content + structuredContent."""
        with _patch_mkn(), _patch_pubmed():
            result = await _diagnosis_assistant(
                "bolest v krku"
            )

        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    async def test_candidates_from_mkn(self):
        """Should return MKN candidates."""
        with _patch_mkn(), _patch_pubmed():
            result = await _diagnosis_assistant(
                "bolest v krku", 2
            )

        sc = json.loads(result)["structuredContent"]
        assert len(sc["candidates"]) == 2
        assert sc["candidates"][0]["code"] == "J06.9"

    async def test_disclaimer_present(self):
        """Disclaimer must be in both content and data."""
        with _patch_mkn(), _patch_pubmed():
            result = await _diagnosis_assistant("kašel")

        parsed = json.loads(result)
        assert "disclaimer" in parsed["structuredContent"]
        assert "pomůcka" in parsed["content"]

    async def test_graceful_pubmed_failure(self):
        """Should work even when PubMed fails."""

        async def _fail(*a, **kw):
            raise ConnectionError("PubMed down")

        with _patch_mkn(), _patch_pubmed(side_effect=_fail):
            result = await _diagnosis_assistant(
                "bolest hlavy"
            )

        sc = json.loads(result)["structuredContent"]
        assert len(sc["candidates"]) > 0

    async def test_query_preserved(self):
        """Original query should be in output."""
        with _patch_mkn(), _patch_pubmed():
            result = await _diagnosis_assistant("horečka")

        sc = json.loads(result)["structuredContent"]
        assert sc["query"] == "horečka"
