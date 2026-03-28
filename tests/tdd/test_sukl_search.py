"""Unit tests for SUKL SearchMedicine / DrugIndex."""

import json
from unittest.mock import patch

import pytest

from czechmedmcp.czech.sukl.drug_index import (
    DrugIndex,
    DrugIndexEntry,
    _detail_to_entry,
    reset_drug_index,
    search_index,
)


def _make_detail(code: str, name: str, atc: str = "M01AE01") -> dict:
    return {
        "kodSUKL": code,
        "nazev": name,
        "sila": "400MG",
        "ATCkod": atc,
        "lekovaFormaKod": "TBL",
        "doplnek": "GALMED",
        "drzitelKod": "GAL001",
    }


def _make_entry(code: str, name: str, atc: str = "M01AE01") -> DrugIndexEntry:
    return _detail_to_entry(_make_detail(code, name, atc))


class TestDrugIndexPersistentCache:
    """T007: Persistent disk cache for DrugIndex."""

    @pytest.fixture(autouse=True)
    def _reset(self):
        reset_drug_index()
        yield
        reset_drug_index()

    async def test_build_persists_to_cache(self):
        """Index build should write to disk cache."""
        idx = DrugIndex()
        codes = ["0000001", "0000002"]
        details = {
            "0000001": _make_detail("0000001", "DrugA"),
            "0000002": _make_detail("0000002", "DrugB"),
        }

        async def mock_fetch_list(*a, **kw):
            return codes

        async def mock_fetch_detail(code, **kw):
            return details.get(code)

        with (
            patch(
                "czechmedmcp.czech.sukl.drug_index._fetch_drug_list",
                side_effect=mock_fetch_list,
            ),
            patch(
                "czechmedmcp.czech.sukl.drug_index.fetch_drug_detail",
                side_effect=mock_fetch_detail,
            ),
            patch(
                "czechmedmcp.czech.sukl.drug_index.cache_response"
            ) as mock_cache,
            patch(
                "czechmedmcp.czech.sukl.drug_index.get_cached_response",
                return_value=None,
            ),
        ):
            await idx.ensure_built()
            assert idx.size == 2
            mock_cache.assert_called_once()

    async def test_build_loads_from_cache(self):
        """Index should load from disk cache without API calls."""
        cached_entries = [
            {
                "sukl_code": "0000001",
                "name": "CachedDrug",
                "name_normalized": "cacheddrug",
                "strength": "100MG",
                "atc_code": "N02BE01",
                "atc_normalized": "n02be01",
                "form": "TBL",
                "supplement": "",
                "supplement_normalized": "",
                "holder_code": "x",
            }
        ]
        idx = DrugIndex()

        with patch(
            "czechmedmcp.czech.sukl.drug_index.get_cached_response",
            return_value=json.dumps(cached_entries),
        ):
            await idx.ensure_built()
            assert idx.size == 1


class TestDrugIndexPartialBuild:
    """T008: Partial build tolerance."""

    async def test_partial_fetch_still_builds(self):
        """Index builds even if some drug details fail."""
        idx = DrugIndex()
        codes = ["0000001", "0000002", "0000003", "0000004"]

        async def mock_fetch_list(*a, **kw):
            return codes

        call_count = 0

        async def mock_fetch_detail(code, **kw):
            nonlocal call_count
            call_count += 1
            # 50% success
            if code in ("0000001", "0000003"):
                return _make_detail(code, f"Drug{code}")
            return None

        with (
            patch(
                "czechmedmcp.czech.sukl.drug_index._fetch_drug_list",
                side_effect=mock_fetch_list,
            ),
            patch(
                "czechmedmcp.czech.sukl.drug_index.fetch_drug_detail",
                side_effect=mock_fetch_detail,
            ),
            patch(
                "czechmedmcp.czech.sukl.drug_index.cache_response"
            ),
            patch(
                "czechmedmcp.czech.sukl.drug_index.get_cached_response",
                return_value=None,
            ),
        ):
            await idx.ensure_built()
            assert idx.size == 2  # 2 out of 4 succeeded


class TestSearchIndex:
    """Verify search_index returns correct results."""

    def test_search_by_name(self):
        idx = DrugIndex()
        idx._entries = [
            _make_entry("0000001", "IBUPROFEN GALMED"),
            _make_entry("0000002", "WARFARIN ORION"),
        ]
        idx._built_at = 9999999999.0

        results, total = search_index(idx, "ibuprofen")
        assert total == 1
        assert results[0].sukl_code == "0000001"

    def test_search_empty_query(self):
        idx = DrugIndex()
        idx._entries = [_make_entry("0000001", "X")]
        idx._built_at = 9999999999.0

        results, total = search_index(idx, "")
        assert total == 0
