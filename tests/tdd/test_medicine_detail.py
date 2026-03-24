"""Tests for GetMedicineDetail substance names and SPC/PIL URLs.

US7: Verify substance name lookup and SPC/PIL URL handling.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest

# -- Fixtures --------------------------------------------------------

_DRUG_DETAIL = {
    "kodSUKL": "0124137",
    "nazev": "IBUPROFEN 400MG",
    "sila": "400MG",
    "lekovaFormaKod": "TBL FLM",
    "ATCkod": "M01AE01",
    "registracniCislo": "07/456/01-C",
    "drzitelKod": "Zentiva",
    "registracePlatDo": "2029-06-30",
    "jeDodavka": True,
}

_COMPOSITION = [
    {
        "kodLatky": 1593,
        "mnozstvi": "400",
        "jednotkaKod": "MG",
    }
]

_COMPOSITION_WITH_INLINE_NAME = [
    {
        "kodLatky": 1593,
        "nazevLatky": "IBUPROFENUM",
        "mnozstvi": "400",
        "jednotkaKod": "MG",
    }
]

_COMPOSITION_TWO = [
    {
        "kodLatky": 1593,
        "mnozstvi": "400",
        "jednotkaKod": "MG",
    },
    {
        "kodLatky": 999,
        "mnozstvi": "50",
        "jednotkaKod": "MG",
    },
]

_SUBSTANCE_RESPONSE = {"nazev": "IBUPROFENUM"}

_DOC_META_SPC = [
    {
        "typ": "spc",
        "idDokumentu": "DOC001",
        "nazevSouboru": "spc_0124137.pdf",
    }
]

_DOC_META_PIL = [
    {
        "typ": "pil",
        "idDokumentu": "DOC002",
        "nazevSouboru": "pil_0124137.pdf",
    }
]

_DOC_META_BOTH = _DOC_META_SPC + _DOC_META_PIL


# -- Helpers ---------------------------------------------------------

def _getter():
    """Import lazily to avoid import-time side effects."""
    from czechmedmcp.czech.sukl import getter
    return getter


def _patch_all(
    detail=_DRUG_DETAIL,
    composition=None,
    doc_meta=None,
    substance_resp=None,
):
    """Return a context manager patching all external calls."""
    if composition is None:
        composition = _COMPOSITION
    if doc_meta is None:
        doc_meta = []
    if substance_resp is None:
        substance_resp = _SUBSTANCE_RESPONSE

    mod = "czechmedmcp.czech.sukl.getter"

    class _Ctx:
        def __enter__(self_):
            self_._patches = [
                patch(
                    f"{mod}._fetch_drug_detail",
                    new_callable=AsyncMock,
                    return_value=detail,
                ),
                patch(
                    f"{mod}._fetch_composition",
                    new_callable=AsyncMock,
                    return_value=composition,
                ),
                patch(
                    f"{mod}._fetch_doc_metadata",
                    new_callable=AsyncMock,
                    return_value=doc_meta,
                ),
                patch(
                    f"{mod}._fetch_substance_name",
                    new_callable=AsyncMock,
                    return_value=(
                        substance_resp.get("nazev")
                        if isinstance(substance_resp, dict)
                        else substance_resp
                    ),
                ),
            ]
            for p in self_._patches:
                p.start()
            return self_

        def __exit__(self_, *args):
            for p in self_._patches:
                p.stop()

    return _Ctx()


# -- Test class ------------------------------------------------------

class TestMedicineDetailSubstanceNames:
    """Substance name resolution in GetMedicineDetail."""

    @pytest.mark.asyncio
    async def test_substance_name_from_api_lookup(self):
        """Substance name resolved via /latky/ endpoint."""
        g = _getter()
        with _patch_all():
            raw = await g._sukl_drug_details("0124137")
        result = json.loads(raw)

        subs = result["active_substances"]
        assert len(subs) == 1
        assert subs[0]["substance_code"] == 1593
        assert subs[0]["substance_name"] == "IBUPROFENUM"
        assert subs[0]["strength"] == "400 MG"

    @pytest.mark.asyncio
    async def test_substance_name_inline_in_composition(
        self,
    ):
        """If composition already has nazevLatky, use it."""
        g = _getter()
        with _patch_all(
            composition=_COMPOSITION_WITH_INLINE_NAME,
        ):
            raw = await g._sukl_drug_details("0124137")
        result = json.loads(raw)

        subs = result["active_substances"]
        assert subs[0]["substance_name"] == "IBUPROFENUM"

    @pytest.mark.asyncio
    async def test_substance_name_null_on_failure(self):
        """Substance name is None when lookup fails."""
        g = _getter()
        mod = "czechmedmcp.czech.sukl.getter"

        with patch(
            f"{mod}._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=_DRUG_DETAIL,
        ), patch(
            f"{mod}._fetch_composition",
            new_callable=AsyncMock,
            return_value=_COMPOSITION,
        ), patch(
            f"{mod}._fetch_doc_metadata",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            f"{mod}._fetch_substance_name",
            new_callable=AsyncMock,
            return_value=None,
        ):
            raw = await g._sukl_drug_details("0124137")
        result = json.loads(raw)

        subs = result["active_substances"]
        assert subs[0]["substance_name"] is None

    @pytest.mark.asyncio
    async def test_multiple_substances(self):
        """Multiple substances each get names resolved."""
        g = _getter()
        mod = "czechmedmcp.czech.sukl.getter"

        async def _mock_fetch_name(code):
            return {
                1593: "IBUPROFENUM",
                999: "COFFEINUM",
            }.get(code)

        with patch(
            f"{mod}._fetch_drug_detail",
            new_callable=AsyncMock,
            return_value=_DRUG_DETAIL,
        ), patch(
            f"{mod}._fetch_composition",
            new_callable=AsyncMock,
            return_value=_COMPOSITION_TWO,
        ), patch(
            f"{mod}._fetch_doc_metadata",
            new_callable=AsyncMock,
            return_value=[],
        ), patch(
            f"{mod}._fetch_substance_name",
            side_effect=_mock_fetch_name,
        ):
            raw = await g._sukl_drug_details("0124137")
        result = json.loads(raw)

        subs = result["active_substances"]
        assert len(subs) == 2
        assert subs[0]["substance_name"] == "IBUPROFENUM"
        assert subs[1]["substance_name"] == "COFFEINUM"


class TestMedicineDetailSpcPilUrls:
    """SPC/PIL URL and note handling."""

    @pytest.mark.asyncio
    async def test_spc_url_present_when_metadata_exists(
        self,
    ):
        """SPC URL built when doc metadata has spc."""
        g = _getter()
        with _patch_all(doc_meta=_DOC_META_BOTH):
            raw = await g._sukl_drug_details("0124137")
        result = json.loads(raw)

        assert result["spc_url"] is not None
        assert "spc" in result["spc_url"]
        assert result["spc_note"] is None

    @pytest.mark.asyncio
    async def test_pil_url_present_when_metadata_exists(
        self,
    ):
        """PIL URL built when doc metadata has pil."""
        g = _getter()
        with _patch_all(doc_meta=_DOC_META_BOTH):
            raw = await g._sukl_drug_details("0124137")
        result = json.loads(raw)

        assert result["pil_url"] is not None
        assert "pil" in result["pil_url"]
        assert result["pil_note"] is None

    @pytest.mark.asyncio
    async def test_spc_url_null_with_note_when_missing(
        self,
    ):
        """SPC URL is null with explanatory note."""
        g = _getter()
        with _patch_all(doc_meta=[]):
            raw = await g._sukl_drug_details("0124137")
        result = json.loads(raw)

        assert result["spc_url"] is None
        assert result["spc_note"] is not None
        assert "SPC" in result["spc_note"]
        assert "SÚKL" in result["spc_note"]

    @pytest.mark.asyncio
    async def test_pil_url_null_with_note_when_missing(
        self,
    ):
        """PIL URL is null with explanatory note."""
        g = _getter()
        with _patch_all(doc_meta=[]):
            raw = await g._sukl_drug_details("0124137")
        result = json.loads(raw)

        assert result["pil_url"] is None
        assert result["pil_note"] is not None
        assert "PIL" in result["pil_note"]
        assert "SÚKL" in result["pil_note"]

    @pytest.mark.asyncio
    async def test_partial_docs_spc_only(self):
        """Only SPC available, PIL shows note."""
        g = _getter()
        with _patch_all(doc_meta=_DOC_META_SPC):
            raw = await g._sukl_drug_details("0124137")
        result = json.loads(raw)

        assert result["spc_url"] is not None
        assert result["spc_note"] is None
        assert result["pil_url"] is None
        assert result["pil_note"] is not None

    @pytest.mark.asyncio
    async def test_partial_docs_pil_only(self):
        """Only PIL available, SPC shows note."""
        g = _getter()
        with _patch_all(doc_meta=_DOC_META_PIL):
            raw = await g._sukl_drug_details("0124137")
        result = json.loads(raw)

        assert result["spc_url"] is None
        assert result["spc_note"] is not None
        assert result["pil_url"] is not None
        assert result["pil_note"] is None


class TestFetchSubstanceName:
    """Direct tests for _fetch_substance_name."""

    @pytest.mark.asyncio
    async def test_fetch_returns_nazev(self):
        """API returns nazev field."""
        g = _getter()
        mod = "czechmedmcp.czech.sukl.getter"

        with patch(
            f"{mod}.get_cached_response",
            return_value=None,
        ), patch(
            f"{mod}.cache_response",
        ), patch(
            f"{mod}.httpx.AsyncClient",
        ) as mock_client_cls:
            from unittest.mock import MagicMock

            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {
                "nazev": "PARACETAMOLUM"
            }

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                return_value=mock_resp
            )
            mock_client.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client.__aexit__ = AsyncMock(
                return_value=False
            )
            mock_client_cls.return_value = mock_client

            name = await g._fetch_substance_name(500)
            assert name == "PARACETAMOLUM"

    @pytest.mark.asyncio
    async def test_fetch_returns_none_on_404(self):
        """API 404 returns None."""
        g = _getter()
        mod = "czechmedmcp.czech.sukl.getter"

        with patch(
            f"{mod}.get_cached_response",
            return_value=None,
        ), patch(
            f"{mod}.httpx.AsyncClient",
        ) as mock_client_cls:
            mock_resp = AsyncMock()
            mock_resp.status_code = 404

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(
                return_value=mock_resp
            )
            mock_client.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client.__aexit__ = AsyncMock(
                return_value=False
            )
            mock_client_cls.return_value = mock_client

            name = await g._fetch_substance_name(99999)
            assert name is None

    @pytest.mark.asyncio
    async def test_fetch_uses_cache(self):
        """Cached response is used without API call."""
        g = _getter()
        mod = "czechmedmcp.czech.sukl.getter"

        cached = json.dumps({"nazev": "CACHED_NAME"})
        with patch(
            f"{mod}.get_cached_response",
            return_value=cached,
        ):
            name = await g._fetch_substance_name(123)
            assert name == "CACHED_NAME"
