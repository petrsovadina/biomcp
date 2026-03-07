"""Unit tests for NRPZS healthcare provider getter (CSV-based)."""

import json

import pytest

_MOCK_PROVIDERS = [
    {
        "ZZ_misto_poskytovani_ID": "12345",
        "ZZ_nazev": "MUDr. Jan Novák",
        "ZZ_obec": "Praha",
        "ZZ_obor_pece": "kardiologie",
        "ZZ_druh_pece": "ambulantní",
        "ZZ_ulice": "Hlavní 123",
        "ZZ_PSC": "11000",
        "ZZ_kraj_nazev": "Praha",
        "poskytovatel_pravni_forma_nazev": "fyzická osoba",
        "poskytovatel_ICO": "12345678",
        "poskytovatel_telefon": "+420 123 456 789",
        "poskytovatel_email": "novak@example.cz",
        "poskytovatel_web": "",
        "ZZ_forma_pece": "ambulantní",
        "ZZ_druh_nazev": "Ordinace",
        "ZZ_okres_nazev": "Praha",
        "poskytovatel_nazev": "MUDr. Jan Novák",
    },
]


@pytest.fixture(autouse=True)
def inject_providers():
    """Inject mock data into module-level cache."""
    import biomcp.czech.nrpzs.search as mod

    old = mod._PROVIDERS
    mod._PROVIDERS = list(_MOCK_PROVIDERS)
    yield
    mod._PROVIDERS = old


class TestNrpzsGetter:
    """Tests for _nrpzs_get function."""

    @pytest.mark.asyncio
    async def test_get_provider_details(self):
        from biomcp.czech.nrpzs.search import _nrpzs_get

        result = json.loads(await _nrpzs_get("12345"))
        assert result["provider_id"] == "12345"
        assert result["name"] == "MUDr. Jan Novák"
        assert result["source"] == "NRPZS"

    @pytest.mark.asyncio
    async def test_get_provider_address(self):
        from biomcp.czech.nrpzs.search import _nrpzs_get

        result = json.loads(await _nrpzs_get("12345"))
        address = result["address"]
        assert address is not None
        assert address["street"] == "Hlavní 123"
        assert address["city"] == "Praha"
        assert address["postal_code"] == "11000"

    @pytest.mark.asyncio
    async def test_get_provider_contact(self):
        from biomcp.czech.nrpzs.search import _nrpzs_get

        result = json.loads(await _nrpzs_get("12345"))
        contact = result["contact"]
        assert contact is not None
        assert contact["phone"] == "+420 123 456 789"

    @pytest.mark.asyncio
    async def test_get_invalid_id(self):
        from biomcp.czech.nrpzs.search import _nrpzs_get

        result = json.loads(
            await _nrpzs_get("nonexistent999")
        )
        assert "error" in result
        assert "nonexistent999" in result["error"]

    @pytest.mark.asyncio
    async def test_get_provider_specialties(self):
        from biomcp.czech.nrpzs.search import _nrpzs_get

        result = json.loads(await _nrpzs_get("12345"))
        assert "kardiologie" in result["specialties"]

    @pytest.mark.asyncio
    async def test_get_provider_legal_form(self):
        from biomcp.czech.nrpzs.search import _nrpzs_get

        result = json.loads(await _nrpzs_get("12345"))
        assert result["legal_form"] == "fyzická osoba"
        assert result["ico"] == "12345678"
