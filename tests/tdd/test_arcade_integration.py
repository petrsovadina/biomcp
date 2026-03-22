"""Integration tests for Arcade server tool registration.

Verifies that the Arcade entrypoint registers exactly 60 tools,
matching the FastMCP tool count. This is a regression test per FR-009.
"""

import pytest


@pytest.mark.asyncio
class TestArcadeIntegration:
    """Integration tests for the Arcade MCP server."""

    async def test_arcade_full_tools_registered(self):
        """Test that Arcade full entrypoint registers exactly 60 tools."""
        import czechmedmcp.arcade.czech_tools

        # Import all wrapper modules to trigger registration
        import czechmedmcp.arcade.individual_tools
        import czechmedmcp.arcade.metrics_tool
        import czechmedmcp.arcade.router_tools
        import czechmedmcp.arcade.thinking_tool  # noqa: F401
        from czechmedmcp.arcade import arcade_app

        # Get registered tool count from Arcade app catalog
        tool_count = len(arcade_app._catalog)

        # Should have exactly 60 tools
        # (33 individual + 23 czech + 2 router + 1 think + 1 metrics)
        assert tool_count == 60, (
            f"Expected 60 Arcade tools, got {tool_count}"
        )

        # Extract tool names (Arcade uses PascalCase internally)
        tool_names = [
            str(k).split(".")[-1]
            for k in arcade_app._catalog._tools
        ]

        # Verify key tool names are present (PascalCase)
        assert "ArticleSearcher" in tool_names
        assert "ArticleGetter" in tool_names
        assert "TrialSearcher" in tool_names
        assert "VariantSearcher" in tool_names
        assert "GeneGetter" in tool_names
        assert "DiseaseGetter" in tool_names
        assert "DrugGetter" in tool_names
        assert "EnrichrAnalyzer" in tool_names
        assert "AlphagenomePredictor" in tool_names

        # OpenFDA tools
        assert "OpenfdaAdverseSearcher" in tool_names
        assert "OpenfdaLabelSearcher" in tool_names
        assert "OpenfdaDeviceSearcher" in tool_names
        assert "OpenfdaShortageSearcher" in tool_names

        # NCI tools
        assert "NciOrganizationSearcher" in tool_names
        assert "NciInterventionSearcher" in tool_names
        assert "NciBiomarkerSearcher" in tool_names
        assert "NciDiseaseSearcher" in tool_names

        # Router tools
        assert "Search" in tool_names
        assert "Fetch" in tool_names

        # Think + metrics
        assert "Think" in tool_names
        assert "GetPerformanceMetrics" in tool_names

        # Czech tools
        assert "CzechmedSearchMedicine" in tool_names
        assert "CzechmedGetMedicineDetail" in tool_names
        assert "CzechmedSearchDiagnosis" in tool_names
        assert "CzechmedSearchProviders" in tool_names
        assert "CzechmedSearchProcedures" in tool_names
        assert "CzechmedDrugProfile" in tool_names
        assert "CzechmedFindPharmacies" in tool_names
        assert "CzechmedReferralAssist" in tool_names
        assert "CzechmedCompareAlternatives" in tool_names
