"""PoC validation tests for Arcade Deploy integration.

Verifies that PoC tools are registered in the Arcade catalog.
"""

import pytest


@pytest.mark.asyncio
class TestArcadePoC:
    """Tests for the Arcade PoC (5-tool) deployment."""

    async def test_poc_tools_present(self):
        """Test that PoC tools are present in Arcade catalog."""
        import czechmedmcp.arcade.czech_tools

        # Import PoC-relevant wrapper modules
        import czechmedmcp.arcade.individual_tools
        import czechmedmcp.arcade.metrics_tool
        import czechmedmcp.arcade.thinking_tool  # noqa: F401
        from czechmedmcp.arcade import arcade_app

        tool_names = [
            str(k).split(".")[-1]
            for k in arcade_app._catalog._tools
        ]

        # PoC tools must be present (PascalCase in Arcade)
        poc_tools = [
            "ArticleSearcher",
            "ArticleGetter",
            "CzechmedSearchMedicine",
            "Think",
            "GetPerformanceMetrics",
        ]
        for tool_name in poc_tools:
            assert tool_name in tool_names, (
                f"PoC tool '{tool_name}' not found in "
                f"registered tools: {tool_names}"
            )
