"""Tests for drug profile workflow."""

import json
from unittest.mock import patch

from biomcp.czech.workflows.drug_profile import (
    _drug_profile,
)

MOCK_SEARCH = json.dumps({
    "results": [
        {"sukl_code": "0012345", "name": "Ibuprofen"},
    ],
})

MOCK_DETAIL = json.dumps({
    "sukl_code": "0012345",
    "name": "Ibuprofen 400mg",
    "source": "SUKL",
})

MOCK_AVAIL = json.dumps({
    "sukl_code": "0012345",
    "status": "available",
})

MOCK_REIMB = json.dumps({
    "content": "",
    "structuredContent": {
        "sukl_code": "0012345",
        "patient_copay": 22.50,
    },
})

MOCK_EVIDENCE = json.dumps([
    {"pmid": "12345", "title": "Ibuprofen study"},
])


def _patch_search():
    return patch(
        "biomcp.czech.sukl.search._sukl_drug_search",
        return_value=MOCK_SEARCH,
    )


def _patch_detail():
    return patch(
        "biomcp.czech.sukl.getter._sukl_drug_details",
        return_value=MOCK_DETAIL,
    )


def _patch_avail():
    return patch(
        "biomcp.czech.sukl.availability."
        "_sukl_availability_check",
        return_value=MOCK_AVAIL,
    )


def _patch_reimb():
    return patch(
        "biomcp.czech.sukl.reimbursement."
        "_get_reimbursement",
        return_value=MOCK_REIMB,
    )


def _patch_evidence():
    return patch(
        "biomcp.articles.search._article_searcher",
        return_value=MOCK_EVIDENCE,
    )


class TestDrugProfile:
    """Test _drug_profile()."""

    async def test_returns_dual_output(self):
        """Result must have content + structuredContent."""
        with (
            _patch_search(),
            _patch_detail(),
            _patch_avail(),
            _patch_reimb(),
            _patch_evidence(),
        ):
            result = await _drug_profile("ibuprofen")

        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    async def test_all_sections_ok(self):
        """All 4 sections should succeed."""
        with (
            _patch_search(),
            _patch_detail(),
            _patch_avail(),
            _patch_reimb(),
            _patch_evidence(),
        ):
            result = await _drug_profile("ibuprofen")

        sc = json.loads(result)["structuredContent"]
        assert sc["sukl_code"] == "0012345"
        sections = sc["sections"]
        assert len(sections) == 4
        ok_count = sum(
            1 for s in sections if s["status"] == "ok"
        )
        assert ok_count == 4

    async def test_graceful_degradation(self):
        """Profile should work with partial failures."""

        async def _fail(*a, **kw):
            raise ConnectionError("API down")

        with (
            _patch_search(),
            _patch_detail(),
            patch(
                "biomcp.czech.sukl.availability."
                "_sukl_availability_check",
                side_effect=_fail,
            ),
            _patch_reimb(),
            _patch_evidence(),
        ):
            result = await _drug_profile("ibuprofen")

        sc = json.loads(result)["structuredContent"]
        sections = sc["sections"]
        statuses = {
            s["section"]: s["status"] for s in sections
        }
        assert statuses["availability"] == "error"
        assert statuses["registration"] == "ok"

    async def test_drug_not_found(self):
        """Should return error for unknown drug."""
        no_results = json.dumps({"results": []})
        with patch(
            "biomcp.czech.sukl.search._sukl_drug_search",
            return_value=no_results,
        ):
            result = await _drug_profile("neexistuje")

        parsed = json.loads(result)
        assert "error" in parsed

    async def test_query_preserved(self):
        """Original query should be in output."""
        with (
            _patch_search(),
            _patch_detail(),
            _patch_avail(),
            _patch_reimb(),
            _patch_evidence(),
        ):
            result = await _drug_profile("ibuprofen")

        sc = json.loads(result)["structuredContent"]
        assert sc["query"] == "ibuprofen"
