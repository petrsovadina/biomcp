"""Tests for OpenFDA drug recall search and getter."""

from unittest.mock import AsyncMock, patch

# -- Fixtures -------------------------------------------------------

MOCK_RECALL_RESULT = {
    "meta": {"results": {"total": 2}},
    "results": [
        {
            "recall_number": "D-0001-2025",
            "classification": "Class II",
            "status": "Ongoing",
            "recall_initiation_date": "20250101",
            "product_description": "Metformin HCl 500mg",
            "reason_for_recall": "CGMP Deviations",
            "recalling_firm": "TestPharma Inc",
            "openfda": {
                "brand_name": ["METFORMIN"],
                "generic_name": ["METFORMIN HCL"],
            },
        },
        {
            "recall_number": "D-0002-2025",
            "classification": "Class I",
            "status": "Completed",
            "recall_initiation_date": "20250215",
            "product_description": "Metformin ER 750mg",
            "reason_for_recall": "NDMA impurity",
            "recalling_firm": "OtherPharma",
            "openfda": {
                "brand_name": ["GLUMETZA"],
            },
        },
    ],
}

MOCK_RECALL_DETAIL = {
    "meta": {"results": {"total": 1}},
    "results": [
        {
            "recall_number": "D-0001-2025",
            "classification": "Class II",
            "status": "Ongoing",
            "event_id": "EVT-99",
            "recall_initiation_date": "20250101",
            "report_date": "20250115",
            "product_description": "Metformin HCl 500mg",
            "reason_for_recall": "CGMP Deviations",
            "product_quantity": "10,000 bottles",
            "code_info": "Lot 12345",
            "recalling_firm": "TestPharma Inc",
            "city": "Newark",
            "state": "NJ",
            "country": "US",
            "distribution_pattern": "Nationwide",
            "voluntary_mandated": "Voluntary",
            "openfda": {
                "brand_name": ["METFORMIN"],
                "generic_name": ["METFORMIN HCL"],
                "manufacturer_name": ["TestPharma"],
                "application_number": ["ANDA12345"],
                "route": ["ORAL"],
                "pharm_class_epc": [
                    "Biguanide [EPC]"
                ],
            },
        },
    ],
}


# -- search_drug_recalls tests ------------------------------------


class TestSearchDrugRecalls:
    """Tests for search_drug_recalls."""

    @patch(
        "czechmedmcp.openfda.drug_recalls"
        ".make_openfda_request"
    )
    async def test_successful_search(
        self, mock_req: AsyncMock
    ):
        """Search with results returns formatted md."""
        mock_req.return_value = (
            MOCK_RECALL_RESULT,
            None,
        )

        from czechmedmcp.openfda.drug_recalls import (
            search_drug_recalls,
        )

        result = await search_drug_recalls(
            drug="metformin"
        )

        assert "FDA Drug Recall Records" in result
        assert "D-0001-2025" in result
        assert "D-0002-2025" in result
        assert "Metformin HCl 500mg" in result
        assert "2 recalls" in result

    @patch(
        "czechmedmcp.openfda.drug_recalls"
        ".make_openfda_request"
    )
    async def test_empty_results(
        self, mock_req: AsyncMock
    ):
        """Empty result set returns friendly message."""
        mock_req.return_value = (
            {"results": []},
            None,
        )

        from czechmedmcp.openfda.drug_recalls import (
            search_drug_recalls,
        )

        result = await search_drug_recalls(
            drug="nonexistentdrug12345"
        )

        assert "No drug recall records found" in result

    @patch(
        "czechmedmcp.openfda.drug_recalls"
        ".make_openfda_request"
    )
    async def test_no_response(
        self, mock_req: AsyncMock
    ):
        """None response returns friendly message."""
        mock_req.return_value = (None, None)

        from czechmedmcp.openfda.drug_recalls import (
            search_drug_recalls,
        )

        result = await search_drug_recalls(
            drug="test"
        )

        assert "No drug recall records found" in result

    @patch(
        "czechmedmcp.openfda.drug_recalls"
        ".make_openfda_request"
    )
    async def test_api_error(
        self, mock_req: AsyncMock
    ):
        """API error returns error message."""
        mock_req.return_value = (
            None,
            "Server error 500",
        )

        from czechmedmcp.openfda.drug_recalls import (
            search_drug_recalls,
        )

        result = await search_drug_recalls(
            drug="metformin"
        )

        assert "Error searching drug recalls" in result
        assert "500" in result

    @patch(
        "czechmedmcp.openfda.drug_recalls"
        ".make_openfda_request"
    )
    async def test_connection_timeout(
        self, mock_req: AsyncMock
    ):
        """Connection timeout returns friendly msg."""
        from czechmedmcp.openfda.exceptions import (
            OpenFDATimeoutError,
        )

        mock_req.side_effect = OpenFDATimeoutError(
            "Request timeout"
        )

        from czechmedmcp.openfda.drug_recalls import (
            search_drug_recalls,
        )

        result = await search_drug_recalls(
            drug="metformin"
        )

        assert "FDA API unavailable" in result

    @patch(
        "czechmedmcp.openfda.drug_recalls"
        ".make_openfda_request"
    )
    async def test_unexpected_exception(
        self, mock_req: AsyncMock
    ):
        """Unexpected exception returns error msg."""
        mock_req.side_effect = RuntimeError("boom")

        from czechmedmcp.openfda.drug_recalls import (
            search_drug_recalls,
        )

        result = await search_drug_recalls(
            drug="metformin"
        )

        assert "Unexpected error" in result
        assert "boom" in result

    @patch(
        "czechmedmcp.openfda.drug_recalls"
        ".make_openfda_request"
    )
    async def test_class_summary(
        self, mock_req: AsyncMock
    ):
        """Multiple results include class summary."""
        mock_req.return_value = (
            MOCK_RECALL_RESULT,
            None,
        )

        from czechmedmcp.openfda.drug_recalls import (
            search_drug_recalls,
        )

        result = await search_drug_recalls(
            drug="metformin"
        )

        assert "Class I" in result
        assert "Class II" in result
        assert "most serious" in result


# -- get_drug_recall tests ----------------------------------------


class TestGetDrugRecall:
    """Tests for get_drug_recall (detail getter)."""

    @patch(
        "czechmedmcp.openfda.drug_recalls"
        ".make_openfda_request"
    )
    async def test_successful_get(
        self, mock_req: AsyncMock
    ):
        """Valid recall number returns detail."""
        mock_req.return_value = (
            MOCK_RECALL_DETAIL,
            None,
        )

        from czechmedmcp.openfda.drug_recalls import (
            get_drug_recall,
        )

        result = await get_drug_recall("D-0001-2025")

        assert "Drug Recall Details" in result
        assert "D-0001-2025" in result
        assert "Class II" in result
        assert "Ongoing" in result
        assert "TestPharma Inc" in result
        assert "Nationwide" in result
        assert "METFORMIN" in result

    @patch(
        "czechmedmcp.openfda.drug_recalls"
        ".make_openfda_request"
    )
    async def test_not_found(
        self, mock_req: AsyncMock
    ):
        """Unknown recall number returns not-found."""
        mock_req.return_value = (
            {"results": []},
            None,
        )

        from czechmedmcp.openfda.drug_recalls import (
            get_drug_recall,
        )

        result = await get_drug_recall("FAKE-999")

        assert "No recall record found" in result
        assert "FAKE-999" in result

    @patch(
        "czechmedmcp.openfda.drug_recalls"
        ".make_openfda_request"
    )
    async def test_api_error(
        self, mock_req: AsyncMock
    ):
        """API error returns error message."""
        mock_req.return_value = (
            None,
            "Bad request",
        )

        from czechmedmcp.openfda.drug_recalls import (
            get_drug_recall,
        )

        result = await get_drug_recall("D-0001-2025")

        assert "Error retrieving drug recall" in result

    @patch(
        "czechmedmcp.openfda.drug_recalls"
        ".make_openfda_request"
    )
    async def test_connection_error(
        self, mock_req: AsyncMock
    ):
        """Connection error returns friendly msg."""
        from czechmedmcp.openfda.exceptions import (
            OpenFDAConnectionError,
        )

        mock_req.side_effect = OpenFDAConnectionError(
            "DNS failed"
        )

        from czechmedmcp.openfda.drug_recalls import (
            get_drug_recall,
        )

        result = await get_drug_recall("D-0001-2025")

        assert "FDA API unavailable" in result


# -- Helper function tests -----------------------------------------


class TestRecallHelpers:
    """Tests for drug_recalls_helpers module."""

    def test_build_drug_search_query(self):
        from czechmedmcp.openfda.drug_recalls_helpers import (
            build_drug_search_query,
        )

        q = build_drug_search_query("aspirin")
        assert 'openfda.brand_name:"aspirin"' in q
        assert 'openfda.generic_name:"aspirin"' in q
        assert 'product_description:"aspirin"' in q

    def test_build_class_search_query(self):
        from czechmedmcp.openfda.drug_recalls_helpers import (
            build_class_search_query,
        )

        assert '"Class I"' in build_class_search_query(
            "1"
        )
        assert (
            '"Class II"'
            in build_class_search_query("II")
        )
        assert (
            build_class_search_query("invalid") is None
        )

    def test_build_recall_search_params(self):
        from czechmedmcp.openfda.drug_recalls_helpers import (
            build_recall_search_params,
        )

        params = build_recall_search_params(
            drug="aspirin",
            recall_class="1",
            status="ongoing",
            reason=None,
            since_date=None,
            limit=10,
            skip=0,
        )

        assert "search" in params
        assert "aspirin" in params["search"]
        assert "Class I" in params["search"]
        assert params["limit"] == "10"
