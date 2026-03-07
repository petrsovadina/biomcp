"""Unit tests for SZV health procedure search (Excel-based)."""

import json

import pytest

_MOCK_PROCEDURES = [
    {
        "Kód": "09513",
        "Název": "EKG 12ti svodové",
        "Odbornost": "101",
        "Celkové": 113,
        "Kategorie": "P",
    },
    {
        "Kód": "12345",
        "Název": "Elektrokardiografické vyšetření",
        "Odbornost": "102",
        "Celkové": 200,
        "Kategorie": "P",
    },
]


@pytest.fixture(autouse=True)
def inject_procedures():
    """Inject mock data into module-level cache."""
    import biomcp.czech.szv.search as mod

    old = mod._PROCEDURES
    mod._PROCEDURES = list(_MOCK_PROCEDURES)
    yield
    mod._PROCEDURES = old


class TestSzvSearch:
    """Tests for _szv_search function."""

    @pytest.mark.asyncio
    async def test_search_by_code(self):
        from biomcp.czech.szv.search import _szv_search

        result = json.loads(await _szv_search("09513"))
        assert result["total"] >= 1
        assert result["results"][0]["code"] == "09513"

    @pytest.mark.asyncio
    async def test_search_by_name(self):
        from biomcp.czech.szv.search import _szv_search

        result = json.loads(await _szv_search("EKG"))
        assert result["total"] >= 1
        assert (
            result["results"][0]["name"]
            == "EKG 12ti svodové"
        )

    @pytest.mark.asyncio
    async def test_search_by_name_partial(self):
        from biomcp.czech.szv.search import _szv_search

        result = json.loads(await _szv_search("svodove"))
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        from biomcp.czech.szv.search import _szv_search

        result = json.loads(
            await _szv_search("XYZNONEXISTENT99999")
        )
        assert result["total"] == 0
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_search_result_has_keys(self):
        from biomcp.czech.szv.search import _szv_search

        result = json.loads(await _szv_search("09513"))
        entry = result["results"][0]
        for key in ("code", "name", "point_value", "category"):
            assert key in entry

    @pytest.mark.asyncio
    async def test_search_diacritics(self):
        from biomcp.czech.szv.search import _szv_search

        result = json.loads(
            await _szv_search(
                "elektrokardiograficke vysetreni"
            )
        )
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_respects_max_results(self):
        from biomcp.czech.szv.search import _szv_search

        result = json.loads(
            await _szv_search("EKG", max_results=1)
        )
        assert len(result["results"]) <= 1

    @pytest.mark.asyncio
    async def test_search_error_on_load_failure(self):
        import biomcp.czech.szv.search as mod
        from biomcp.czech.szv.search import _szv_search

        old = mod._PROCEDURES
        mod._PROCEDURES = None
        try:
            from unittest.mock import AsyncMock, patch

            with patch.object(
                mod,
                "_download_excel",
                new_callable=AsyncMock,
                side_effect=Exception("fail"),
            ):
                result = json.loads(
                    await _szv_search("EKG")
                )
            assert "error" in result
        finally:
            mod._PROCEDURES = old
