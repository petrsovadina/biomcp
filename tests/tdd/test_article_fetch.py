"""Unit tests for articles/fetch.py — offline, all HTTP mocked."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from czechmedmcp.articles.fetch import (
    Article,
    FetchArticlesResponse,
    Passage,
    PassageInfo,
    _article_details,
    _convert_pmc_to_pmid,
    _fetch_abstract_efetch,
    call_pubtator_api,
    fetch_articles,
    is_doi,
    is_pmc_id,
    is_pmid,
)
from czechmedmcp.http_client import RequestError


# ── Identifier helpers ──────────────────────────────────


class TestIsDoi:
    def test_valid_doi(self):
        assert is_doi("10.1101/2024.01.20.23288905")

    def test_valid_doi_short(self):
        assert is_doi("10.1038/s41586-020-2649-2")

    def test_invalid_doi_no_prefix(self):
        assert not is_doi("1101/2024.01.20.23288905")

    def test_invalid_doi_numeric(self):
        assert not is_doi("34397683")

    def test_invalid_doi_pmc(self):
        assert not is_doi("PMC11193658")

    def test_empty_string(self):
        assert not is_doi("")


class TestIsPmid:
    def test_valid_pmid(self):
        assert is_pmid("34397683")

    def test_valid_pmid_short(self):
        assert is_pmid("123")

    def test_invalid_pmid_letters(self):
        assert not is_pmid("PMC11193658")

    def test_invalid_pmid_doi(self):
        assert not is_pmid("10.1038/foo")

    def test_empty_string(self):
        assert not is_pmid("")


class TestIsPmcId:
    def test_valid_pmc_7_digits(self):
        assert is_pmc_id("PMC1234567")

    def test_valid_pmc_8_digits(self):
        assert is_pmc_id("PMC11193658")

    def test_case_insensitive(self):
        assert is_pmc_id("pmc11193658")

    def test_invalid_pmc_too_short(self):
        assert not is_pmc_id("PMC123")

    def test_invalid_pmc_no_prefix(self):
        assert not is_pmc_id("11193658")

    def test_invalid_pmc_numeric(self):
        assert not is_pmc_id("34397683")

    def test_empty_string(self):
        assert not is_pmc_id("")


# ── Passage / Article models ────────────────────────────


def _make_passage(section_type, text, passage_type=None):
    info = PassageInfo(
        section_type=section_type,
        **{"type": passage_type} if passage_type else {},
    )
    return Passage(infons=info, text=text)


class TestPassage:
    def test_section_type_from_section_type(self):
        p = _make_passage("abstract", "txt")
        assert p.section_type == "ABSTRACT"

    def test_section_type_fallback_to_passage_type(self):
        p = Passage(
            infons=PassageInfo(
                section_type=None,
                **{"type": "title"},
            ),
            text="t",
        )
        assert p.section_type == "TITLE"

    def test_section_type_unknown_when_none(self):
        p = Passage(infons=None, text="t")
        assert p.section_type == "UNKNOWN"

    def test_is_title(self):
        p = _make_passage("title", "My Title")
        assert p.is_title

    def test_is_abstract(self):
        p = _make_passage("abstract", "Some abstract")
        assert p.is_abstract

    def test_is_text_intro(self):
        p = _make_passage("INTRO", "Intro text")
        assert p.is_text

    def test_is_text_results(self):
        p = _make_passage("RESULTS", "Results text")
        assert p.is_text

    def test_is_text_false_for_title(self):
        p = _make_passage("title", "Title")
        assert not p.is_text


class TestArticleModel:
    def _article(self, passages):
        return Article(
            pmid=12345,
            pmcid="PMC1234567",
            passages=passages,
        )

    def test_title_from_passages(self):
        a = self._article([
            _make_passage("title", "My Title"),
            _make_passage("abstract", "Abstract text"),
        ])
        assert a.title == "My Title"

    def test_title_fallback_when_no_title_passage(self):
        a = self._article([
            _make_passage("abstract", "Abstract text"),
        ])
        assert a.title == "Article: 12345"

    def test_title_joins_multiple_titles(self):
        a = self._article([
            _make_passage("title", "Part 1"),
            _make_passage("title", "Part 2"),
        ])
        assert a.title == "Part 1 ... Part 2"

    def test_abstract_from_passages(self):
        a = self._article([
            _make_passage("abstract", "Line 1"),
            _make_passage("abstract", "Line 2"),
        ])
        assert a.abstract == "Line 1\n\nLine 2"

    def test_abstract_fallback(self):
        a = self._article([
            _make_passage("title", "T"),
        ])
        assert a.abstract == "Article: 12345"

    def test_full_text_from_passages(self):
        a = self._article([
            _make_passage("INTRO", "Intro"),
            _make_passage("RESULTS", "Results"),
        ])
        assert a.full_text == "Intro\n\nResults"

    def test_full_text_empty_when_none(self):
        a = self._article([
            _make_passage("title", "T"),
        ])
        assert a.full_text == ""

    def test_pubmed_url(self):
        a = self._article([_make_passage("title", "T")])
        assert a.pubmed_url == (
            "https://pubmed.ncbi.nlm.nih.gov/12345/"
        )

    def test_pubmed_url_none_when_no_pmid(self):
        a = Article(pmid=None, passages=[
            _make_passage("title", "T"),
        ])
        assert a.pubmed_url is None

    def test_pmc_url(self):
        a = self._article([_make_passage("title", "T")])
        assert a.pmc_url == (
            "https://www.ncbi.nlm.nih.gov/pmc/articles/"
            "PMC1234567/"
        )

    def test_pmc_url_none(self):
        a = Article(pmid=1, pmcid=None, passages=[
            _make_passage("title", "T"),
        ])
        assert a.pmc_url is None


class TestFetchArticlesResponse:
    def test_get_abstract_found(self):
        a = Article(
            pmid=111,
            passages=[_make_passage("abstract", "AB")],
        )
        resp = FetchArticlesResponse(**{"PubTator3": [a]})
        assert resp.get_abstract(111) == "AB"

    def test_get_abstract_not_found(self):
        a = Article(
            pmid=111,
            passages=[_make_passage("abstract", "AB")],
        )
        resp = FetchArticlesResponse(**{"PubTator3": [a]})
        assert resp.get_abstract(999) is None

    def test_get_abstract_none_pmid(self):
        a = Article(
            pmid=111,
            passages=[_make_passage("abstract", "AB")],
        )
        resp = FetchArticlesResponse(**{"PubTator3": [a]})
        assert resp.get_abstract(None) is None


# ── _convert_pmc_to_pmid ────────────────────────────────


class TestConvertPmcToPmid:
    @patch(
        "czechmedmcp.articles.fetch.get_cached_response",
        return_value=None,
    )
    @patch("httpx.AsyncClient")
    async def test_success(self, mock_client_cls, _cache):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "records": [{"pmid": "34397683"}],
        }

        client_inst = AsyncMock()
        client_inst.get = AsyncMock(return_value=mock_resp)
        client_inst.__aenter__ = AsyncMock(
            return_value=client_inst,
        )
        client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = client_inst

        with patch(
            "czechmedmcp.articles.fetch.cache_response"
        ):
            result = await _convert_pmc_to_pmid("PMC11193658")

        assert result == 34397683

    @patch(
        "czechmedmcp.articles.fetch.get_cached_response",
        return_value="34397683",
    )
    async def test_cached(self, _cache):
        result = await _convert_pmc_to_pmid("PMC11193658")
        assert result == 34397683

    @patch(
        "czechmedmcp.articles.fetch.get_cached_response",
        return_value="not_an_int",
    )
    @patch("httpx.AsyncClient")
    async def test_cached_invalid_falls_through(
        self, mock_client_cls, _cache
    ):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"records": []}

        client_inst = AsyncMock()
        client_inst.get = AsyncMock(return_value=mock_resp)
        client_inst.__aenter__ = AsyncMock(
            return_value=client_inst,
        )
        client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = client_inst

        result = await _convert_pmc_to_pmid("PMC11193658")
        assert result is None

    @patch(
        "czechmedmcp.articles.fetch.get_cached_response",
        return_value=None,
    )
    @patch("httpx.AsyncClient")
    async def test_no_records(self, mock_client_cls, _cache):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"records": []}

        client_inst = AsyncMock()
        client_inst.get = AsyncMock(return_value=mock_resp)
        client_inst.__aenter__ = AsyncMock(
            return_value=client_inst,
        )
        client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = client_inst

        result = await _convert_pmc_to_pmid("PMC0000000")
        assert result is None

    @patch(
        "czechmedmcp.articles.fetch.get_cached_response",
        return_value=None,
    )
    @patch("httpx.AsyncClient")
    async def test_http_error(self, mock_client_cls, _cache):
        client_inst = AsyncMock()
        client_inst.get = AsyncMock(
            side_effect=httpx.HTTPError("timeout"),
        )
        client_inst.__aenter__ = AsyncMock(
            return_value=client_inst,
        )
        client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = client_inst

        result = await _convert_pmc_to_pmid("PMC1234567")
        assert result is None

    @patch(
        "czechmedmcp.articles.fetch.get_cached_response",
        return_value=None,
    )
    @patch("httpx.AsyncClient")
    async def test_pmid_none_in_record(
        self, mock_client_cls, _cache
    ):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "records": [{"pmid": None}],
        }

        client_inst = AsyncMock()
        client_inst.get = AsyncMock(return_value=mock_resp)
        client_inst.__aenter__ = AsyncMock(
            return_value=client_inst,
        )
        client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = client_inst

        result = await _convert_pmc_to_pmid("PMC1234567")
        assert result is None


# ── _fetch_abstract_efetch ───────────────────────────────


class TestFetchAbstractEfetch:
    @patch(
        "czechmedmcp.articles.fetch.get_cached_response",
        return_value=None,
    )
    @patch("httpx.AsyncClient")
    async def test_success(self, mock_client_cls, _cache):
        long_abstract = "A" * 100
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.text = f"  {long_abstract}  "

        client_inst = AsyncMock()
        client_inst.get = AsyncMock(return_value=mock_resp)
        client_inst.__aenter__ = AsyncMock(
            return_value=client_inst,
        )
        client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = client_inst

        with patch(
            "czechmedmcp.articles.fetch.cache_response"
        ) as mock_cache:
            result = await _fetch_abstract_efetch(12345)

        assert result == long_abstract
        mock_cache.assert_called_once()

    @patch(
        "czechmedmcp.articles.fetch.get_cached_response",
        return_value="cached abstract text here (long enough)",
    )
    async def test_returns_cached(self, _cache):
        result = await _fetch_abstract_efetch(12345)
        assert result == (
            "cached abstract text here (long enough)"
        )

    @patch(
        "czechmedmcp.articles.fetch.get_cached_response",
        return_value=None,
    )
    @patch("httpx.AsyncClient")
    async def test_short_text_returns_none(
        self, mock_client_cls, _cache
    ):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.text = "Short"

        client_inst = AsyncMock()
        client_inst.get = AsyncMock(return_value=mock_resp)
        client_inst.__aenter__ = AsyncMock(
            return_value=client_inst,
        )
        client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = client_inst

        result = await _fetch_abstract_efetch(12345)
        assert result is None

    @patch(
        "czechmedmcp.articles.fetch.get_cached_response",
        return_value=None,
    )
    @patch("httpx.AsyncClient")
    async def test_http_error_returns_none(
        self, mock_client_cls, _cache
    ):
        client_inst = AsyncMock()
        client_inst.get = AsyncMock(
            side_effect=httpx.HTTPError("fail"),
        )
        client_inst.__aenter__ = AsyncMock(
            return_value=client_inst,
        )
        client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = client_inst

        result = await _fetch_abstract_efetch(12345)
        assert result is None

    @patch(
        "czechmedmcp.articles.fetch.get_cached_response",
        return_value=None,
    )
    @patch("httpx.AsyncClient")
    async def test_empty_text_returns_none(
        self, mock_client_cls, _cache
    ):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.text = "   "

        client_inst = AsyncMock()
        client_inst.get = AsyncMock(return_value=mock_resp)
        client_inst.__aenter__ = AsyncMock(
            return_value=client_inst,
        )
        client_inst.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = client_inst

        result = await _fetch_abstract_efetch(12345)
        assert result is None


# ── fetch_articles ───────────────────────────────────────


def _pubtator_response(
    pmid=12345,
    title="Test Title",
    abstract_text="Test Abstract",
):
    """Build a FetchArticlesResponse for testing."""
    passages = [
        _make_passage("title", title),
        _make_passage("abstract", abstract_text),
        _make_passage("INTRO", "Introduction text"),
    ]
    article = Article(
        pmid=pmid,
        pmcid=f"PMC{pmid}0",
        passages=passages,
    )
    return FetchArticlesResponse(
        **{"PubTator3": [article]}
    )


class TestFetchArticles:
    @patch(
        "czechmedmcp.articles.fetch.call_pubtator_api",
    )
    async def test_success_markdown(self, mock_api):
        mock_api.return_value = (
            _pubtator_response(),
            None,
        )
        result = await fetch_articles(
            [12345], full=False
        )
        # Should be markdown (not JSON)
        assert not result.startswith("[")
        assert "Test Title" in result

    @patch(
        "czechmedmcp.articles.fetch.call_pubtator_api",
    )
    async def test_success_json(self, mock_api):
        mock_api.return_value = (
            _pubtator_response(),
            None,
        )
        result = await fetch_articles(
            [12345], full=False, output_json=True
        )
        data = json.loads(result)
        assert len(data) == 1
        assert data[0]["title"] == "Test Title"
        assert data[0]["abstract"] == "Test Abstract"

    @patch(
        "czechmedmcp.articles.fetch.call_pubtator_api",
    )
    async def test_full_false_excludes_full_text(
        self, mock_api
    ):
        mock_api.return_value = (
            _pubtator_response(),
            None,
        )
        result = await fetch_articles(
            [12345], full=False, output_json=True
        )
        data = json.loads(result)
        assert "full_text" not in data[0]

    @patch(
        "czechmedmcp.articles.fetch.call_pubtator_api",
    )
    async def test_full_true_includes_full_text(
        self, mock_api
    ):
        mock_api.return_value = (
            _pubtator_response(),
            None,
        )
        result = await fetch_articles(
            [12345], full=True, output_json=True
        )
        data = json.loads(result)
        assert "full_text" in data[0]
        assert data[0]["full_text"] == "Introduction text"

    @patch(
        "czechmedmcp.articles.fetch.call_pubtator_api",
    )
    async def test_error_response(self, mock_api):
        err = RequestError(code=500, message="Server err")
        mock_api.return_value = (None, err)
        result = await fetch_articles(
            [12345], full=True, output_json=True
        )
        data = json.loads(result)
        assert "error" in data[0]
        assert "500" in data[0]["error"]

    @patch(
        "czechmedmcp.articles.fetch._fetch_abstract_efetch",
    )
    @patch(
        "czechmedmcp.articles.fetch.call_pubtator_api",
    )
    async def test_abstract_fallback_triggered(
        self, mock_api, mock_efetch
    ):
        """When abstract is placeholder, efetch fallback."""
        resp = _pubtator_response(
            abstract_text=None,  # will produce placeholder
        )
        # Force the abstract to be placeholder
        mock_api.return_value = (resp, None)
        mock_efetch.return_value = "Real abstract text"

        result = await fetch_articles(
            [12345], full=False, output_json=True
        )
        data = json.loads(result)
        # The placeholder "Article: 12345" triggers fallback
        assert data[0]["abstract"] == "Real abstract text"
        mock_efetch.assert_called_once_with(12345)

    @patch(
        "czechmedmcp.articles.fetch._fetch_abstract_efetch",
    )
    @patch(
        "czechmedmcp.articles.fetch.call_pubtator_api",
    )
    async def test_abstract_fallback_not_triggered(
        self, mock_api, mock_efetch
    ):
        """Real abstract does not trigger fallback."""
        mock_api.return_value = (
            _pubtator_response(
                abstract_text="Real abstract"
            ),
            None,
        )
        result = await fetch_articles(
            [12345], full=False, output_json=True
        )
        data = json.loads(result)
        assert data[0]["abstract"] == "Real abstract"
        mock_efetch.assert_not_called()

    @patch(
        "czechmedmcp.articles.fetch.call_pubtator_api",
    )
    async def test_empty_response(self, mock_api):
        mock_api.return_value = (None, None)
        result = await fetch_articles(
            [12345], full=True, output_json=True
        )
        data = json.loads(result)
        assert data == []


# ── _article_details (main entry point) ─────────────────


class TestArticleDetails:
    @patch(
        "czechmedmcp.articles.fetch.fetch_articles",
    )
    async def test_pmid_route(self, mock_fetch):
        mock_fetch.return_value = json.dumps([
            {"pmid": 12345, "title": "T"}
        ])
        result = await _article_details(
            call_benefit="test", pmid="12345"
        )
        data = json.loads(result)
        assert data[0]["pmid"] == 12345
        mock_fetch.assert_called_once_with(
            [12345], full=True, output_json=True
        )

    @patch(
        "czechmedmcp.articles.preprints"
        ".fetch_europe_pmc_article",
        new_callable=AsyncMock,
    )
    async def test_doi_route(self, mock_pmc):
        mock_pmc.return_value = json.dumps([
            {"doi": "10.1038/foo", "title": "T"}
        ])
        result = await _article_details(
            call_benefit="test",
            pmid="10.1038/s41586-020-2649-2",
        )
        data = json.loads(result)
        assert len(data) == 1

    @patch(
        "czechmedmcp.articles.fetch._convert_pmc_to_pmid",
    )
    @patch(
        "czechmedmcp.articles.fetch.fetch_articles",
    )
    async def test_pmc_id_route_success(
        self, mock_fetch, mock_convert
    ):
        mock_convert.return_value = 99999
        mock_fetch.return_value = json.dumps([
            {"pmid": 99999, "title": "T"}
        ])
        result = await _article_details(
            call_benefit="test", pmid="PMC1234567"
        )
        data = json.loads(result)
        assert data[0]["pmid"] == 99999
        mock_convert.assert_called_once_with("PMC1234567")

    @patch(
        "czechmedmcp.articles.fetch._convert_pmc_to_pmid",
    )
    async def test_pmc_id_conversion_failure(
        self, mock_convert
    ):
        mock_convert.return_value = None
        result = await _article_details(
            call_benefit="test", pmid="PMC1234567"
        )
        data = json.loads(result)
        assert "error" in data[0]
        assert "Could not convert" in data[0]["error"]

    async def test_invalid_identifier(self):
        result = await _article_details(
            call_benefit="test", pmid="not-valid-id"
        )
        data = json.loads(result)
        assert "error" in data[0]
        assert "Invalid identifier" in data[0]["error"]

    @patch(
        "czechmedmcp.articles.preprints"
        ".fetch_europe_pmc_article",
        new_callable=AsyncMock,
    )
    @patch(
        "czechmedmcp.articles.fetch.fetch_articles",
    )
    async def test_pmid_pubtator_failure_with_fallback(
        self, mock_fetch, mock_epmc
    ):
        """When PubTator fails, Europe PMC fallback."""
        mock_fetch.side_effect = Exception("API down")
        mock_epmc.return_value = json.dumps([
            {"pmid": "12345", "title": "Fallback"}
        ])
        result = await _article_details(
            call_benefit="test", pmid="12345"
        )
        data = json.loads(result)
        assert data[0]["title"] == "Fallback"

    @patch(
        "czechmedmcp.articles.preprints"
        ".fetch_europe_pmc_article",
        new_callable=AsyncMock,
    )
    @patch(
        "czechmedmcp.articles.fetch.fetch_articles",
    )
    async def test_pmid_both_fail(
        self, mock_fetch, mock_epmc
    ):
        """When both PubTator and Europe PMC fail."""
        mock_fetch.side_effect = Exception("API down")
        mock_epmc.side_effect = Exception("also down")
        result = await _article_details(
            call_benefit="test", pmid="12345"
        )
        data = json.loads(result)
        assert "error" in data[0]
        assert "unavailable" in data[0]["error"]

    @patch(
        "czechmedmcp.articles.preprints"
        ".fetch_europe_pmc_article",
        new_callable=AsyncMock,
    )
    @patch(
        "czechmedmcp.articles.fetch.fetch_articles",
    )
    async def test_pmid_error_in_pubtator_result(
        self, mock_fetch, mock_epmc
    ):
        """PubTator returns error dict -> fallback."""
        mock_fetch.return_value = json.dumps([
            {"error": "Not found"}
        ])
        mock_epmc.return_value = json.dumps([
            {"pmid": "12345", "title": "FB"}
        ])
        result = await _article_details(
            call_benefit="test", pmid="12345"
        )
        data = json.loads(result)
        assert data[0]["title"] == "FB"

    @patch(
        "czechmedmcp.articles.preprints"
        ".fetch_europe_pmc_article",
        new_callable=AsyncMock,
    )
    async def test_doi_europe_pmc_failure(self, mock_pmc):
        mock_pmc.side_effect = Exception("timeout")
        result = await _article_details(
            call_benefit="test",
            pmid="10.1038/s41586-020-2649-2",
        )
        data = json.loads(result)
        assert "error" in data[0]
        assert "Europe PMC" in data[0]["error"]


# ── call_pubtator_api ────────────────────────────────────


class TestCallPubtatorApi:
    @patch(
        "czechmedmcp.articles.fetch.http_client"
        ".request_api",
    )
    async def test_calls_with_correct_params(
        self, mock_req
    ):
        mock_req.return_value = (
            _pubtator_response(),
            None,
        )
        resp, err = await call_pubtator_api(
            [111, 222], full=True
        )
        assert err is None
        assert resp is not None
        call_kwargs = mock_req.call_args
        assert call_kwargs.kwargs["request"]["pmids"] == (
            "111,222"
        )
        assert (
            call_kwargs.kwargs["request"]["full"] == "true"
        )

    @patch(
        "czechmedmcp.articles.fetch.http_client"
        ".request_api",
    )
    async def test_full_false(self, mock_req):
        mock_req.return_value = (
            _pubtator_response(),
            None,
        )
        await call_pubtator_api([111], full=False)
        call_kwargs = mock_req.call_args
        assert (
            call_kwargs.kwargs["request"]["full"] == "false"
        )
