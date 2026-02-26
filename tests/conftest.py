"""Pytest configuration and fixtures."""

import os

import pytest

# Check if we should skip integration tests
SKIP_INTEGRATION = os.environ.get("SKIP_INTEGRATION_TESTS", "").lower() in (
    "true",
    "1",
    "yes",
)


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers",
        "integration: marks tests as integration tests (deselect with '-m \"not integration\"')",
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to handle integration tests."""
    if SKIP_INTEGRATION:
        skip_integration = pytest.mark.skip(
            reason="Integration tests disabled via SKIP_INTEGRATION_TESTS env var"
        )
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
