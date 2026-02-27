"""Unit tests for VZP insurance codebook detail retrieval."""

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
]


@pytest.fixture(autouse=True)
def inject_entries():
    """Inject mock data into module-level cache."""
    import biomcp.czech.vzp.search as mod

    old = mod._ENTRIES
    mod._ENTRIES = list(_MOCK_ENTRIES)
    yield
    mod._ENTRIES = old


class TestVzpGetter:
    """Tests for _vzp_get function."""

    @pytest.mark.asyncio
    async def test_get_entry(self):
        from biomcp.czech.vzp.search import _vzp_get

        result = json.loads(
            await _vzp_get("seznam_vykonu", "09513")
        )
        assert result["code"] == "09513"
        assert result["name"] == "EKG"
        assert result["source"] == "VZP"

    @pytest.mark.asyncio
    async def test_get_entry_description(self):
        from biomcp.czech.vzp.search import _vzp_get

        result = json.loads(
            await _vzp_get("seznam_vykonu", "09513")
        )
        assert result["description"] == "Elektrokardiografie"

    @pytest.mark.asyncio
    async def test_get_codebook_type_preserved(self):
        from biomcp.czech.vzp.search import _vzp_get

        result = json.loads(
            await _vzp_get("seznam_vykonu", "09513")
        )
        assert result["codebook_type"] == "seznam_vykonu"

    @pytest.mark.asyncio
    async def test_get_invalid_entry(self):
        from biomcp.czech.vzp.search import _vzp_get

        result = json.loads(
            await _vzp_get("seznam_vykonu", "INVALID")
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_point_value(self):
        from biomcp.czech.vzp.search import _vzp_get

        result = json.loads(
            await _vzp_get("seznam_vykonu", "09513")
        )
        assert result["point_value"] == "113"

    @pytest.mark.asyncio
    async def test_get_specialty(self):
        from biomcp.czech.vzp.search import _vzp_get

        result = json.loads(
            await _vzp_get("seznam_vykonu", "09513")
        )
        assert result["specialty"] == "101"
