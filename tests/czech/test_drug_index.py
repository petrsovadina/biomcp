"""Unit tests for SUKL drug index."""

from unittest.mock import AsyncMock, patch

import pytest

from biomcp.czech.sukl.drug_index import (
    DrugIndex,
    _detail_to_entry,
    get_drug_index,
    reset_drug_index,
    search_index,
)

# -- Fixtures --

SAMPLE_DETAIL_IBUPROFEN = {
    "kodSUKL": "0001234",
    "nazev": "IBUPROFEN AL 400",
    "sila": "400MG",
    "ATCkod": "M01AE01",
    "lekovaFormaKod": "TBL FLM",
    "doplnek": "400MG TBL FLM 30",
    "drzitelKod": "ALIUD",
}

SAMPLE_DETAIL_PARALEN = {
    "kodSUKL": "0005678",
    "nazev": "PARALEN 500",
    "sila": "500MG",
    "ATCkod": "N02BE01",
    "lekovaFormaKod": "TBL NOB",
    "doplnek": "500MG TBL NOB 24",
    "drzitelKod": "ZENTIVA",
}

SAMPLE_DETAIL_NUROFEN = {
    "kodSUKL": "0009012",
    "nazev": "NUROFEN 400MG",
    "sila": "400MG",
    "ATCkod": "M01AE01",
    "lekovaFormaKod": "TBL FLM",
    "doplnek": "400MG TBL FLM 24",
    "drzitelKod": "RECKITT",
}

SAMPLE_CODES = ["0001234", "0005678", "0009012"]

DETAIL_MAP = {
    "0001234": SAMPLE_DETAIL_IBUPROFEN,
    "0005678": SAMPLE_DETAIL_PARALEN,
    "0009012": SAMPLE_DETAIL_NUROFEN,
}


async def mock_fetch_detail(code, **kwargs):
    return DETAIL_MAP.get(code)


# -- Tests --


class TestDetailToEntry:
    def test_converts_basic_fields(self):
        entry = _detail_to_entry(SAMPLE_DETAIL_IBUPROFEN)
        assert entry.sukl_code == "0001234"
        assert entry.name == "IBUPROFEN AL 400"
        assert entry.atc_code == "M01AE01"
        assert entry.strength == "400MG"
        assert entry.form == "TBL FLM"

    def test_normalizes_name(self):
        entry = _detail_to_entry(SAMPLE_DETAIL_IBUPROFEN)
        assert entry.name_normalized == "ibuprofen al 400"

    def test_normalizes_atc(self):
        entry = _detail_to_entry(SAMPLE_DETAIL_IBUPROFEN)
        assert entry.atc_normalized == "m01ae01"

    def test_handles_missing_fields(self):
        entry = _detail_to_entry({"kodSUKL": "0000001"})
        assert entry.sukl_code == "0000001"
        assert entry.name == ""
        assert entry.atc_code == ""
        assert entry.strength == ""


class TestSearchIndex:
    @pytest.fixture
    def index(self):
        idx = DrugIndex()
        idx._entries = [
            _detail_to_entry(d)
            for d in [
                SAMPLE_DETAIL_IBUPROFEN,
                SAMPLE_DETAIL_PARALEN,
                SAMPLE_DETAIL_NUROFEN,
            ]
        ]
        idx._built_at = 9999999999.0
        return idx

    def test_search_by_name(self, index):
        results, total = search_index(index, "ibuprofen")
        assert total == 1
        assert results[0].sukl_code == "0001234"

    def test_search_by_atc_exact(self, index):
        results, total = search_index(index, "M01AE01")
        assert total == 2
        codes = {r.sukl_code for r in results}
        assert codes == {"0001234", "0009012"}

    def test_search_by_name_partial(self, index):
        results, total = search_index(index, "NUROFEN")
        assert total == 1
        assert results[0].name == "NUROFEN 400MG"

    def test_search_case_insensitive(self, index):
        results, total = search_index(index, "paralen")
        assert total == 1
        assert results[0].sukl_code == "0005678"

    def test_search_empty_query(self, index):
        results, total = search_index(index, "")
        assert total == 0
        assert results == []

    def test_search_no_match(self, index):
        results, total = search_index(
            index, "xyznonexistent"
        )
        assert total == 0
        assert results == []

    def test_search_pagination_page1(self, index):
        results, total = search_index(
            index, "TBL", page=1, page_size=2
        )
        assert total == 3
        assert len(results) == 2

    def test_search_pagination_page2(self, index):
        results, total = search_index(
            index, "TBL", page=2, page_size=2
        )
        assert total == 3
        assert len(results) == 1

    def test_search_with_diacritics(self, index):
        """Czech diacritics should be stripped for matching."""
        results, total = search_index(index, "ibuprofén")
        assert total == 1


class TestDrugIndex:
    @patch(
        "biomcp.czech.sukl.drug_index._fetch_drug_list",
        new_callable=AsyncMock,
        return_value=SAMPLE_CODES,
    )
    @patch(
        "biomcp.czech.sukl.drug_index.fetch_drug_detail",
        side_effect=mock_fetch_detail,
    )
    async def test_build_index(self, mock_detail, mock_list):
        idx = DrugIndex()
        await idx._build()
        assert idx.size == 3
        assert not idx.is_expired

    @patch(
        "biomcp.czech.sukl.drug_index._fetch_drug_list",
        new_callable=AsyncMock,
        return_value=SAMPLE_CODES,
    )
    @patch(
        "biomcp.czech.sukl.drug_index.fetch_drug_detail",
        side_effect=mock_fetch_detail,
    )
    async def test_ensure_built_only_once(
        self, mock_detail, mock_list
    ):
        idx = DrugIndex()
        await idx.ensure_built()
        await idx.ensure_built()
        # Only one build call
        mock_list.assert_called_once()

    @patch(
        "biomcp.czech.sukl.drug_index._fetch_drug_list",
        new_callable=AsyncMock,
        return_value=[],
    )
    async def test_build_empty_list(self, mock_list):
        idx = DrugIndex()
        await idx._build()
        assert idx.size == 0

    def test_is_expired_when_empty(self):
        idx = DrugIndex()
        assert idx.is_expired

    @patch(
        "biomcp.czech.sukl.drug_index._fetch_drug_list",
        new_callable=AsyncMock,
        return_value=SAMPLE_CODES,
    )
    @patch(
        "biomcp.czech.sukl.drug_index.fetch_drug_detail",
        side_effect=mock_fetch_detail,
    )
    async def test_handles_failed_details(
        self, mock_detail, mock_list
    ):
        """Some codes returning None should not break build."""

        async def _partial_fetch(code, **kwargs):
            if code == "0005678":
                return None
            return DETAIL_MAP.get(code)

        mock_detail.side_effect = _partial_fetch
        idx = DrugIndex()
        await idx._build()
        assert idx.size == 2


class TestGetDrugIndex:
    @patch(
        "biomcp.czech.sukl.drug_index._fetch_drug_list",
        new_callable=AsyncMock,
        return_value=SAMPLE_CODES,
    )
    @patch(
        "biomcp.czech.sukl.drug_index.fetch_drug_detail",
        side_effect=mock_fetch_detail,
    )
    async def test_singleton(self, mock_detail, mock_list):
        reset_drug_index()
        idx1 = await get_drug_index()
        idx2 = await get_drug_index()
        assert idx1 is idx2
        reset_drug_index()

    @patch(
        "biomcp.czech.sukl.drug_index._fetch_drug_list",
        new_callable=AsyncMock,
        return_value=SAMPLE_CODES,
    )
    @patch(
        "biomcp.czech.sukl.drug_index.fetch_drug_detail",
        side_effect=mock_fetch_detail,
    )
    async def test_reset_clears_singleton(
        self, mock_detail, mock_list
    ):
        reset_drug_index()
        idx1 = await get_drug_index()
        reset_drug_index()
        idx2 = await get_drug_index()
        assert idx1 is not idx2
        reset_drug_index()
