"""Tests for SUKL batch availability check."""

import json
from unittest.mock import patch

from czechmedmcp.czech.sukl.availability import _batch_availability


def _mock_check_distribution(status_map):
    """Create a mock for _check_distribution."""

    async def _mock(code):
        return status_map.get(code, "unavailable")

    return _mock


def _mock_fetch_detail(name_map):
    """Create a mock for _fetch_drug_detail."""

    async def _mock(code):
        name = name_map.get(code)
        if name:
            return {"kodSUKL": code, "nazev": name}
        return None

    return _mock


class TestBatchAvailability:
    """Test _batch_availability() function."""

    async def test_returns_dual_output(self):
        """Result must have content + structuredContent."""
        with (
            patch(
                "czechmedmcp.czech.sukl.availability."
                "_check_distribution",
                side_effect=_mock_check_distribution(
                    {"0012345": "available"}
                ),
            ),
            patch(
                "czechmedmcp.czech.sukl.availability."
                "_fetch_drug_detail",
                side_effect=_mock_fetch_detail(
                    {"0012345": "Ibuprofen"}
                ),
            ),
        ):
            result = await _batch_availability(["0012345"])

        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    async def test_multiple_codes(self):
        """Should check multiple codes in parallel."""
        codes = ["0012345", "0012346", "0012347"]
        status_map = {
            "0012345": "available",
            "0012346": "available",
            "0012347": "unavailable",
        }
        name_map = {
            "0012345": "Drug A",
            "0012346": "Drug B",
            "0012347": "Drug C",
        }

        with (
            patch(
                "czechmedmcp.czech.sukl.availability."
                "_check_distribution",
                side_effect=_mock_check_distribution(
                    status_map
                ),
            ),
            patch(
                "czechmedmcp.czech.sukl.availability."
                "_fetch_drug_detail",
                side_effect=_mock_fetch_detail(name_map),
            ),
        ):
            result = await _batch_availability(codes)

        sc = json.loads(result)["structuredContent"]
        assert sc["total_checked"] == 3
        assert sc["available_count"] == 2
        assert len(sc["items"]) == 3

    async def test_partial_failure(self):
        """Some codes failing should not break others."""

        async def _fail_one(code):
            if code == "BAD":
                raise ValueError("Invalid code")
            return "available"

        with (
            patch(
                "czechmedmcp.czech.sukl.availability."
                "_check_distribution",
                side_effect=_fail_one,
            ),
            patch(
                "czechmedmcp.czech.sukl.availability."
                "_fetch_drug_detail",
                side_effect=_mock_fetch_detail(
                    {"0012345": "Drug A"}
                ),
            ),
        ):
            result = await _batch_availability(
                ["0012345", "BAD"]
            )

        sc = json.loads(result)["structuredContent"]
        assert sc["total_checked"] == 2
        assert sc["error_count"] >= 1

    async def test_markdown_table(self):
        """Content should contain Markdown table."""
        with (
            patch(
                "czechmedmcp.czech.sukl.availability."
                "_check_distribution",
                side_effect=_mock_check_distribution(
                    {"0012345": "available"}
                ),
            ),
            patch(
                "czechmedmcp.czech.sukl.availability."
                "_fetch_drug_detail",
                side_effect=_mock_fetch_detail(
                    {"0012345": "Ibuprofen"}
                ),
            ),
        ):
            result = await _batch_availability(["0012345"])

        content = json.loads(result)["content"]
        assert "Hromadná kontrola" in content
        assert "0012345" in content
        assert "Ibuprofen" in content

    async def test_single_code(self):
        """Single code should still work."""
        with (
            patch(
                "czechmedmcp.czech.sukl.availability."
                "_check_distribution",
                side_effect=_mock_check_distribution(
                    {"0012345": "available"}
                ),
            ),
            patch(
                "czechmedmcp.czech.sukl.availability."
                "_fetch_drug_detail",
                side_effect=_mock_fetch_detail(
                    {"0012345": "Drug"}
                ),
            ),
        ):
            result = await _batch_availability(["0012345"])

        sc = json.loads(result)["structuredContent"]
        assert sc["total_checked"] == 1
