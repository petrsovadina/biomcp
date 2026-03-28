"""Unit tests for SUKL tool timeout handling."""

import asyncio
from unittest.mock import AsyncMock, patch


async def _timeout_func(*_a, **_kw):
    """Simulate a function that triggers asyncio.TimeoutError."""
    raise asyncio.TimeoutError()


async def test_search_medicine_timeout():
    """czechmed_search_medicine returns user message on timeout."""
    from czechmedmcp.czech.czech_tools import (
        czechmed_search_medicine,
    )

    with patch(
        "czechmedmcp.czech.czech_tools._sukl_drug_search",
        side_effect=_timeout_func,
    ):
        result = await czechmed_search_medicine("Metformin")
    assert "building" in result.lower() or "try again" in result.lower()


async def test_get_medicine_detail_timeout():
    """czechmed_get_medicine_detail returns user message on timeout."""
    from czechmedmcp.czech.czech_tools import (
        czechmed_get_medicine_detail,
    )

    with patch(
        "czechmedmcp.czech.czech_tools._sukl_drug_details",
        side_effect=_timeout_func,
    ):
        result = await czechmed_get_medicine_detail("0011114")
    assert "building" in result.lower() or "try again" in result.lower()


async def test_get_drug_reimbursement_timeout():
    """czechmed_get_drug_reimbursement returns user message on timeout."""
    from czechmedmcp.czech.czech_tools import (
        czechmed_get_drug_reimbursement,
    )

    with patch(
        "czechmedmcp.czech.czech_tools._get_vzp_drug_reimbursement",
        side_effect=_timeout_func,
    ):
        result = await czechmed_get_drug_reimbursement("0011114")
    assert "timed out" in result.lower() or "try again" in result.lower()


async def test_compare_alternatives_timeout():
    """czechmed_compare_alternatives returns user message on timeout."""
    from czechmedmcp.czech.czech_tools import (
        czechmed_compare_alternatives,
    )

    with patch(
        "czechmedmcp.czech.czech_tools._compare_alternatives",
        side_effect=_timeout_func,
    ):
        result = await czechmed_compare_alternatives("0011114")
    assert "timed out" in result.lower() or "try again" in result.lower()


async def test_search_medicine_success_within_timeout():
    """Normal fast call still works."""
    from czechmedmcp.czech.czech_tools import (
        czechmed_search_medicine,
    )

    with patch(
        "czechmedmcp.czech.czech_tools._sukl_drug_search",
        new_callable=AsyncMock,
        return_value="ok",
    ):
        result = await czechmed_search_medicine("Metformin")
    assert result == "ok"
