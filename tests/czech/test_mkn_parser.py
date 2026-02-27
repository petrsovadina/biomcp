"""Unit tests for the MKN-10 CSV parser."""

import json
from unittest.mock import patch

import pytest

from biomcp.czech.mkn.parser import _parse_csv

# Minimal CSV sample matching the real MZ ČR open data schema
SAMPLE_CSV = """\
kod_tecka,nazev,kod_kapitola_rozsah,kod_kapitola_cislo,nazev_kapitola,platnost_do
J06,"Akutní infekce horních cest dýchacích na více a neurčených místech",J00-J99,X,"Nemoci dýchací soustavy",
J06.9,"Akutní infekce horních cest dýchacích NS",J00-J99,X,"Nemoci dýchací soustavy",
A00,"Cholera",A00-B99,I,"Některé infekční a parazitární nemoci",
A00.0,"Cholera vyvolaná Vibrio cholerae 01 biotypem cholerae",A00-B99,I,"Některé infekční a parazitární nemoci",
Z99,"Závislost na pomůckách",Z00-Z99,XXI,"Faktory ovlivňující zdravotní stav a kontakt se zdravotnickými službami",2020-01-01
"""


class TestParseCSV:
    """Tests for _parse_csv() function."""

    def test_returns_two_indices(self):
        """_parse_csv returns (code_index, text_index)."""
        code_index, text_index = _parse_csv(SAMPLE_CSV)
        assert isinstance(code_index, dict)
        assert isinstance(text_index, dict)

    def test_chapter_parsed(self):
        """Chapter J00-J99 is parsed with kind='chapter'."""
        code_index, _ = _parse_csv(SAMPLE_CSV)
        assert "J00-J99" in code_index
        node = code_index["J00-J99"]
        assert node["kind"] == "chapter"
        assert "dýchací" in node["name_cs"]

    def test_block_parsed(self):
        """Block code J06 is parsed with kind='block'."""
        code_index, _ = _parse_csv(SAMPLE_CSV)
        assert "J06" in code_index
        node = code_index["J06"]
        assert node["kind"] == "block"
        assert node["parent_code"] == "J00-J99"

    def test_subcategory_parsed(self):
        """Subcategory J06.9 is parsed with correct parent."""
        code_index, _ = _parse_csv(SAMPLE_CSV)
        assert "J06.9" in code_index
        node = code_index["J06.9"]
        assert node["kind"] == "category"
        assert node["parent_code"] == "J06"

    def test_label_extraction_czech(self):
        """Czech labels are correctly extracted."""
        code_index, _ = _parse_csv(SAMPLE_CSV)
        assert "Akutní" in code_index["J06"]["name_cs"]
        assert "NS" in code_index["J06.9"]["name_cs"]

    def test_hierarchy_children(self):
        """Children are recorded correctly."""
        code_index, _ = _parse_csv(SAMPLE_CSV)
        assert "J06" in code_index["J00-J99"]["children"]
        assert "J06.9" in code_index["J06"]["children"]

    def test_leaf_node_has_no_children(self):
        """J06.9 is a leaf and has no children."""
        code_index, _ = _parse_csv(SAMPLE_CSV)
        assert code_index["J06.9"]["children"] == []

    def test_text_index_contains_words(self):
        """Text index is built from Czech labels."""
        _, text_index = _parse_csv(SAMPLE_CSV)
        assert any(
            "akutni" in w or "akut" in w
            for w in text_index
        )

    def test_text_index_maps_to_codes(self):
        """Text index maps words to code lists."""
        _, text_index = _parse_csv(SAMPLE_CSV)
        matching = [
            codes
            for word, codes in text_index.items()
            if "infekce" in word
        ]
        assert matching, "Expected 'infekce' to be indexed"
        all_codes = {c for codes in matching for c in codes}
        assert "J06" in all_codes or "J06.9" in all_codes

    def test_expired_codes_excluded(self):
        """Codes with platnost_do are excluded."""
        code_index, _ = _parse_csv(SAMPLE_CSV)
        assert "Z99" not in code_index

    def test_multiple_chapters(self):
        """Multiple chapters are created from distinct ranges."""
        code_index, _ = _parse_csv(SAMPLE_CSV)
        assert "J00-J99" in code_index
        assert "A00-B99" in code_index
        assert code_index["J00-J99"]["kind"] == "chapter"
        assert code_index["A00-B99"]["kind"] == "chapter"


class TestLoadMkn10:
    """Tests for load_mkn10() function."""

    @pytest.mark.asyncio
    async def test_diskcache_used_on_hit(self):
        """load_mkn10 returns cached result without download."""
        from biomcp.czech.mkn.parser import load_mkn10

        cached_payload = json.dumps(
            {
                "code_index": {
                    "X": {"code": "X", "name_cs": "cached"},
                },
                "text_index": {},
            }
        )
        with patch(
            "biomcp.czech.mkn.parser.get_cached_response",
            return_value=cached_payload,
        ):
            code_index, text_index = await load_mkn10()
        assert code_index == {
            "X": {"code": "X", "name_cs": "cached"},
        }
        assert text_index == {}
