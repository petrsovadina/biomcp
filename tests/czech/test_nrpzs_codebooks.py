"""Tests for NRPZS codebooks."""

import json
from unittest.mock import patch

from czechmedmcp.czech.nrpzs.search import _get_codebooks

MOCK_PROVIDERS = [
    {
        "ZZ_obor_pece": "kardiologie, neurologie",
        "ZZ_forma_pece": "ambulantní",
        "ZZ_druh_pece": "lůžková",
    },
    {
        "ZZ_obor_pece": "kardiologie",
        "ZZ_forma_pece": "ambulantní, lůžková",
        "ZZ_druh_pece": "ambulantní",
    },
    {
        "ZZ_obor_pece": "oftalmologie",
        "ZZ_forma_pece": "ambulantní",
        "ZZ_druh_pece": "ambulantní",
    },
]


def _patch_providers(data=MOCK_PROVIDERS):
    return patch(
        "czechmedmcp.czech.nrpzs.search._get_providers",
        return_value=data,
    )


class TestGetCodebooks:
    """Test _get_codebooks()."""

    async def test_returns_dual_output(self):
        """Result must have content + structuredContent."""
        with _patch_providers():
            result = await _get_codebooks("specialties")

        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    async def test_specialties_unique(self):
        """Should extract unique specialties."""
        with _patch_providers():
            result = await _get_codebooks("specialties")

        sc = json.loads(result)["structuredContent"]
        names = [it["name"] for it in sc["items"]]
        assert "kardiologie" in names
        assert "neurologie" in names
        assert "oftalmologie" in names
        # kardiologie appears twice but should be unique
        assert names.count("kardiologie") == 1

    async def test_care_forms(self):
        """Should extract unique care forms."""
        with _patch_providers():
            result = await _get_codebooks("care_forms")

        sc = json.loads(result)["structuredContent"]
        names = [it["name"] for it in sc["items"]]
        assert "ambulantní" in names

    async def test_invalid_codebook(self):
        """Should return error for unknown type."""
        result = await _get_codebooks("invalid")

        parsed = json.loads(result)
        assert "error" in parsed

    async def test_total_count(self):
        """Total should match items count."""
        with _patch_providers():
            result = await _get_codebooks("specialties")

        sc = json.loads(result)["structuredContent"]
        assert sc["total"] == len(sc["items"])
