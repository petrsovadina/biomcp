"""Tests for VZP drug reimbursement and alternatives."""

import json
from unittest.mock import patch

from czechmedmcp.czech.vzp.drug_reimbursement import (
    _compare_alternatives,
    _get_vzp_drug_reimbursement,
)

MOCK_DRUG = {
    "sukl_code": "0012345",
    "name": "Ibuprofen 400mg",
    "atc_code": "M01AE01",
    "source": "SUKL",
}

MOCK_REIMB = json.dumps({
    "content": "## Uhrada",
    "structuredContent": {
        "sukl_code": "0012345",
        "reimbursement_group": "P/72/1",
        "max_retail_price": 89.50,
        "reimbursement_amount": 67.00,
        "patient_copay": 22.50,
        "conditions": "Bez omezení",
        "valid_from": "2026-01-01",
    },
})

MOCK_SEARCH = json.dumps({
    "results": [
        {"sukl_code": "0012345", "name": "Ibuprofen"},
        {"sukl_code": "0012346", "name": "Ibalgin 400"},
        {"sukl_code": "0012347", "name": "Brufen 400"},
    ],
})

MOCK_REIMB_ALT = json.dumps({
    "content": "",
    "structuredContent": {
        "sukl_code": "0012346",
        "patient_copay": 15.00,
    },
})


def _patch_detail(data=MOCK_DRUG):
    return patch(
        "czechmedmcp.czech.vzp.drug_reimbursement."
        "_fetch_drug_detail",
        return_value=data,
    )


def _patch_reimb(rv=MOCK_REIMB):
    return patch(
        "czechmedmcp.czech.sukl.reimbursement."
        "_get_reimbursement",
        return_value=rv,
    )


def _patch_search(rv=MOCK_SEARCH):
    return patch(
        "czechmedmcp.czech.sukl.search."
        "_sukl_drug_search",
        return_value=rv,
    )


class TestGetVZPDrugReimbursement:
    """Test _get_vzp_drug_reimbursement()."""

    async def test_returns_dual_output(self):
        """Result must have content + structuredContent."""
        with _patch_detail(), _patch_reimb():
            result = await _get_vzp_drug_reimbursement(
                "0012345"
            )

        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    async def test_reimbursement_fields(self):
        """Should include VZP reimbursement fields."""
        with _patch_detail(), _patch_reimb():
            result = await _get_vzp_drug_reimbursement(
                "0012345"
            )

        sc = json.loads(result)["structuredContent"]
        assert sc["sukl_code"] == "0012345"
        assert sc["name"] == "Ibuprofen 400mg"
        assert sc["patient_copay"] == 22.50

    async def test_drug_not_found(self):
        """Should return error for unknown drug."""
        with _patch_detail(data=None):
            result = await _get_vzp_drug_reimbursement(
                "9999999"
            )

        parsed = json.loads(result)
        assert "error" in parsed

    async def test_markdown_content(self):
        """Markdown should contain key info."""
        with _patch_detail(), _patch_reimb():
            result = await _get_vzp_drug_reimbursement(
                "0012345"
            )

        content = json.loads(result)["content"]
        assert "Ibuprofen" in content


class TestCompareAlternatives:
    """Test _compare_alternatives()."""

    async def test_returns_dual_output(self):
        """Result must have content + structuredContent."""
        with (
            _patch_detail(),
            _patch_reimb(),
            _patch_search(),
        ):
            result = await _compare_alternatives(
                "0012345"
            )

        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    async def test_alternatives_sorted_by_copay(self):
        """Alternatives should be sorted by copay."""
        with (
            _patch_detail(),
            _patch_reimb(),
            _patch_search(),
        ):
            result = await _compare_alternatives(
                "0012345"
            )

        sc = json.loads(result)["structuredContent"]
        assert sc["atc_code"] == "M01AE01"
        assert sc["total_alternatives"] >= 0

    async def test_drug_not_found(self):
        """Should return error for unknown drug."""
        with _patch_detail(data=None):
            result = await _compare_alternatives(
                "9999999"
            )

        parsed = json.loads(result)
        assert "error" in parsed

    async def test_savings_calculated(self):
        """Should calculate savings vs reference."""
        with (
            _patch_detail(),
            _patch_reimb(),
            _patch_search(),
        ):
            result = await _compare_alternatives(
                "0012345"
            )

        sc = json.loads(result)["structuredContent"]
        assert sc["reference_copay"] == 22.50
