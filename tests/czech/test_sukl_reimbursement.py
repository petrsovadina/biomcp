"""Tests for SUKL reimbursement lookup."""

import json
from unittest.mock import MagicMock, patch

from czechmedmcp.czech.sukl.reimbursement import _get_reimbursement

MOCK_DETAIL = {"kodSUKL": "0012345", "nazev": "Ibuprofen 400mg"}

MOCK_REIMBURSEMENT_DATA = {
    "cenaVyrobce": 45.20,
    "maxMaloobchodniCena": 89.50,
    "uhrada": 67.00,
    "doplatek": 22.50,
    "uhradovaSkupina": "P/72/1",
    "podminky": None,
    "platnostOd": "2026-01-01",
    "platnostDo": None,
}


def _make_httpx_response(status_code, data=None):
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    if data is not None:
        resp.json.return_value = data
    resp.raise_for_status.return_value = None
    return resp


def _patch_http(status_code=200, data=None):
    """Patch httpx.AsyncClient for reimbursement tests."""

    resp = _make_httpx_response(status_code, data)

    async def mock_get(url, **kwargs):
        return resp

    class MockClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url, **kwargs):
            return resp

    return patch(
        "czechmedmcp.czech.sukl.reimbursement.httpx.AsyncClient",
        return_value=MockClient(),
    )


class TestGetReimbursement:
    """Test _get_reimbursement() function."""

    async def test_returns_dual_output(self):
        """Result must have content + structuredContent."""
        with (
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "_fetch_drug_detail",
                return_value=MOCK_DETAIL,
            ),
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "get_cached_response",
                return_value=None,
            ),
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "cache_response",
            ),
            _patch_http(200, MOCK_REIMBURSEMENT_DATA),
        ):
            result = await _get_reimbursement("0012345")

        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    async def test_structured_content_fields(self):
        """structuredContent must have Reimbursement fields."""
        with (
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "_fetch_drug_detail",
                return_value=MOCK_DETAIL,
            ),
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "get_cached_response",
                return_value=None,
            ),
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "cache_response",
            ),
            _patch_http(200, MOCK_REIMBURSEMENT_DATA),
        ):
            result = await _get_reimbursement("0012345")

        sc = json.loads(result)["structuredContent"]
        assert sc["sukl_code"] == "0012345"
        assert sc["name"] == "Ibuprofen 400mg"
        assert sc["manufacturer_price"] == 45.20
        assert sc["patient_copay"] == 22.50
        assert sc["reimbursement_group"] == "P/72/1"

    async def test_markdown_content(self):
        """Content should contain Czech Markdown."""
        with (
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "_fetch_drug_detail",
                return_value=MOCK_DETAIL,
            ),
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "get_cached_response",
                return_value=None,
            ),
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "cache_response",
            ),
            _patch_http(200, MOCK_REIMBURSEMENT_DATA),
        ):
            result = await _get_reimbursement("0012345")

        content = json.loads(result)["content"]
        assert "Úhrada" in content
        assert "Ibuprofen" in content
        assert "45.20" in content

    async def test_404_returns_error(self):
        """404 should return error in dual output."""
        with (
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "_fetch_drug_detail",
                return_value=MOCK_DETAIL,
            ),
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "get_cached_response",
                return_value=None,
            ),
            _patch_http(404),
        ):
            result = await _get_reimbursement("9999999")

        sc = json.loads(result)["structuredContent"]
        assert "error" in sc

    async def test_cached_response_used(self):
        """Should use cached data when available."""
        cached = json.dumps(MOCK_REIMBURSEMENT_DATA)

        with (
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "_fetch_drug_detail",
                return_value=MOCK_DETAIL,
            ),
            patch(
                "czechmedmcp.czech.sukl.reimbursement."
                "get_cached_response",
                return_value=cached,
            ),
        ):
            result = await _get_reimbursement("0012345")

        sc = json.loads(result)["structuredContent"]
        assert sc["manufacturer_price"] == 45.20
