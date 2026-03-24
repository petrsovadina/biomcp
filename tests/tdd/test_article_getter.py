"""Tests for ArticleGetter — PMC ID support and error handling."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from czechmedmcp.articles.fetch import (
    _article_details,
    _convert_pmc_to_pmid,
    is_pmc_id,
)


class TestIsPmcId:
    """Test is_pmc_id() detection function."""

    def test_valid_pmc_ids(self):
        valid = [
            "PMC11193658",
            "PMC1234567",
            "PMC12345678",
            "pmc11193658",  # case-insensitive
            "Pmc1234567",
        ]
        for pmc_id in valid:
            assert is_pmc_id(pmc_id) is True, (
                f"Expected {pmc_id} to be a valid PMC ID"
            )

    def test_invalid_pmc_ids(self):
        invalid = [
            "PMC123456",  # too few digits (6)
            "PMC123456789",  # too many digits (9)
            "PMC",  # no digits
            "11193658",  # missing PMC prefix
            "PMCABC1234",  # non-numeric after PMC
            "",
            "10.1038/nature12373",  # DOI
            "abc123",
        ]
        for val in invalid:
            assert is_pmc_id(val) is False, (
                f"Expected {val} NOT to be a valid PMC ID"
            )


class TestConvertPmcToPmid:
    """Test _convert_pmc_to_pmid() with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_successful_conversion(self):
        """PMC ID is converted to PMID via NCBI API."""
        mock_json = {
            "records": [
                {
                    "pmcid": "PMC11193658",
                    "pmid": "38768446",
                    "doi": "10.1234/example",
                }
            ]
        }
        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_json
        mock_resp.raise_for_status = lambda: None

        with patch(
            "czechmedmcp.articles.fetch.get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.articles.fetch.cache_response"
        ) as mock_cache, patch(
            "httpx.AsyncClient.get",
            return_value=mock_resp,
        ):
            result = await _convert_pmc_to_pmid("PMC11193658")

        assert result == 38768446
        mock_cache.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_result(self):
        """Cached PMID is returned without HTTP call."""
        with patch(
            "czechmedmcp.articles.fetch.get_cached_response",
            return_value="38768446",
        ), patch(
            "httpx.AsyncClient.get"
        ) as mock_get:
            result = await _convert_pmc_to_pmid("PMC11193658")

        assert result == 38768446
        mock_get.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_records_returns_none(self):
        """Empty records list returns None."""
        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"records": []}
        mock_resp.raise_for_status = lambda: None

        with patch(
            "czechmedmcp.articles.fetch.get_cached_response",
            return_value=None,
        ), patch(
            "httpx.AsyncClient.get",
            return_value=mock_resp,
        ):
            result = await _convert_pmc_to_pmid("PMC99999999")

        assert result is None

    @pytest.mark.asyncio
    async def test_no_pmid_in_record_returns_none(self):
        """Record without pmid field returns None."""
        mock_resp = AsyncMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "records": [{"pmcid": "PMC11193658", "doi": "10.1/x"}]
        }
        mock_resp.raise_for_status = lambda: None

        with patch(
            "czechmedmcp.articles.fetch.get_cached_response",
            return_value=None,
        ), patch(
            "httpx.AsyncClient.get",
            return_value=mock_resp,
        ):
            result = await _convert_pmc_to_pmid("PMC11193658")

        assert result is None

    @pytest.mark.asyncio
    async def test_http_error_returns_none(self):
        """HTTP errors return None gracefully."""
        with patch(
            "czechmedmcp.articles.fetch.get_cached_response",
            return_value=None,
        ), patch(
            "httpx.AsyncClient.get",
            side_effect=httpx.ConnectError("connection refused"),
        ):
            result = await _convert_pmc_to_pmid("PMC11193658")

        assert result is None


class TestArticleDetailsRouting:
    """Test _article_details routing for PMID, DOI, and PMC ID."""

    @pytest.mark.asyncio
    async def test_pmid_routes_to_pubtator(self):
        """Numeric PMID routes to PubTator3."""
        with patch(
            "czechmedmcp.articles.fetch.fetch_articles"
        ) as mock_fa:
            mock_fa.return_value = json.dumps(
                [{"title": "Test"}]
            )
            result = await _article_details("Test", "35271234")

        mock_fa.assert_called_once_with(
            [35271234], full=True, output_json=True
        )
        assert "Test" in result

    @pytest.mark.asyncio
    async def test_doi_routes_to_europe_pmc(self):
        """DOI routes to Europe PMC."""
        doi = "10.1101/2024.01.20.23288905"
        with patch(
            "czechmedmcp.articles.preprints.fetch_europe_pmc_article",
            new_callable=AsyncMock,
        ) as mock_epmc:
            mock_epmc.return_value = json.dumps(
                [{"doi": doi}]
            )
            result = await _article_details("Test", doi)

        mock_epmc.assert_called_once_with(
            doi, output_json=True
        )
        assert doi in result

    @pytest.mark.asyncio
    async def test_pmc_id_converts_and_routes(self):
        """PMC ID is converted then fetched via PubTator3."""
        with patch(
            "czechmedmcp.articles.fetch._convert_pmc_to_pmid",
            new_callable=AsyncMock,
            return_value=38768446,
        ) as mock_conv, patch(
            "czechmedmcp.articles.fetch.fetch_articles"
        ) as mock_fa:
            mock_fa.return_value = json.dumps(
                [{"title": "Converted article"}]
            )
            result = await _article_details(
                "Test", "PMC11193658"
            )

        mock_conv.assert_called_once_with("PMC11193658")
        mock_fa.assert_called_once_with(
            [38768446], full=True, output_json=True
        )
        assert "Converted article" in result

    @pytest.mark.asyncio
    async def test_pmc_id_conversion_failure(self):
        """Failed PMC-to-PMID conversion returns clear error."""
        with patch(
            "czechmedmcp.articles.fetch._convert_pmc_to_pmid",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await _article_details(
                "Test", "PMC99999999"
            )

        data = json.loads(result)
        assert len(data) == 1
        assert "Could not convert PMC99999999" in data[0]["error"]

    @pytest.mark.asyncio
    async def test_invalid_identifier_returns_error(self):
        """Completely invalid identifier returns clear error."""
        result = await _article_details("Test", "xyz_garbage")

        data = json.loads(result)
        assert len(data) == 1
        assert "Invalid identifier format" in data[0]["error"]
        assert "PMC ID" in data[0]["error"]

    @pytest.mark.asyncio
    async def test_pubtator_failure_falls_back_to_europe_pmc(
        self,
    ):
        """When PubTator3 fails, fallback to Europe PMC."""
        with patch(
            "czechmedmcp.articles.fetch.fetch_articles",
            side_effect=Exception("PubTator down"),
        ), patch(
            "czechmedmcp.articles.preprints.fetch_europe_pmc_article",
            new_callable=AsyncMock,
        ) as mock_epmc:
            mock_epmc.return_value = json.dumps(
                [{"title": "Fallback result", "source": "Europe PMC"}]
            )
            result = await _article_details("Test", "12345678")

        data = json.loads(result)
        assert data[0]["title"] == "Fallback result"

    @pytest.mark.asyncio
    async def test_both_apis_fail_returns_error(self):
        """When both PubTator3 and Europe PMC fail."""
        with patch(
            "czechmedmcp.articles.fetch.fetch_articles",
            side_effect=Exception("PubTator down"),
        ), patch(
            "czechmedmcp.articles.preprints.fetch_europe_pmc_article",
            new_callable=AsyncMock,
            side_effect=Exception("Europe PMC down"),
        ):
            result = await _article_details("Test", "12345678")

        data = json.loads(result)
        assert "Failed to fetch article" in data[0]["error"]
        assert "12345678" in data[0]["error"]
