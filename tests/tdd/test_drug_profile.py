"""Tests for drug profile workflow and compare alternatives."""

import json
from unittest.mock import patch

# -- Fixtures -------------------------------------------------------

MOCK_SEARCH_RESULT = json.dumps({
    "results": [
        {"sukl_code": "0000001", "name": "Paralen"}
    ],
})

MOCK_DETAIL = json.dumps({
    "sukl_code": "0000001",
    "name": "Paralen",
    "atc_code": "N02BE01",
    "pharmaceutical_form": "Tablety",
})

MOCK_AVAILABILITY = json.dumps({
    "sukl_code": "0000001",
    "status": "available",
})

MOCK_REIMBURSEMENT = json.dumps({
    "content": "",
    "structuredContent": {
        "type": "get_reimbursement",
        "sukl_code": "0000001",
        "max_retail_price": 39.0,
        "reimbursement_amount": 25.0,
        "patient_copay": 14.0,
        "reimbursement_group": "ATC-N02",
    },
})

MOCK_REIMBURSEMENT_ERROR = json.dumps({
    "content": "",
    "structuredContent": {
        "error": "Reimbursement not available",
    },
})

MOCK_ARTICLES = json.dumps([
    {"title": "Paracetamol study", "pmid": "123"},
])

MOCK_DETAIL_WITH_ATC = json.dumps({
    "sukl_code": "0000001",
    "name": "Paralen",
    "nazev": "Paralen",
    "atc_code": "N02BE01",
    "ATCkod": "N02BE01",
})

MOCK_ATC_SEARCH = json.dumps({
    "results": [
        {"sukl_code": "0000001", "name": "Paralen"},
        {"sukl_code": "0000002", "name": "Panadol"},
        {"sukl_code": "0000003", "name": "Tylenol"},
    ],
})


# -- DrugProfile tests ---------------------------------------------

_PROFILE = (
    "czechmedmcp.czech.workflows.drug_profile"
)


class TestDrugProfile:
    """Tests for _drug_profile workflow."""

    @patch(f"{_PROFILE}._fetch_evidence")
    @patch(f"{_PROFILE}._fetch_reimbursement")
    @patch(f"{_PROFILE}._fetch_availability")
    @patch(f"{_PROFILE}._fetch_detail")
    @patch(f"{_PROFILE}._resolve_sukl_code")
    async def test_all_sections_ok(
        self,
        mock_resolve,
        mock_detail,
        mock_avail,
        mock_reimb,
        mock_evidence,
    ):
        """All sections succeed -> full profile."""
        mock_resolve.return_value = "0000001"
        mock_detail.return_value = {
            "name": "Paralen"
        }
        mock_avail.return_value = {
            "status": "available"
        }
        mock_reimb.return_value = {
            "patient_copay": 14.0
        }
        mock_evidence.return_value = {
            "articles": []
        }

        from czechmedmcp.czech.workflows.drug_profile import (
            _drug_profile,
        )

        result = await _drug_profile("paralen")
        data = json.loads(result)

        assert "error" not in data
        sc = data.get("structuredContent", data)
        sections = sc.get("sections", [])
        assert len(sections) == 4
        for s in sections:
            assert s["status"] == "ok"

    @patch(f"{_PROFILE}._fetch_evidence")
    @patch(f"{_PROFILE}._fetch_reimbursement")
    @patch(f"{_PROFILE}._fetch_availability")
    @patch(f"{_PROFILE}._fetch_detail")
    @patch(f"{_PROFILE}._resolve_sukl_code")
    async def test_reimbursement_fails(
        self,
        mock_resolve,
        mock_detail,
        mock_avail,
        mock_reimb,
        mock_evidence,
    ):
        """Reimbursement error -> partial profile."""
        mock_resolve.return_value = "0000001"
        mock_detail.return_value = {
            "name": "Paralen"
        }
        mock_avail.return_value = {
            "status": "available"
        }
        mock_reimb.side_effect = ValueError(
            "Reimbursement unavailable"
        )
        mock_evidence.return_value = {
            "articles": []
        }

        from czechmedmcp.czech.workflows.drug_profile import (
            _drug_profile,
        )

        result = await _drug_profile("paralen")
        data = json.loads(result)

        # Should not be a top-level error
        assert data.get("error") is None
        sc = data.get("structuredContent", data)
        sections = sc.get("sections", [])

        # 3 ok, 1 error
        statuses = [s["status"] for s in sections]
        assert statuses.count("ok") == 3
        assert statuses.count("error") == 1

        reimb = next(
            s for s in sections
            if s["section"] == "reimbursement"
        )
        assert reimb["status"] == "error"
        assert "unavailable" in reimb["error"].lower()

        # Markdown shows status icon
        content = data.get("content", "")
        assert "3/4" in content

    @patch(f"{_PROFILE}._resolve_sukl_code")
    async def test_drug_not_found(
        self, mock_resolve
    ):
        """Unknown drug -> clear error message."""
        mock_resolve.return_value = None

        from czechmedmcp.czech.workflows.drug_profile import (
            _drug_profile,
        )

        result = await _drug_profile("nonexistent")
        data = json.loads(result)

        assert "error" in data
        assert "not found" in data["error"].lower()
        assert "nonexistent" in data["error"]

    @patch(f"{_PROFILE}._resolve_sukl_code")
    async def test_resolve_exception(
        self, mock_resolve
    ):
        """Resolve crash -> error, not 500."""
        mock_resolve.side_effect = RuntimeError(
            "connection failed"
        )

        from czechmedmcp.czech.workflows.drug_profile import (
            _drug_profile,
        )

        result = await _drug_profile("paralen")
        data = json.loads(result)

        assert "error" in data
        assert "Failed to search" in data["error"]


class TestFetchAllSections:
    """Tests for _fetch_all_sections."""

    @patch(f"{_PROFILE}._fetch_evidence")
    @patch(f"{_PROFILE}._fetch_reimbursement")
    @patch(f"{_PROFILE}._fetch_availability")
    @patch(f"{_PROFILE}._fetch_detail")
    async def test_mixed_results(
        self,
        mock_detail,
        mock_avail,
        mock_reimb,
        mock_evidence,
    ):
        """Some ok, some error."""
        mock_detail.return_value = {"name": "X"}
        mock_avail.side_effect = Exception("fail")
        mock_reimb.return_value = None
        mock_evidence.return_value = {"articles": []}

        from czechmedmcp.czech.workflows.drug_profile import (
            _fetch_all_sections,
        )

        sections = await _fetch_all_sections("001")

        assert len(sections) == 4

        reg = sections[0]
        assert reg.section == "registration"
        assert reg.status == "ok"

        avail = sections[1]
        assert avail.section == "availability"
        assert avail.status == "error"
        assert "fail" in avail.error

        reimb = sections[2]
        assert reimb.section == "reimbursement"
        assert reimb.status == "error"
        assert "No data" in reimb.error

        evi = sections[3]
        assert evi.section == "evidence"
        assert evi.status == "ok"


class TestFormatMarkdown:
    """Test _format_markdown formatting."""

    def test_all_ok_sections(self):
        from czechmedmcp.czech.sukl.models import (
            DrugProfile,
            DrugProfileSection,
        )
        from czechmedmcp.czech.workflows.drug_profile import (
            _format_markdown,
        )

        p = DrugProfile(
            query="Paralen",
            sukl_code="0000001",
            sections=[
                DrugProfileSection(
                    section="registration",
                    status="ok",
                    data={"name": "Paralen"},
                ),
                DrugProfileSection(
                    section="availability",
                    status="ok",
                    data={"status": "available"},
                ),
            ],
        )

        md = _format_markdown(p)
        assert "Profil léku: Paralen" in md
        # No partial warning when all ok
        assert "/2" not in md

    def test_partial_sections(self):
        from czechmedmcp.czech.sukl.models import (
            DrugProfile,
            DrugProfileSection,
        )
        from czechmedmcp.czech.workflows.drug_profile import (
            _format_markdown,
        )

        p = DrugProfile(
            query="Paralen",
            sukl_code="0000001",
            sections=[
                DrugProfileSection(
                    section="registration",
                    status="ok",
                    data={"name": "Paralen"},
                ),
                DrugProfileSection(
                    section="reimbursement",
                    status="error",
                    error="Timeout",
                ),
            ],
        )

        md = _format_markdown(p)
        assert "1/2 sekcí" in md
        assert "Nedostupné: Timeout" in md


# -- CompareAlternatives tests ------------------------------------

_REIMB = (
    "czechmedmcp.czech.vzp.drug_reimbursement"
)


class TestCompareAlternatives:
    """Tests for _compare_alternatives."""

    @patch(f"{_REIMB}._find_atc_alternatives")
    @patch(f"{_REIMB}._fetch_reimbursement")
    @patch(f"{_REIMB}._fetch_drug_detail")
    async def test_with_alternatives(
        self,
        mock_detail,
        mock_reimb,
        mock_find,
    ):
        """Alternatives found -> table output."""
        from czechmedmcp.czech.vzp.models import (
            DrugAlternative,
        )

        mock_detail.return_value = {
            "name": "Paralen",
            "atc_code": "N02BE01",
        }
        mock_reimb.return_value = {
            "patient_copay": 14.0
        }
        mock_find.return_value = [
            DrugAlternative(
                sukl_code="0000002",
                name="Panadol",
                patient_copay=10.0,
                savings_vs_reference=4.0,
            ),
        ]

        from czechmedmcp.czech.vzp.drug_reimbursement import (
            _compare_alternatives,
        )

        result = await _compare_alternatives(
            "0000001"
        )
        data = json.loads(result)

        content = data.get("content", "")
        assert "Panadol" in content
        assert "10.0 CZK" in content
        assert "4.0 CZK" in content

    @patch(f"{_REIMB}._find_atc_alternatives")
    @patch(f"{_REIMB}._fetch_reimbursement")
    @patch(f"{_REIMB}._fetch_drug_detail")
    async def test_reimbursement_unavailable(
        self,
        mock_detail,
        mock_reimb,
        mock_find,
    ):
        """Missing reimbursement -> N/A copay."""
        from czechmedmcp.czech.vzp.models import (
            DrugAlternative,
        )

        mock_detail.return_value = {
            "name": "Paralen",
            "atc_code": "N02BE01",
        }
        # Empty dict = reimbursement failed
        mock_reimb.return_value = {}
        mock_find.return_value = [
            DrugAlternative(
                sukl_code="0000002",
                name="Panadol",
                patient_copay=None,
                savings_vs_reference=None,
            ),
        ]

        from czechmedmcp.czech.vzp.drug_reimbursement import (
            _compare_alternatives,
        )

        result = await _compare_alternatives(
            "0000001"
        )
        data = json.loads(result)

        content = data.get("content", "")
        assert "N/A" in content
        assert "nedostupné" in content

    @patch(f"{_REIMB}._fetch_drug_detail")
    async def test_drug_not_found(
        self, mock_detail
    ):
        """Unknown drug -> error json."""
        mock_detail.return_value = None

        from czechmedmcp.czech.vzp.drug_reimbursement import (
            _compare_alternatives,
        )

        result = await _compare_alternatives("999")
        data = json.loads(result)

        assert "error" in data
        assert "not found" in data["error"].lower()

    @patch(f"{_REIMB}._find_atc_alternatives")
    @patch(f"{_REIMB}._fetch_reimbursement")
    @patch(f"{_REIMB}._fetch_drug_detail")
    async def test_no_atc_code(
        self,
        mock_detail,
        mock_reimb,
        mock_find,
    ):
        """No ATC code -> no alternatives found."""
        mock_detail.return_value = {
            "name": "Mystery Drug",
        }
        mock_reimb.return_value = {}

        from czechmedmcp.czech.vzp.drug_reimbursement import (
            _compare_alternatives,
        )

        result = await _compare_alternatives(
            "0000001"
        )
        data = json.loads(result)

        content = data.get("content", "")
        assert "Žádné alternativy" in content
        # _find_atc_alternatives not called
        mock_find.assert_not_called()


# -- VZP Reimbursement tests --------------------------------------


class TestVzpDrugReimbursement:
    """Tests for _get_vzp_drug_reimbursement."""

    @patch(f"{_REIMB}._fetch_reimbursement")
    @patch(f"{_REIMB}._fetch_drug_detail")
    async def test_successful(
        self, mock_detail, mock_reimb
    ):
        """Full reimbursement -> formatted output."""
        mock_detail.return_value = {
            "name": "Paralen",
        }
        mock_reimb.return_value = {
            "reimbursement_group": "ATC-N02",
            "max_retail_price": 39.0,
            "reimbursement_amount": 25.0,
            "patient_copay": 14.0,
            "conditions": None,
            "valid_from": None,
        }

        from czechmedmcp.czech.vzp.drug_reimbursement import (
            _get_vzp_drug_reimbursement,
        )

        result = await _get_vzp_drug_reimbursement(
            "0000001"
        )
        data = json.loads(result)

        content = data.get("content", "")
        assert "Paralen" in content
        assert "39.0 CZK" in content
        assert "14.0 CZK" in content

    @patch(f"{_REIMB}._fetch_reimbursement")
    @patch(f"{_REIMB}._fetch_drug_detail")
    async def test_empty_reimbursement(
        self, mock_detail, mock_reimb
    ):
        """Empty reimbursement -> still returns."""
        mock_detail.return_value = {
            "name": "Paralen",
        }
        mock_reimb.return_value = {}

        from czechmedmcp.czech.vzp.drug_reimbursement import (
            _get_vzp_drug_reimbursement,
        )

        result = await _get_vzp_drug_reimbursement(
            "0000001"
        )
        data = json.loads(result)

        # Should not crash — returns model with Nones
        content = data.get("content", "")
        assert "Paralen" in content

    @patch(f"{_REIMB}._fetch_drug_detail")
    async def test_drug_not_found(
        self, mock_detail
    ):
        """Unknown drug -> error."""
        mock_detail.return_value = None

        from czechmedmcp.czech.vzp.drug_reimbursement import (
            _get_vzp_drug_reimbursement,
        )

        result = await _get_vzp_drug_reimbursement(
            "999"
        )
        data = json.loads(result)

        assert "error" in data
