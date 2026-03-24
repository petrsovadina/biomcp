"""Tests for VariantQuery gene-only validation.

Gene-only queries to MyVariant.info return too many results and
timeout.  The VariantQuery model validator must reject them with
a helpful message while still allowing narrowed gene queries.
"""

import pytest

from czechmedmcp.variants.search import VariantQuery


class TestGeneOnlyValidation:
    """Gene-only queries must be rejected."""

    def test_gene_only_raises(self):
        with pytest.raises(ValueError, match="too many results"):
            VariantQuery(gene="TP53")

    def test_gene_with_significance_only_raises(self):
        """significance alone does not narrow enough."""
        with pytest.raises(ValueError, match="too many results"):
            VariantQuery(
                gene="BRAF", significance="pathogenic"
            )

    def test_gene_with_polyphen_passes(self):
        """polyphen narrows results sufficiently."""
        q = VariantQuery(gene="EGFR", polyphen="D")
        assert q.gene == "EGFR"

    def test_gene_with_sift_passes(self):
        """sift narrows results sufficiently."""
        q = VariantQuery(gene="EGFR", sift="D")
        assert q.gene == "EGFR"


class TestNarrowedGeneQueries:
    """Gene combined with narrowing params must pass."""

    def test_gene_plus_hgvsp(self):
        q = VariantQuery(gene="BRAF", hgvsp="V600E")
        assert q.gene == "BRAF"
        assert q.hgvsp == "V600E"

    def test_gene_plus_hgvsc(self):
        q = VariantQuery(gene="BRAF", hgvsc="c.1799T>A")
        assert q.gene == "BRAF"

    def test_gene_plus_rsid(self):
        q = VariantQuery(gene="BRAF", rsid="rs113488022")
        assert q.gene == "BRAF"

    def test_gene_plus_region(self):
        q = VariantQuery(
            gene="BRAF", region="chr7:140753336-140753337"
        )
        assert q.gene == "BRAF"

    def test_gene_plus_max_frequency(self):
        q = VariantQuery(gene="TP53", max_frequency=0.01)
        assert q.gene == "TP53"

    def test_gene_plus_cadd(self):
        q = VariantQuery(gene="TP53", cadd=20.0)
        assert q.gene == "TP53"


class TestNonGeneQueries:
    """Queries without gene must still work."""

    def test_rsid_only(self):
        q = VariantQuery(rsid="rs113488022")
        assert q.rsid == "rs113488022"

    def test_region_only(self):
        q = VariantQuery(region="chr7:140753336-140753337")
        assert q.region is not None

    def test_hgvsp_only(self):
        q = VariantQuery(hgvsp="V600E")
        assert q.hgvsp == "V600E"

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="At least one"):
            VariantQuery()
