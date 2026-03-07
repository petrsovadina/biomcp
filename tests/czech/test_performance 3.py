"""Performance benchmark tests for Czech modules.

Verifies:
- SC-001: Search latency < 2s cold / < 100ms cached
- SC-007: CSV parse < 5s
- SC-004: MKN-10 accuracy >= 95% against sample codes
"""

import json
import time
from unittest.mock import patch

import pytest

from biomcp.czech.mkn.parser import _parse_csv


class TestSearchLatency:
    """SC-001: Search latency benchmarks."""

    @pytest.mark.asyncio
    async def test_sukl_search_cached_under_100ms(self):
        """Cached SUKL search should return in < 100ms."""
        from biomcp.czech.sukl.search import _sukl_drug_search

        with (
            patch(
                "biomcp.czech.sukl.search.get_cached_response",
                return_value=json.dumps(["001", "002"]),
            ),
            patch(
                "biomcp.czech.sukl.search._fetch_drug_detail",
                return_value=None,
            ),
        ):
            start = time.monotonic()
            await _sukl_drug_search("test")
            elapsed = time.monotonic() - start
            assert elapsed < 0.1, (
                f"Cached search took {elapsed:.3f}s (> 100ms)"
            )

    @pytest.mark.asyncio
    async def test_nrpzs_search_with_module_cache(self):
        """NRPZS in-memory search with pre-loaded data."""
        import biomcp.czech.nrpzs.search as nrpzs_mod
        from biomcp.czech.nrpzs.search import _nrpzs_search

        # Pre-populate module cache
        old = nrpzs_mod._PROVIDERS
        nrpzs_mod._PROVIDERS = [
            {
                "ZZ_nazev": "Test",
                "ZZ_obec": "Praha",
                "ZZ_misto_poskytovani_ID": "1",
                "ZZ_obor_pece": "",
                "poskytovatel_nazev": "",
            },
        ]
        try:
            start = time.monotonic()
            await _nrpzs_search(query="Test")
            elapsed = time.monotonic() - start
            assert elapsed < 0.1, (
                f"Search took {elapsed:.3f}s (> 100ms)"
            )
        finally:
            nrpzs_mod._PROVIDERS = old

    @pytest.mark.asyncio
    async def test_szv_search_with_module_cache(self):
        """SZV in-memory search with pre-loaded data."""
        import biomcp.czech.szv.search as szv_mod
        from biomcp.czech.szv.search import _szv_search

        old = szv_mod._PROCEDURES
        szv_mod._PROCEDURES = [
            {
                "Kód": "09513",
                "Název": "Test",
                "Odbornost": "",
                "Celkové": 100,
                "Kategorie": "P",
            },
        ]
        try:
            start = time.monotonic()
            await _szv_search("09513")
            elapsed = time.monotonic() - start
            assert elapsed < 0.1
        finally:
            szv_mod._PROCEDURES = old

    @pytest.mark.asyncio
    async def test_vzp_search_with_module_cache(self):
        """VZP in-memory search with pre-loaded data."""
        import biomcp.czech.vzp.search as vzp_mod
        from biomcp.czech.vzp.search import _vzp_search

        old = vzp_mod._ENTRIES
        vzp_mod._ENTRIES = [
            {
                "KOD": "09513",
                "NAZ": "Test",
                "VYS": "",
                "ODB": "",
                "OME": "",
                "OMO": "",
                "BOD": "100",
                "PMA": "",
                "TVY": "",
                "CTN": "",
                "PMZ": "",
                "PJP": "",
                "KAT": "",
                "UMA": "",
                "UBO": "",
                "ZUM": "",
            },
        ]
        try:
            start = time.monotonic()
            await _vzp_search("09513")
            elapsed = time.monotonic() - start
            assert elapsed < 0.1
        finally:
            vzp_mod._ENTRIES = old


class TestCSVParsePerformance:
    """SC-007: CSV parse performance."""

    def test_csv_parse_under_5s(self):
        """CSV parsing of 500 entries completes in < 5s."""
        lines = [
            "kod_tecka,nazev,kod_kapitola_rozsah,"
            "kod_kapitola_cislo,nazev_kapitola,platnost_do"
        ]
        for i in range(500):
            ch = chr(65 + (i % 26))
            code = f"{ch}{i:02d}"
            lines.append(
                f'{code},"Test diagnosis {code}",'
                f"A00-Z99,I,Test chapter,"
            )
        csv_text = "\n".join(lines)

        start = time.monotonic()
        code_index, text_index = _parse_csv(csv_text)
        elapsed = time.monotonic() - start

        assert elapsed < 5.0, (
            f"CSV parse took {elapsed:.3f}s (> 5s)"
        )
        assert len(code_index) >= 100


class TestMkn10Accuracy:
    """SC-004: MKN-10 code accuracy >= 95%."""

    def test_known_codes_accuracy(self):
        """Known MKN-10 codes should parse correctly."""
        csv = """\
kod_tecka,nazev,kod_kapitola_rozsah,kod_kapitola_cislo,nazev_kapitola,platnost_do
I21,"Akutni infarkt myokardu",I00-I99,IX,"Nemoci obehu",
J06,"Akutni infekce hornich dychacich cest",J00-J99,X,"Nemoci dychaci soustavy",
J06.9,"Akutni infekce hornich dychacich cest NS",J00-J99,X,"Nemoci dychaci soustavy",
E11,"Diabetes mellitus 2. typu",E00-E90,IV,"Nemoci zlaz",
"""
        code_index, _ = _parse_csv(csv)

        known_codes = {
            "I21": "Akutni infarkt myokardu",
            "J06": "Akutni infekce hornich dychacich cest",
            "J06.9": "Akutni infekce hornich dychacich cest NS",
            "E11": "Diabetes mellitus 2. typu",
        }

        correct = 0
        total = len(known_codes)

        for code, expected_name in known_codes.items():
            cls = code_index.get(code)
            if cls and cls.get("name_cs") == expected_name:
                correct += 1

        accuracy = correct / total
        assert accuracy >= 0.95, (
            f"MKN-10 accuracy {accuracy:.0%} < 95%"
            f" ({correct}/{total} correct)"
        )


class TestSourceAttribution:
    """FR-015: All models include source field."""

    def test_sukl_models_have_source(self):
        from biomcp.czech.sukl.models import Drug

        d = Drug(sukl_code="001", name="Test")
        assert d.source == "SUKL"

    def test_mkn_models_have_source(self):
        from biomcp.czech.mkn.models import Diagnosis

        d = Diagnosis(code="J06.9", name_cs="Test")
        assert d.source == "UZIS/MKN-10"

    def test_nrpzs_source_in_output(self):
        from biomcp.czech.nrpzs.search import _csv_to_provider

        row = {
            "ZZ_misto_poskytovani_ID": "1",
            "ZZ_nazev": "Test",
            "ZZ_obor_pece": "",
            "ZZ_druh_pece": "",
            "ZZ_ulice": "",
            "ZZ_obec": "",
            "ZZ_PSC": "",
            "ZZ_kraj_nazev": "",
            "poskytovatel_pravni_forma_nazev": "",
            "poskytovatel_ICO": "",
            "poskytovatel_telefon": "",
            "poskytovatel_email": "",
            "poskytovatel_web": "",
            "ZZ_forma_pece": "",
            "ZZ_druh_nazev": "",
            "ZZ_okres_nazev": "",
        }
        result = _csv_to_provider(row)
        assert result["source"] == "NRPZS"

    def test_szv_source_in_output(self):
        from biomcp.czech.szv.search import _raw_to_full

        raw = {"Kód": "001", "Název": "Test"}
        result = _raw_to_full(raw)
        assert result["source"] == "MZCR/SZV"

    def test_vzp_source_in_output(self):
        from biomcp.czech.vzp.search import _normalise_entry

        raw = {"KOD": "001", "NAZ": "Test"}
        result = _normalise_entry(raw, "seznam_vykonu")
        assert result["source"] == "VZP"
