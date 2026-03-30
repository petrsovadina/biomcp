"""Unit tests for czechmedmcp.trials.search module.

Tests convert_query(), search_trials(), helper functions,
TrialQuery validation, and edge cases. All HTTP calls mocked.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from czechmedmcp.trials.search import (
    CLOSED_STATUSES,
    CTGOV_SORT_MAPPING,
    DEFAULT_FORMAT,
    DEFAULT_MARKUP,
    LINE_OF_THERAPY_PATTERNS,
    OPEN_STATUSES,
    SEARCH_FIELDS_PARAM,
    AgeGroup,
    DateField,
    InterventionType,
    LineOfTherapy,
    PrimaryPurpose,
    RecruitingStatus,
    SortOrder,
    SponsorType,
    StudyDesign,
    StudyType,
    TrialPhase,
    TrialQuery,
    _build_biomarker_expression_essie,
    _build_brain_mets_essie,
    _build_excluded_mutations_essie,
    _build_line_of_therapy_essie,
    _build_prior_therapy_essie,
    _build_progression_essie,
    _build_required_mutations_essie,
    _inject_ids,
    convert_query,
    search_trials,
)


# ─── TrialQuery validation ────────────────────────────


class TestTrialQueryValidation:
    """Test TrialQuery pydantic model validation."""

    def test_minimal_query(self):
        q = TrialQuery()
        assert q.conditions is None
        assert q.expand_synonyms is True

    def test_conditions_string_to_list(self):
        q = TrialQuery(conditions="diabetes,cancer")
        assert q.conditions == ["diabetes", "cancer"]

    def test_conditions_list_preserved(self):
        q = TrialQuery(conditions=["diabetes", "cancer"])
        assert q.conditions == ["diabetes", "cancer"]

    def test_recruiting_status_alias_recruiting(self):
        q = TrialQuery(recruiting_status="recruiting")
        assert q.recruiting_status == RecruitingStatus.OPEN

    def test_recruiting_status_alias_active(self):
        q = TrialQuery(recruiting_status="active")
        assert q.recruiting_status == RecruitingStatus.OPEN

    def test_recruiting_status_alias_completed(self):
        q = TrialQuery(recruiting_status="completed")
        assert q.recruiting_status == RecruitingStatus.CLOSED

    def test_recruiting_status_enum_value(self):
        q = TrialQuery(recruiting_status="OPEN")
        assert q.recruiting_status == RecruitingStatus.OPEN

    def test_nct_ids_string_to_list(self):
        q = TrialQuery(nct_ids="NCT001,NCT002")
        assert q.nct_ids == ["NCT001", "NCT002"]

    def test_page_size_valid(self):
        q = TrialQuery(page_size=100)
        assert q.page_size == 100

    def test_page_size_too_low(self):
        with pytest.raises(Exception):
            TrialQuery(page_size=0)

    def test_page_size_too_high(self):
        with pytest.raises(Exception):
            TrialQuery(page_size=1001)

    def test_multiple_list_fields_converted(self):
        q = TrialQuery(
            terms="a,b",
            interventions="c,d",
            lead_sponsor="org1,org2",
        )
        assert q.terms == ["a", "b"]
        assert q.interventions == ["c", "d"]
        assert q.lead_sponsor == ["org1", "org2"]


# ─── Helper functions ─────────────────────────────────


class TestInjectIds:
    """Test _inject_ids helper."""

    def test_with_other_filters(self):
        params: dict[str, list[str]] = {}
        _inject_ids(params, ["NCT001", "NCT002"], True)
        assert params["filter.ids"] == ["NCT001,NCT002"]

    def test_without_other_filters_small(self):
        params: dict[str, list[str]] = {}
        _inject_ids(params, ["NCT001"], False)
        assert params["query.id"] == ["NCT001"]

    def test_without_other_filters_large(self):
        """Large ID list uses filter.ids even without filters."""
        params: dict[str, list[str]] = {}
        ids = [f"NCT{i:06d}" for i in range(300)]
        _inject_ids(params, ids, False)
        assert "filter.ids" in params


class TestBuildPriorTherapyEssie:
    def test_single_therapy(self):
        result = _build_prior_therapy_essie(["cisplatin"])
        assert len(result) == 1
        assert '"cisplatin"' in result[0]
        assert "prior OR previous OR received" in result[0]

    def test_multiple_therapies(self):
        result = _build_prior_therapy_essie(
            ["cisplatin", "carboplatin"]
        )
        assert len(result) == 2

    def test_empty_string_skipped(self):
        result = _build_prior_therapy_essie(["", "cisplatin"])
        assert len(result) == 1


class TestBuildProgressionEssie:
    def test_single(self):
        result = _build_progression_essie(["imatinib"])
        assert len(result) == 1
        assert '"imatinib"' in result[0]
        assert "progression OR resistant" in result[0]

    def test_empty_skipped(self):
        result = _build_progression_essie(["  "])
        assert len(result) == 0


class TestBuildRequiredMutationsEssie:
    def test_single(self):
        result = _build_required_mutations_essie(["BRAF V600E"])
        assert len(result) == 1
        assert '"BRAF V600E"' in result[0]
        assert "NOT" not in result[0]


class TestBuildExcludedMutationsEssie:
    def test_single(self):
        result = _build_excluded_mutations_essie(["KRAS G12C"])
        assert len(result) == 1
        assert 'NOT "KRAS G12C"' in result[0]


class TestBuildBiomarkerExpressionEssie:
    def test_single_marker(self):
        result = _build_biomarker_expression_essie(
            {"PD-L1": ">=50%"}
        )
        assert len(result) == 1
        assert '"PD-L1"' in result[0]
        assert '">=50%"' in result[0]

    def test_empty_values_skipped(self):
        result = _build_biomarker_expression_essie({"": "val"})
        assert len(result) == 0

    def test_multiple_markers(self):
        result = _build_biomarker_expression_essie(
            {"PD-L1": ">=50%", "HER2": "3+"}
        )
        assert len(result) == 2


class TestBuildLineOfTherapyEssie:
    def test_first_line(self):
        result = _build_line_of_therapy_essie(
            LineOfTherapy.FIRST_LINE
        )
        assert "AREA[EligibilityCriteria]" in result
        assert '"first line"' in result

    def test_second_line(self):
        result = _build_line_of_therapy_essie(
            LineOfTherapy.SECOND_LINE
        )
        assert '"second line"' in result

    def test_third_line_plus(self):
        result = _build_line_of_therapy_essie(
            LineOfTherapy.THIRD_LINE_PLUS
        )
        assert '"third line"' in result


class TestBuildBrainMetsEssie:
    def test_disallow(self):
        result = _build_brain_mets_essie(False)
        assert 'NOT "brain metastases"' in result

    def test_allow(self):
        result = _build_brain_mets_essie(True)
        assert result == ""

    def test_none_returns_empty(self):
        # None != False, so should return empty
        result = _build_brain_mets_essie(None)
        assert result == ""


# ─── convert_query() ──────────────────────────────────


MOCK_SYNONYMS_PATH = (
    "czechmedmcp.integrations.biothings_client"
    ".BioThingsClient.get_disease_synonyms"
)


class TestConvertQueryMinimal:
    """Test convert_query with minimal/empty queries."""

    async def test_empty_query(self):
        q = TrialQuery()
        params = await convert_query(q)
        assert params["format"] == [DEFAULT_FORMAT]
        assert params["markupFormat"] == [DEFAULT_MARKUP]
        assert params["sort"] == [
            CTGOV_SORT_MAPPING[SortOrder.RELEVANCE]
        ]
        assert params["pageSize"] == ["40"]
        assert params["fields"] == SEARCH_FIELDS_PARAM
        # Default OPEN status applied
        assert "filter.overallStatus" in params
        assert params["filter.overallStatus"] == [
            ",".join(OPEN_STATUSES)
        ]

    async def test_custom_page_size(self):
        q = TrialQuery(page_size=10)
        params = await convert_query(q)
        assert params["pageSize"] == ["10"]

    async def test_next_page_hash(self):
        q = TrialQuery(next_page_hash="abc123")
        params = await convert_query(q)
        assert params["pageToken"] == ["abc123"]


class TestConvertQueryConditions:
    """Test condition handling with synonym expansion."""

    @patch(MOCK_SYNONYMS_PATH, new_callable=AsyncMock)
    async def test_single_condition_with_synonyms(
        self, mock_syn
    ):
        mock_syn.return_value = [
            "diabetes",
            "diabetes mellitus",
        ]
        q = TrialQuery(
            conditions=["diabetes"], expand_synonyms=True
        )
        params = await convert_query(q)
        cond = params["query.cond"][0]
        assert "diabetes" in cond
        assert "diabetes mellitus" in cond

    @patch(MOCK_SYNONYMS_PATH, new_callable=AsyncMock)
    async def test_single_condition_no_synonyms(
        self, mock_syn
    ):
        q = TrialQuery(
            conditions=["diabetes"], expand_synonyms=False
        )
        params = await convert_query(q)
        assert params["query.cond"] == ["diabetes"]
        mock_syn.assert_not_called()

    @patch(MOCK_SYNONYMS_PATH, new_callable=AsyncMock)
    async def test_synonym_expansion_failure_fallback(
        self, mock_syn
    ):
        mock_syn.side_effect = Exception("API down")
        q = TrialQuery(
            conditions=["diabetes"], expand_synonyms=True
        )
        params = await convert_query(q)
        assert params["query.cond"] == ["diabetes"]

    @patch(MOCK_SYNONYMS_PATH, new_callable=AsyncMock)
    async def test_multiple_conditions_joined_with_or(
        self, mock_syn
    ):
        mock_syn.side_effect = lambda c: [c]
        q = TrialQuery(
            conditions=["diabetes", "obesity"],
            expand_synonyms=True,
        )
        params = await convert_query(q)
        cond = params["query.cond"][0]
        assert "OR" in cond
        assert "diabetes" in cond
        assert "obesity" in cond

    @patch(MOCK_SYNONYMS_PATH, new_callable=AsyncMock)
    async def test_duplicate_synonyms_deduplicated(
        self, mock_syn
    ):
        mock_syn.return_value = ["Diabetes", "diabetes"]
        q = TrialQuery(
            conditions=["diabetes"], expand_synonyms=True
        )
        params = await convert_query(q)
        # Should be a single term, not wrapped in OR
        assert params["query.cond"] == ["Diabetes"]


class TestConvertQueryFilters:
    """Test various filter parameters."""

    async def test_terms_single(self):
        q = TrialQuery(
            terms=["BRAF"], expand_synonyms=False
        )
        params = await convert_query(q)
        assert params["query.term"] == ["BRAF"]

    async def test_terms_multiple_joined(self):
        q = TrialQuery(
            terms=["BRAF", "KRAS"], expand_synonyms=False
        )
        params = await convert_query(q)
        assert "OR" in params["query.term"][0]

    async def test_interventions(self):
        q = TrialQuery(
            interventions=["pembrolizumab"],
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert params["query.intr"] == ["pembrolizumab"]

    async def test_lead_sponsor(self):
        q = TrialQuery(
            lead_sponsor=["Pfizer"],
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert params["query.lead"] == ["Pfizer"]


class TestConvertQueryPhase:
    """Test phase filtering."""

    async def test_phase3(self):
        q = TrialQuery(
            phase=TrialPhase.PHASE3,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert "filter.advanced" in params
        assert "AREA[Phase]" in params["filter.advanced"][0]
        assert "PHASE3" in params["filter.advanced"][0]

    async def test_early_phase1(self):
        q = TrialQuery(
            phase=TrialPhase.EARLY_PHASE1,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert "EARLY_PHASE1" in params["filter.advanced"][0]


class TestConvertQueryRecruitingStatus:
    """Test recruiting status filtering."""

    async def test_default_applies_open(self):
        """No status set => default OPEN statuses."""
        q = TrialQuery(expand_synonyms=False)
        params = await convert_query(q)
        assert params["filter.overallStatus"] == [
            ",".join(OPEN_STATUSES)
        ]

    async def test_closed_status(self):
        q = TrialQuery(
            recruiting_status=RecruitingStatus.CLOSED,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert params["filter.overallStatus"] == [
            ",".join(CLOSED_STATUSES)
        ]

    async def test_any_status_no_filter(self):
        q = TrialQuery(
            recruiting_status=RecruitingStatus.ANY,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        # ANY maps to None so no overallStatus filter
        assert "filter.overallStatus" not in params

    async def test_nct_ids_only_no_status_filter(self):
        """NCT IDs alone => no default status filter."""
        q = TrialQuery(
            nct_ids=["NCT00000001"],
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert "filter.overallStatus" not in params


class TestConvertQueryGeo:
    """Test geospatial filtering."""

    async def test_geo_filter(self):
        q = TrialQuery(
            lat=41.4993,
            long=-81.6944,
            distance=50,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        geo = params["filter.geo"][0]
        assert "distance(41.4993,-81.6944,50mi)" == geo

    async def test_geo_no_distance(self):
        q = TrialQuery(
            lat=41.4993,
            long=-81.6944,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        geo = params["filter.geo"][0]
        assert "distance(41.4993,-81.6944,Nonemi)" == geo

    async def test_lat_only_no_filter(self):
        """Lat without long => no geo filter."""
        q = TrialQuery(
            lat=41.4993, expand_synonyms=False
        )
        params = await convert_query(q)
        assert "filter.geo" not in params


class TestConvertQueryDate:
    """Test date filtering."""

    async def test_date_range(self):
        q = TrialQuery(
            date_field=DateField.LAST_UPDATE,
            min_date="2024-01-01",
            max_date="2024-12-31",
            expand_synonyms=False,
        )
        params = await convert_query(q)
        adv = params["filter.advanced"][0]
        assert "LastUpdatePostDate" in adv
        assert "2024-01-01" in adv
        assert "2024-12-31" in adv

    async def test_date_min_only(self):
        q = TrialQuery(
            date_field=DateField.STUDY_START,
            min_date="2024-01-01",
            expand_synonyms=False,
        )
        params = await convert_query(q)
        adv = params["filter.advanced"][0]
        assert "RANGE[2024-01-01,MAX]" in adv

    async def test_date_max_only(self):
        q = TrialQuery(
            date_field=DateField.COMPLETION,
            max_date="2025-12-31",
            expand_synonyms=False,
        )
        params = await convert_query(q)
        adv = params["filter.advanced"][0]
        assert "RANGE[MIN,2025-12-31]" in adv

    async def test_date_field_without_dates_ignored(self):
        q = TrialQuery(
            date_field=DateField.LAST_UPDATE,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert "filter.advanced" not in params


class TestConvertQueryAdvancedFilters:
    """Test study_type, intervention_type, sponsor_type, etc."""

    async def test_study_type(self):
        q = TrialQuery(
            study_type=StudyType.INTERVENTIONAL,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        adv = params["filter.advanced"][0]
        assert "AREA[StudyType]Interventional" in adv

    async def test_intervention_type(self):
        q = TrialQuery(
            intervention_type=InterventionType.DRUG,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        adv = params["filter.advanced"][0]
        assert "AREA[InterventionType]Drug" in adv

    async def test_sponsor_type(self):
        q = TrialQuery(
            sponsor_type=SponsorType.INDUSTRY,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        adv = params["filter.advanced"][0]
        assert "AREA[SponsorType]Industry" in adv

    async def test_study_design(self):
        q = TrialQuery(
            study_design=StudyDesign.RANDOMIZED,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        adv = params["filter.advanced"][0]
        assert "AREA[StudyDesign]Randomized" in adv

    async def test_primary_purpose(self):
        q = TrialQuery(
            primary_purpose=PrimaryPurpose.TREATMENT,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        adv = params["filter.advanced"][0]
        assert (
            "AREA[DesignPrimaryPurpose]Treatment" in adv
        )

    async def test_multiple_advanced_filters_and_joined(
        self,
    ):
        q = TrialQuery(
            study_type=StudyType.INTERVENTIONAL,
            phase=TrialPhase.PHASE3,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        adv = params["filter.advanced"][0]
        assert " AND " in adv
        assert "AREA[StudyType]" in adv
        assert "AREA[Phase]" in adv


class TestConvertQueryAgeGroup:
    """Test age group filtering."""

    async def test_child(self):
        q = TrialQuery(
            age_group=AgeGroup.CHILD,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        adv = params["filter.advanced"][0]
        assert "AREA[StdAge]Child" in adv

    async def test_senior(self):
        q = TrialQuery(
            age_group=AgeGroup.SENIOR,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        adv = params["filter.advanced"][0]
        assert "AREA[StdAge]Older Adult" in adv

    async def test_all_no_filter(self):
        q = TrialQuery(
            age_group=AgeGroup.ALL,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        # ALL should not produce an age filter
        assert "filter.advanced" not in params


class TestConvertQueryEligibility:
    """Test eligibility-based Essie fragment injection."""

    async def test_prior_therapies_in_query_term(self):
        q = TrialQuery(
            prior_therapies=["cisplatin"],
            expand_synonyms=False,
        )
        params = await convert_query(q)
        term = params["query.term"][0]
        assert "cisplatin" in term
        assert "AREA[EligibilityCriteria]" in term

    async def test_required_mutations(self):
        q = TrialQuery(
            required_mutations=["BRAF V600E"],
            expand_synonyms=False,
        )
        params = await convert_query(q)
        term = params["query.term"][0]
        assert '"BRAF V600E"' in term

    async def test_excluded_mutations(self):
        q = TrialQuery(
            excluded_mutations=["KRAS G12C"],
            expand_synonyms=False,
        )
        params = await convert_query(q)
        term = params["query.term"][0]
        assert 'NOT "KRAS G12C"' in term

    async def test_biomarker_expression(self):
        q = TrialQuery(
            biomarker_expression={"PD-L1": ">=50%"},
            expand_synonyms=False,
        )
        params = await convert_query(q)
        term = params["query.term"][0]
        assert '"PD-L1"' in term
        assert '">=50%"' in term

    async def test_line_of_therapy(self):
        q = TrialQuery(
            line_of_therapy=LineOfTherapy.FIRST_LINE,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        term = params["query.term"][0]
        assert '"first line"' in term

    async def test_brain_mets_disallowed(self):
        q = TrialQuery(
            allow_brain_mets=False,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        term = params["query.term"][0]
        assert 'NOT "brain metastases"' in term

    async def test_brain_mets_allowed_no_fragment(self):
        q = TrialQuery(
            allow_brain_mets=True,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        # allow=True produces no fragment
        assert "query.term" not in params

    async def test_essie_appended_to_existing_terms(self):
        q = TrialQuery(
            terms=["oncology"],
            prior_therapies=["cisplatin"],
            expand_synonyms=False,
        )
        params = await convert_query(q)
        term = params["query.term"][0]
        assert "oncology" in term
        assert " AND " in term
        assert "cisplatin" in term

    async def test_multiple_essie_fragments_combined(self):
        q = TrialQuery(
            prior_therapies=["cisplatin"],
            required_mutations=["BRAF V600E"],
            expand_synonyms=False,
        )
        params = await convert_query(q)
        term = params["query.term"][0]
        assert " AND " in term
        assert "cisplatin" in term
        assert "BRAF V600E" in term


class TestConvertQuerySort:
    """Test sort order."""

    async def test_default_relevance(self):
        q = TrialQuery(expand_synonyms=False)
        params = await convert_query(q)
        assert params["sort"] == ["@relevance"]

    async def test_enrollment_sort(self):
        q = TrialQuery(
            sort=SortOrder.ENROLLMENT,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert params["sort"] == ["EnrollmentCount:desc"]

    async def test_start_date_sort(self):
        q = TrialQuery(
            sort=SortOrder.START_DATE,
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert params["sort"] == ["StudyStartDate:desc"]


class TestConvertQueryReturnFields:
    """Test custom return fields."""

    async def test_custom_fields(self):
        q = TrialQuery(
            return_fields=["NCT Number", "Study Title"],
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert params["fields"] == [
            "NCT Number,Study Title"
        ]

    async def test_default_fields(self):
        q = TrialQuery(expand_synonyms=False)
        params = await convert_query(q)
        assert params["fields"] == SEARCH_FIELDS_PARAM


class TestConvertQueryNctIds:
    """Test NCT ID handling and intersection logic."""

    async def test_nct_ids_only_uses_query_id(self):
        q = TrialQuery(
            nct_ids=["NCT00000001"],
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert "query.id" in params
        assert params["query.id"] == ["NCT00000001"]

    @patch(MOCK_SYNONYMS_PATH, new_callable=AsyncMock)
    async def test_nct_ids_with_condition_uses_filter(
        self, mock_syn
    ):
        mock_syn.return_value = ["lung cancer"]
        q = TrialQuery(
            nct_ids=["NCT00000001"],
            conditions=["lung cancer"],
            expand_synonyms=True,
        )
        params = await convert_query(q)
        assert "filter.ids" in params

    async def test_nct_ids_with_condition_no_synonyms(
        self,
    ):
        q = TrialQuery(
            nct_ids=["NCT00000001"],
            conditions=["lung cancer"],
            expand_synonyms=False,
        )
        params = await convert_query(q)
        assert "filter.ids" in params


class TestConvertQueryComplex:
    """Test complex multi-parameter queries."""

    @patch(MOCK_SYNONYMS_PATH, new_callable=AsyncMock)
    async def test_full_oncology_query(self, mock_syn):
        mock_syn.return_value = [
            "breast cancer",
            "breast neoplasm",
        ]
        q = TrialQuery(
            conditions=["breast cancer"],
            interventions=["pembrolizumab"],
            phase=TrialPhase.PHASE3,
            recruiting_status=RecruitingStatus.OPEN,
            study_type=StudyType.INTERVENTIONAL,
            primary_purpose=PrimaryPurpose.TREATMENT,
            age_group=AgeGroup.ADULT,
            sort=SortOrder.RELEVANCE,
            page_size=20,
            expand_synonyms=True,
        )
        params = await convert_query(q)
        assert "query.cond" in params
        assert "query.intr" in params
        assert "filter.advanced" in params
        assert params["pageSize"] == ["20"]
        adv = params["filter.advanced"][0]
        assert "AREA[Phase]" in adv
        assert "AREA[StudyType]" in adv
        assert (
            "AREA[DesignPrimaryPurpose]Treatment" in adv
        )
        assert "AREA[StdAge]Adult" in adv


# ─── search_trials() ──────────────────────────────────


class TestSearchTrials:
    """Test search_trials with mocked HTTP."""

    @patch(
        "czechmedmcp.trials.search.http_client.request_api",
        new_callable=AsyncMock,
    )
    @patch(
        "czechmedmcp.trials.search.render.to_markdown",
    )
    async def test_success_returns_markdown(
        self, mock_render, mock_api
    ):
        mock_api.return_value = (
            {"studies": [{"nctId": "NCT001"}]},
            None,
        )
        mock_render.return_value = "# Results\n- NCT001"
        q = TrialQuery(
            conditions=["diabetes"],
            expand_synonyms=False,
        )
        result = await search_trials(q)
        assert result == "# Results\n- NCT001"
        mock_render.assert_called_once()

    @patch(
        "czechmedmcp.trials.search.http_client.request_api",
        new_callable=AsyncMock,
    )
    async def test_success_json_output(self, mock_api):
        data = {"studies": [{"nctId": "NCT001"}]}
        mock_api.return_value = (data, None)
        q = TrialQuery(
            conditions=["diabetes"],
            expand_synonyms=False,
        )
        result = await search_trials(q, output_json=True)
        parsed = json.loads(result)
        assert parsed["studies"][0]["nctId"] == "NCT001"

    @patch(
        "czechmedmcp.trials.search.http_client.request_api",
        new_callable=AsyncMock,
    )
    async def test_api_error_returns_error_json(
        self, mock_api
    ):
        from czechmedmcp.http_client import RequestError

        err = RequestError(code=500, message="Server Error")
        mock_api.return_value = (None, err)
        q = TrialQuery(
            conditions=["diabetes"],
            expand_synonyms=False,
        )
        result = await search_trials(q, output_json=True)
        parsed = json.loads(result)
        assert "error" in parsed
        assert "500" in parsed["error"]

    @patch(
        "czechmedmcp.trials.search.http_client.request_api",
        new_callable=AsyncMock,
    )
    async def test_empty_response_json(self, mock_api):
        mock_api.return_value = (None, None)
        q = TrialQuery(expand_synonyms=False)
        result = await search_trials(q, output_json=True)
        assert result == "null"

    @patch(
        "czechmedmcp.trials.search.http_client.request_api",
        new_callable=AsyncMock,
    )
    @patch(
        "czechmedmcp.trials.search.render.to_markdown",
    )
    async def test_calls_api_with_correct_url(
        self, mock_render, mock_api
    ):
        mock_api.return_value = ({"studies": []}, None)
        mock_render.return_value = ""
        q = TrialQuery(expand_synonyms=False)
        await search_trials(q)
        call_kwargs = mock_api.call_args
        assert (
            "clinicaltrials.gov" in call_kwargs.kwargs["url"]
        )
        assert call_kwargs.kwargs["method"] == "GET"
        assert call_kwargs.kwargs["domain"] == "trial"

    @patch(
        "czechmedmcp.trials.search.http_client.request_api",
        new_callable=AsyncMock,
    )
    @patch(
        "czechmedmcp.trials.search.render.to_markdown",
    )
    async def test_error_with_markdown_output(
        self, mock_render, mock_api
    ):
        from czechmedmcp.http_client import RequestError

        err = RequestError(code=404, message="Not found")
        mock_api.return_value = (None, err)
        q = TrialQuery(expand_synonyms=False)
        result = await search_trials(
            q, output_json=False
        )
        # With error + not output_json, data becomes
        # {"error": ...} and goes through to_markdown
        mock_render.assert_called_once()


# ─── Enum tests ────────────────────────────────────────


class TestEnums:
    """Test enum values and mappings."""

    def test_sort_order_values(self):
        assert SortOrder.RELEVANCE == "RELEVANCE"
        assert SortOrder.ENROLLMENT == "ENROLLMENT"

    def test_trial_phase_values(self):
        assert TrialPhase.PHASE1 == "PHASE1"
        assert TrialPhase.PHASE4 == "PHASE4"

    def test_recruiting_status_values(self):
        assert RecruitingStatus.OPEN == "OPEN"
        assert RecruitingStatus.CLOSED == "CLOSED"
        assert RecruitingStatus.ANY == "ANY"

    def test_open_statuses_tuple(self):
        assert "RECRUITING" in OPEN_STATUSES
        assert "NOT_YET_RECRUITING" in OPEN_STATUSES

    def test_closed_statuses_tuple(self):
        assert "COMPLETED" in CLOSED_STATUSES
        assert "TERMINATED" in CLOSED_STATUSES

    def test_line_of_therapy_patterns(self):
        patterns = LINE_OF_THERAPY_PATTERNS
        assert LineOfTherapy.FIRST_LINE in patterns
        assert any(
            "first line" in p
            for p in patterns[LineOfTherapy.FIRST_LINE]
        )
