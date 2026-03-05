"""Tests for dual output format_czech_response() utility."""

import json

from biomcp.czech.response import format_czech_response


class TestFormatCzechResponse:
    """Verify dual output (Markdown + JSON structuredContent)."""

    def test_returns_valid_json(self):
        """Output must be a valid JSON string."""
        result = format_czech_response(
            data={"name": "Test"},
            tool_name="test_tool",
        )
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_has_content_and_structured(self):
        """Output must have content and structuredContent keys."""
        result = format_czech_response(
            data={"sukl_code": "0012345", "name": "Ibuprofen"},
            tool_name="search_drug",
        )
        parsed = json.loads(result)
        assert "content" in parsed
        assert "structuredContent" in parsed

    def test_structured_content_has_type(self):
        """structuredContent must include tool type."""
        result = format_czech_response(
            data={"sukl_code": "0012345"},
            tool_name="get_drug_detail",
        )
        parsed = json.loads(result)
        sc = parsed["structuredContent"]
        assert sc["type"] == "get_drug_detail"
        assert sc["sukl_code"] == "0012345"

    def test_structured_content_preserves_data(self):
        """All data keys must be preserved in structuredContent."""
        data = {
            "sukl_code": "0012345",
            "name": "Ibuprofen 400mg",
            "status": "available",
        }
        result = format_czech_response(
            data=data, tool_name="check_availability"
        )
        parsed = json.loads(result)
        sc = parsed["structuredContent"]
        for key, val in data.items():
            assert sc[key] == val

    def test_custom_markdown_template(self):
        """Custom markdown_template should be used as content."""
        md = "## Lék: Ibuprofen\n\n**Kód**: 0012345"
        result = format_czech_response(
            data={"sukl_code": "0012345"},
            tool_name="drug_detail",
            markdown_template=md,
        )
        parsed = json.loads(result)
        assert parsed["content"] == md

    def test_auto_markdown_without_template(self):
        """Without template, auto-generate Markdown from data."""
        result = format_czech_response(
            data={"sukl_code": "0012345", "name": "Test"},
            tool_name="search_drug",
        )
        parsed = json.loads(result)
        content = parsed["content"]
        assert "Search Drug" in content
        assert "0012345" in content
        assert "Test" in content

    def test_none_values_skipped_in_auto_markdown(self):
        """None values should not appear in auto-generated MD."""
        result = format_czech_response(
            data={"name": "Test", "note": None},
            tool_name="tool",
        )
        parsed = json.loads(result)
        assert "Note" not in parsed["content"]

    def test_ensure_ascii_false(self):
        """Czech diacritics must be preserved (not escaped)."""
        result = format_czech_response(
            data={"name": "Příbalový leták"},
            tool_name="pil",
        )
        assert "Příbalový" in result
        assert "\\u" not in result

    def test_list_value_in_auto_markdown(self):
        """List values show item count in auto Markdown."""
        result = format_czech_response(
            data={"items": [1, 2, 3]},
            tool_name="batch",
        )
        parsed = json.loads(result)
        assert "3 položek" in parsed["content"]

    def test_empty_data(self):
        """Empty data dict should still produce valid output."""
        result = format_czech_response(
            data={}, tool_name="empty"
        )
        parsed = json.loads(result)
        assert parsed["structuredContent"]["type"] == "empty"
        assert isinstance(parsed["content"], str)
