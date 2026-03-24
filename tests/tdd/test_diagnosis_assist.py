"""TDD tests for diagnosis assistant (US3).

Focused on the end-to-end flow via the public tool
function, testing CZ/EN inputs, code detection, and
error handling.
"""

import json
from unittest.mock import AsyncMock, patch

from czechmedmcp.czech.workflows.diagnosis_assistant import (
    _diagnosis_assistant,
)

MOCK_MKN = json.dumps({
    "results": [
        {"code": "R51", "name_cs": "Bolest hlavy NS"},
    ],
    "total": 1,
})

MOCK_PUBMED = json.dumps([
    {"pmid": "99999", "title": "Test article"},
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


class TestDiagnosisAssistCzech:
    """CZ symptom input."""

    async def test_bolest_hlavy(self):
        with _pm(), _pp():
            raw = await _diagnosis_assistant(
                "bolest hlavy"
            )
        sc = json.loads(raw)["structuredContent"]
        assert len(sc["candidates"]) > 0

    async def test_horecka(self):
        with _pm(), _pp():
            raw = await _diagnosis_assistant("horečka")
        sc = json.loads(raw)["structuredContent"]
        codes = [c["code"] for c in sc["candidates"]]
        assert "R50" in codes

    async def test_kasel_dusnost(self):
        with _pm(), _pp():
            raw = await _diagnosis_assistant(
                "kašel, dušnost"
            )
        sc = json.loads(raw)["structuredContent"]
        assert len(sc["candidates"]) > 0


class TestDiagnosisAssistEnglish:
    """EN symptom input."""

    async def test_headache(self):
        with _pm(), _pp():
            raw = await _diagnosis_assistant("headache")
        sc = json.loads(raw)["structuredContent"]
        assert len(sc["candidates"]) > 0

    async def test_fever_cough(self):
        with _pm(), _pp():
            raw = await _diagnosis_assistant(
                "fever, cough"
            )
        sc = json.loads(raw)["structuredContent"]
        assert len(sc["candidates"]) > 0


class TestDiagnosisAssistEdgeCases:
    """Edge cases and error handling."""

    async def test_mkn_code_returns_guidance(self):
        raw = await _diagnosis_assistant("J06.9")
        parsed = json.loads(raw)
        assert "GetDiagnosisDetail" in parsed["content"]
        sc = parsed["structuredContent"]
        assert len(sc["candidates"]) == 0

    async def test_empty_input(self):
        raw = await _diagnosis_assistant("")
        parsed = json.loads(raw)
        assert "Zadejte" in parsed["content"]

    async def test_code_range_returns_guidance(self):
        raw = await _diagnosis_assistant("A00-B99")
        parsed = json.loads(raw)
        assert "GetDiagnosisDetail" in parsed["content"]

    async def test_combined_cz_en(self):
        with _pm(), _pp():
            raw = await _diagnosis_assistant(
                "bolest hlavy; fever"
            )
        sc = json.loads(raw)["structuredContent"]
        codes = [c["code"] for c in sc["candidates"]]
        assert any(
            c in ("G43", "G44", "R51") for c in codes
        )
        assert "R50" in codes

    async def test_unknown_symptom_handled(self):
        """Unknown symptom should not crash."""
        with _pm(), _pp():
            raw = await _diagnosis_assistant(
                "xyznonexistent"
            )
        parsed = json.loads(raw)
        assert "structuredContent" in parsed
