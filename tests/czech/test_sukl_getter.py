"""Unit tests for SUKL drug getter functionality."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest


# -- Fixtures ------------------------------------------------


DRUG_DETAIL = {
    "kodSUKL": "0000123",
    "nazev": "NUROFEN 400MG",
    "doplnek": "400MG TBL FLM 24",
    "lekovaFormaKod": "TBL FLM",
    "sila": "400MG",
    "ATCkod": "M01AE01",
    "registracniCislo": "07/123/01-C",
    "drzitelKod": "Reckitt Benckiser",
    "registracePlatDo": "2028-12-31",
    "jeDodavka": True,
}

COMPOSITION = [
    {
        "kodLatky": 1234,
        "mnozstvi": "400",
        "jednotkaKod": "MG",
    },
    {
        "kodLatky": 5678,
        "mnozstvi": "50",
        "jednotkaKod": "MG",
        "nazevLatky": "Excipient",
    },
]

DOC_META_SPC = [
    {
        "typ": "spc",
        "idDokumentu": "DOC001",
        "nazevSouboru": "spc_0000123.pdf",
    }
]

DOC_META_PIL = [
    {
        "typ": "pil",
        "idDokumentu": "DOC002",
        "nazevSouboru": "pil_0000123.pdf",
    }
]

DOC_META_BOTH = DOC_META_SPC + DOC_META_PIL


def _mock_response(
    status_code: int = 200,
    json_data=None,
    text: str = "",
):
    """Build a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.is_success = 200 <= status_code < 300
    resp.json.return_value = json_data
    resp.text = text
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = (
            httpx.HTTPStatusError(
                "error",
                request=MagicMock(),
                response=resp,
            )
        )
    return resp


# ============================================================
# _fetch_composition
# ============================================================


class TestFetchComposition:
    """Tests for _fetch_composition helper."""

    async def test_returns_list_on_success(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_composition,
        )

        resp = _mock_response(
            json_data=COMPOSITION
        )
        mock_client = AsyncMock()
        mock_client.get.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".cache_response",
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_composition("0000123")
            assert result == COMPOSITION

    async def test_returns_empty_on_404(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_composition,
        )

        resp = _mock_response(status_code=404)
        resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_composition("9999999")
            assert result == []

    async def test_returns_empty_on_http_error(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_composition,
        )

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError(
            "timeout"
        )
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_composition("0000123")
            assert result == []

    async def test_uses_cache_when_available(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_composition,
        )

        cached = json.dumps(COMPOSITION)
        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=cached,
        ):
            result = await _fetch_composition("0000123")
            assert result == COMPOSITION

    async def test_returns_empty_when_response_not_list(
        self,
    ):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_composition,
        )

        resp = _mock_response(json_data={"key": "val"})
        mock_client = AsyncMock()
        mock_client.get.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".cache_response",
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_composition("0000123")
            assert result == []


# ============================================================
# _fetch_doc_metadata
# ============================================================


class TestFetchDocMetadata:
    """Tests for _fetch_doc_metadata helper."""

    async def test_returns_metadata_list(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_doc_metadata,
        )

        resp = _mock_response(json_data=DOC_META_SPC)
        mock_client = AsyncMock()
        mock_client.get.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".cache_response",
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_doc_metadata("0000123")
            assert result == DOC_META_SPC

    async def test_passes_typ_param(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_doc_metadata,
        )

        resp = _mock_response(json_data=DOC_META_PIL)
        mock_client = AsyncMock()
        mock_client.get.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".cache_response",
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_doc_metadata(
                "0000123", typ="pil"
            )
            assert len(result) == 1
            assert result[0]["typ"] == "pil"

    async def test_returns_empty_on_404(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_doc_metadata,
        )

        resp = _mock_response(status_code=404)
        resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_doc_metadata("9999999")
            assert result == []

    async def test_returns_empty_on_http_error(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_doc_metadata,
        )

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError(
            "timeout"
        )
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_doc_metadata("0000123")
            assert result == []


# ============================================================
# _build_doc_url
# ============================================================


class TestBuildDocUrl:
    """Tests for _build_doc_url helper."""

    def test_builds_spc_url(self):
        from czechmedmcp.czech.sukl.getter import (
            _build_doc_url,
        )

        url = _build_doc_url("0000123", "spc")
        assert "dokumenty/0000123/spc" in url

    def test_builds_pil_url(self):
        from czechmedmcp.czech.sukl.getter import (
            _build_doc_url,
        )

        url = _build_doc_url("0000123", "pil")
        assert "dokumenty/0000123/pil" in url


# ============================================================
# _url_is_reachable
# ============================================================


class TestUrlIsReachable:
    """Tests for _url_is_reachable helper."""

    async def test_returns_true_on_200(self):
        from czechmedmcp.czech.sukl.getter import (
            _url_is_reachable,
        )

        resp = _mock_response(status_code=200)
        mock_client = AsyncMock()
        mock_client.head.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            assert await _url_is_reachable(
                "http://example.com"
            )

    async def test_returns_false_on_404(self):
        from czechmedmcp.czech.sukl.getter import (
            _url_is_reachable,
        )

        resp = _mock_response(status_code=404)
        mock_client = AsyncMock()
        mock_client.head.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            assert not await _url_is_reachable(
                "http://example.com/nope"
            )

    async def test_returns_false_on_http_error(self):
        from czechmedmcp.czech.sukl.getter import (
            _url_is_reachable,
        )

        mock_client = AsyncMock()
        mock_client.head.side_effect = httpx.HTTPError(
            "timeout"
        )
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            assert not await _url_is_reachable(
                "http://example.com"
            )


# ============================================================
# _fetch_substance_name
# ============================================================


class TestFetchSubstanceName:
    """Tests for _fetch_substance_name helper."""

    async def test_returns_name_from_api(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_substance_name,
        )

        resp = _mock_response(
            json_data={
                "nazev": "Ibuprofen",
                "kodLatky": 1234,
            }
        )
        mock_client = AsyncMock()
        mock_client.get.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".cache_response",
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            name = await _fetch_substance_name(1234)
            assert name == "Ibuprofen"

    async def test_falls_back_to_nazevLatky(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_substance_name,
        )

        resp = _mock_response(
            json_data={"nazevLatky": "Paracetamol"}
        )
        mock_client = AsyncMock()
        mock_client.get.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".cache_response",
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            name = await _fetch_substance_name(5678)
            assert name == "Paracetamol"

    async def test_returns_none_on_404(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_substance_name,
        )

        resp = _mock_response(status_code=404)
        resp.raise_for_status = MagicMock()
        mock_client = AsyncMock()
        mock_client.get.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            name = await _fetch_substance_name(9999)
            assert name is None

    async def test_returns_none_on_http_error(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_substance_name,
        )

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError(
            "conn"
        )
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            name = await _fetch_substance_name(1234)
            assert name is None

    async def test_uses_cache(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_substance_name,
        )

        cached = json.dumps({"nazev": "Ibuprofen"})
        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=cached,
        ):
            name = await _fetch_substance_name(1234)
            assert name == "Ibuprofen"


# ============================================================
# _resolve_substance_names
# ============================================================


class TestResolveSubstanceNames:
    """Tests for _resolve_substance_names."""

    async def test_uses_inline_names(self):
        from czechmedmcp.czech.sukl.getter import (
            _resolve_substance_names,
        )

        comp = [
            {
                "kodLatky": 10,
                "nazevLatky": "Inline",
            }
        ]
        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_substance_name",
            new_callable=AsyncMock,
        ) as mock_fetch:
            result = await _resolve_substance_names(comp)
            assert result[10] == "Inline"
            mock_fetch.assert_not_called()

    async def test_fetches_missing_names(self):
        from czechmedmcp.czech.sukl.getter import (
            _resolve_substance_names,
        )

        comp = [{"kodLatky": 20}]
        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_substance_name",
            new_callable=AsyncMock,
            return_value="Fetched",
        ):
            result = await _resolve_substance_names(comp)
            assert result[20] == "Fetched"

    async def test_skips_zero_code(self):
        from czechmedmcp.czech.sukl.getter import (
            _resolve_substance_names,
        )

        comp = [{"kodLatky": 0}]
        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_substance_name",
            new_callable=AsyncMock,
        ) as mock_fetch:
            await _resolve_substance_names(comp)
            mock_fetch.assert_not_called()


# ============================================================
# _composition_to_substances
# ============================================================


class TestCompositionToSubstances:
    """Tests for _composition_to_substances."""

    async def test_converts_composition(self):
        from czechmedmcp.czech.sukl.getter import (
            _composition_to_substances,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._resolve_substance_names",
            new_callable=AsyncMock,
            return_value={
                1234: "Ibuprofen",
                5678: "Excipient",
            },
        ):
            result = await _composition_to_substances(
                COMPOSITION
            )
            assert len(result) == 2
            assert result[0]["substance_code"] == 1234
            assert (
                result[0]["substance_name"] == "Ibuprofen"
            )
            assert result[0]["strength"] == "400 MG"

    async def test_deduplicates_codes(self):
        from czechmedmcp.czech.sukl.getter import (
            _composition_to_substances,
        )

        dup_comp = [
            {"kodLatky": 1234, "mnozstvi": "400",
             "jednotkaKod": "MG"},
            {"kodLatky": 1234, "mnozstvi": "200",
             "jednotkaKod": "MG"},
        ]
        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._resolve_substance_names",
            new_callable=AsyncMock,
            return_value={1234: "Ibuprofen"},
        ):
            result = await _composition_to_substances(
                dup_comp
            )
            assert len(result) == 1

    async def test_empty_composition(self):
        from czechmedmcp.czech.sukl.getter import (
            _composition_to_substances,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._resolve_substance_names",
            new_callable=AsyncMock,
            return_value={},
        ):
            result = await _composition_to_substances([])
            assert result == []

    async def test_strength_none_when_no_amount(self):
        from czechmedmcp.czech.sukl.getter import (
            _composition_to_substances,
        )

        comp = [{"kodLatky": 1, "jednotkaKod": "MG"}]
        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._resolve_substance_names",
            new_callable=AsyncMock,
            return_value={1: "X"},
        ):
            result = await _composition_to_substances(
                comp
            )
            assert result[0]["strength"] is None


# ============================================================
# _sukl_drug_details  (main function)
# ============================================================


class TestSuklDrugDetails:
    """Tests for _sukl_drug_details main function."""

    async def test_full_detail_with_docs(self):
        """Full drug detail with SPC and PIL metadata."""
        from czechmedmcp.czech.sukl.getter import (
            _sukl_drug_details,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=DRUG_DETAIL,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_composition",
            new_callable=AsyncMock,
            return_value=COMPOSITION,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_metadata",
            new_callable=AsyncMock,
            return_value=DOC_META_BOTH,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._resolve_substance_names",
            new_callable=AsyncMock,
            return_value={
                1234: "Ibuprofen",
                5678: "Excipient",
            },
        ):
            raw = await _sukl_drug_details("0000123")
            result = json.loads(raw)

        assert result["sukl_code"] == "0000123"
        assert result["name"] == "NUROFEN 400MG"
        assert result["strength"] == "400MG"
        assert result["atc_code"] == "M01AE01"
        assert result["registration_number"] == (
            "07/123/01-C"
        )
        assert result["is_delivered"] is True
        assert result["source"] == "SUKL"
        assert result["spc_url"] is not None
        assert result["pil_url"] is not None
        assert result["spc_note"] is None
        assert result["pil_note"] is None
        assert len(result["active_substances"]) == 2

    async def test_drug_not_found(self):
        """Returns error JSON when drug not found."""
        from czechmedmcp.czech.sukl.getter import (
            _sukl_drug_details,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=None,
        ):
            raw = await _sukl_drug_details("9999999")
            result = json.loads(raw)

        assert "error" in result
        assert "9999999" in result["error"]

    async def test_no_doc_metadata_fallback_reachable(
        self,
    ):
        """Falls back to direct URL check when no metadata.

        When URL is reachable, spc_url/pil_url are set.
        """
        from czechmedmcp.czech.sukl.getter import (
            _sukl_drug_details,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=DRUG_DETAIL,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_composition",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_metadata",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._url_is_reachable",
            new_callable=AsyncMock,
            return_value=True,
        ):
            raw = await _sukl_drug_details("0000123")
            result = json.loads(raw)

        assert result["spc_url"] is not None
        assert result["pil_url"] is not None
        assert result["spc_note"] is None
        assert result["pil_note"] is None

    async def test_no_doc_metadata_fallback_unreachable(
        self,
    ):
        """When no metadata and URL unreachable, notes set."""
        from czechmedmcp.czech.sukl.getter import (
            _sukl_drug_details,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=DRUG_DETAIL,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_composition",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_metadata",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._url_is_reachable",
            new_callable=AsyncMock,
            return_value=False,
        ):
            raw = await _sukl_drug_details("0000123")
            result = json.loads(raw)

        assert result["spc_url"] is None
        assert result["pil_url"] is None
        assert result["spc_note"] is not None
        assert result["pil_note"] is not None
        assert "SÚKL" in result["spc_note"]

    async def test_empty_composition(self):
        """Drug with no composition has empty substances."""
        from czechmedmcp.czech.sukl.getter import (
            _sukl_drug_details,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=DRUG_DETAIL,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_composition",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_metadata",
            new_callable=AsyncMock,
            return_value=DOC_META_BOTH,
        ):
            raw = await _sukl_drug_details("0000123")
            result = json.loads(raw)

        assert result["active_substances"] == []


# ============================================================
# _fetch_doc_html
# ============================================================


class TestFetchDocHtml:
    """Tests for _fetch_doc_html."""

    async def test_returns_html_on_success(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_doc_html,
        )

        html = "<html><body>Test</body></html>"
        resp = _mock_response(text=html)
        mock_client = AsyncMock()
        mock_client.get.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".cache_response",
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_doc_html(
                "http://example.com/doc"
            )
            assert result == html

    async def test_returns_none_on_failure(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_doc_html,
        )

        resp = _mock_response(status_code=500)
        mock_client = AsyncMock()
        mock_client.get.return_value = resp
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_doc_html(
                "http://example.com/doc"
            )
            assert result is None

    async def test_returns_none_on_http_error(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_doc_html,
        )

        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.HTTPError(
            "fail"
        )
        mock_client.__aenter__ = AsyncMock(
            return_value=mock_client
        )
        mock_client.__aexit__ = AsyncMock(
            return_value=False
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=None,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            ".httpx.AsyncClient",
            return_value=mock_client,
        ):
            result = await _fetch_doc_html(
                "http://example.com"
            )
            assert result is None

    async def test_uses_cache(self):
        from czechmedmcp.czech.sukl.getter import (
            _fetch_doc_html,
        )

        cached_html = "<html>cached</html>"
        with patch(
            "czechmedmcp.czech.sukl.getter"
            ".get_cached_response",
            return_value=cached_html,
        ):
            result = await _fetch_doc_html(
                "http://example.com"
            )
            assert result == cached_html


# ============================================================
# _classify_pil_section
# ============================================================


class TestClassifyPilSection:
    """Tests for _classify_pil_section mapping."""

    @pytest.mark.parametrize(
        "heading,expected",
        [
            ("Dávkování a způsob podání", "dosage"),
            (
                "Jak se přípravek užívá",
                "dosage",
            ),
            ("Kontraindikace", "contraindications"),
            (
                "Neužívejte přípravek",
                "contraindications",
            ),
            (
                "Nežádoucí účinky",
                "side_effects",
            ),
            (
                "Možné nežádoucí účinky",
                "side_effects",
            ),
            ("Interakce", "interactions"),
            (
                "Jiné léky a tento přípravek",
                "interactions",
            ),
            ("Těhotenství a kojení", "pregnancy"),
            ("Uchovávání", "storage"),
        ],
    )
    def test_known_sections(self, heading, expected):
        from czechmedmcp.czech.sukl.getter import (
            _classify_pil_section,
        )

        assert _classify_pil_section(heading) == expected

    def test_unknown_section_fallback(self):
        from czechmedmcp.czech.sukl.getter import (
            _classify_pil_section,
        )

        result = _classify_pil_section(
            "Nějaká neznámá sekce"
        )
        assert isinstance(result, str)
        assert len(result) <= 30

    def test_long_heading_truncated(self):
        from czechmedmcp.czech.sukl.getter import (
            _classify_pil_section,
        )

        long = "A" * 100
        result = _classify_pil_section(long)
        assert len(result) <= 30


# ============================================================
# _parse_pil_sections / _parse_spc_sections
# ============================================================


class TestParsePilSections:
    """Tests for _parse_pil_sections."""

    def test_parses_blocks(self):
        from czechmedmcp.czech.sukl.getter import (
            _parse_pil_sections,
        )

        blocks = [
            ("Dávkování", "Take 1 tablet daily."),
            ("Nežádoucí účinky", "Headache, nausea."),
        ]
        sections = _parse_pil_sections(blocks)
        assert len(sections) == 2
        assert sections[0].section_id == "dosage"
        assert sections[1].section_id == "side_effects"

    def test_skips_empty_text(self):
        from czechmedmcp.czech.sukl.getter import (
            _parse_pil_sections,
        )

        blocks = [
            ("Dávkování", ""),
            ("Nežádoucí účinky", "Some text"),
        ]
        sections = _parse_pil_sections(blocks)
        assert len(sections) == 1

    def test_empty_blocks(self):
        from czechmedmcp.czech.sukl.getter import (
            _parse_pil_sections,
        )

        assert _parse_pil_sections([]) == []


class TestParseSpcSections:
    """Tests for _parse_spc_sections."""

    def test_parses_numbered_heading(self):
        from czechmedmcp.czech.sukl.getter import (
            _parse_spc_sections,
        )

        blocks = [
            (
                "4.1 Terapeutické indikace",
                "Pain relief.",
            ),
            (
                "4.2 Dávkování",
                "Adults: 400mg.",
            ),
        ]
        sections = _parse_spc_sections(blocks)
        assert len(sections) == 2
        assert sections[0].section_id == "4.1"
        assert sections[0].title == (
            "Terapeutické indikace"
        )
        assert sections[1].section_id == "4.2"

    def test_unnumbered_heading_fallback(self):
        from czechmedmcp.czech.sukl.getter import (
            _parse_spc_sections,
        )

        blocks = [
            ("Introduction", "Some intro text."),
        ]
        sections = _parse_spc_sections(blocks)
        assert len(sections) == 1
        assert sections[0].section_id == "Introducti"
        assert sections[0].title == "Introduction"

    def test_skips_empty_text(self):
        from czechmedmcp.czech.sukl.getter import (
            _parse_spc_sections,
        )

        blocks = [("4.1 Heading", "")]
        assert _parse_spc_sections(blocks) == []


# ============================================================
# _filter_sections
# ============================================================


class TestFilterSections:
    """Tests for _filter_sections."""

    def test_no_filter_returns_all(self):
        from czechmedmcp.czech.sukl.getter import (
            _filter_sections,
        )
        from czechmedmcp.czech.sukl.models import (
            DocumentSection,
        )

        sections = [
            DocumentSection(
                section_id="4.1",
                title="A",
                content="x",
            ),
            DocumentSection(
                section_id="4.2",
                title="B",
                content="y",
            ),
        ]
        assert _filter_sections(sections, None) == sections

    def test_filters_by_prefix(self):
        from czechmedmcp.czech.sukl.getter import (
            _filter_sections,
        )
        from czechmedmcp.czech.sukl.models import (
            DocumentSection,
        )

        sections = [
            DocumentSection(
                section_id="4.1",
                title="A",
                content="x",
            ),
            DocumentSection(
                section_id="4.2",
                title="B",
                content="y",
            ),
            DocumentSection(
                section_id="5.1",
                title="C",
                content="z",
            ),
        ]
        result = _filter_sections(sections, "4")
        assert len(result) == 2

    def test_filter_no_match(self):
        from czechmedmcp.czech.sukl.getter import (
            _filter_sections,
        )
        from czechmedmcp.czech.sukl.models import (
            DocumentSection,
        )

        sections = [
            DocumentSection(
                section_id="4.1",
                title="A",
                content="x",
            ),
        ]
        result = _filter_sections(sections, "9")
        assert result == []


# ============================================================
# _format_doc_markdown
# ============================================================


class TestFormatDocMarkdown:
    """Tests for _format_doc_markdown."""

    def test_format_with_sections(self):
        from czechmedmcp.czech.sukl.getter import (
            _format_doc_markdown,
        )
        from czechmedmcp.czech.sukl.models import (
            DocumentContent,
            DocumentSection,
        )

        doc = DocumentContent(
            sukl_code="0000123",
            document_type="SPC",
            title="NUROFEN 400MG",
            sections=[
                DocumentSection(
                    section_id="4.1",
                    title="Indikace",
                    content="Pain relief.",
                ),
            ],
            url="http://example.com/spc",
        )
        md = _format_doc_markdown(doc, None)
        assert "## SPC: NUROFEN 400MG" in md
        assert "### Indikace" in md
        assert "Pain relief." in md
        assert "0000123" in md

    def test_format_no_sections_shows_url(self):
        from czechmedmcp.czech.sukl.getter import (
            _format_doc_markdown,
        )
        from czechmedmcp.czech.sukl.models import (
            DocumentContent,
        )

        doc = DocumentContent(
            sukl_code="0000123",
            document_type="PIL",
            title="Drug X",
            sections=[],
            url="http://example.com/pil",
        )
        md = _format_doc_markdown(doc, None)
        assert "http://example.com/pil" in md

    def test_format_with_filter_note(self):
        from czechmedmcp.czech.sukl.getter import (
            _format_doc_markdown,
        )
        from czechmedmcp.czech.sukl.models import (
            DocumentContent,
            DocumentSection,
        )

        doc = DocumentContent(
            sukl_code="0000123",
            document_type="SPC",
            title="Drug",
            sections=[
                DocumentSection(
                    section_id="4.1",
                    title="X",
                    content="Y",
                ),
            ],
            url="http://example.com",
        )
        md = _format_doc_markdown(doc, "4.1")
        assert "Filtr sekce: 4.1" in md


# ============================================================
# _sukl_document_getter / _sukl_spc_getter / _sukl_pil_getter
# ============================================================


class TestSuklDocumentGetter:
    """Tests for document getter functions."""

    async def test_spc_getter_success(self):
        from czechmedmcp.czech.sukl.getter import (
            _sukl_spc_getter,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=DRUG_DETAIL,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_metadata",
            new_callable=AsyncMock,
            return_value=DOC_META_SPC,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._scrape_document",
            new_callable=AsyncMock,
            return_value=[],
        ):
            raw = await _sukl_spc_getter("0000123")
            result = json.loads(raw)
            sc = result["structuredContent"]
            assert sc["sukl_code"] == "0000123"
            assert sc["document_type"] == "SPC"
            assert sc["source"] == "SUKL"

    async def test_pil_getter_success(self):
        from czechmedmcp.czech.sukl.getter import (
            _sukl_pil_getter,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=DRUG_DETAIL,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_metadata",
            new_callable=AsyncMock,
            return_value=DOC_META_PIL,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._scrape_document",
            new_callable=AsyncMock,
            return_value=[],
        ):
            raw = await _sukl_pil_getter("0000123")
            result = json.loads(raw)
            sc = result["structuredContent"]
            assert sc["document_type"] == "PIL"

    async def test_document_getter_drug_not_found(self):
        from czechmedmcp.czech.sukl.getter import (
            _sukl_spc_getter,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=None,
        ):
            raw = await _sukl_spc_getter("9999999")
            result = json.loads(raw)
            assert "error" in result
            assert "9999999" in result["error"]

    async def test_document_getter_no_metadata(self):
        from czechmedmcp.czech.sukl.getter import (
            _sukl_spc_getter,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=DRUG_DETAIL,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_metadata",
            new_callable=AsyncMock,
            return_value=[],
        ):
            raw = await _sukl_spc_getter("0000123")
            result = json.loads(raw)
            assert "error" in result
            assert result["sukl_code"] == "0000123"

    async def test_document_getter_with_section_filter(
        self,
    ):
        from czechmedmcp.czech.sukl.getter import (
            _sukl_spc_getter,
        )
        from czechmedmcp.czech.sukl.models import (
            DocumentSection,
        )

        sections = [
            DocumentSection(
                section_id="4.1",
                title="Indikace",
                content="Pain.",
            ),
            DocumentSection(
                section_id="5.1",
                title="PD",
                content="Pharma.",
            ),
        ]
        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=DRUG_DETAIL,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_metadata",
            new_callable=AsyncMock,
            return_value=DOC_META_SPC,
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._scrape_document",
            new_callable=AsyncMock,
            return_value=sections,
        ):
            raw = await _sukl_spc_getter(
                "0000123", section="4"
            )
            result = json.loads(raw)
            sc = result["structuredContent"]
            assert len(sc["sections"]) == 1
            assert (
                sc["sections"][0]["section_id"] == "4.1"
            )


# ============================================================
# _scrape_document
# ============================================================


class TestScrapeDocument:
    """Tests for _scrape_document."""

    async def test_returns_empty_when_no_html(self):
        from czechmedmcp.czech.sukl.getter import (
            _scrape_document,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_html",
            new_callable=AsyncMock,
            return_value=None,
        ):
            result = await _scrape_document(
                "http://example.com", "spc"
            )
            assert result == []

    async def test_returns_empty_on_unparseable_html(
        self,
    ):
        from czechmedmcp.czech.sukl.getter import (
            _scrape_document,
        )

        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_html",
            new_callable=AsyncMock,
            return_value="<html>test</html>",
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._parse_html_to_tree",
            return_value=None,
        ):
            result = await _scrape_document(
                "http://example.com", "pil"
            )
            assert result == []

    async def test_pil_type_uses_pil_parser(self):
        from czechmedmcp.czech.sukl.getter import (
            _scrape_document,
        )
        from czechmedmcp.czech.sukl.models import (
            DocumentSection,
        )

        mock_sections = [
            DocumentSection(
                section_id="dosage",
                title="Dávkování",
                content="Take 1 tablet.",
            ),
        ]
        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_html",
            new_callable=AsyncMock,
            return_value="<html>x</html>",
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._parse_html_to_tree",
            return_value=MagicMock(),
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._extract_text_blocks",
            return_value=[
                ("Dávkování", "Take 1 tablet.")
            ],
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._parse_pil_sections",
            return_value=mock_sections,
        ) as mock_pil:
            result = await _scrape_document(
                "http://example.com", "pil"
            )
            mock_pil.assert_called_once()
            assert len(result) == 1

    async def test_spc_type_uses_spc_parser(self):
        from czechmedmcp.czech.sukl.getter import (
            _scrape_document,
        )
        from czechmedmcp.czech.sukl.models import (
            DocumentSection,
        )

        mock_sections = [
            DocumentSection(
                section_id="4.1",
                title="Indikace",
                content="Pain.",
            ),
        ]
        with patch(
            "czechmedmcp.czech.sukl.getter"
            "._fetch_doc_html",
            new_callable=AsyncMock,
            return_value="<html>x</html>",
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._parse_html_to_tree",
            return_value=MagicMock(),
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._extract_text_blocks",
            return_value=[
                ("4.1 Indikace", "Pain.")
            ],
        ), patch(
            "czechmedmcp.czech.sukl.getter"
            "._parse_spc_sections",
            return_value=mock_sections,
        ) as mock_spc:
            result = await _scrape_document(
                "http://example.com", "spc"
            )
            mock_spc.assert_called_once()
            assert len(result) == 1


# ============================================================
# _SPC_SECTION_RE regex
# ============================================================


class TestSpcSectionRegex:
    """Tests for _SPC_SECTION_RE pattern."""

    @pytest.mark.parametrize(
        "heading,num,title",
        [
            ("4.1 Terapeutické indikace", "4.1", "Terapeutické indikace"),
            ("1 Název přípravku", "1", "Název přípravku"),
            ("4.8 Nežádoucí účinky", "4.8", "Nežádoucí účinky"),
            ("5.1 Farmakodynamické", "5.1", "Farmakodynamické"),
        ],
    )
    def test_matches_numbered_headings(
        self, heading, num, title
    ):
        from czechmedmcp.czech.sukl.getter import (
            _SPC_SECTION_RE,
        )

        m = _SPC_SECTION_RE.match(heading)
        assert m is not None
        assert m.group(1) == num
        assert m.group(2).strip() == title

    def test_no_match_on_plain_text(self):
        from czechmedmcp.czech.sukl.getter import (
            _SPC_SECTION_RE,
        )

        assert _SPC_SECTION_RE.match("Introduction") is None
