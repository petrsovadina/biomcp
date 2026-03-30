"""Tests for drug name resolution (BUG-8).

Verifies that drug_getter and fetch handler resolve
common drug names (e.g. "metformin") via MyChem.info
query, while DrugBank IDs still work directly.
"""


import pytest

from czechmedmcp.drugs.getter import get_drug
from czechmedmcp.fetch_handlers import handle_drug_fetch
from czechmedmcp.integrations.biothings_client import (
    BioThingsClient,
    _extract_name_from_hit,
)

# -- Fixtures -------------------------------------------------------

@pytest.fixture
def metformin_query_response():
    """MyChem.info query response for 'metformin'."""
    return {
        "hits": [
            {
                "_id": "ZSLZBFCDCINBPY-ZSJPKINUSA-N",
                "_score": 12.5,
                "drugbank": {"name": "Metformin"},
                "chembl": {
                    "pref_name": "METFORMIN",
                },
                "unii": {
                    "display_name": "Metformin",
                },
            },
            {
                "_id": "OTHER-COMPOUND-ID",
                "_score": 5.0,
                "chebi": {"name": "metformin salt"},
            },
        ],
    }


@pytest.fixture
def metformin_detail_response():
    """MyChem.info GET response for metformin (no name)."""
    return {
        "_id": "ZSLZBFCDCINBPY-ZSJPKINUSA-N",
        "drugbank": {
            "id": "DB00331",
            "name": "Metformin",
            "description": (
                "Metformin is a biguanide antihyperglycemic"
                " agent used in diabetes."
            ),
            "indication": (
                "Treatment of type 2 diabetes mellitus."
            ),
            "mechanism_of_action": (
                "Decreases hepatic glucose production."
            ),
            "products": {
                "name": ["Glucophage", "Fortamet"],
            },
        },
        "chembl": {
            "molecule_chembl_id": "CHEMBL1431",
            "pref_name": "METFORMIN",
        },
        "pubchem": {"cid": 4091},
        "chebi": {
            "id": "CHEBI:6801",
            "name": "metformin",
        },
        "formula": "C4H11N5",
    }


@pytest.fixture
def metformin_detail_no_name():
    """MyChem.info GET response lacking name fields."""
    return {
        "_id": "ZSLZBFCDCINBPY-ZSJPKINUSA-N",
        "pubchem": {"cid": 4091},
        "formula": "C4H11N5",
    }


@pytest.fixture
def drugbank_detail_response():
    """MyChem.info GET response for DrugBank ID."""
    return {
        "_id": "DB00331",
        "drugbank": {
            "id": "DB00331",
            "name": "Metformin",
            "description": "A biguanide agent.",
        },
        "formula": "C4H11N5",
    }


# -- _extract_name_from_hit tests ----------------------------------

class TestExtractNameFromHit:
    """Test the helper that extracts names from hits."""

    def test_drugbank_name(self):
        hit = {"drugbank": {"name": "Metformin"}}
        assert _extract_name_from_hit(hit) == "Metformin"

    def test_chembl_pref_name(self):
        hit = {"chembl": {"pref_name": "METFORMIN"}}
        assert _extract_name_from_hit(hit) == "METFORMIN"

    def test_unii_display_name(self):
        hit = {"unii": {"display_name": "Metformin"}}
        assert _extract_name_from_hit(hit) == "Metformin"

    def test_chebi_name(self):
        hit = {"chebi": {"name": "metformin"}}
        assert _extract_name_from_hit(hit) == "metformin"

    def test_top_level_name(self):
        hit = {"name": "Metformin hydrochloride"}
        assert (
            _extract_name_from_hit(hit)
            == "Metformin hydrochloride"
        )

    def test_no_name_returns_none(self):
        hit = {"_id": "XYZ", "_score": 5.0}
        assert _extract_name_from_hit(hit) is None

    def test_priority_drugbank_over_chembl(self):
        hit = {
            "drugbank": {"name": "Metformin"},
            "chembl": {"pref_name": "METFORMIN"},
        }
        assert _extract_name_from_hit(hit) == "Metformin"


# -- BioThingsClient.get_drug_info tests ----------------------------

class TestDrugNameResolution:
    """Test that drug names resolve via MyChem query."""

    async def test_metformin_resolves_by_name(
        self,
        monkeypatch,
        metformin_query_response,
        metformin_detail_response,
    ):
        """drug_getter('metformin') should return drug."""
        call_count = 0
        responses = [
            (metformin_query_response, None),
            (metformin_detail_response, None),
        ]

        async def mock_api(url, request, method, domain):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        monkeypatch.setattr(
            "czechmedmcp.http_client.request_api",
            mock_api,
        )

        result = await get_drug("metformin")

        assert "## Drug: Metformin" in result
        assert "DrugBank ID**: DB00331" in result
        assert "Formula**: C4H11N5" in result

    async def test_name_fallback_from_query_hit(
        self,
        monkeypatch,
        metformin_query_response,
        metformin_detail_no_name,
    ):
        """When GET response has no name, use query hit."""
        call_count = 0
        responses = [
            (metformin_query_response, None),
            (metformin_detail_no_name, None),
        ]

        async def mock_api(url, request, method, domain):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        monkeypatch.setattr(
            "czechmedmcp.http_client.request_api",
            mock_api,
        )

        result = await get_drug("metformin")

        # Name should come from query hit fallback
        assert "## Drug: Metformin" in result
        assert "Drug: Unknown" not in result

    async def test_drugbank_id_passes_through(
        self,
        monkeypatch,
        drugbank_detail_response,
    ):
        """DrugBank ID 'DB00331' should go to GET."""
        async def mock_api(url, request, method, domain):
            return (drugbank_detail_response, None)

        monkeypatch.setattr(
            "czechmedmcp.http_client.request_api",
            mock_api,
        )

        result = await get_drug("DB00331")

        assert "## Drug: Metformin" in result
        assert "DrugBank ID**: DB00331" in result

    async def test_nonexistent_drug_returns_error(
        self,
        monkeypatch,
    ):
        """Nonexistent drug name returns clear error."""
        call_count = 0

        async def mock_api(url, request, method, domain):
            nonlocal call_count
            call_count += 1
            # Both query and retry return empty
            return ({"hits": []}, None)

        monkeypatch.setattr(
            "czechmedmcp.http_client.request_api",
            mock_api,
        )

        result = await get_drug("xyznonexistent123")

        assert "not found" in result.lower()
        assert "xyznonexistent123" in result


# -- fetch handler tests -------------------------------------------

class TestDrugFetchHandler:
    """Test handle_drug_fetch with name resolution."""

    async def test_fetch_drug_by_name(
        self,
        monkeypatch,
        metformin_query_response,
        metformin_detail_response,
    ):
        """fetch(domain='drug', id='metformin') works."""
        call_count = 0
        responses = [
            (metformin_query_response, None),
            (metformin_detail_response, None),
        ]

        async def mock_api(url, request, method, domain):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        monkeypatch.setattr(
            "czechmedmcp.http_client.request_api",
            mock_api,
        )

        result = await handle_drug_fetch(identifier="metformin")

        assert result["title"] == "Metformin"
        assert "Drug: Metformin" in result["text"]

    async def test_fetch_drug_not_found(
        self,
        monkeypatch,
    ):
        """Nonexistent drug returns error dict."""
        async def mock_api(url, request, method, domain):
            return ({"hits": []}, None)

        monkeypatch.setattr(
            "czechmedmcp.http_client.request_api",
            mock_api,
        )

        result = await handle_drug_fetch(
            identifier="xyznonexistent123",
        )

        assert "error" in result


# -- Query hit scoring tests ---------------------------------------

class TestQueryHitScoring:
    """Test that query scoring prefers exact matches."""

    async def test_exact_name_match_ranked_first(
        self,
        monkeypatch,
    ):
        """Hit with exact name match should rank first."""
        query_response = {
            "hits": [
                {
                    "_id": "WRONG-ID",
                    "_score": 20.0,
                    "chebi": {
                        "name": "metformin derivative",
                    },
                },
                {
                    "_id": "CORRECT-ID",
                    "_score": 10.0,
                    "drugbank": {"name": "Metformin"},
                },
            ],
        }

        detail_response = {
            "_id": "CORRECT-ID",
            "drugbank": {
                "id": "DB00331",
                "name": "Metformin",
            },
        }

        call_count = 0
        responses = [
            (query_response, None),
            (detail_response, None),
        ]

        async def mock_api(url, request, method, domain):
            nonlocal call_count
            result = responses[call_count]
            call_count += 1
            return result

        monkeypatch.setattr(
            "czechmedmcp.http_client.request_api",
            mock_api,
        )

        client = BioThingsClient()
        info = await client.get_drug_info("metformin")

        assert info is not None
        assert info.drug_id == "CORRECT-ID"
