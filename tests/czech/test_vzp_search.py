"""Unit tests for VZP insurance codebook search (ZIP/CSV-based)."""

import json

import pytest

_MOCK_ENTRIES = [
    {
        "KOD": "09513",
        "NAZ": "EKG",
        "VYS": "Elektrokardiografie",
        "ODB": "101",
        "OME": "A",
        "OMO": "",
        "BOD": "113",
        "PMA": "50",
        "TVY": "10",
        "CTN": "5",
        "PMZ": "",
        "PJP": "",
        "KAT": "P",
        "UMA": "",
        "UBO": "",
        "ZUM": "",
    },
    {
        "KOD": "I10",
        "NAZ": "Esenciální hypertenze",
        "VYS": "Primární hypertenze",
        "ODB": "",
        "OME": "",
        "OMO": "",
        "BOD": "",
        "PMA": "",
        "TVY": "",
        "CTN": "",
        "PMZ": "",
        "PJP": "",
        "KAT": "",
        "UMA": "",
        "UBO": "",
        "ZUM": "",
    },
]


@pytest.fixture(autouse=True)
def inject_entries():
    """Inject mock data into module-level cache."""
    import biomcp.czech.vzp.search as mod

    old = mod._ENTRIES
    mod._ENTRIES = list(_MOCK_ENTRIES)
    yield
    mod._ENTRIES = old


class TestVzpSearch:
    """Tests for _vzp_search function."""

    @pytest.mark.asyncio
    async def test_search_by_code(self):
        from biomcp.czech.vzp.search import _vzp_search

        result = json.loads(
            await _vzp_search("09513", "seznam_vykonu")
        )
        assert result["total"] >= 1
        assert result["results"][0]["code"] == "09513"

    @pytest.mark.asyncio
    async def test_search_by_name(self):
        from biomcp.czech.vzp.search import _vzp_search

        result = json.loads(
            await _vzp_search("EKG", "seznam_vykonu")
        )
        assert result["total"] >= 1
        assert result["results"][0]["name"] == "EKG"

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        from biomcp.czech.vzp.search import _vzp_search

        result = json.loads(
            await _vzp_search(
                "NONEXISTENT99999", "seznam_vykonu"
            )
        )
        assert result["total"] == 0
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_search_result_has_keys(self):
        from biomcp.czech.vzp.search import _vzp_search

        result = json.loads(
            await _vzp_search("09513", "seznam_vykonu")
        )
        entry = result["results"][0]
        for key in ("codebook_type", "code", "name"):
            assert key in entry

    @pytest.mark.asyncio
    async def test_search_without_type(self):
        from biomcp.czech.vzp.search import _vzp_search

        result = json.loads(await _vzp_search("EKG"))
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_respects_max_results(self):
        from biomcp.czech.vzp.search import _vzp_search

        result = json.loads(
            await _vzp_search(
                "EKG", "seznam_vykonu", max_results=1
            )
        )
        assert len(result["results"]) <= 1

    @pytest.mark.asyncio
    async def test_search_diacritics(self):
        from biomcp.czech.vzp.search import _vzp_search

        result = json.loads(
            await _vzp_search(
                "esencialni hypertenze"
            )
        )
        assert result["total"] >= 1
