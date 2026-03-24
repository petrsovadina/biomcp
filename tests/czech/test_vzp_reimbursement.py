"""Tests for VZP reimbursement data loader and fallback."""

import json
from unittest.mock import patch

from czechmedmcp.czech.vzp.data_loader import (
    _parse_reimbursement_csv,
    clear_cache,
    load_vzp_reimbursement_data,
)
from czechmedmcp.czech.vzp.drug_reimbursement import (
    _get_vzp_drug_reimbursement,
)

MOCK_CSV = (
    "sukl_code;reimbursement_group;max_price;"
    "reimbursement_amount;patient_copay\n"
    "0012345;P/72/1;89.50;67.00;22.50\n"
    "0099999;P/10/2;150.00;120.00;30.00\n"
)

MOCK_DRUG = {
    "sukl_code": "0012345",
    "name": "TestDrug 100mg",
    "atc_code": "N02BE01",
}

MOCK_EMPTY_REIMB = json.dumps({
    "content": "",
    "structuredContent": {
        "sukl_code": "0012345",
    },
})


class TestParseReimbursementCsv:
    """Test CSV parsing logic."""

    def test_semicolon_delimiter(self):
        data = _parse_reimbursement_csv(MOCK_CSV)
        assert "0012345" in data
        assert data["0012345"]["max_price"] == 89.50
        assert data["0012345"]["patient_copay"] == 22.50

    def test_comma_delimiter(self):
        csv_text = "sukl_code,max_price,patient_copay\n0011111,50.00,10.00\n"
        data = _parse_reimbursement_csv(csv_text)
        assert "0011111" in data
        assert data["0011111"]["max_price"] == 50.00

    def test_empty_csv(self):
        data = _parse_reimbursement_csv("sukl_code;max_price\n")
        assert data == {}

    def test_czech_column_names(self):
        csv_text = (
            "kod_sukl;skupina_uhrady;max_cena;"
            "uhrada;doplatek\n"
            "0055555;P/1/1;200.00;180.00;20.00\n"
        )
        data = _parse_reimbursement_csv(csv_text)
        assert "0055555" in data
        entry = data["0055555"]
        assert entry["reimbursement_group"] == "P/1/1"
        assert entry["max_price"] == 200.00
        assert entry["patient_copay"] == 20.00


class TestLoadVzpData:
    """Test async data loader."""

    async def test_download_success(self):
        clear_cache()

        class MockResp:
            is_success = True
            text = MOCK_CSV
            status_code = 200

        class MockClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def get(self, url, **kw):
                return MockResp()

        with patch(
            "czechmedmcp.czech.vzp.data_loader.httpx.AsyncClient",
            return_value=MockClient(),
        ):
            data = await load_vzp_reimbursement_data()

        assert "0012345" in data
        assert len(data) == 2

    async def test_download_failure_local_fallback(self):
        clear_cache()

        class MockResp:
            is_success = False
            text = ""
            status_code = 500

        class MockClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *a):
                pass

            async def get(self, url, **kw):
                return MockResp()

        with (
            patch(
                "czechmedmcp.czech.vzp.data_loader.httpx.AsyncClient",
                return_value=MockClient(),
            ),
            patch(
                "czechmedmcp.czech.vzp.data_loader._read_local_csv",
                return_value=MOCK_CSV,
            ),
        ):
            data = await load_vzp_reimbursement_data()

        assert "0012345" in data


class TestVzpFallbackIntegration:
    """Test VZP fallback in GetDrugReimbursement."""

    async def test_sukl_empty_triggers_fallback(self):
        """When SUKL has no reimb, VZP CSV fills in."""
        clear_cache()

        with (
            patch(
                "czechmedmcp.czech.vzp.drug_reimbursement._fetch_drug_detail",
                return_value=MOCK_DRUG,
            ),
            patch(
                "czechmedmcp.czech.vzp"
                ".drug_reimbursement._fetch_reimbursement",
                return_value={},
            ),
            patch(
                "czechmedmcp.czech.vzp"
                ".drug_reimbursement"
                ".load_vzp_reimbursement_data",
            ),
            patch(
                "czechmedmcp.czech.vzp"
                ".drug_reimbursement"
                ".get_vzp_reimbursement_for_code",
                return_value={
                    "reimbursement_group": "P/72/1",
                    "max_price": 89.50,
                    "reimbursement_amount": 67.00,
                    "patient_copay": 22.50,
                },
            ),
        ):
            result = await _get_vzp_drug_reimbursement("0012345")

        parsed = json.loads(result)
        sc = parsed["structuredContent"]
        assert sc["patient_copay"] == 22.50

    async def test_both_empty_shows_message(self):
        """When both sources empty, show clear message."""
        clear_cache()

        with (
            patch(
                "czechmedmcp.czech.vzp.drug_reimbursement._fetch_drug_detail",
                return_value=MOCK_DRUG,
            ),
            patch(
                "czechmedmcp.czech.vzp"
                ".drug_reimbursement._fetch_reimbursement",
                return_value={},
            ),
            patch(
                "czechmedmcp.czech.vzp"
                ".drug_reimbursement"
                ".load_vzp_reimbursement_data",
            ),
            patch(
                "czechmedmcp.czech.vzp"
                ".drug_reimbursement"
                ".get_vzp_reimbursement_for_code",
                return_value=None,
            ),
        ):
            result = await _get_vzp_drug_reimbursement("0012345")

        parsed = json.loads(result)
        content = parsed["content"]
        assert "Úhradová data nejsou dostupná" in content
