"""Integration tests for all 4 fixed Czech modules."""
import json

import pytest


@pytest.mark.integration
class TestMKN10:
    async def test_search_code(self):
        from biomcp.czech.mkn.search import _mkn_search
        r = json.loads(await _mkn_search("E10"))
        assert r["total"] > 0
        assert r["results"][0]["code"].startswith("E10")

    async def test_search_text(self):
        from biomcp.czech.mkn.search import _mkn_search
        r = json.loads(await _mkn_search("cholera"))
        assert r["total"] > 0

    async def test_get(self):
        from biomcp.czech.mkn.search import _mkn_get
        r = json.loads(await _mkn_get("A00.0"))
        assert r["code"] == "A00.0"
        assert r["name_cs"]

    async def test_browse(self):
        from biomcp.czech.mkn.search import _mkn_browse
        r = json.loads(await _mkn_browse())
        assert len(r["items"]) == 22


@pytest.mark.integration
class TestNRPZS:
    async def test_search_city(self):
        from biomcp.czech.nrpzs.search import _nrpzs_search
        r = json.loads(
            await _nrpzs_search(city="Praha", page_size=5)
        )
        assert r["total"] > 0
        assert len(r["results"]) <= 5
        print(f"NRPZS Praha: {r['total']} total")

    async def test_search_name(self):
        from biomcp.czech.nrpzs.search import _nrpzs_search
        r = json.loads(
            await _nrpzs_search(query="nemocnice", page_size=5)
        )
        assert r["total"] > 0
        print(f"NRPZS nemocnice: {r['total']} total")

    async def test_get(self):
        from biomcp.czech.nrpzs.search import (
            _nrpzs_get,
            _nrpzs_search,
        )
        # First find a provider
        s = json.loads(
            await _nrpzs_search(city="Brno", page_size=1)
        )
        if s["results"]:
            pid = s["results"][0]["provider_id"]
            r = json.loads(await _nrpzs_get(pid))
            assert "error" not in r
            assert r["name"]
            print(f"NRPZS get: {r['name']}")


@pytest.mark.integration
class TestSZV:
    async def test_search(self):
        from biomcp.czech.szv.search import _szv_search
        r = json.loads(await _szv_search("09513"))
        assert r["total"] > 0
        print(f"SZV 09513: {r['results'][0]}")

    async def test_search_text(self):
        from biomcp.czech.szv.search import _szv_search
        r = json.loads(await _szv_search("vyšetření"))
        assert r["total"] > 0
        print(f"SZV vyšetření: {r['total']} results")

    async def test_get(self):
        from biomcp.czech.szv.search import _szv_get
        r = json.loads(await _szv_get("09513"))
        assert "error" not in r
        assert r["code"] == "09513"
        assert r["name"]
        print(f"SZV get: {r['name']}")


@pytest.mark.integration
class TestVZP:
    async def test_search(self):
        from biomcp.czech.vzp.search import _vzp_search
        r = json.loads(await _vzp_search("09513"))
        assert r["total"] > 0
        print(f"VZP 09513: {r['results'][0]}")

    async def test_search_text(self):
        from biomcp.czech.vzp.search import _vzp_search
        r = json.loads(await _vzp_search("krev"))
        assert r["total"] > 0
        print(f"VZP krev: {r['total']} results")

    async def test_get(self):
        from biomcp.czech.vzp.search import _vzp_get
        r = json.loads(
            await _vzp_get("seznam_vykonu", "09513")
        )
        assert "error" not in r
        assert r["code"] == "09513"
        print(f"VZP get: {r['name']}")
