"""Unit tests for NRPZS multi-field provider lookup.

Tests cover:
- Lookup by facility ID (ZZ_misto_poskytovani_ID)
- Lookup by ICO (poskytovatel_ICO)
- Lookup by name substring (ZZ_nazev)
- Not found returns clear error message
"""

import json

import pytest

import czechmedmcp.czech.nrpzs.search as nrpzs_mod
from czechmedmcp.czech.nrpzs.search import _nrpzs_get

_MOCK_PROVIDERS = [
    {
        "ZZ_misto_poskytovani_ID": "10001",
        "ZZ_nazev": "MUDr. Jan Novák",
        "ZZ_obec": "Praha",
        "ZZ_obor_pece": "kardiologie",
        "ZZ_druh_pece": "ambulantní",
        "ZZ_ulice": "Hlavní 1",
        "ZZ_PSC": "11000",
        "ZZ_kraj_nazev": "Praha",
        "poskytovatel_pravni_forma_nazev": (
            "fyzická osoba"
        ),
        "poskytovatel_ICO": "12345678",
        "poskytovatel_telefon": "",
        "poskytovatel_email": "",
        "poskytovatel_web": "",
        "ZZ_forma_pece": "ambulantní",
        "ZZ_druh_nazev": "Ordinace",
        "ZZ_okres_nazev": "Praha",
        "poskytovatel_nazev": "MUDr. Jan Novák",
    },
    {
        "ZZ_misto_poskytovani_ID": "20002",
        "ZZ_nazev": "Nemocnice Na Bulovce",
        "ZZ_obec": "Praha",
        "ZZ_obor_pece": "chirurgie",
        "ZZ_druh_pece": "lůžková",
        "ZZ_ulice": "Budínova 67/2",
        "ZZ_PSC": "18000",
        "ZZ_kraj_nazev": "Praha",
        "poskytovatel_pravni_forma_nazev": (
            "příspěvková organizace"
        ),
        "poskytovatel_ICO": "99887766",
        "poskytovatel_telefon": "+420 111 222",
        "poskytovatel_email": "info@bulovka.cz",
        "poskytovatel_web": "https://bulovka.cz",
        "ZZ_forma_pece": "lůžková",
        "ZZ_druh_nazev": "Nemocnice",
        "ZZ_okres_nazev": "Praha",
        "poskytovatel_nazev": (
            "Nemocnice Na Bulovce"
        ),
    },
]


@pytest.fixture(autouse=True)
def _inject_providers():
    """Inject mock CSV data into module cache."""
    old = nrpzs_mod._PROVIDERS
    nrpzs_mod._PROVIDERS = list(_MOCK_PROVIDERS)
    yield
    nrpzs_mod._PROVIDERS = old


class TestLookupByFacilityId:
    """Lookup by ZZ_misto_poskytovani_ID."""

    async def test_exact_id_match(self):
        result = json.loads(
            await _nrpzs_get("10001")
        )
        assert result["provider_id"] == "10001"
        assert result["name"] == "MUDr. Jan Novák"

    async def test_exact_id_match_second(self):
        result = json.loads(
            await _nrpzs_get("20002")
        )
        assert result["provider_id"] == "20002"
        assert "Bulovce" in result["name"]


class TestLookupByICO:
    """Lookup by poskytovatel_ICO (fallback)."""

    async def test_ico_match(self):
        result = json.loads(
            await _nrpzs_get("12345678")
        )
        assert result["ico"] == "12345678"
        assert result["name"] == "MUDr. Jan Novák"

    async def test_ico_match_second_provider(self):
        result = json.loads(
            await _nrpzs_get("99887766")
        )
        assert result["ico"] == "99887766"
        assert "Bulovce" in result["name"]


class TestLookupByNameSubstring:
    """Lookup by ZZ_nazev substring (last fallback)."""

    async def test_name_substring_match(self):
        result = json.loads(
            await _nrpzs_get("Bulovce")
        )
        assert "Bulovce" in result["name"]
        assert result["provider_id"] == "20002"

    async def test_name_diacritics_insensitive(self):
        result = json.loads(
            await _nrpzs_get("Novak")
        )
        assert result["provider_id"] == "10001"

    async def test_name_case_insensitive(self):
        result = json.loads(
            await _nrpzs_get("nemocnice na bulovce")
        )
        assert result["provider_id"] == "20002"


class TestLookupNotFound:
    """Not found returns clear error message."""

    async def test_not_found_returns_error(self):
        result = json.loads(
            await _nrpzs_get("ZZZZZ_nonexistent")
        )
        assert "error" in result
        assert "not found" in result["error"].lower()

    async def test_error_mentions_search_methods(self):
        result = json.loads(
            await _nrpzs_get("xyz999")
        )
        assert "error" in result
        assert "ICO" in result["error"]
        assert "name" in result["error"]

    async def test_data_unavailable_error(self):
        """Load failure returns error JSON."""
        from unittest.mock import AsyncMock, patch

        old = nrpzs_mod._PROVIDERS
        nrpzs_mod._PROVIDERS = None
        try:
            with patch.object(
                nrpzs_mod,
                "_download_csv",
                new_callable=AsyncMock,
                side_effect=Exception("conn fail"),
            ):
                result = json.loads(
                    await _nrpzs_get("10001")
                )
            assert "error" in result
            assert "unavailable" in result["error"]
        finally:
            nrpzs_mod._PROVIDERS = old
