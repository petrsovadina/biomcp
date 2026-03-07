"""Test that all Czech MCP tools register correctly."""

from typing import ClassVar


class TestToolRegistration:
    """Verify all 23 Czech tools are registered with czechmed_ prefix."""

    EXPECTED_CZECH_TOOLS: ClassVar[list[str]] = [
        "czechmed_search_medicine",
        "czechmed_get_medicine_detail",
        "czechmed_get_spc",
        "czechmed_get_pil",
        "czechmed_check_availability",
        "czechmed_get_reimbursement",
        "czechmed_batch_check_availability",
        "czechmed_get_diagnosis_stats",
        "czechmed_diagnosis_assist",
        "czechmed_search_diagnosis",
        "czechmed_get_diagnosis_detail",
        "czechmed_browse_diagnosis",
        "czechmed_search_providers",
        "czechmed_get_provider_detail",
        "czechmed_search_procedures",
        "czechmed_get_procedure_detail",
        "czechmed_get_drug_reimbursement",
        "czechmed_compare_alternatives",
        "czechmed_calculate_reimbursement",
        "czechmed_get_nrpzs_codebooks",
        "czechmed_referral_assist",
        "czechmed_drug_profile",
        "czechmed_find_pharmacies",
    ]

    def test_all_czech_tools_registered(self):
        """All 23 Czech tools must be registered."""
        import biomcp.czech.czech_tools  # noqa: F401
        from biomcp.core import mcp_app

        tool_names = [
            t.name
            for t in mcp_app._tool_manager._tools.values()
        ]

        for name in self.EXPECTED_CZECH_TOOLS:
            assert name in tool_names, (
                f"Tool '{name}' not registered"
            )

    def test_czech_tool_count(self):
        """Exactly 23 Czech tools registered."""
        import biomcp.czech.czech_tools  # noqa: F401
        from biomcp.core import mcp_app

        tool_names = [
            t.name
            for t in mcp_app._tool_manager._tools.values()
        ]
        czech_tools = [
            n for n in tool_names if n.startswith("czechmed_")
        ]
        assert len(czech_tools) == 23

    def test_global_tools_still_present(self):
        """Global BioMCP tools coexist with Czech tools."""
        import biomcp.czech.czech_tools  # noqa: F401
        from biomcp.core import mcp_app

        tool_names = [
            t.name
            for t in mcp_app._tool_manager._tools.values()
        ]
        assert len(tool_names) > 14
