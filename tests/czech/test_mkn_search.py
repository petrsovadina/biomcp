"""Unit tests for MKN-10 search, getter, and browse functions."""

import json
from unittest.mock import AsyncMock, patch

import pytest

from biomcp.czech.mkn.parser import _parse_csv

# Minimal CSV matching MZ ČR open data schema
_SAMPLE_CSV = """\
kod_tecka,nazev,kod_kapitola_rozsah,kod_kapitola_cislo,nazev_kapitola,platnost_do
J06,"Akutní infekce horních cest dýchacích na více a neurčených místech",J00-J99,X,"Nemoci dýchací soustavy",
J06.9,"Akutní infekce horních cest dýchacích NS",J00-J99,X,"Nemoci dýchací soustavy",
A00,"Cholera",A00-B99,I,"Některé infekční a parazitární nemoci",
A00.0,"Cholera vyvolaná Vibrio cholerae 01 biotypem cholerae",A00-B99,I,"Některé infekční a parazitární nemoci",
"""

# Pre-parse the test CSV into indices
_CODE_INDEX, _TEXT_INDEX = _parse_csv(_SAMPLE_CSV)


@pytest.fixture(autouse=True)
def mock_index():
    """Mock _get_index to return our test data."""
    import biomcp.czech.mkn.search as search_mod

    search_mod._INDEX_CACHE = None

    async def _fake_get_index():
        return _CODE_INDEX, _TEXT_INDEX

    with patch.object(
        search_mod, "_get_index", new=_fake_get_index
    ):
        yield

    search_mod._INDEX_CACHE = None


# -------------------------------------------------------------------
# _mkn_search
# -------------------------------------------------------------------


class TestMknSearch:
    """Tests for _mkn_search()."""

    @pytest.mark.asyncio
    async def test_search_by_code_exact(self):
        """Searching 'J06.9' returns exact code match."""
        from biomcp.czech.mkn.search import _mkn_search

        result = json.loads(await _mkn_search("J06.9"))
        assert result["total"] >= 1
        codes = [r["code"] for r in result["results"]]
        assert "J06.9" in codes

    @pytest.mark.asyncio
    async def test_search_by_code_prefix(self):
        """Searching 'J06' returns both J06 and J06.9."""
        from biomcp.czech.mkn.search import _mkn_search

        result = json.loads(await _mkn_search("J06"))
        codes = [r["code"] for r in result["results"]]
        assert "J06" in codes
        assert "J06.9" in codes

    @pytest.mark.asyncio
    async def test_search_by_text_czech(self):
        """Searching 'infekce' returns matching entries."""
        from biomcp.czech.mkn.search import _mkn_search

        result = json.loads(await _mkn_search("infekce"))
        assert result["total"] >= 1
        kinds = [r.get("kind") for r in result["results"]]
        assert any(k in ("block", "category") for k in kinds)

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        """Searching unknown term returns empty result set."""
        from biomcp.czech.mkn.search import _mkn_search

        result = json.loads(await _mkn_search("infarkt"))
        assert result["total"] == 0
        assert result["results"] == []

    @pytest.mark.asyncio
    async def test_search_diacritics_with(self):
        """Searching 'dýchací' finds entries."""
        from biomcp.czech.mkn.search import _mkn_search

        result = json.loads(await _mkn_search("dýchací"))
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_diacritics_without(self):
        """Searching 'dychaci' finds same entries."""
        from biomcp.czech.mkn.search import _mkn_search

        result = json.loads(await _mkn_search("dychaci"))
        assert result["total"] >= 1

    @pytest.mark.asyncio
    async def test_search_diacritics_same_results(self):
        """'dýchací' and 'dychaci' return the same codes."""
        from biomcp.czech.mkn.search import _mkn_search

        r1 = json.loads(await _mkn_search("dýchací"))
        r2 = json.loads(await _mkn_search("dychaci"))
        codes1 = {r["code"] for r in r1["results"]}
        codes2 = {r["code"] for r in r2["results"]}
        assert codes1 == codes2

    @pytest.mark.asyncio
    async def test_search_max_results_respected(self):
        """max_results parameter limits result count."""
        from biomcp.czech.mkn.search import _mkn_search

        result = json.loads(
            await _mkn_search("J", max_results=1)
        )
        assert len(result["results"]) <= 1

    @pytest.mark.asyncio
    async def test_search_query_preserved_in_response(self):
        """Response includes the original query string."""
        from biomcp.czech.mkn.search import _mkn_search

        result = json.loads(await _mkn_search("J06.9"))
        assert result["query"] == "J06.9"


# -------------------------------------------------------------------
# _mkn_get
# -------------------------------------------------------------------


class TestMknGet:
    """Tests for _mkn_get()."""

    @pytest.mark.asyncio
    async def test_get_leaf_code(self):
        """Getting J06.9 returns full Diagnosis dict."""
        from biomcp.czech.mkn.search import _mkn_get

        result = json.loads(await _mkn_get("J06.9"))
        assert result["code"] == "J06.9"
        assert result["source"] == "UZIS/MKN-10"
        assert result["name_cs"]

    @pytest.mark.asyncio
    async def test_get_hierarchy_present(self):
        """Getting J06.9 includes hierarchy with chapter."""
        from biomcp.czech.mkn.search import _mkn_get

        result = json.loads(await _mkn_get("J06.9"))
        hierarchy = result.get("hierarchy")
        assert hierarchy is not None
        assert hierarchy["chapter"] == "J00-J99"

    @pytest.mark.asyncio
    async def test_get_invalid_code_returns_error(self):
        """Getting nonexistent code returns {'error': ...}."""
        from biomcp.czech.mkn.search import _mkn_get

        result = json.loads(await _mkn_get("Z99.9"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_get_chapter_code(self):
        """Getting chapter code returns valid result."""
        from biomcp.czech.mkn.search import _mkn_get

        result = json.loads(await _mkn_get("J00-J99"))
        assert result["code"] == "J00-J99"

    @pytest.mark.asyncio
    async def test_get_block_code(self):
        """Getting block code J06 returns valid result."""
        from biomcp.czech.mkn.search import _mkn_get

        result = json.loads(await _mkn_get("J06"))
        assert result["code"] == "J06"
        assert result["source"] == "UZIS/MKN-10"

    @pytest.mark.asyncio
    async def test_get_category_code(self):
        """Getting category J06 includes/excludes lists."""
        from biomcp.czech.mkn.search import _mkn_get

        result = json.loads(await _mkn_get("J06"))
        assert result["code"] == "J06"
        assert isinstance(result["includes"], list)
        assert isinstance(result["excludes"], list)


# -------------------------------------------------------------------
# _mkn_browse
# -------------------------------------------------------------------


class TestMknBrowse:
    """Tests for _mkn_browse()."""

    @pytest.mark.asyncio
    async def test_browse_root_returns_chapters(self):
        """Browsing without code returns chapter list."""
        from biomcp.czech.mkn.search import _mkn_browse

        result = json.loads(await _mkn_browse())
        assert result["type"] == "chapters"
        assert isinstance(result["items"], list)
        chapter_codes = [c["code"] for c in result["items"]]
        assert "J00-J99" in chapter_codes

    @pytest.mark.asyncio
    async def test_browse_chapter_returns_children(self):
        """Browsing chapter returns blocks as children."""
        from biomcp.czech.mkn.search import _mkn_browse

        result = json.loads(await _mkn_browse("J00-J99"))
        assert result["code"] == "J00-J99"
        child_codes = [
            c["code"] for c in result["children"]
        ]
        assert "J06" in child_codes

    @pytest.mark.asyncio
    async def test_browse_block_returns_children(self):
        """Browsing block J06 returns subcategories."""
        from biomcp.czech.mkn.search import _mkn_browse

        result = json.loads(await _mkn_browse("J06"))
        assert result["code"] == "J06"
        child_codes = [
            c["code"] for c in result["children"]
        ]
        assert "J06.9" in child_codes

    @pytest.mark.asyncio
    async def test_browse_leaf_has_empty_children(self):
        """Browsing leaf J06.9 returns empty children."""
        from biomcp.czech.mkn.search import _mkn_browse

        result = json.loads(await _mkn_browse("J06.9"))
        assert result["code"] == "J06.9"
        assert result["children"] == []

    @pytest.mark.asyncio
    async def test_browse_invalid_code_returns_error(self):
        """Browsing unknown code returns error."""
        from biomcp.czech.mkn.search import _mkn_browse

        result = json.loads(await _mkn_browse("Z99"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_browse_node_includes_kind(self):
        """Browse result includes the 'kind' field."""
        from biomcp.czech.mkn.search import _mkn_browse

        result = json.loads(
            await _mkn_browse("J00-J99")
        )
        assert result.get("kind") == "chapter"

    @pytest.mark.asyncio
    async def test_browse_parent_code_present(self):
        """Browse of J06 includes its parent_code."""
        from biomcp.czech.mkn.search import _mkn_browse

        result = json.loads(await _mkn_browse("J06"))
        assert result.get("parent_code") == "J00-J99"
