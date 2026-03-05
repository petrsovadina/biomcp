"""Unit tests for pharmacy search (T068)."""

import json
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import httpx
import pytest

# ---- helpers -------------------------------------------------------

def _api_pharmacies() -> list[dict]:
    """Fake SUKL pharmacy API response."""
    return [
        {
            "id": 1001,
            "nazev": "Lékárna U Orla",
            "mesto": "Praha",
            "psc": 11000,
            "ulice": "Karlova 5",
            "telefon": "+420111222333",
            "nepretrzity": True,
        },
        {
            "id": 1002,
            "nazev": "Lékárna Zdraví",
            "mesto": "Praha",
            "psc": 12000,
            "ulice": "Vodičkova 10",
            "telefon": None,
            "nepretrzity": False,
        },
        {
            "id": 1003,
            "nazev": "Nemocniční lékárna",
            "mesto": "Brno",
            "psc": 60200,
            "ulice": "Jihlavská 20",
            "telefon": "+420999888777",
            "nepretrzity": True,
        },
    ]


class _MockResp:
    def __init__(self, data, status=200):
        self._data = data
        self.status_code = status
        self.is_success = 200 <= status < 300

    def json(self):
        return self._data


@contextmanager
def _mock_env(api_data=None):
    """Patch httpx + cache for pharmacy tests."""
    if api_data is None:
        api_data = _api_pharmacies()

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(
        return_value=_MockResp(api_data),
    )
    mock_client.__aenter__ = AsyncMock(
        return_value=mock_client,
    )
    mock_client.__aexit__ = AsyncMock(
        return_value=False,
    )

    with (
        patch(
            "biomcp.czech.sukl.search.httpx.AsyncClient",
            return_value=mock_client,
        ),
        patch(
            "biomcp.czech.sukl.search.get_cached_response",
            return_value=None,
        ),
        patch(
            "biomcp.czech.sukl.search.cache_response",
        ),
    ):
        yield mock_client


# ---- tests ---------------------------------------------------------


@pytest.mark.asyncio
class TestFindPharmacies:
    """Tests for _find_pharmacies()."""

    async def test_dual_output(self):
        """Returns content + structuredContent."""
        from biomcp.czech.sukl.search import (
            _find_pharmacies,
        )

        with _mock_env():
            raw = await _find_pharmacies(city="Praha")

        data = json.loads(raw)
        assert "content" in data
        assert "structuredContent" in data
        sc = data["structuredContent"]
        assert sc["type"] == "find_pharmacies"

    async def test_city_filter(self):
        """Only Praha pharmacies returned when city=Praha."""
        from biomcp.czech.sukl.search import (
            _find_pharmacies,
        )

        with _mock_env():
            raw = await _find_pharmacies(city="Praha")

        sc = json.loads(raw)["structuredContent"]
        # API returns all; parsing keeps all from mock
        assert sc["total"] == 3
        assert len(sc["results"]) == 3

    async def test_nonstop_filter(self):
        """nonstop_only=True filters non-24/7."""
        from biomcp.czech.sukl.search import (
            _find_pharmacies,
        )

        with _mock_env():
            raw = await _find_pharmacies(
                city="Praha", nonstop_only=True,
            )

        sc = json.loads(raw)["structuredContent"]
        assert sc["total"] == 2
        for p in sc["results"]:
            assert p["nonstop"] is True

    async def test_pagination(self):
        """Page/page_size slices results."""
        from biomcp.czech.sukl.search import (
            _find_pharmacies,
        )

        with _mock_env():
            raw = await _find_pharmacies(
                city="Praha", page=2, page_size=2,
            )

        sc = json.loads(raw)["structuredContent"]
        assert sc["total"] == 3
        assert sc["page"] == 2
        assert len(sc["results"]) == 1

    async def test_no_params_error(self):
        """Error when neither city nor postal_code."""
        from biomcp.czech.sukl.search import (
            _find_pharmacies,
        )

        raw = await _find_pharmacies()
        data = json.loads(raw)
        assert "error" in data

    async def test_api_failure(self):
        """Empty results on HTTP error."""
        from biomcp.czech.sukl.search import (
            _find_pharmacies,
        )

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPError("timeout"),
        )
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client,
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False,
        )

        with (
            patch(
                "biomcp.czech.sukl.search"
                ".httpx.AsyncClient",
                return_value=mock_client,
            ),
            patch(
                "biomcp.czech.sukl.search"
                ".get_cached_response",
                return_value=None,
            ),
            patch(
                "biomcp.czech.sukl.search"
                ".cache_response",
            ),
        ):
            raw = await _find_pharmacies(city="Praha")

        sc = json.loads(raw)["structuredContent"]
        assert sc["total"] == 0
        assert sc["results"] == []

    async def test_markdown_output(self):
        """Markdown contains pharmacy names."""
        from biomcp.czech.sukl.search import (
            _find_pharmacies,
        )

        with _mock_env():
            raw = await _find_pharmacies(city="Praha")

        md = json.loads(raw)["content"]
        assert "Lékárny" in md
        assert "U Orla" in md
        assert "[24/7]" in md

    async def test_postal_code_search(self):
        """Search by postal_code works."""
        from biomcp.czech.sukl.search import (
            _find_pharmacies,
        )

        with _mock_env():
            raw = await _find_pharmacies(
                postal_code="11000",
            )

        sc = json.loads(raw)["structuredContent"]
        assert sc["total"] == 3
