"""Comprehensive tests for the query_parser module."""

from czechmedmcp.query_parser import (
    FieldDefinition,
    FieldType,
    Operator,
    ParsedQuery,
    QueryParser,
    QueryTerm,
)


class TestOperatorEnum:
    """Test the Operator enum values."""

    def test_operator_values(self):
        """All operator values match expected strings."""
        assert Operator.EQ == ":"
        assert Operator.GT == ">"
        assert Operator.LT == "<"
        assert Operator.GTE == ">="
        assert Operator.LTE == "<="
        assert Operator.RANGE == ".."
        assert Operator.AND == "AND"
        assert Operator.OR == "OR"
        assert Operator.NOT == "NOT"

    def test_operator_is_str_enum(self):
        """Operator members are strings."""
        for op in Operator:
            assert isinstance(op, str)


class TestFieldTypeEnum:
    """Test the FieldType enum values."""

    def test_field_type_values(self):
        """All field type values match expected strings."""
        assert FieldType.STRING == "string"
        assert FieldType.NUMBER == "number"
        assert FieldType.DATE == "date"
        assert FieldType.ENUM == "enum"
        assert FieldType.BOOLEAN == "boolean"


class TestFieldDefinition:
    """Test the FieldDefinition dataclass."""

    def test_basic_creation(self):
        """Create a FieldDefinition with required fields."""
        fd = FieldDefinition(
            name="gene",
            domain="cross",
            type=FieldType.STRING,
            operators=[Operator.EQ],
            example_values=["BRAF"],
            description="Gene symbol",
            underlying_api_field="gene",
        )
        assert fd.name == "gene"
        assert fd.domain == "cross"
        assert fd.aliases is None

    def test_with_aliases(self):
        """Create a FieldDefinition with aliases."""
        fd = FieldDefinition(
            name="gene",
            domain="cross",
            type=FieldType.STRING,
            operators=[Operator.EQ],
            example_values=["BRAF"],
            description="Gene symbol",
            underlying_api_field="gene",
            aliases=["g", "gene_symbol"],
        )
        assert fd.aliases == ["g", "gene_symbol"]


class TestQueryTerm:
    """Test the QueryTerm dataclass."""

    def test_defaults(self):
        """QueryTerm defaults: domain=None, is_negated=False."""
        qt = QueryTerm(
            field="gene",
            operator=Operator.EQ,
            value="BRAF",
        )
        assert qt.domain is None
        assert qt.is_negated is False

    def test_with_domain_and_negation(self):
        """QueryTerm with explicit domain and negation."""
        qt = QueryTerm(
            field="gene",
            operator=Operator.EQ,
            value="TP53",
            domain="cross",
            is_negated=True,
        )
        assert qt.domain == "cross"
        assert qt.is_negated is True


class TestParsedQuery:
    """Test the ParsedQuery dataclass."""

    def test_creation(self):
        """Create a ParsedQuery with all fields."""
        pq = ParsedQuery(
            terms=[],
            cross_domain_fields={},
            domain_specific_fields={"trials": {}},
            raw_query="test",
        )
        assert pq.raw_query == "test"
        assert pq.terms == []


class TestQueryParserInit:
    """Test QueryParser initialization."""

    def test_field_registry_built(self):
        """Parser builds field registry on init."""
        parser = QueryParser()
        assert isinstance(parser.field_registry, dict)
        assert len(parser.field_registry) > 0

    def test_cross_domain_fields_registered(self):
        """Cross-domain fields are in the registry."""
        parser = QueryParser()
        assert "gene" in parser.field_registry
        assert "variant" in parser.field_registry
        assert "disease" in parser.field_registry

    def test_cross_domain_field_properties(self):
        """Cross-domain fields have domain='cross'."""
        parser = QueryParser()
        gene = parser.field_registry["gene"]
        assert gene.domain == "cross"
        assert gene.type == FieldType.STRING

    def test_trial_fields_registered(self):
        """Trial-specific fields are in the registry."""
        parser = QueryParser()
        for name in [
            "trials.condition",
            "trials.intervention",
            "trials.phase",
            "trials.status",
        ]:
            assert name in parser.field_registry
            fd = parser.field_registry[name]
            assert fd.domain == "trials"

    def test_article_fields_registered(self):
        """Article-specific fields are in the registry."""
        parser = QueryParser()
        for name in [
            "articles.title",
            "articles.author",
            "articles.journal",
            "articles.date",
        ]:
            assert name in parser.field_registry
            fd = parser.field_registry[name]
            assert fd.domain == "articles"

    def test_variant_fields_registered(self):
        """Variant-specific fields are in the registry."""
        parser = QueryParser()
        for name in [
            "variants.rsid",
            "variants.gene",
            "variants.significance",
            "variants.frequency",
        ]:
            assert name in parser.field_registry
            fd = parser.field_registry[name]
            assert fd.domain == "variants"

    def test_gene_fields_registered(self):
        """Gene-specific fields are in the registry."""
        parser = QueryParser()
        for name in [
            "genes.symbol",
            "genes.name",
            "genes.type",
        ]:
            assert name in parser.field_registry
            fd = parser.field_registry[name]
            assert fd.domain == "genes"

    def test_drug_fields_registered(self):
        """Drug-specific fields are in the registry."""
        parser = QueryParser()
        for name in [
            "drugs.name",
            "drugs.tradename",
            "drugs.indication",
        ]:
            assert name in parser.field_registry
            fd = parser.field_registry[name]
            assert fd.domain == "drugs"

    def test_disease_fields_registered(self):
        """Disease-specific fields are in the registry."""
        parser = QueryParser()
        for name in [
            "diseases.name",
            "diseases.mondo",
            "diseases.synonym",
        ]:
            assert name in parser.field_registry
            fd = parser.field_registry[name]
            assert fd.domain == "diseases"

    def test_total_field_count(self):
        """Registry has expected total field count."""
        parser = QueryParser()
        # 3 cross + 4 trials + 4 articles + 4 variants
        # + 3 genes + 3 drugs + 3 diseases = 24
        assert len(parser.field_registry) == 24


class TestTokenizer:
    """Test the _tokenize method."""

    def test_simple_token(self):
        """Single field:value is one token."""
        parser = QueryParser()
        tokens = parser._tokenize("gene:BRAF")
        assert tokens == ["gene:BRAF"]

    def test_multiple_tokens(self):
        """Multiple space-separated terms."""
        parser = QueryParser()
        tokens = parser._tokenize(
            "gene:BRAF trials.phase:3"
        )
        assert tokens == ["gene:BRAF", "trials.phase:3"]

    def test_quoted_value_preserved(self):
        """Quoted values with spaces stay as one token."""
        parser = QueryParser()
        tokens = parser._tokenize(
            'disease:"lung cancer"'
        )
        assert len(tokens) == 1
        assert tokens[0] == 'disease:"lung cancer"'

    def test_and_operator_filtered(self):
        """AND operator is filtered from tokens."""
        parser = QueryParser()
        tokens = parser._tokenize(
            "gene:BRAF AND disease:melanoma"
        )
        assert "AND" not in tokens
        assert "gene:BRAF" in tokens
        assert "disease:melanoma" in tokens

    def test_or_operator_filtered(self):
        """OR operator is filtered from tokens."""
        parser = QueryParser()
        tokens = parser._tokenize(
            "gene:BRAF OR gene:TP53"
        )
        assert "OR" not in tokens
        assert len(tokens) == 2

    def test_not_operator_filtered(self):
        """NOT operator is filtered from tokens."""
        parser = QueryParser()
        tokens = parser._tokenize(
            "gene:BRAF NOT disease:melanoma"
        )
        assert "NOT" not in tokens
        assert len(tokens) == 2

    def test_empty_string(self):
        """Empty string yields no tokens."""
        parser = QueryParser()
        tokens = parser._tokenize("")
        assert tokens == []

    def test_whitespace_only(self):
        """Whitespace-only string yields no tokens."""
        parser = QueryParser()
        tokens = parser._tokenize("   ")
        assert tokens == []

    def test_multiple_spaces_between_tokens(self):
        """Multiple spaces between tokens are handled."""
        parser = QueryParser()
        tokens = parser._tokenize("gene:BRAF    disease:cancer")
        assert tokens == ["gene:BRAF", "disease:cancer"]

    def test_mixed_operators(self):
        """Multiple operators filtered correctly."""
        parser = QueryParser()
        tokens = parser._tokenize(
            "gene:BRAF AND disease:melanoma OR trials.phase:3"
        )
        assert tokens == [
            "gene:BRAF",
            "disease:melanoma",
            "trials.phase:3",
        ]

    def test_quoted_value_with_colon(self):
        """Quoted value containing colon."""
        parser = QueryParser()
        tokens = parser._tokenize(
            'diseases.mondo:"MONDO:0005105"'
        )
        assert len(tokens) == 1


class TestParse:
    """Test the parse method."""

    def test_single_cross_domain_field(self):
        """Parse a single cross-domain field."""
        parser = QueryParser()
        result = parser.parse("gene:BRAF")

        assert isinstance(result, ParsedQuery)
        assert result.raw_query == "gene:BRAF"
        assert len(result.terms) == 1

        term = result.terms[0]
        assert term.field == "gene"
        assert term.operator == Operator.EQ
        assert term.value == "BRAF"
        assert term.domain == "cross"

    def test_cross_domain_in_cross_domain_fields(self):
        """Cross-domain terms populate cross_domain_fields."""
        parser = QueryParser()
        result = parser.parse("gene:BRAF")

        assert result.cross_domain_fields == {"gene": "BRAF"}

    def test_domain_specific_field(self):
        """Parse a domain-specific field."""
        parser = QueryParser()
        result = parser.parse("trials.condition:melanoma")

        assert len(result.terms) == 1
        term = result.terms[0]
        assert term.field == "trials.condition"
        assert term.value == "melanoma"
        assert term.domain == "trials"

    def test_domain_specific_in_domain_fields(self):
        """Domain-specific terms populate domain_specific_fields."""
        parser = QueryParser()
        result = parser.parse("trials.condition:melanoma")

        assert "condition" in result.domain_specific_fields["trials"]
        assert (
            result.domain_specific_fields["trials"]["condition"]
            == "melanoma"
        )

    def test_multiple_fields_mixed_domains(self):
        """Parse multiple fields across domains."""
        parser = QueryParser()
        result = parser.parse(
            "gene:BRAF trials.condition:melanoma"
        )

        assert len(result.terms) == 2
        assert result.cross_domain_fields == {"gene": "BRAF"}
        assert (
            result.domain_specific_fields["trials"]["condition"]
            == "melanoma"
        )

    def test_quoted_value_stripped(self):
        """Quoted values have quotes stripped."""
        parser = QueryParser()
        result = parser.parse('disease:"lung cancer"')

        assert len(result.terms) == 1
        assert result.terms[0].value == "lung cancer"
        assert (
            result.cross_domain_fields["disease"]
            == "lung cancer"
        )

    def test_unknown_field_ignored(self):
        """Unknown field:value pairs are not parsed."""
        parser = QueryParser()
        result = parser.parse("unknown_field:value")

        assert len(result.terms) == 0
        assert result.cross_domain_fields == {}

    def test_empty_query(self):
        """Empty query produces empty ParsedQuery."""
        parser = QueryParser()
        result = parser.parse("")

        assert result.terms == []
        assert result.cross_domain_fields == {}
        assert result.raw_query == ""

    def test_only_operators(self):
        """Query with only operators produces empty terms."""
        parser = QueryParser()
        result = parser.parse("AND OR NOT")

        assert result.terms == []

    def test_token_without_colon_ignored(self):
        """Tokens without colon separator are ignored."""
        parser = QueryParser()
        result = parser.parse("melanoma")

        assert result.terms == []

    def test_all_domain_specific_keys_present(self):
        """ParsedQuery always has all domain keys."""
        parser = QueryParser()
        result = parser.parse("gene:BRAF")

        expected_domains = {
            "trials",
            "articles",
            "variants",
            "genes",
            "drugs",
            "diseases",
        }
        assert (
            set(result.domain_specific_fields.keys())
            == expected_domains
        )

    def test_article_fields(self):
        """Parse article-specific fields."""
        parser = QueryParser()
        result = parser.parse(
            "articles.author:Smith articles.journal:Nature"
        )

        assert len(result.terms) == 2
        arts = result.domain_specific_fields["articles"]
        assert arts["author"] == "Smith"
        assert arts["journal"] == "Nature"

    def test_variant_fields(self):
        """Parse variant-specific fields."""
        parser = QueryParser()
        result = parser.parse(
            "variants.rsid:rs113488022"
        )

        assert len(result.terms) == 1
        vs = result.domain_specific_fields["variants"]
        assert vs["rsid"] == "rs113488022"

    def test_gene_fields(self):
        """Parse gene-specific fields."""
        parser = QueryParser()
        result = parser.parse("genes.symbol:TP53")

        gs = result.domain_specific_fields["genes"]
        assert gs["symbol"] == "TP53"

    def test_drug_fields(self):
        """Parse drug-specific fields."""
        parser = QueryParser()
        result = parser.parse("drugs.name:imatinib")

        ds = result.domain_specific_fields["drugs"]
        assert ds["name"] == "imatinib"

    def test_disease_fields(self):
        """Parse disease-specific fields."""
        parser = QueryParser()
        result = parser.parse("diseases.name:melanoma")

        ds = result.domain_specific_fields["diseases"]
        assert ds["name"] == "melanoma"

    def test_complex_query(self):
        """Parse a complex multi-domain query with AND."""
        parser = QueryParser()
        result = parser.parse(
            "gene:BRAF AND trials.condition:melanoma "
            "AND articles.journal:Nature"
        )

        assert len(result.terms) == 3
        assert result.cross_domain_fields["gene"] == "BRAF"
        assert (
            result.domain_specific_fields["trials"]["condition"]
            == "melanoma"
        )
        assert (
            result.domain_specific_fields["articles"]["journal"]
            == "Nature"
        )

    def test_special_characters_in_value(self):
        """Values with special characters are preserved."""
        parser = QueryParser()
        result = parser.parse(
            "variants.rsid:rs121913529"
        )

        assert result.terms[0].value == "rs121913529"

    def test_colon_in_value(self):
        """Value containing colon (e.g. MONDO ID)."""
        parser = QueryParser()
        # diseases.mondo:MONDO:0005105 -> field="diseases.mondo"
        # value="MONDO:0005105" (split on first colon)
        result = parser.parse(
            "diseases.mondo:MONDO:0005105"
        )

        assert len(result.terms) == 1
        assert result.terms[0].value == "MONDO:0005105"

    def test_multiple_cross_domain_fields(self):
        """Multiple cross-domain fields parsed together."""
        parser = QueryParser()
        result = parser.parse(
            "gene:EGFR variant:L858R disease:lung"
        )

        assert len(result.terms) == 3
        assert result.cross_domain_fields["gene"] == "EGFR"
        assert result.cross_domain_fields["variant"] == "L858R"
        assert result.cross_domain_fields["disease"] == "lung"

    def test_same_domain_multiple_fields(self):
        """Multiple fields from the same domain."""
        parser = QueryParser()
        result = parser.parse(
            "trials.condition:melanoma "
            "trials.phase:3 "
            "trials.status:recruiting"
        )

        assert len(result.terms) == 3
        trials = result.domain_specific_fields["trials"]
        assert trials["condition"] == "melanoma"
        assert trials["phase"] == "3"
        assert trials["status"] == "recruiting"


class TestGetSchema:
    """Test the get_schema method."""

    def test_schema_has_required_keys(self):
        """Schema contains all top-level keys."""
        parser = QueryParser()
        schema = parser.get_schema()

        assert "domains" in schema
        assert "cross_domain_fields" in schema
        assert "domain_fields" in schema
        assert "operators" in schema
        assert "examples" in schema

    def test_schema_domains_list(self):
        """Schema lists all expected domains."""
        parser = QueryParser()
        schema = parser.get_schema()

        expected = [
            "trials",
            "articles",
            "variants",
            "genes",
            "drugs",
            "diseases",
        ]
        assert schema["domains"] == expected

    def test_schema_operators(self):
        """Schema lists all operator values."""
        parser = QueryParser()
        schema = parser.get_schema()

        expected_ops = [op.value for op in Operator]
        assert schema["operators"] == expected_ops

    def test_schema_cross_domain_fields(self):
        """Schema includes cross-domain field info."""
        parser = QueryParser()
        schema = parser.get_schema()

        cdf = schema["cross_domain_fields"]
        assert "gene" in cdf
        assert "variant" in cdf
        assert "disease" in cdf

        gene_info = cdf["gene"]
        assert gene_info["type"] == "string"
        assert "description" in gene_info
        assert "examples" in gene_info
        assert "operators" in gene_info

    def test_schema_domain_fields_structure(self):
        """Schema has domain_fields for each domain."""
        parser = QueryParser()
        schema = parser.get_schema()

        df = schema["domain_fields"]
        for domain in [
            "trials",
            "articles",
            "variants",
            "genes",
            "drugs",
            "diseases",
        ]:
            assert domain in df
            assert isinstance(df[domain], dict)

    def test_schema_trials_fields(self):
        """Schema trial fields use short names."""
        parser = QueryParser()
        schema = parser.get_schema()

        trials = schema["domain_fields"]["trials"]
        assert "condition" in trials
        assert "intervention" in trials
        assert "phase" in trials
        assert "status" in trials

    def test_schema_articles_fields(self):
        """Schema article fields use short names."""
        parser = QueryParser()
        schema = parser.get_schema()

        articles = schema["domain_fields"]["articles"]
        assert "title" in articles
        assert "author" in articles
        assert "journal" in articles
        assert "date" in articles

    def test_schema_field_info_structure(self):
        """Each field info has type, operators, examples, desc."""
        parser = QueryParser()
        schema = parser.get_schema()

        for domain_fields in schema["domain_fields"].values():
            for field_info in domain_fields.values():
                assert "type" in field_info
                assert "operators" in field_info
                assert "examples" in field_info
                assert "description" in field_info

    def test_schema_examples_non_empty(self):
        """Schema has at least one example query."""
        parser = QueryParser()
        schema = parser.get_schema()

        assert len(schema["examples"]) > 0
        for example in schema["examples"]:
            assert isinstance(example, str)
            assert len(example) > 0

    def test_schema_date_field_type(self):
        """articles.date field has type 'date'."""
        parser = QueryParser()
        schema = parser.get_schema()

        date_info = schema["domain_fields"]["articles"]["date"]
        assert date_info["type"] == "date"

    def test_schema_enum_field_type(self):
        """trials.phase field has type 'enum'."""
        parser = QueryParser()
        schema = parser.get_schema()

        phase_info = schema["domain_fields"]["trials"]["phase"]
        assert phase_info["type"] == "enum"

    def test_schema_number_field_type(self):
        """variants.frequency field has type 'number'."""
        parser = QueryParser()
        schema = parser.get_schema()

        freq_info = (
            schema["domain_fields"]["variants"]["frequency"]
        )
        assert freq_info["type"] == "number"


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_parse_preserves_raw_query(self):
        """raw_query is always the original input string."""
        parser = QueryParser()
        raw = "  gene:BRAF  AND  disease:melanoma  "
        result = parser.parse(raw)
        assert result.raw_query == raw

    def test_unicode_in_value(self):
        """Unicode characters in values are preserved."""
        parser = QueryParser()
        result = parser.parse("disease:leukemie")
        # Not a known field value issue - just no terms
        # because 'disease' IS a known field
        assert len(result.terms) == 1
        assert result.terms[0].value == "leukemie"

    def test_numeric_value(self):
        """Numeric values are stored as strings."""
        parser = QueryParser()
        result = parser.parse("trials.phase:3")

        assert result.terms[0].value == "3"
        assert isinstance(result.terms[0].value, str)

    def test_empty_value_after_colon(self):
        """Field with empty value after colon."""
        parser = QueryParser()
        result = parser.parse("gene:")

        # gene is a known field, value is empty string
        assert len(result.terms) == 1
        assert result.terms[0].value == ""

    def test_multiple_colons_in_token(self):
        """Token with multiple colons splits on first."""
        parser = QueryParser()
        result = parser.parse(
            "diseases.mondo:MONDO:0005105"
        )
        term = result.terms[0]
        assert term.field == "diseases.mondo"
        assert term.value == "MONDO:0005105"

    def test_parser_reusable(self):
        """Same parser instance can parse multiple queries."""
        parser = QueryParser()

        r1 = parser.parse("gene:BRAF")
        r2 = parser.parse("disease:melanoma")

        assert r1.terms[0].value == "BRAF"
        assert r2.terms[0].value == "melanoma"

    def test_very_long_value(self):
        """Very long values are handled."""
        parser = QueryParser()
        long_val = "x" * 10000
        result = parser.parse(f"gene:{long_val}")

        assert result.terms[0].value == long_val

    def test_whitespace_in_unquoted_value(self):
        """Unquoted multi-word value splits into tokens."""
        parser = QueryParser()
        # "disease:lung cancer" without quotes ->
        # tokens: ["disease:lung", "cancer"]
        # only "disease:lung" is parsed (cancer has no colon)
        result = parser.parse("disease:lung cancer")

        assert len(result.terms) == 1
        assert result.terms[0].value == "lung"

    def test_operator_as_field_value(self):
        """Operator words as values are not filtered."""
        parser = QueryParser()
        # gene:AND -> field=gene, value=AND
        result = parser.parse("gene:AND")

        assert len(result.terms) == 1
        assert result.terms[0].value == "AND"

    def test_term_operator_always_eq(self):
        """Parsed terms always use EQ operator."""
        parser = QueryParser()
        result = parser.parse(
            "gene:BRAF trials.condition:melanoma "
            "variants.rsid:rs113488022"
        )
        for term in result.terms:
            assert term.operator == Operator.EQ
