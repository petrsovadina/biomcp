"""Tests for enhanced PIL/SPC document getters."""

import json
from contextlib import contextmanager
from unittest.mock import patch

from czechmedmcp.czech.sukl.getter import (
    _sukl_pil_getter,
    _sukl_spc_getter,
)

MOCK_DETAIL = {
    "kodSUKL": "0012345",
    "nazev": "Ibalgin 400",
}

MOCK_DOC_META = [{"typ": "pil", "id": 1}]

MOCK_PIL_HTML = """
<html><body>
<h2>Jak se přípravek užívá</h2>
<p>Užívejte 1 tabletu 3x denně.</p>
<h2>Možné nežádoucí účinky</h2>
<p>Bolest hlavy, nevolnost.</p>
<h2>Uchovávání</h2>
<p>Uchovávejte při teplotě do 25°C.</p>
</body></html>
"""

MOCK_SPC_HTML = """
<html><body>
<h2>4.1 Terapeutické indikace</h2>
<p>Léčba mírné až střední bolesti.</p>
<h2>4.2 Dávkování a způsob podání</h2>
<p>400 mg 3x denně.</p>
<h2>4.3 Kontraindikace</h2>
<p>Přecitlivělost na ibuprofen.</p>
<h2>5.1 Farmakodynamické vlastnosti</h2>
<p>Nesteroidní protizánětlivý lék.</p>
</body></html>
"""


class MockResp:
    """Mock httpx response."""

    def __init__(self, data=None, html=None, ok=True):
        self.is_success = ok
        self.status_code = 200 if ok else 404
        self._data = data
        self._html = html

    def json(self):
        return self._data

    @property
    def text(self):
        return self._html or ""

    def raise_for_status(self):
        if not self.is_success:
            raise Exception("HTTP error")


class MockClient:
    """Mock httpx.AsyncClient."""

    def __init__(self, responses=None):
        self._responses = responses or {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        pass

    async def get(self, url, **kw):
        for pattern, resp in self._responses.items():
            if pattern in url:
                return resp
        return MockResp(ok=False)


def _make_client(
    detail=MOCK_DETAIL,
    doc_meta=MOCK_DOC_META,
    html=MOCK_PIL_HTML,
):
    """Build a MockClient with standard routes."""
    detail_resp = MockResp(data=detail, ok=True)
    meta_resp = MockResp(
        data=doc_meta, ok=bool(doc_meta)
    )
    html_resp = MockResp(html=html, ok=True)

    return MockClient({
        "lecive-pripravky": detail_resp,
        "dokumenty-metadata": meta_resp,
        "dokumenty/": html_resp,
    })


@contextmanager
def _mock_env(
    detail=MOCK_DETAIL,
    doc_meta=MOCK_DOC_META,
    html=MOCK_PIL_HTML,
    client=None,
):
    """Patch httpx + caching for SUKL getter tests."""
    if client is None:
        client = _make_client(detail, doc_meta, html)

    with (
        patch(
            "czechmedmcp.czech.sukl.getter."
            "httpx.AsyncClient",
            return_value=client,
        ),
        patch(
            "czechmedmcp.czech.sukl.getter."
            "get_cached_response",
            return_value=None,
        ),
        patch(
            "czechmedmcp.czech.sukl.getter."
            "cache_response",
        ),
        patch(
            "czechmedmcp.czech.sukl.client."
            "get_cached_response",
            return_value=None,
        ),
        patch(
            "czechmedmcp.czech.sukl.client."
            "cache_response",
        ),
    ):
        yield


class TestPILGetter:
    """Test enhanced PIL getter."""

    async def test_returns_dual_output(self):
        """Result must have content + structuredContent."""
        with _mock_env():
            result = await _sukl_pil_getter("0012345")

        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    async def test_sections_parsed(self):
        """PIL HTML should be parsed into sections."""
        with _mock_env():
            result = await _sukl_pil_getter("0012345")

        sc = json.loads(result)["structuredContent"]
        sections = sc["sections"]
        assert len(sections) >= 2
        ids = [s["section_id"] for s in sections]
        assert "dosage" in ids
        assert "side_effects" in ids

    async def test_section_filter(self):
        """Section filter should return only matching."""
        with _mock_env():
            result = await _sukl_pil_getter(
                "0012345", section="dosage"
            )

        sc = json.loads(result)["structuredContent"]
        sections = sc["sections"]
        assert len(sections) == 1
        assert sections[0]["section_id"] == "dosage"

    async def test_fallback_on_no_html(self):
        """Should return URL when HTML unavailable."""
        html_fail = MockResp(ok=False)
        client = MockClient({
            "lecive-pripravky": MockResp(
                data=MOCK_DETAIL, ok=True
            ),
            "dokumenty-metadata": MockResp(
                data=MOCK_DOC_META, ok=True
            ),
            "dokumenty/": html_fail,
        })
        with _mock_env(client=client):
            result = await _sukl_pil_getter("0012345")

        sc = json.loads(result)["structuredContent"]
        assert sc["sections"] == []
        assert sc["url"] != ""

    async def test_no_doc_available(self):
        """Should return error when no PIL exists."""
        with _mock_env(doc_meta=[]):
            result = await _sukl_pil_getter("0012345")

        parsed = json.loads(result)
        assert "error" in parsed


class TestSPCGetter:
    """Test enhanced SPC getter."""

    async def test_spc_sections_parsed(self):
        """SPC numbered sections should be parsed."""
        with _mock_env(
            doc_meta=[{"typ": "spc", "id": 1}],
            html=MOCK_SPC_HTML,
        ):
            result = await _sukl_spc_getter("0012345")

        sc = json.loads(result)["structuredContent"]
        sections = sc["sections"]
        assert len(sections) >= 3
        ids = [s["section_id"] for s in sections]
        assert "4.1" in ids
        assert "4.2" in ids

    async def test_spc_section_filter(self):
        """Should filter SPC by section number."""
        with _mock_env(
            doc_meta=[{"typ": "spc", "id": 1}],
            html=MOCK_SPC_HTML,
        ):
            result = await _sukl_spc_getter(
                "0012345", section="4.1"
            )

        sc = json.loads(result)["structuredContent"]
        sections = sc["sections"]
        assert len(sections) == 1
        assert sections[0]["section_id"] == "4.1"

    async def test_spc_markdown_content(self):
        """Markdown should contain section headings."""
        with _mock_env(
            doc_meta=[{"typ": "spc", "id": 1}],
            html=MOCK_SPC_HTML,
        ):
            result = await _sukl_spc_getter("0012345")

        content = json.loads(result)["content"]
        assert "Terapeutické indikace" in content
        assert "Ibalgin" in content
