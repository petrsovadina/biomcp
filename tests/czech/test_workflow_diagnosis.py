"""Tests for diagnosis assistant workflow."""

import json
from unittest.mock import AsyncMock, patch

from czechmedmcp.czech.workflows.diagnosis_assistant import (
    _diagnosis_assistant,
)

MOCK_MKN_RESULT = json.dumps({
    "results": [
        {"code": "J06.9", "name_cs": "Akutní infekce NS"},
        {"code": "J06.0", "name_cs": "Akutní laryngitis"},
    ],
    "total": 2,
})

MOCK_PUBMED_RESULT = json.dumps([
    {"pmid": "12345", "title": "Acute respiratory infection"},
])


def _patch_mkn():
    """Patch _mkn_search in the searcher module."""
    return patch(
        "czechmedmcp.czech.diagnosis_embed.searcher"
        "._mkn_search",
        new_callable=AsyncMock,
        return_value=MOCK_MKN_RESULT,
    )


def _patch_pubmed(side_effect=None):
    kw: dict = {"return_value": MOCK_PUBMED_RESULT}
    if side_effect is not None:
        kw = {"side_effect": side_effect}
    return patch(
        "czechmedmcp.articles.search._article_searcher",
        new_callable=AsyncMock,
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

    async def test_candidates_from_symptom_map(self):
        """Known symptom should return map candidates."""
        with _patch_mkn(), _patch_pubmed():
            result = await _diagnosis_assistant(
                "bolest hlavy", 5
            )

        sc = json.loads(result)["structuredContent"]
        assert len(sc["candidates"]) > 0
        codes = [c["code"] for c in sc["candidates"]]
        assert any(
            c in ("G43", "G44", "R51") for c in codes
        )

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

        with _patch_mkn(), _patch_pubmed(
            side_effect=_fail
        ):
            result = await _diagnosis_assistant(
                "bolest hlavy"
            )

        sc = json.loads(result)["structuredContent"]
        assert len(sc["candidates"]) > 0

    async def test_query_preserved(self):
        """Original query should be in output."""
        with _patch_mkn(), _patch_pubmed():
            result = await _diagnosis_assistant(
                "horečka"
            )

        sc = json.loads(result)["structuredContent"]
        assert sc["query"] == "horečka"

    async def test_mkn_code_returns_guidance(self):
        """MKN-10 code input should return guidance."""
        result = await _diagnosis_assistant("J06.9")
        parsed = json.loads(result)
        assert "GetDiagnosisDetail" in parsed["content"]

    async def test_empty_input_returns_error(self):
        """Empty input should return guidance."""
        result = await _diagnosis_assistant("")
        parsed = json.loads(result)
        assert "Zadejte" in parsed["content"]

    async def test_english_input_works(self):
        """English symptoms should also find candidates."""
        with _patch_mkn(), _patch_pubmed():
            result = await _diagnosis_assistant(
                "headache, fever"
            )

        sc = json.loads(result)["structuredContent"]
        assert len(sc["candidates"]) > 0

    async def test_no_candidates_shows_message(self):
        """When no candidates found, show guidance."""
        mock_empty = json.dumps({
            "results": [], "total": 0,
        })
        with _patch_mkn() as m:
            m.return_value = mock_empty
            result = await _diagnosis_assistant(
                "xyznonexistent"
            )

        parsed = json.loads(result)
        # Should still return valid structure
        assert "structuredContent" in parsed
        # Content should mention no results
        content = parsed["content"]
        assert (
            "Nebyly nalezeny" in content
            or "upřesnit" in content
        )
