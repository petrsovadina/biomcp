"""Unit tests for SUKL drug search functionality."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from biomcp.czech.sukl.drug_index import (
    DrugIndex,
    DrugIndexEntry,
    _detail_to_entry,
)


def _make_entry(
    code: str,
    name: str,
    atc: str = "M01AE01",
    supplement: str = "",
    holder: str = "",
) -> DrugIndexEntry:
    """Create a DrugIndexEntry for testing."""
    return _detail_to_entry({
        "kodSUKL": code,
        "nazev": name,
        "sila": "400MG",
        "ATCkod": atc,
        "lekovaFormaKod": "TBL FLM",
        "doplnek": supplement or f"{name} 400MG",
        "drzitelKod": holder,
    })


def _make_index(entries: list[DrugIndexEntry]) -> DrugIndex:
    """Create a DrugIndex with pre-loaded entries."""
    idx = DrugIndex()
    idx._entries = entries
    idx._built_at = 9999999999.0
    return idx


NUROFEN = _make_entry(
    "0000123", "NUROFEN 400MG", holder="reckitt"
)
IBUPROFEN = _make_entry(
    "0000456", "IBUPROFEN AL 400", holder="aliud"
)
PARALEN = _make_entry(
    "0000789", "PARALEN 500", atc="N02BE01", holder="zentiva"
)


class TestSuklDrugSearch:
    """Tests for _sukl_drug_search using DrugIndex."""

    @pytest.fixture
    def mock_index(self):
        return _make_index([NUROFEN, IBUPROFEN, PARALEN])

    async def test_search_by_name(self, mock_index):
        """Search by drug name returns matching results."""
        from biomcp.czech.sukl.search import (
            _sukl_drug_search,
        )

        with patch(
            "biomcp.czech.sukl.search.get_drug_index",
            new_callable=AsyncMock,
            return_value=mock_index,
        ):
            result = json.loads(
                await _sukl_drug_search("Nurofen")
            )
            assert result["total"] >= 1
            assert len(result["results"]) >= 1
            assert (
                result["results"][0]["sukl_code"] == "0000123"
            )

    async def test_search_by_atc_code(self, mock_index):
        """Search by ATC code returns matching drugs."""
        from biomcp.czech.sukl.search import (
            _sukl_drug_search,
        )

        with patch(
            "biomcp.czech.sukl.search.get_drug_index",
            new_callable=AsyncMock,
            return_value=mock_index,
        ):
            result = json.loads(
                await _sukl_drug_search("M01AE01")
            )
            assert result["total"] == 2
            codes = {
                r["sukl_code"] for r in result["results"]
            }
            assert codes == {"0000123", "0000456"}

    async def test_search_pagination(self):
        """Search supports pagination parameters."""
        from biomcp.czech.sukl.search import (
            _sukl_drug_search,
        )

        entries = [
            _make_entry(
                f"000{i:04d}", f"DRUG {i}", supplement=f"DRUG {i} 400MG"
            )
            for i in range(5)
        ]
        index = _make_index(entries)

        with patch(
            "biomcp.czech.sukl.search.get_drug_index",
            new_callable=AsyncMock,
            return_value=index,
        ):
            result = json.loads(
                await _sukl_drug_search(
                    "DRUG", page=2, page_size=2
                )
            )
            assert result["page"] == 2
            assert result["page_size"] == 2
            assert len(result["results"]) == 2

    async def test_search_empty_results(self):
        """Search with no matches returns empty result set."""
        from biomcp.czech.sukl.search import (
            _sukl_drug_search,
        )

        index = _make_index([NUROFEN])

        with patch(
            "biomcp.czech.sukl.search.get_drug_index",
            new_callable=AsyncMock,
            return_value=index,
        ):
            result = json.loads(
                await _sukl_drug_search(
                    "nonexistentdrug12345"
                )
            )
            assert result["total"] == 0
            assert result["results"] == []

    async def test_search_diacritics_handling(self):
        """Search handles Czech diacritics transparently."""
        from biomcp.czech.sukl.search import (
            _sukl_drug_search,
        )

        entry = _make_entry(
            "0000123",
            "LÉČIVÝ PŘÍPRAVEK",
            supplement="LÉČIVÝ PŘÍPRAVEK 400MG",
        )
        index = _make_index([entry])

        with patch(
            "biomcp.czech.sukl.search.get_drug_index",
            new_callable=AsyncMock,
            return_value=index,
        ):
            result = json.loads(
                await _sukl_drug_search("lecivy pripravek")
            )
            assert result["total"] >= 1

    async def test_search_api_error_returns_error(self):
        """Search handles API errors gracefully."""
        from biomcp.czech.sukl.search import (
            _sukl_drug_search,
        )

        with patch(
            "biomcp.czech.sukl.search.get_drug_index",
            new_callable=AsyncMock,
            side_effect=Exception("API unavailable"),
        ):
            result = json.loads(
                await _sukl_drug_search("test")
            )
            assert "error" in result
            assert result["total"] == 0

    async def test_search_result_fields(self, mock_index):
        """Search results contain expected fields."""
        from biomcp.czech.sukl.search import (
            _sukl_drug_search,
        )

        with patch(
            "biomcp.czech.sukl.search.get_drug_index",
            new_callable=AsyncMock,
            return_value=mock_index,
        ):
            result = json.loads(
                await _sukl_drug_search("Nurofen")
            )
            drug = result["results"][0]
            assert "sukl_code" in drug
            assert "name" in drug
            assert "strength" in drug
            assert "atc_code" in drug
            assert "pharmaceutical_form" in drug
