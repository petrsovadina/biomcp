"""Unit tests for NRPZS healthcare provider search (CSV-based)."""

import json

import pytest

_MOCK_PROVIDERS = [
    {
        "ZZ_misto_poskytovani_ID": "12345",
        "ZZ_nazev": "MUDr. Jan Novák",
        "ZZ_obec": "Praha",
        "ZZ_obor_pece": "kardiologie",
        "poskytovatel_nazev": "MUDr. Jan Novák",
    },
    {
        "ZZ_misto_poskytovani_ID": "67890",
        "ZZ_nazev": "Nemocnice Brno",
        "ZZ_obec": "Brno",
        "ZZ_obor_pece": "chirurgie, interna",
        "poskytovatel_nazev": "Nemocnice Brno",
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


class TestNrpzsSearch:
    """Tests for _nrpzs_search function."""

    @pytest.mark.asyncio
    async def test_search_by_city(self):
        from biomcp.czech.nrpzs.search import _nrpzs_search

        result = json.loads(
            await _nrpzs_search(city="Praha")
        )
        assert result["total"] == 1
        assert result["results"][0]["city"] == "Praha"

    @pytest.mark.asyncio
    async def test_search_by_specialty(self):
        from biomcp.czech.nrpzs.search import _nrpzs_search

        result = json.loads(
            await _nrpzs_search(specialty="kardiologie")
        )
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_by_name(self):
        from biomcp.czech.nrpzs.search import _nrpzs_search

        result = json.loads(
            await _nrpzs_search(query="Novák")
        )
        assert result["total"] >= 1
        names = [r["name"] for r in result["results"]]
        assert any("Nov" in n for n in names)

    @pytest.mark.asyncio
    async def test_search_combined_filters(self):
        from biomcp.czech.nrpzs.search import _nrpzs_search

        result = json.loads(
            await _nrpzs_search(
                query="Novák",
                city="Praha",
                specialty="kardiologie",
            )
        )
        assert result["total"] == 1
        assert (
            result["results"][0]["provider_id"] == "12345"
        )

    @pytest.mark.asyncio
    async def test_search_empty_results(self):
        from biomcp.czech.nrpzs.search import _nrpzs_search

        result = json.loads(
            await _nrpzs_search(query="nonexistentxyz")
        )
        assert result["total"] == 0
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_search_diacritics(self):
        from biomcp.czech.nrpzs.search import _nrpzs_search

        result = json.loads(
            await _nrpzs_search(query="Novak")
        )
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_pagination(self):
        from biomcp.czech.nrpzs.search import _nrpzs_search

        result = json.loads(
            await _nrpzs_search(page=1, page_size=1)
        )
        assert result["page"] == 1
        assert result["page_size"] == 1
        assert len(result["results"]) <= 1

    @pytest.mark.asyncio
    async def test_search_error_on_load_failure(self):
        """Load failure returns error JSON."""
        import biomcp.czech.nrpzs.search as mod
        from biomcp.czech.nrpzs.search import _nrpzs_search

        old = mod._PROVIDERS
        mod._PROVIDERS = None
        try:
            from unittest.mock import AsyncMock, patch

            with patch.object(
                mod,
                "_download_csv",
                new_callable=AsyncMock,
                side_effect=Exception("fail"),
            ):
                result = json.loads(
                    await _nrpzs_search(query="test")
                )
            assert "error" in result
        finally:
            mod._PROVIDERS = old
