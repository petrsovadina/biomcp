"""Unit tests for SZV health procedure detail retrieval."""

import json

import pytest

_MOCK_PROCEDURES = [
    {
        "Kód": "09513",
        "Název": "EKG 12ti svodové",
        "Odbornost": "101",
        "Další odbornosti": "102, 103",
        "Celkové": 113,
        "Přímé náklady": 50,
        "Osobní": 40,
        "Režijní": 23,
        "Trvání": 10,
        "Čas nositele": 5,
        "Nositel": "L1",
        "OF": "1x rok",
        "OM": "A",
        "Podmínky výkonu": "EKG přístroj",
        "Poznámka výkonu": "Standardní vyšetření",
        "Popis výkonu": "Popis EKG",
        "ZULP": "",
        "ZUM": "",
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


class TestSzvGetter:
    """Tests for _szv_get function."""

    @pytest.mark.asyncio
    async def test_get_procedure_details(self):
        from biomcp.czech.szv.search import _szv_get

        result = json.loads(await _szv_get("09513"))
        assert result["code"] == "09513"
        assert result["name"] == "EKG 12ti svodové"
        assert result["source"] == "MZCR/SZV"

    @pytest.mark.asyncio
    async def test_get_includes_point_value(self):
        from biomcp.czech.szv.search import _szv_get

        result = json.loads(await _szv_get("09513"))
        assert result["point_value"] == 113

    @pytest.mark.asyncio
    async def test_get_includes_time(self):
        from biomcp.czech.szv.search import _szv_get

        result = json.loads(await _szv_get("09513"))
        assert result["time_minutes"] == 10

    @pytest.mark.asyncio
    async def test_get_includes_specialty(self):
        from biomcp.czech.szv.search import _szv_get

        result = json.loads(await _szv_get("09513"))
        assert result["specialty"] == "101"

    @pytest.mark.asyncio
    async def test_get_invalid_code(self):
        from biomcp.czech.szv.search import _szv_get

        result = json.loads(await _szv_get("INVALID_CODE"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_description(self):
        from biomcp.czech.szv.search import _szv_get

        result = json.loads(await _szv_get("09513"))
        assert result["description"] == "Popis EKG"
