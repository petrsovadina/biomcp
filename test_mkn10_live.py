import json

import pytest

from biomcp.czech.mkn.search import (
    _mkn_browse,
    _mkn_get,
    _mkn_search,
)


@pytest.mark.integration
async def test_mkn_search_by_code():
    r = json.loads(await _mkn_search("J06"))
    print(f"Search J06: {r['total']} results")
    assert r["total"] > 0
    assert r["results"][0]["code"].startswith("J06")
    print(f"  First: {r['results'][0]}")


@pytest.mark.integration
async def test_mkn_search_by_text():
    r = json.loads(await _mkn_search("diabetes"))
    print(f"Search diabetes: {r['total']} results")
    assert r["total"] > 0
    print(f"  First: {r['results'][0]}")


@pytest.mark.integration
async def test_mkn_get():
    r = json.loads(await _mkn_get("J06.9"))
    print(f"Get J06.9: {r.get('name_cs', r.get('error'))}")
    assert "error" not in r
    assert r["code"] == "J06.9"
    assert r["name_cs"]
    assert r["hierarchy"]
    print(f"  Hierarchy: {r['hierarchy']}")


@pytest.mark.integration
async def test_mkn_browse_chapters():
    r = json.loads(await _mkn_browse())
    items = r.get("items", [])
    print(f"Browse chapters: {len(items)}")
    assert len(items) > 0
    print(f"  First: {items[0]}")


@pytest.mark.integration
async def test_mkn_browse_children():
    r = json.loads(await _mkn_browse())
    items = r["items"]
    first_chap = items[0]["code"]
    r2 = json.loads(await _mkn_browse(first_chap))
    children = r2.get("children", [])
    print(
        f"Browse {first_chap}: {len(children)} children"
    )
    assert len(children) > 0
    print(f"  First child: {children[0]}")
