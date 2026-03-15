"""Tests for SUKL module internal functions to improve coverage."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSuklSearchInternals:
    """Test internal search functions via DrugIndex."""

    def test_search_matches_by_name(self):
        from czechmedmcp.czech.sukl.drug_index import (
            DrugIndex,
            _detail_to_entry,
            search_index,
        )

        entry = _detail_to_entry({
            "kodSUKL": "0000123",
            "nazev": "NUROFEN 400MG",
            "doplnek": "",
            "ATCkod": "",
            "drzitelKod": "",
        })
        idx = DrugIndex()
        idx._entries = [entry]
        idx._built_at = 9999999999.0
        results, total = search_index(idx, "nurofen")
        assert total == 1

    def test_search_matches_by_atc(self):
        from czechmedmcp.czech.sukl.drug_index import (
            DrugIndex,
            _detail_to_entry,
            search_index,
        )

        entry = _detail_to_entry({
            "kodSUKL": "0000123",
            "nazev": "",
            "doplnek": "",
            "ATCkod": "M01AE01",
            "drzitelKod": "",
        })
        idx = DrugIndex()
        idx._entries = [entry]
        idx._built_at = 9999999999.0
        results, total = search_index(idx, "m01ae01")
        assert total == 1

    def test_search_matches_by_holder(self):
        from czechmedmcp.czech.sukl.drug_index import (
            DrugIndex,
            _detail_to_entry,
            search_index,
        )

        entry = _detail_to_entry({
            "kodSUKL": "0000123",
            "nazev": "",
            "doplnek": "",
            "ATCkod": "",
            "drzitelKod": "Reckitt Benckiser",
        })
        idx = DrugIndex()
        idx._entries = [entry]
        idx._built_at = 9999999999.0
        results, total = search_index(idx, "reckitt")
        assert total == 1

    def test_search_no_match(self):
        from czechmedmcp.czech.sukl.drug_index import (
            DrugIndex,
            _detail_to_entry,
            search_index,
        )

        entry = _detail_to_entry({
            "kodSUKL": "0000123",
            "nazev": "ABC",
            "doplnek": "",
            "ATCkod": "",
            "drzitelKod": "",
        })
        idx = DrugIndex()
        idx._entries = [entry]
        idx._built_at = 9999999999.0
        results, total = search_index(idx, "xyz")
        assert total == 0

    def test_search_empty_query(self):
        from czechmedmcp.czech.sukl.drug_index import (
            DrugIndex,
            _detail_to_entry,
            search_index,
        )

        entry = _detail_to_entry({
            "kodSUKL": "0000123",
            "nazev": "TEST",
        })
        idx = DrugIndex()
        idx._entries = [entry]
        idx._built_at = 9999999999.0
        results, total = search_index(idx, "")
        assert total == 0

    def test_entry_to_summary(self):
        from czechmedmcp.czech.sukl.drug_index import (
            _detail_to_entry,
        )
        from czechmedmcp.czech.sukl.search import (
            _entry_to_summary,
        )

        entry = _detail_to_entry({
            "kodSUKL": "0000123",
            "nazev": "NUROFEN",
            "ATCkod": "M01AE01",
            "lekovaFormaKod": "TBL FLM",
        })
        s = _entry_to_summary(entry)
        assert s["sukl_code"] == "0000123"
        assert s["name"] == "NUROFEN"
        assert s["atc_code"] == "M01AE01"


class TestSuklGetterInternals:
    """Test internal getter functions."""

    def test_composition_to_substances(self):
        from czechmedmcp.czech.sukl.getter import (
            _composition_to_substances,
        )

        comp = [
            {
                "kodLatky": 1234,
                "mnozstvi": "400",
                "jednotkaKod": "MG",
            }
        ]
        result = _composition_to_substances(comp)
        assert len(result) == 1
        assert result[0]["substance_code"] == 1234
        assert result[0]["strength"] == "400 MG"

    def test_composition_to_substances_empty(self):
        from czechmedmcp.czech.sukl.getter import (
            _composition_to_substances,
        )

        assert _composition_to_substances([]) == []

    def test_composition_no_amount(self):
        from czechmedmcp.czech.sukl.getter import (
            _composition_to_substances,
        )

        comp = [
            {"kodLatky": 99, "mnozstvi": "", "jednotkaKod": ""}
        ]
        result = _composition_to_substances(comp)
        assert result[0]["strength"] is None

    def test_build_doc_url(self):
        from czechmedmcp.czech.sukl.getter import _build_doc_url

        url = _build_doc_url("0000123", "spc")
        assert "0000123" in url
        assert "spc" in url

    @pytest.mark.asyncio
    async def test_fetch_doc_metadata_404(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_doc_metadata,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 404

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter.get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter.httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_doc_metadata("9999999")
            assert result == []

    @pytest.mark.asyncio
    async def test_fetch_composition_404(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_composition,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 404

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter.get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter.httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_composition("9999999")
            assert result == []


class TestSuklAvailabilityInternals:
    """Test internal availability functions."""

    @pytest.mark.asyncio
    async def test_check_distribution_404(self):
        from czechmedmcp.czech.sukl.availability import (
            _check_distribution,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 404

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.availability.get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.availability.httpx.AsyncClient",
            return_value=mock_client,
        ), patch(
            "czechmedmcp.czech.sukl.availability.cache_response",
        ):
            result = await _check_distribution("9999999")
            assert result == "unavailable"

    @pytest.mark.asyncio
    async def test_check_distribution_success(self):
        from czechmedmcp.czech.sukl.availability import (
            _check_distribution,
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.is_success = True

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.availability.get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.availability.httpx.AsyncClient",
            return_value=mock_client,
        ), patch(
            "czechmedmcp.czech.sukl.availability.cache_response",
        ):
            result = await _check_distribution("0000123")
            assert result == "available"

    @pytest.mark.asyncio
    async def test_check_distribution_cached(self):
        from czechmedmcp.czech.sukl.availability import (
            _check_distribution,
        )

        with patch(
            "czechmedmcp.czech.sukl.availability.get_cached_response",
            return_value=json.dumps(
                {"_status": "limited"}
            ),
        ):
            result = await _check_distribution("0000123")
            assert result == "limited"

    @pytest.mark.asyncio
    async def test_fetch_drug_detail_cached(self):
        from czechmedmcp.czech.sukl.availability import (
            _fetch_drug_detail,
        )

        cached_data = {"kodSukl": "0000123", "nazev": "Test"}
        with patch(
            "czechmedmcp.czech.sukl.client.get_cached_response",
            return_value=json.dumps(cached_data),
        ):
            result = await _fetch_drug_detail("0000123")
            assert result["kodSukl"] == "0000123"
