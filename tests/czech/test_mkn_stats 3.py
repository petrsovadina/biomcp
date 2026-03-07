"""Tests for MKN-10 diagnosis statistics."""

import json
from unittest.mock import patch

from biomcp.czech.mkn.stats import _get_diagnosis_stats

MOCK_CSV = (
    "mkn;nazev;pohlavi;vekova_skupina;kraj;pocet\n"
    "J06;Akutní infekce;M;0-14;Praha;1000\n"
    "J06;Akutní infekce;Z;0-14;Praha;1200\n"
    "J06;Akutní infekce;M;15-24;Brno;500\n"
    "J06.9;Akutní infekce NS;Z;25-34;Praha;300\n"
    "A00;Cholera;M;15-24;Praha;10\n"
)


def _patch_nzip(csv_text=MOCK_CSV, status=200):
    """Patch httpx for NZIP CSV fetch."""

    class MockResp:
        is_success = 200 <= status < 300
        text = csv_text
        status_code = status

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def get(self, url, **kw):
            return MockResp()

    return patch(
        "biomcp.czech.mkn.stats.httpx.AsyncClient",
        return_value=MockClient(),
    )


class TestGetDiagnosisStats:
    """Test _get_diagnosis_stats() function."""

    async def test_returns_dual_output(self):
        """Result must have content + structuredContent."""
        with (
            patch(
                "biomcp.czech.mkn.stats."
                "get_cached_response",
                return_value=None,
            ),
            patch(
                "biomcp.czech.mkn.stats.cache_response"
            ),
            _patch_nzip(),
        ):
            result = await _get_diagnosis_stats("J06", 2024)

        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    async def test_aggregates_total(self):
        """Total cases should sum matching rows."""
        with (
            patch(
                "biomcp.czech.mkn.stats."
                "get_cached_response",
                return_value=None,
            ),
            patch(
                "biomcp.czech.mkn.stats.cache_response"
            ),
            _patch_nzip(),
        ):
            result = await _get_diagnosis_stats("J06", 2024)

        sc = json.loads(result)["structuredContent"]
        # J06 + J06.9 rows: 1000+1200+500+300 = 3000
        assert sc["total_cases"] == 3000
        assert sc["code"] == "J06"

    async def test_gender_breakdown(self):
        """Male/female counts should be aggregated."""
        with (
            patch(
                "biomcp.czech.mkn.stats."
                "get_cached_response",
                return_value=None,
            ),
            patch(
                "biomcp.czech.mkn.stats.cache_response"
            ),
            _patch_nzip(),
        ):
            result = await _get_diagnosis_stats("J06", 2024)

        sc = json.loads(result)["structuredContent"]
        # M: 1000+500=1500, Z: 1200+300=1500
        assert sc["male_count"] == 1500
        assert sc["female_count"] == 1500

    async def test_does_not_match_other_codes(self):
        """A00 should not be included in J06 stats."""
        with (
            patch(
                "biomcp.czech.mkn.stats."
                "get_cached_response",
                return_value=None,
            ),
            patch(
                "biomcp.czech.mkn.stats.cache_response"
            ),
            _patch_nzip(),
        ):
            result = await _get_diagnosis_stats("A00", 2024)

        sc = json.loads(result)["structuredContent"]
        assert sc["total_cases"] == 10

    async def test_empty_when_api_fails(self):
        """Should return zero stats on HTTP error."""
        with (
            patch(
                "biomcp.czech.mkn.stats."
                "get_cached_response",
                return_value=None,
            ),
            patch(
                "biomcp.czech.mkn.stats.cache_response"
            ),
            _patch_nzip(status=500),
        ):
            result = await _get_diagnosis_stats("J06", 2024)

        sc = json.loads(result)["structuredContent"]
        assert sc["total_cases"] == 0

    async def test_markdown_content(self):
        """Content should contain Czech stats."""
        with (
            patch(
                "biomcp.czech.mkn.stats."
                "get_cached_response",
                return_value=None,
            ),
            patch(
                "biomcp.czech.mkn.stats.cache_response"
            ),
            _patch_nzip(),
        ):
            result = await _get_diagnosis_stats("J06", 2024)

        content = json.loads(result)["content"]
        assert "Statistika" in content
        assert "J06" in content
        assert "3,000" in content or "3000" in content
