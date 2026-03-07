"""Tests for referral assistant workflow."""

import json
from unittest.mock import patch

from biomcp.czech.workflows.referral_assistant import (
    _referral_assistant,
)

MOCK_DIAGNOSIS = json.dumps({
    "code": "I25.1",
    "name": "Aterosklerotická nemoc srdeční",
})

MOCK_PROVIDERS = json.dumps({
    "total": 2,
    "page": 1,
    "page_size": 10,
    "results": [
        {
            "name": "Kardiologické centrum Brno",
            "city": "Brno",
            "specialties": ["kardiologie"],
        },
        {
            "name": "FN Brno — Kardiologie",
            "city": "Brno",
            "specialties": ["kardiologie"],
        },
    ],
})


def _patch_mkn(data=MOCK_DIAGNOSIS):
    return patch(
        "biomcp.czech.workflows."
        "referral_assistant._mkn_get",
        return_value=data,
    )


def _patch_nrpzs(data=MOCK_PROVIDERS):
    return patch(
        "biomcp.czech.workflows."
        "referral_assistant._nrpzs_search",
        return_value=data,
    )


class TestReferralAssistant:
    """Test _referral_assistant()."""

    async def test_returns_dual_output(self):
        """Result must have content + structuredContent."""
        with _patch_mkn(), _patch_nrpzs():
            result = await _referral_assistant(
                "I25.1", "Brno"
            )

        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    async def test_specialty_mapping(self):
        """I-codes should map to kardiologie."""
        with _patch_mkn(), _patch_nrpzs():
            result = await _referral_assistant(
                "I25.1", "Brno"
            )

        sc = json.loads(result)["structuredContent"]
        assert sc["recommended_specialty"] == "kardiologie"

    async def test_providers_returned(self):
        """Should include matching providers."""
        with _patch_mkn(), _patch_nrpzs():
            result = await _referral_assistant(
                "I25.1", "Brno"
            )

        sc = json.loads(result)["structuredContent"]
        assert len(sc["providers"]) == 2

    async def test_diagnosis_info(self):
        """Should include diagnosis details."""
        with _patch_mkn(), _patch_nrpzs():
            result = await _referral_assistant(
                "I25.1", "Brno"
            )

        sc = json.loads(result)["structuredContent"]
        assert sc["diagnosis_code"] == "I25.1"

    async def test_graceful_mkn_failure(self):
        """Should work even if MKN fails."""
        with (
            _patch_mkn(data='{"error": "not found"}'),
            _patch_nrpzs(),
        ):
            result = await _referral_assistant(
                "X99", "Praha"
            )

        sc = json.loads(result)["structuredContent"]
        assert sc["diagnosis_code"] == "X99"

    async def test_markdown_content(self):
        """Markdown should contain key info."""
        with _patch_mkn(), _patch_nrpzs():
            result = await _referral_assistant(
                "I25.1", "Brno"
            )

        content = json.loads(result)["content"]
        assert "I25.1" in content
        assert "Brno" in content
        assert "kardiologie" in content
