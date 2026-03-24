"""Unit tests for SZV error handling and Excel download.

Tests cover:
- Successful Excel parse with mocked binary
- Search by code and text
- Timeout returns error JSON (not exception)
- HTTP 504 returns error JSON
"""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

import czechmedmcp.czech.szv.search as szv_mod
from czechmedmcp.czech.szv.search import (
    _szv_get,
    _szv_search,
)

_MOCK_PROCEDURES = [
    {
        "Kód": "09513",
        "Název": "EKG 12ti svodové",
        "Odbornost": "101",
        "Celkové": 113,
        "Kategorie": "P",
        "Popis výkonu": "EKG vyšetření",
    },
    {
        "Kód": "12345",
        "Název": "Odběr krve",
        "Odbornost": "102",
        "Celkové": 50,
        "Kategorie": "P",
        "Popis výkonu": "Odběr venózní krve",
    },
]


@pytest.fixture(autouse=True)
def _reset_cache():
    """Reset module cache before/after each test."""
    old = szv_mod._PROCEDURES
    szv_mod._PROCEDURES = None
    yield
    szv_mod._PROCEDURES = old


def _inject(procs: list[dict] | None = None):
    """Inject mock procedures into module cache."""
    szv_mod._PROCEDURES = (
        list(procs) if procs is not None
        else list(_MOCK_PROCEDURES)
    )


class TestSzvSearchByCode:
    """Search by procedure code."""

    async def test_search_by_code_returns_match(self):
        _inject()
        result = json.loads(await _szv_search("09513"))
        assert result["total"] >= 1
        assert result["results"][0]["code"] == "09513"

    async def test_get_by_code_returns_detail(self):
        _inject()
        result = json.loads(await _szv_get("09513"))
        assert result["code"] == "09513"
        assert result["name"] == "EKG 12ti svodové"
        assert result["source"] == "MZCR/SZV"


class TestSzvSearchByText:
    """Search by name text."""

    async def test_search_by_name(self):
        _inject()
        result = json.loads(await _szv_search("EKG"))
        assert result["total"] >= 1
        assert "EKG" in result["results"][0]["name"]

    async def test_search_by_partial_name(self):
        _inject()
        result = json.loads(
            await _szv_search("odber")
        )
        assert result["total"] >= 1
        assert (
            result["results"][0]["code"] == "12345"
        )

    async def test_search_diacritics_insensitive(self):
        _inject()
        result = json.loads(
            await _szv_search("svodove")
        )
        assert result["total"] >= 1


class TestSzvDownloadTimeout:
    """Download timeout returns error JSON."""

    async def test_timeout_returns_error_json(self):
        with patch.object(
            szv_mod,
            "_download_excel",
            new_callable=AsyncMock,
            side_effect=RuntimeError(
                "SZV server timeout — try again later"
            ),
        ):
            result = json.loads(
                await _szv_search("EKG")
            )
        assert "error" in result
        assert "unavailable" in result["error"]

    async def test_timeout_in_download_excel(self):
        """Actual httpx timeout is wrapped."""
        with patch(
            "czechmedmcp.czech.szv.search"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.szv.search"
            ".httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.side_effect = (
                httpx.TimeoutException("timeout")
            )
            mock_client_cls.return_value.__aenter__ = (
                AsyncMock(return_value=mock_client)
            )
            mock_client_cls.return_value.__aexit__ = (
                AsyncMock(return_value=False)
            )

            from czechmedmcp.czech.szv.search import (
                _download_excel,
            )

            with pytest.raises(RuntimeError, match="timeout"):
                await _download_excel()


class TestSzvHttp504:
    """HTTP 504 returns error JSON."""

    async def test_504_returns_error_json(self):
        with patch.object(
            szv_mod,
            "_download_excel",
            new_callable=AsyncMock,
            side_effect=RuntimeError(
                "SZV server HTTP 504"
            ),
        ):
            result = json.loads(
                await _szv_get("09513")
            )
        assert "error" in result
        assert "unavailable" in result["error"]

    async def test_http_status_error_in_download(self):
        """HTTP status error is wrapped properly."""
        mock_resp = httpx.Response(
            504,
            request=httpx.Request("GET", "http://x"),
        )
        with patch(
            "czechmedmcp.czech.szv.search"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.szv.search"
            ".httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.get.return_value = mock_resp
            mock_client.get.return_value.raise_for_status = (
                lambda: (_ for _ in ()).throw(
                    httpx.HTTPStatusError(
                        "504",
                        request=mock_resp.request,
                        response=mock_resp,
                    )
                )
            )
            mock_client_cls.return_value.__aenter__ = (
                AsyncMock(return_value=mock_client)
            )
            mock_client_cls.return_value.__aexit__ = (
                AsyncMock(return_value=False)
            )

            from czechmedmcp.czech.szv.search import (
                _download_excel,
            )

            with pytest.raises(
                RuntimeError, match="HTTP 504"
            ):
                await _download_excel()


class TestSzvExcelParse:
    """Successful Excel parse with mock data."""

    async def test_parse_populates_cache(self):
        """After _get_procedures, cache is populated."""
        _inject()
        procs = await szv_mod._get_procedures()
        assert len(procs) == 2
        assert szv_mod._PROCEDURES is not None

    async def test_get_nonexistent_code(self):
        _inject()
        result = json.loads(
            await _szv_get("XXXXX")
        )
        assert "error" in result
        assert "not found" in result["error"]
