"""Unit tests for METRICS_ENABLED default behavior.

Verifies that BIOMCP_METRICS_ENABLED defaults to "true"
and can be disabled via environment variable.
"""

import importlib
import os
from unittest.mock import patch


class TestMetricsEnabledDefault:
    """METRICS_ENABLED is True by default."""

    def test_default_is_true(self):
        """Without env var, METRICS_ENABLED is True."""
        with patch.dict(
            os.environ,
            {},
            clear=False,
        ):
            # Remove the key if present
            os.environ.pop(
                "BIOMCP_METRICS_ENABLED", None
            )
            import czechmedmcp.metrics as mod

            importlib.reload(mod)
            assert mod.METRICS_ENABLED is True

    def test_explicit_true(self):
        """BIOMCP_METRICS_ENABLED=true => True."""
        with patch.dict(
            os.environ,
            {"BIOMCP_METRICS_ENABLED": "true"},
        ):
            import czechmedmcp.metrics as mod

            importlib.reload(mod)
            assert mod.METRICS_ENABLED is True

    def test_disabled_when_false(self):
        """BIOMCP_METRICS_ENABLED=false => False."""
        with patch.dict(
            os.environ,
            {"BIOMCP_METRICS_ENABLED": "false"},
        ):
            import czechmedmcp.metrics as mod

            importlib.reload(mod)
            assert mod.METRICS_ENABLED is False

    def test_disabled_case_insensitive(self):
        """BIOMCP_METRICS_ENABLED=False => False."""
        with patch.dict(
            os.environ,
            {"BIOMCP_METRICS_ENABLED": "False"},
        ):
            import czechmedmcp.metrics as mod

            importlib.reload(mod)
            assert mod.METRICS_ENABLED is False
