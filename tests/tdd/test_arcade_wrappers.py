"""Tests for Arcade wrapper behavior.

Validates that wrappers correctly:
- Clamp Field constraints (ge/le)
- Serialize dict results to JSON str
- Delegate to private implementation functions
"""

import json
from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
class TestArcadeWrapperBehavior:
    """Test Arcade wrapper contract compliance."""

    async def test_think_wrapper_returns_str(self):
        """Think wrapper must serialize dict to JSON string."""
        from czechmedmcp.arcade.thinking_tool import think

        mock_result = {
            "thought": "test thought",
            "thoughtNumber": 1,
        }

        with patch(
            "czechmedmcp.arcade.thinking_tool._sequential_thinking",
            new_callable=AsyncMock,
            return_value=mock_result,
        ), patch(
            "czechmedmcp.arcade.thinking_tool"
            ".mark_thinking_used"
        ):
            result = await think(
                thought="test",
                thoughtNumber=1,
                totalThoughts=3,
                nextThoughtNeeded=True,
            )

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["domain"] == "thinking"
        assert parsed["thoughtNumber"] == 1
        assert parsed["nextThoughtNeeded"] is True

    async def test_think_wrapper_clamps_ge(self):
        """Think wrapper must clamp thoughtNumber >= 1."""
        from czechmedmcp.arcade.thinking_tool import think

        with patch(
            "czechmedmcp.arcade.thinking_tool._sequential_thinking",
            new_callable=AsyncMock,
            return_value={},
        ) as mock_fn, patch(
            "czechmedmcp.arcade.thinking_tool"
            ".mark_thinking_used"
        ):
            await think(
                thought="test",
                thoughtNumber=0,  # Below ge=1
                totalThoughts=-5,  # Below ge=1
                nextThoughtNeeded=False,
            )

        # The clamped values should be passed to impl
        call_kwargs = mock_fn.call_args.kwargs
        assert call_kwargs["thoughtNumber"] >= 1
        assert call_kwargs["totalThoughts"] >= 1

    async def test_article_searcher_returns_str(self):
        """Article searcher wrapper returns str."""
        from czechmedmcp.arcade.individual_tools import (
            article_searcher,
        )

        with patch(
            "czechmedmcp.arcade.individual_tools._article_searcher",
            new_callable=AsyncMock,
            return_value="# Results\n\nSome markdown",
        ):
            result = await article_searcher(
                keywords="BRAF melanoma",
            )

        assert isinstance(result, str)
        assert "Results" in result

    async def test_metrics_wrapper_returns_str(self):
        """Metrics wrapper returns str."""
        from czechmedmcp.arcade.metrics_tool import (
            get_performance_metrics,
        )

        with patch(
            "czechmedmcp.arcade.metrics_tool.get_all_metrics",
            new_callable=AsyncMock,
            return_value={},
        ):
            result = await get_performance_metrics()

        assert isinstance(result, str)
