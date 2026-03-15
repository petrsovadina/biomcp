"""Tests for SZV procedure reimbursement calculation."""

import json
from unittest.mock import patch

from czechmedmcp.czech.szv.reimbursement import (
    _calculate_reimbursement,
)

MOCK_PROCEDURE = {
    "code": "09543",
    "name": "Vyšetření EKG",
    "point_value": 350,
    "source": "MZCR/SZV",
}


def _patch_szv_get(data=MOCK_PROCEDURE):
    """Patch _szv_get to return mock procedure."""
    return patch(
        "czechmedmcp.czech.szv.reimbursement._szv_get",
        return_value=json.dumps(
            data, ensure_ascii=False
        ),
    )


class TestCalculateReimbursement:
    """Test _calculate_reimbursement()."""

    async def test_returns_dual_output(self):
        """Result must have content + structuredContent."""
        with _patch_szv_get():
            result = await _calculate_reimbursement(
                "09543"
            )

        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    async def test_vzp_calculation(self):
        """VZP (111) rate 1.15 * 350 = 402.50."""
        with _patch_szv_get():
            result = await _calculate_reimbursement(
                "09543", "111", 1
            )

        sc = json.loads(result)["structuredContent"]
        assert sc["point_value"] == 350
        assert sc["rate_per_point"] == 1.15
        assert sc["unit_price_czk"] == 402.50
        assert sc["total_czk"] == 402.50

    async def test_vozp_with_count(self):
        """VoZP (201) rate 1.10 * 350 * 2 = 770.00."""
        with _patch_szv_get():
            result = await _calculate_reimbursement(
                "09543", "201", 2
            )

        sc = json.loads(result)["structuredContent"]
        assert sc["insurance_code"] == "201"
        assert sc["insurance_name"] == "VoZP"
        assert sc["unit_price_czk"] == 385.0
        assert sc["total_czk"] == 770.0

    async def test_invalid_insurance_code(self):
        """Should return error for unknown code."""
        result = await _calculate_reimbursement(
            "09543", "999"
        )

        parsed = json.loads(result)
        assert "error" in parsed

    async def test_unknown_procedure(self):
        """Should return error when procedure not found."""
        err = {"error": "Procedure not found: 99999"}
        with _patch_szv_get(err):
            result = await _calculate_reimbursement(
                "99999"
            )

        parsed = json.loads(result)
        assert "error" in parsed

    async def test_markdown_content(self):
        """Markdown should contain key info."""
        with _patch_szv_get():
            result = await _calculate_reimbursement(
                "09543", "111", 1
            )

        content = json.loads(result)["content"]
        assert "Kalkulace" in content
        assert "09543" in content
        assert "VZP" in content
